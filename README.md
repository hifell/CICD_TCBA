# CI/CD Pipeline Data Supply Perumahan

Proyek ini mengolah `sup-001_data-supply-perumahan.xlsx` dengan Python, menguji
pipeline melalui GitHub Actions, menjalankannya setiap 6 jam, dan menyimpan hasil
ke Azure Blob Storage.

## Ringkasan dataset

- 274.823 baris dan 18 kolom
- 38 provinsi dan 457 kabupaten
- Periode data Juni 2020–November 2026
- Tema: supply perumahan subsidi dan komersial di Indonesia

## Struktur proyek

```text
src/housing_pipeline/             # Source code ingestion Python
tests/                            # Unit test
.github/workflows/ci.yaml         # Continuous Integration
.github/workflows/scheduled-ingestion.yaml
.github/workflows/azure-infrastructure.yaml
infra/main.bicep                  # Azure Storage Account + Blob Container
scripts/                          # Profiling, screenshot, dan laporan PDF
docs/                             # Panduan bukti dan laporan
```

## Menjalankan secara lokal

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m housing_pipeline.ingest \
  --input sup-001_data-supply-perumahan.xlsx \
  --output data/processed
pytest -v
```

Hasil pipeline:

- `housing_supply_clean.csv.gz`: data yang sudah dibersihkan
- `housing_supply_by_province_month.csv`: agregasi provinsi/bulan
- `summary.json`: metadata dan indikator kualitas data

## Menyiapkan Azure

1. Buat resource group, misalnya `rg-housing-cicd`.
2. Jalankan Bicep:

   ```bash
   az deployment group create \
     --resource-group rg-housing-cicd \
     --template-file infra/main.bicep \
     --parameters storageAccountName=<nama-unik-storage>
   ```

3. Ambil connection string Storage Account dan simpan sebagai GitHub Actions
   secret `AZURE_STORAGE_CONNECTION_STRING`.
4. Untuk workflow deployment infrastruktur, tambahkan `AZURE_CREDENTIALS`,
   `AZURE_RESOURCE_GROUP`, dan variable `AZURE_STORAGE_ACCOUNT`.

Jangan pernah menulis connection string atau kredensial Azure ke repository.

## Scheduler

Cron `0 */6 * * *` pada `.github/workflows/scheduled-ingestion.yaml` berjalan
pukul 00:00, 06:00, 12:00, dan 18:00 UTC. GitHub dapat menunda scheduled job
beberapa menit ketika antrean sedang padat.

## Skenario Git

Skenario tugas menggunakan branch `feature/data-quality` dan merge commit ke
`main`. Perintah dan daftar screenshot wajib tersedia di
[`docs/SCREENSHOT_CHECKLIST.md`](docs/SCREENSHOT_CHECKLIST.md).
