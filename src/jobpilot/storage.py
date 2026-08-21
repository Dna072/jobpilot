from __future__ import annotations

from pathlib import Path

from jobpilot.config import get_settings


def persist_directory(local: Path, object_prefix: str) -> str:
    """Upload a directory to GCS when GCS_BUCKET is set; otherwise return the local path."""
    settings = get_settings()
    if not settings.gcs_bucket:
        return str(local)
    from google.cloud import storage  # optional extra: jobpilot[gcp]

    client = storage.Client()
    bucket = client.bucket(settings.gcs_bucket)
    prefix = f"{settings.gcs_prefix.rstrip('/')}/{object_prefix.strip('/')}"
    for path in local.rglob("*"):
        if path.is_file():
            rel = path.relative_to(local).as_posix()
            bucket.blob(f"{prefix}/{rel}").upload_from_filename(str(path))
    return f"gs://{settings.gcs_bucket}/{prefix}"
