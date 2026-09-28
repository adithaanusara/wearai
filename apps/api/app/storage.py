"""Where uploaded product images live.

Admin code only talks to `ImageStorage` (save, delete, the public URL of a stored file, and finding
the stored name back from a URL), so moving between backends means writing one more class with the
same four methods and returning it from `get_storage`. Nothing else has to change.

Two implementations exist: `LocalStorage`, for development, keeps files in a folder on this machine,
served by the API itself under /api/v1/media. `CloudinaryStorage`, for production, uses Cloudinary's
free tier, so uploads survive a redeploy. `IMAGE_STORAGE` picks between them.
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

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

    def name_for(self, url: str) -> str | None:
        """The stored name behind `url`, or None for a URL this storage did not create (such as a
        seed placeholder, or a URL from the other backend, left over from before a switch)."""
        ...


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

    def name_for(self, url: str) -> str | None:
        if not url.startswith(MEDIA_PREFIX):
            return None
        name = url.removeprefix(MEDIA_PREFIX)
        return name if STORED_NAME.fullmatch(name) else None


# Cloudinary asks that a public_id carry no file extension: giving it one anyway (as our own
# name, "<32 hex>.jpg", does) makes its *upload result* end up double-extensioned ("....jpg.jpg"),
# found by trying it against a real account. The delivery URL this class builds never has that
# problem, because it is built from the bare id and never from that upload result, but the bare
# id is what Cloudinary actually needs, so any of our names is stripped down to it first.
_KNOWN_EXTENSION = re.compile(r"\.(jpg|png|webp)$")


def _public_id(name: str) -> str:
    return _KNOWN_EXTENSION.sub("", name)


class CloudinaryStorage:
    """Files on Cloudinary's free tier. For production, so uploads survive a redeploy."""

    def __init__(self, cloudinary_url: str) -> None:
        import cloudinary

        parsed = urlparse(cloudinary_url)
        if parsed.scheme != "cloudinary" or not (
            parsed.hostname and parsed.username and parsed.password
        ):
            raise ValueError(
                "CLOUDINARY_URL must look like cloudinary://<api_key>:<api_secret>@<cloud_name>, "
                "exactly as Cloudinary's dashboard shows it (not with a repeated "
                "'CLOUDINARY_URL=')."
            )
        cloudinary.config(
            cloud_name=parsed.hostname,
            api_key=parsed.username,
            api_secret=parsed.password,
            secure=True,
        )
        self.cloud_name = parsed.hostname
        # Fixed and always the same, so a URL this class built is always recognised by name_for.
        # f_auto and q_auto let Cloudinary pick the smallest format and quality a browser will
        # accept, which matters on a free tier metered by bandwidth as well as storage.
        self._url_prefix = (
            f"https://res.cloudinary.com/{self.cloud_name}/image/upload/f_auto,q_auto/"
        )

    def save(self, name: str, data: bytes) -> None:
        import cloudinary.uploader

        cloudinary.uploader.upload(
            data,
            public_id=_public_id(name),
            resource_type="image",
            overwrite=True,
            unique_filename=False,
            use_filename=False,
        )

    def delete(self, name: str) -> None:
        import cloudinary.uploader

        cloudinary.uploader.destroy(_public_id(name), resource_type="image")

    def url_for(self, name: str) -> str:
        return f"{self._url_prefix}{_public_id(name)}"

    def name_for(self, url: str) -> str | None:
        if not url.startswith(self._url_prefix):
            return None
        public_id = url.removeprefix(self._url_prefix)
        return public_id or None


_storage: ImageStorage | None = None


def get_storage() -> ImageStorage:
    """The configured storage: `LocalStorage` by default, `CloudinaryStorage` when set up.

    Built once and reused (constructing `CloudinaryStorage` configures the SDK's shared, global
    state), and built lazily rather than at import time, so tests can set `IMAGE_STORAGE` first.
    """
    global _storage
    if _storage is None:
        if settings.image_storage == "cloudinary":
            if not settings.cloudinary_url:
                raise RuntimeError("IMAGE_STORAGE=cloudinary needs CLOUDINARY_URL to be set too.")
            _storage = CloudinaryStorage(settings.cloudinary_url)
        else:
            _storage = LocalStorage(settings.upload_dir)
    return _storage
