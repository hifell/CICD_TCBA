"""Capture actual GitHub and Azure CLI results for the assignment report."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from capture_evidence import ROOT, save_evidence

GH = Path("C:/Program Files/GitHub CLI/gh.exe")


def execute(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    label = "PS> " + " ".join(command)
    return result.returncode, f"{label}\n\n{result.stdout}\nExit code: {result.returncode}"


def capture_github() -> None:
    commands = [
        (
            9,
            "github_repository",
            "GitHub Repository",
            [str(GH), "repo", "view", "hifell/CICD_TCBA"],
        ),
        (
            10,
            "pull_request",
            "Merged Pull Request #1",
            [str(GH), "pr", "view", "1", "--repo", "hifell/CICD_TCBA"],
        ),
    ]
    for index, slug, title, command in commands:
        code, output = execute(command)
        if code:
            raise RuntimeError(output)
        save_evidence(index, slug, title, output)

    run_result = subprocess.run(
        [
            str(GH),
            "run",
            "list",
            "--repo",
            "hifell/CICD_TCBA",
            "--workflow",
            "Continuous Integration",
            "--event",
            "pull_request",
            "--limit",
            "1",
            "--json",
            "databaseId",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    run_id = json.loads(run_result.stdout)[0]["databaseId"]
    code, output = execute(
        [str(GH), "run", "view", str(run_id), "--repo", "hifell/CICD_TCBA"]
    )
    if code:
        raise RuntimeError(output)
    save_evidence(11, "ci_success", "GitHub Actions CI - Success", output)


def capture_scheduler() -> None:
    result = subprocess.run(
        [
            str(GH),
            "run",
            "list",
            "--repo",
            "hifell/CICD_TCBA",
            "--workflow",
            "Scheduled Housing Ingestion",
            "--limit",
            "1",
            "--json",
            "databaseId",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    runs = json.loads(result.stdout)
    if not runs:
        raise RuntimeError("Scheduled workflow belum pernah dijalankan")
    run_id = runs[0]["databaseId"]
    code, output = execute(
        [str(GH), "run", "view", str(run_id), "--repo", "hifell/CICD_TCBA"]
    )
    if code:
        raise RuntimeError(output)
    save_evidence(12, "scheduler_success", "Scheduled Ingestion - Success", output)


def capture_azure() -> None:
    resource_command = [
        "az",
        "resource",
        "list",
        "--resource-group",
        "rg-housing-cicd-l0224038",
        "--query",
        "[].{name:name,type:type,location:location}",
        "-o",
        "table",
    ]
    code, output = execute(resource_command)
    if code:
        raise RuntimeError(output)
    save_evidence(13, "azure_resources", "Azure Resources", output)

    blob_command = [
        "az",
        "storage",
        "blob",
        "list",
        "--account-name",
        "sthousingl0224038",
        "--container-name",
        "housing-results",
        "--auth-mode",
        "login",
        "--query",
        "[].{name:name,size:properties.contentLength,tier:properties.blobTier}",
        "-o",
        "table",
    ]
    code, output = execute(blob_command)
    if code:
        raise RuntimeError(output)
    save_evidence(14, "azure_blob_results", "Azure Blob Pipeline Results", output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--github", action="store_true")
    parser.add_argument("--scheduler", action="store_true")
    parser.add_argument("--azure", action="store_true")
    args = parser.parse_args()
    if args.github:
        capture_github()
    if args.scheduler:
        capture_scheduler()
    if args.azure:
        capture_azure()


if __name__ == "__main__":
    main()
