# Checklist Screenshot Deliverable

Gunakan nama file berurutan agar `scripts/build_report.py` memasukkan gambar
secara otomatis. Screenshot lokal 01-08 dibuat oleh `capture_evidence.py` dari
output nyata; screenshot cloud 09-14 harus diambil setelah repository di-push dan
resource Azure di-deploy.

## Bukti lokal (dibuat otomatis)

- [x] `01_dataset_profile.png` - profil workbook sumber
- [x] `02_unit_tests.png` - hasil pytest
- [x] `03_pipeline_run.png` - proses ingestion lengkap
- [x] `04_git_history.png` - branch dan merge commit
- [x] `05_ci_workflow.png` - source workflow CI
- [x] `06_scheduler_workflow.png` - cron setiap 6 jam
- [x] `07_azure_bicep.png` - Infrastructure as Code Azure
- [x] `08_processed_summary.png` - ringkasan hasil data

## Bukti GitHub dan Azure (ambil manual)

- [ ] `09_github_repository.png` - halaman repository dan branch `main`
- [ ] `10_pull_request.png` - Pull Request `feature/data-quality` ke `main`
- [ ] `11_ci_success.png` - halaman Actions, job CI hijau
- [ ] `12_scheduler_success.png` - scheduled/manual workflow berhasil
- [ ] `13_azure_resources.png` - resource group dan Storage Account
- [ ] `14_azure_blob_results.png` - container `housing-results`, folder `runs/` dan `latest/`

## Skenario GitHub yang harus dilakukan

Riwayat branch/merge lokal sudah tersedia. Untuk memperlihatkan proses Pull
Request pada GitHub, buat repository kosong lalu jalankan:

```bash
git remote add origin https://github.com/<username>/<repository>.git
git push -u origin main
git push -u origin feature/data-quality
```

Karena branch fitur telah di-merge lokal, jika ingin screenshot PR yang belum
merge, buat branch demonstrasi dari commit awal:

```bash
git branch demo/pull-request 8c03013
git push -u origin demo/pull-request
```

Tambahkan perubahan kecil melalui GitHub, buka Pull Request ke `main`, tunggu CI
hijau, lalu merge. Jangan force-push atau menaruh secret Azure di source code.

## Menambahkan screenshot cloud ke PDF

1. Simpan PNG dengan nama tepat 09-14 di `evidence/screenshots/`.
2. Jalankan `python scripts/build_report.py`.
3. Periksa PDF final sebelum dikumpulkan.
