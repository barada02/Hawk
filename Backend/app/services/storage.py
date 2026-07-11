"""Media storage.

Everything that produces bytes (images, video clips) saves through the
`Storage` interface and gets back a URL. Today that's the local filesystem;
swapping in Google Cloud Storage later means adding a `GCSStorage` class and
changing `get_storage()` — no callers change.
"""

import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings


class Storage(ABC):
    @abstractmethod
    def save(self, data: bytes, ext: str) -> str:
        """Persist `data` and return a URL that serves it."""
        raise NotImplementedError

    @abstractmethod
    def read(self, url: str) -> bytes:
        """Load back the bytes for a URL previously returned by `save`."""
        raise NotImplementedError


class LocalStorage(Storage):
    """Writes to a local directory served by FastAPI at `url_prefix`."""

    def __init__(self, base_dir: str, url_prefix: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.url_prefix = url_prefix.rstrip("/")

    def save(self, data: bytes, ext: str) -> str:
        name = f"{uuid.uuid4().hex}.{ext.lstrip('.')}"
        (self.base_dir / name).write_bytes(data)
        return f"{self.url_prefix}/{name}"

    def read(self, url: str) -> bytes:
        # Map the served URL back to its file; reject path traversal.
        name = Path(url).name
        path = self.base_dir / name
        if not path.is_file():
            raise FileNotFoundError(url)
        return path.read_bytes()


class GCSStorage(Storage):
    """Writes to a Google Cloud Storage bucket."""

    def __init__(self, bucket_name: str) -> None:
        from google.cloud import storage as gcs
        self.client = gcs.Client()
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket(bucket_name)

    def save(self, data: bytes, ext: str) -> str:
        name = f"{uuid.uuid4().hex}.{ext.lstrip('.')}"
        blob = self.bucket.blob(name)

        ext = ext.lstrip(".").lower()
        content_type = "application/octet-stream"
        if ext == "png":
            content_type = "image/png"
        elif ext in ("jpg", "jpeg"):
            content_type = "image/jpeg"
        elif ext == "webp":
            content_type = "image/webp"
        elif ext == "mp4":
            content_type = "video/mp4"

        blob.upload_from_string(data, content_type=content_type)
        return f"https://storage.googleapis.com/{self.bucket_name}/{name}"

    def read(self, url: str) -> bytes:
        name = url.rsplit("/", 1)[-1]
        blob = self.bucket.blob(name)
        return blob.download_as_bytes()


def get_storage() -> Storage:
    if settings.STORAGE_BACKEND == "gcs":
        return GCSStorage(settings.GCS_BUCKET_NAME)
    return LocalStorage(settings.MEDIA_DIR, settings.MEDIA_URL_PREFIX)


storage = get_storage()
