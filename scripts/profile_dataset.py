"""Print a concise, reproducible profile of the source workbook."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def main() -> None:
    source = Path("sup-001_data-supply-perumahan.xlsx")
    data = pd.read_excel(source, sheet_name="Query result", engine="openpyxl")
    numeric = data.select_dtypes(include="number")
    profile = {
        "file": source.name,
        "rows": len(data),
        "columns": len(data.columns),
        "provinces": int(data["Provinsi"].nunique()),
        "regencies": int(data["Kabupaten"].nunique()),
        "developers": int(data["Pengembang"].nunique()),
        "housing_projects": int(data["Nama Perumahan"].nunique()),
        "minimum_month": data["updatedAt: Month"].min().date().isoformat(),
        "maximum_month": data["updatedAt: Month"].max().date().isoformat(),
        "duplicate_rows": int(data.duplicated().sum()),
        "missing_values": {
            key: int(value) for key, value in data.isna().sum().items() if value
        },
        "negative_numeric_values": int((numeric < 0).sum().sum()),
    }
    print(json.dumps(profile, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
