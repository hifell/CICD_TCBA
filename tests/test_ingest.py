from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from housing_pipeline.ingest import COLUMN_MAP, NUMERIC_COLUMNS, transform, write_outputs


def source_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "Provinsi": " JAWA BARAT ",
        "Kabupaten": "KAB BANDUNG",
        "Asosiasi": None,
        "Kecamatan": "Cileunyi",
        "Pengembang": "PT Contoh",
        "Nama Perumahan": "Griya Contoh",
        "tipeRumah": "tapak",
        "Subsidi-Kavling": 10,
        "Subsidi-Pembangunan": 2,
        "Subsidi-Dibooking": 1,
        "Subsidi-Ready": 3,
        "Subsidi-Terjual": 4,
        "Komersil": 5,
        "Komersil-Pembangunan": 1,
        "Komersil-Dibooking": 1,
        "Komersil-Tersedia": 2,
        "Komersil-Terjual": 1,
        "updatedAt: Month": "2026-11-20",
    }
    row.update(overrides)
    return row


def test_transform_cleans_and_deduplicates() -> None:
    source = pd.DataFrame([source_row(), source_row()])

    clean, metrics = transform(source)

    assert len(clean) == 1
    assert clean.loc[0, "province"] == "JAWA BARAT"
    assert clean.loc[0, "association"] == "TIDAK_DIKETAHUI"
    assert clean.loc[0, "updated_month"] == pd.Timestamp("2026-11-01")
    assert metrics["duplicates_removed"] == 1
    assert metrics["association_missing_filled"] == 2


def test_transform_rejects_missing_column() -> None:
    source = pd.DataFrame([source_row()]).drop(columns="Provinsi")

    with pytest.raises(ValueError, match="Kolom wajib tidak ditemukan"):
        transform(source)


def test_transform_rejects_negative_supply() -> None:
    source = pd.DataFrame([source_row(**{"Subsidi-Kavling": -1})])

    with pytest.raises(ValueError, match="supply negatif"):
        transform(source)


def test_write_outputs(tmp_path: Path) -> None:
    clean, metrics = transform(pd.DataFrame([source_row()]))

    outputs = write_outputs(clean, tmp_path, metrics)

    assert {path.name for path in outputs} == {
        "housing_supply_clean.csv.gz",
        "housing_supply_by_province_month.csv",
        "summary.json",
    }
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["quality"]["output_rows"] == 1
    assert summary["supply_totals"][NUMERIC_COLUMNS[0]] == 10
    assert set(COLUMN_MAP.values()).issubset(clean.columns)
