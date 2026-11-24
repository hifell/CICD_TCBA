# Cloud Deployment Record

Konfigurasi deployment untuk tugas CI/CD:

| Item | Value |
|---|---|
| GitHub repository | `hifell/CICD_TCBA` |
| Azure subscription | `Azure for Students` |
| Resource group | `rg-housing-cicd-l0224038` |
| Region | `southeastasia` |
| Storage account | `sthousingl0224038` |
| Blob container | `housing-results` |
| Scheduler | `0 */6 * * *` |

Connection string disimpan hanya pada GitHub Actions secret
`AZURE_STORAGE_CONNECTION_STRING`. Dokumen ini tidak menyimpan kredensial.
