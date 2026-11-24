"""Extract, validate, transform, and load housing-supply data."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

LOGGER = logging.getLogger("housing_pipeline")

COLUMN_MAP = {
    "Provinsi": "province",
    "Kabupaten": "regency",
    "Asosiasi": "association",
    "Kecamatan": "district",
    "Pengembang": "developer",
    "Nama Perumahan": "housing_name",
    "tipeRumah": "housing_type",
    "Subsidi-Kavling": "subsidized_land",
    "Subsidi-Pembangunan": "subsidized_under_construction",
    "Subsidi-Dibooking": "subsidized_booked",
    "Subsidi-Ready": "subsidized_ready",
    "Subsidi-Terjual": "subsidized_sold",
    "Komersil": "commercial_land",
    "Komersil-Pembangunan": "commercial_under_construction",
    "Komersil-Dibooking": "commercial_booked",
    "Komersil-Tersedia": "commercial_available",
    "Komersil-Terjual": "commercial_sold",
    "updatedAt: Month": "updated_month",
}

TEXT_COLUMNS = [
    "province",
    "regency",
    "association",
    "district",
    "developer",
    "housing_name",
    "housing_type",
]
NUMERIC_COLUMNS = [
    "subsidized_land",
    "subsidized_under_construction",
    "subsidized_booked",
    "subsidized_ready",
    "subsidized_sold",
    "commercial_land",
    "commercial_under_construction",
    "commercial_booked",
    "commercial_available",
    "commercial_sold",
]


def read_source(path: Path, sheet_name: str = "Query result") -> pd.DataFrame:
    """Read the expected worksheet from the source Excel workbook."""
    if not path.is_file():
        raise FileNotFoundError(f"Source file tidak ditemukan: {path}")
    LOGGER.info("Membaca %s (sheet=%s)", path, sheet_name)
    return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")


def transform(source: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Validate and normalize source records, returning data plus quality metrics."""
    missing_columns = sorted(set(COLUMN_MAP) - set(source.columns))
    if missing_columns:
        raise ValueError(f"Kolom wajib tidak ditemukan: {', '.join(missing_columns)}")

    data = source[list(COLUMN_MAP)].rename(columns=COLUMN_MAP).copy()
    source_rows = len(data)

    for column in TEXT_COLUMNS:
        data[column] = data[column].astype("string").str.strip()
        data[column] = data[column].replace("", pd.NA)

    # Asosiasi adalah satu-satunya atribut yang kosong pada sumber. Nilai kosong
    # dipertahankan secara informatif, bukan dihapus bersama seluruh baris.
    association_missing = int(data["association"].isna().sum())
    data["association"] = data["association"].fillna("TIDAK_DIKETAHUI")

    required_text = [column for column in TEXT_COLUMNS if column != "association"]
    missing_required_text = int(data[required_text].isna().sum().sum())
    if missing_required_text:
        raise ValueError(f"Ditemukan {missing_required_text} nilai kosong pada dimensi wajib")

    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    invalid_numbers = int(data[NUMERIC_COLUMNS].isna().sum().sum())
    if invalid_numbers:
        raise ValueError(f"Ditemukan {invalid_numbers} nilai numerik tidak valid")

    negative_numbers = int((data[NUMERIC_COLUMNS] < 0).sum().sum())
    if negative_numbers:
        raise ValueError(f"Ditemukan {negative_numbers} nilai supply negatif")
    data[NUMERIC_COLUMNS] = data[NUMERIC_COLUMNS].astype("int64")

    data["updated_month"] = pd.to_datetime(data["updated_month"], errors="coerce")
    invalid_dates = int(data["updated_month"].isna().sum())
    if invalid_dates:
        raise ValueError(f"Ditemukan {invalid_dates} tanggal tidak valid")
    data["updated_month"] = data["updated_month"].dt.to_period("M").dt.to_timestamp()

    duplicate_rows = int(data.duplicated().sum())
    if duplicate_rows:
        data = data.drop_duplicates().reset_index(drop=True)

    metrics: dict[str, Any] = {
        "source_rows": source_rows,
        "output_rows": len(data),
        "duplicates_removed": duplicate_rows,
        "association_missing_filled": association_missing,
        "province_count": int(data["province"].nunique()),
        "regency_count": int(data["regency"].nunique()),
        "minimum_month": data["updated_month"].min().date().isoformat(),
        "maximum_month": data["updated_month"].max().date().isoformat(),
    }
    return data, metrics


def aggregate_by_province_month(data: pd.DataFrame) -> pd.DataFrame:
    """Produce a compact analytical output for Azure Blob Storage."""
    dimensions = ["province", "updated_month"]
    result = data.groupby(dimensions, as_index=False)[NUMERIC_COLUMNS].sum()
    return result.sort_values(dimensions).reset_index(drop=True)


def build_summary(data: pd.DataFrame, metrics: dict[str, Any]) -> dict[str, Any]:
    """Build a JSON-serializable run summary."""
    supply_totals = {column: int(data[column].sum()) for column in NUMERIC_COLUMNS}
    province_supply = data.groupby("province")[NUMERIC_COLUMNS].sum().sum(axis=1)
    top_provinces = [
        {"province": province, "total_supply": int(total)}
        for province, total in province_supply.nlargest(10).items()
    ]
    return {
        "pipeline": "housing-supply-ingestion",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "quality": metrics,
        "supply_totals": supply_totals,
        "top_provinces": top_provinces,
    }


def write_outputs(data: pd.DataFrame, output_dir: Path, metrics: dict[str, Any]) -> list[Path]:
    """Write clean, aggregate, and summary outputs atomically enough for CI usage."""
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_path = output_dir / "housing_supply_clean.csv.gz"
    aggregate_path = output_dir / "housing_supply_by_province_month.csv"
    summary_path = output_dir / "summary.json"

    data.to_csv(clean_path, index=False, compression="gzip", date_format="%Y-%m-%d")
    aggregate_by_province_month(data).to_csv(
        aggregate_path, index=False, date_format="%Y-%m-%d"
    )
    summary_path.write_text(
        json.dumps(build_summary(data, metrics), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return [clean_path, aggregate_path, summary_path]


def run_pipeline(input_path: Path, output_dir: Path, sheet_name: str) -> list[Path]:
    """Run the complete local ingestion pipeline."""
    source = read_source(input_path, sheet_name)
    clean, metrics = transform(source)
    outputs = write_outputs(clean, output_dir, metrics)
    LOGGER.info(
        "Pipeline selesai: %s -> %s baris; %s duplikat dihapus",
        metrics["source_rows"],
        metrics["output_rows"],
        metrics["duplicates_removed"],
    )
    for output in outputs:
        LOGGER.info("Output: %s", output)
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Path source Excel")
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    parser.add_argument("--sheet", default="Query result")
    parser.add_argument(
        "--upload-azure",
        action="store_true",
        help="Upload output menggunakan AZURE_STORAGE_CONNECTION_STRING",
    )
    parser.add_argument("--container", default="housing-results")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    outputs = run_pipeline(args.input, args.output, args.sheet)
    if args.upload_azure:
        from housing_pipeline.azure_store import upload_outputs

        uploaded = upload_outputs(outputs, args.container)
        for blob_url in uploaded:
            LOGGER.info("Uploaded: %s", blob_url)


if __name__ == "__main__":
    main()
