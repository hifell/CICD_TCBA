"""Azure Blob Storage adapter for pipeline results."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path


def upload_outputs(paths: list[Path], container_name: str) -> list[str]:
    """Upload immutable run outputs and update a `latest/` copy."""
    from azure.core.exceptions import ResourceExistsError
    from azure.storage.blob import BlobServiceClient, ContentSettings

    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise RuntimeError("Secret AZURE_STORAGE_CONNECTION_STRING belum dikonfigurasi")

    service = BlobServiceClient.from_connection_string(connection_string)
    container = service.get_container_client(container_name)
    try:
        container.create_container()
    except ResourceExistsError:
        pass

    run_prefix = datetime.now(UTC).strftime("runs/%Y/%m/%d/%H%M%S")
    uploaded: list[str] = []
    content_types = {
        ".json": "application/json",
        ".csv": "text/csv",
        ".gz": "application/gzip",
    }
    for path in paths:
        content_type = content_types.get(path.suffix.lower(), "application/octet-stream")
        settings = ContentSettings(content_type=content_type)
        with path.open("rb") as stream:
            run_blob = container.upload_blob(
                f"{run_prefix}/{path.name}",
                stream,
                overwrite=False,
                content_settings=settings,
            )
        with path.open("rb") as stream:
            container.upload_blob(
                f"latest/{path.name}",
                stream,
                overwrite=True,
                content_settings=settings,
            )
        uploaded.append(run_blob.url)
    return uploaded
