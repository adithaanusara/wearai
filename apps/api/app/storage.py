"""Where uploaded product images live.

Admin code only talks to `ImageStorage` (save, delete, and the public URL of a stored file), so
moving to a cloud bucket such as S3 or Cloudinary later means writing one more class with the same
methods and returning it from `get_storage`. Nothing else has to change. Until then, files are
kept in a local folder and served by the API itself under /api/v1/media.
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Protocol

from app.config import settings

MEDIA_PREFIX = "/api/v1/media/"
# The only names that are ever stored or served: 32 hex characters and a known extension. Checking
# every name against this before it touches the file system rules out path tricks such as "../".
STORED_NAME = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp)$")
CONTENT_TYPES = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


class ImageStorage(Protocol):
    def save(self, name: str, data: bytes) -> None: ...

    def delete(self, name: str) -> None: ...

    def url_for(self, name: str) -> str: ...


class LocalStorage:
    """Files in a folder on this machine. For development."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def path_for(self, name: str) -> Path | None:
        """The file for a stored name, or None for a name this storage would never have made."""
        if not STORED_NAME.fullmatch(name):
            return None
        return self.root / name

    def save(self, name: str, data: bytes) -> None:
        path = self.path_for(name)
        if path is None:
            raise ValueError("Invalid image name.")
        self.root.mkdir(parents=True, exist_ok=True)
        # Written to a temporary file and then renamed, so a half-written image is never served.
        handle, temporary = tempfile.mkstemp(dir=self.root, suffix=".part")
        try:
            with os.fdopen(handle, "wb") as file:
                file.write(data)
            os.replace(temporary, path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise

    def delete(self, name: str) -> None:
        path = self.path_for(name)
        if path is not None:
            path.unlink(missing_ok=True)

    def url_for(self, name: str) -> str:
        return f"{MEDIA_PREFIX}{name}"


def stored_name(url: str) -> str | None:
    """The stored file name if `url` is one of our uploads (not a placeholder or a cloud URL)."""
    if not url.startswith(MEDIA_PREFIX):
        return None
    name = url.removeprefix(MEDIA_PREFIX)
    return name if STORED_NAME.fullmatch(name) else None


_storage = LocalStorage(settings.upload_dir)


def get_storage() -> LocalStorage:
    """The configured storage. Tests replace this with a temporary folder."""
    return _storage
