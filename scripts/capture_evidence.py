"""Capture reproducible local command output as PNG evidence for the report."""

# ruff: noqa: E501 - long evidence labels are intentionally kept readable.

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "evidence" / "screenshots"
LOGS = ROOT / "evidence" / "logs"


def run(command: list[str]) -> str:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    rendered_command = "PS> " + " ".join(command)
    return f"{rendered_command}\n\n{result.stdout}\nExit code: {result.returncode}"


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("C:/Windows/Fonts/cour.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def wrap_lines(text: str, width: int = 105, max_lines: int = 42) -> list[str]:
    lines: list[str] = []
    for raw_line in text.expandtabs(4).splitlines():
        lines.extend(textwrap.wrap(raw_line, width=width) or [""])
    if len(lines) > max_lines:
        return lines[: max_lines - 1] + ["... output dipotong; log lengkap tersimpan di evidence/logs ..."]
    return lines


def render(title: str, text: str, output: Path) -> None:
    image = Image.new("RGB", (1600, 900), "#10151c")
    draw = ImageDraw.Draw(image)
    title_font = load_font(30)
    body_font = load_font(21)
    draw.rectangle((0, 0, 1600, 64), fill="#202a36")
    draw.ellipse((22, 22, 42, 42), fill="#ff5f57")
    draw.ellipse((52, 22, 72, 42), fill="#febc2e")
    draw.ellipse((82, 22, 102, 42), fill="#28c840")
    draw.text((125, 14), title, font=title_font, fill="#f2f4f8")
    y = 86
    for line in wrap_lines(text):
        color = "#8bd5ca" if line.startswith("PS>") else "#d8dee9"
        draw.text((28, y), line, font=body_font, fill=color)
        y += 29
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def save_evidence(index: int, slug: str, title: str, content: str) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    stem = f"{index:02d}_{slug}"
    (LOGS / f"{stem}.txt").write_text(content, encoding="utf-8")
    render(title, content, SCREENSHOTS / f"{stem}.png")


def excerpt(path: Path, start: int = 0, count: int = 36) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    numbered = [f"{number:>3} | {line}" for number, line in enumerate(lines, start=1)]
    return "\n".join(numbered[start : start + count])


def main() -> None:
    save_evidence(1, "dataset_profile", "Dataset Profile", run(["python", "scripts/profile_dataset.py"]))
    save_evidence(2, "unit_tests", "Python Unit Tests", run(["python", "-m", "pytest", "-v"]))
    save_evidence(
        3,
        "pipeline_run",
        "Housing Ingestion Pipeline",
        run(
            [
                "python",
                "-m",
                "housing_pipeline.ingest",
                "--input",
                "sup-001_data-supply-perumahan.xlsx",
                "--output",
                "data/processed",
            ]
        ),
    )
    save_evidence(4, "git_history", "Git Branch and Merge History", run(["git", "log", "--graph", "--oneline", "--decorate", "--all"]))
    save_evidence(5, "ci_workflow", "GitHub Actions - CI", excerpt(ROOT / ".github/workflows/ci.yaml"))
    save_evidence(
        6,
        "scheduler_workflow",
        "GitHub Actions - Scheduler Every 6 Hours",
        excerpt(ROOT / ".github/workflows/scheduled-ingestion.yaml"),
    )
    save_evidence(7, "azure_bicep", "Azure Blob Storage - Bicep", excerpt(ROOT / "infra/main.bicep"))
    save_evidence(
        8,
        "processed_summary",
        "Processed Data Summary",
        excerpt(ROOT / "data/processed/summary.json", count=38),
    )
    print(f"Evidence tersimpan di {SCREENSHOTS}")


if __name__ == "__main__":
    main()
