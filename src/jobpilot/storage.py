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


def read_bytes(path: str | None) -> bytes | None:
    if not path:
        return None
    local = Path(path)
    if local.exists() and local.is_file():
        return local.read_bytes()
    settings = get_settings()
    if path.startswith("gs://") and settings.gcs_bucket:
        from google.cloud import storage

        _, _, rest = path.partition("gs://")
        bucket_name, _, blob_name = rest.partition("/")
        client = storage.Client()
        blob = client.bucket(bucket_name).blob(blob_name)
        if blob.exists():
            return blob.download_as_bytes()
    if settings.gcs_bucket and "generated/" in path:
        from google.cloud import storage

        client = storage.Client()
        prefix = f"{settings.gcs_prefix.rstrip('/')}/generated"
        name = Path(path).name
        for blob in client.bucket(settings.gcs_bucket).list_blobs(prefix=prefix):
            if blob.name.endswith(name) or blob.name.endswith("tailored_resume.pdf"):
                if Path(path).parent.name in blob.name or name == "tailored_resume.pdf":
                    return blob.download_as_bytes()
    return None
