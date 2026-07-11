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


def get_storage() -> Storage:
    # Later: if settings.STORAGE_BACKEND == "gcs": return GCSStorage(...)
    return LocalStorage(settings.MEDIA_DIR, settings.MEDIA_URL_PREFIX)


storage = get_storage()
