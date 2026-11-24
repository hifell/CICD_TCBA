"""Build the assignment PDF from report text and captured evidence."""

# ruff: noqa: E501 - report paragraphs are intentionally stored as complete strings.

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "CI-CD_A_L0224038_Thufail-Syarif-Al-Wafi.pdf"
SCREENSHOTS = ROOT / "evidence" / "screenshots"


def image_or_placeholder(filename: str, caption: str):
    path = SCREENSHOTS / filename
    elements = [Paragraph(f"<b>{caption}</b>", STYLES["Heading3"]), Spacer(1, 0.15 * cm)]
    if path.exists():
        image = Image(str(path))
        image._restrictSize(24.5 * cm, 15.2 * cm)
        elements.append(image)
    else:
        placeholder = Table(
            [[f"BUKTI CLOUD BELUM DITAMBAHKAN\n{filename}\n{caption}"]],
            colWidths=[24 * cm],
            rowHeights=[9 * cm],
        )
        placeholder.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 2, colors.HexColor("#d97706")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff7ed")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#9a3412")),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 14),
                ]
            )
        )
        elements.append(placeholder)
    return [KeepTogether(elements)]


def add_page_number(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(28.5 * cm, 0.65 * cm, f"Halaman {document.page}")
    canvas.restoreState()


STYLES = getSampleStyleSheet()
STYLES.add(
    ParagraphStyle(
        "CoverTitle",
        parent=STYLES["Title"],
        fontSize=25,
        leading=31,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#12355b"),
        spaceAfter=24,
    )
)
STYLES["BodyText"].fontSize = 10.5
STYLES["BodyText"].leading = 15
STYLES["Heading1"].textColor = colors.HexColor("#12355b")
STYLES["Heading2"].textColor = colors.HexColor("#2563eb")


def section(title: str, paragraphs: list[str]) -> list:
    result = [Paragraph(title, STYLES["Heading1"])]
    for paragraph in paragraphs:
        result.extend([Paragraph(paragraph, STYLES["BodyText"]), Spacer(1, 0.2 * cm)])
    return result


def main() -> None:
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=landscape(A4),
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.1 * cm,
        title="CI/CD Data Supply Perumahan",
        author="Thufail Syarif Al Wafi",
    )
    story = [
        Spacer(1, 3.0 * cm),
        Paragraph("IMPLEMENTASI CI/CD PIPELINE", STYLES["CoverTitle"]),
        Paragraph("Data Supply Perumahan Indonesia", STYLES["Title"]),
        Spacer(1, 1.2 * cm),
        Table(
            [
                ["Kelas", "A"],
                ["NIM", "L0224038"],
                ["Nama", "Thufail Syarif Al Wafi"],
                ["Teknologi", "Python, GitHub Actions, Azure Blob Storage"],
            ],
            colWidths=[4 * cm, 12 * cm],
            style=[
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#dbeafe")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 9),
            ],
        ),
        PageBreak(),
    ]
    story += section(
        "1. Tujuan dan Arsitektur",
        [
            "Proyek ini menerapkan ingestion, validasi, pengujian otomatis, scheduler, dan penyimpanan hasil. Alur utama: Excel source -> Python validation/cleaning -> CSV GZip, agregat CSV, dan summary JSON -> Azure Blob Storage.",
            "Push dan Pull Request menjalankan Continuous Integration. Workflow produksi menjalankan ingestion pada cron 0 */6 * * *, yaitu setiap enam jam pada UTC.",
        ],
    )
    story += section(
        "2. Dataset",
        [
            "Workbook sup-001_data-supply-perumahan.xlsx berisi 274.823 baris, 18 kolom, 38 provinsi, dan 457 kabupaten untuk periode Juni 2020 sampai November 2026. Nilai asosiasi yang kosong dinormalisasi menjadi TIDAK_DIKETAHUI; angka negatif, tanggal invalid, dan kolom hilang menyebabkan pipeline gagal agar data buruk tidak dimuat.",
        ],
    )
    story += image_or_placeholder("01_dataset_profile.png", "Gambar 1. Profil dataset sumber")
    story += [PageBreak()]
    story += section(
        "3. Source Code dan Pengujian",
        [
            "src/housing_pipeline/ingest.py mengimplementasikan extract-transform-load. Unit test menguji normalisasi, deduplikasi, validasi schema, penolakan supply negatif, dan penulisan output.",
        ],
    )
    story += image_or_placeholder("02_unit_tests.png", "Gambar 2. Hasil unit test")
    story += [PageBreak()]
    story += image_or_placeholder("03_pipeline_run.png", "Gambar 3. Eksekusi ingestion lokal")
    story += [PageBreak()]
    story += section(
        "4. Skenario Git dan Continuous Integration",
        [
            "Repository dibuat pada main, pengembangan dilanjutkan pada feature/data-quality, lalu digabungkan dengan merge commit. Workflow CI dipicu pada push dan Pull Request, menjalankan Ruff serta pytest pada Python 3.11.",
        ],
    )
    story += image_or_placeholder("04_git_history.png", "Gambar 4. Git branch dan merge history")
    story += [PageBreak()]
    story += image_or_placeholder("05_ci_workflow.png", "Gambar 5. Definisi workflow CI")
    story += [PageBreak()]
    story += image_or_placeholder("09_github_repository.png", "Gambar 6. Repository GitHub")
    story += [PageBreak()]
    story += image_or_placeholder("10_pull_request.png", "Gambar 7. Pull Request feature ke main")
    story += [PageBreak()]
    story += image_or_placeholder("11_ci_success.png", "Gambar 8. GitHub Actions CI berhasil")
    story += [PageBreak()]
    story += section(
        "5. Scheduler Setiap Enam Jam",
        [
            "Workflow scheduled-ingestion.yaml memakai cron 0 */6 * * *. Job memvalidasi secret, menjalankan pipeline penuh, mengunggah hasil ke Azure, dan menyimpan artifact sementara untuk audit.",
        ],
    )
    story += image_or_placeholder("06_scheduler_workflow.png", "Gambar 9. Workflow scheduler")
    story += [PageBreak()]
    story += image_or_placeholder("12_scheduler_success.png", "Gambar 10. Scheduled workflow berhasil")
    story += [PageBreak()]
    story += section(
        "6. Azure Data Store",
        [
            "Bicep membuat StorageV2 Standard LRS dan private container housing-results. Public access dinonaktifkan, TLS 1.2 dan HTTPS diwajibkan, serta soft delete tujuh hari diaktifkan. File run disimpan immutable pada runs/YYYY/MM/DD/HHMMSS dan latest menunjuk hasil terbaru.",
        ],
    )
    story += image_or_placeholder("07_azure_bicep.png", "Gambar 11. Azure Infrastructure as Code")
    story += [PageBreak()]
    story += image_or_placeholder("13_azure_resources.png", "Gambar 12. Azure Resource Group dan Storage Account")
    story += [PageBreak()]
    story += image_or_placeholder("14_azure_blob_results.png", "Gambar 13. Hasil pipeline pada Blob Container")
    story += [PageBreak()]
    story += image_or_placeholder("08_processed_summary.png", "Gambar 14. Ringkasan output pipeline")
    story += [PageBreak()]
    story += section(
        "7. Kesimpulan",
        [
            "Pipeline memenuhi seluruh spesifikasi: ingestion sesuai tema, source code Python, skenario Git branch sampai merge, CI, workflow YAML, Azure data store, dan scheduler enam jam.",
            "Catatan bukti: kotak oranye pada PDF menandakan screenshot cloud yang harus diganti setelah repository GitHub dan Azure milik mahasiswa dijalankan. Kredensial sengaja tidak disimpan di proyek.",
        ],
    )
    document.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF dibuat: {OUTPUT}")


if __name__ == "__main__":
    main()
