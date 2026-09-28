"""Calls the REAL Cloudinary API, so it needs a real free-tier account. It never runs unless asked.

    RUN_LIVE_CLOUDINARY_TESTS=1 CLOUDINARY_URL=... pytest tests/test_storage_cloudinary_live.py -v

Uploads one tiny test image and deletes it again; leaves nothing behind on success.
"""

import os
import urllib.request
from io import BytesIO

import cloudinary.api
import cloudinary.exceptions
import pytest
from PIL import Image

from app.config import settings
from app.storage import CloudinaryStorage

pytestmark = [
    pytest.mark.live_cloudinary,
    pytest.mark.skipif(
        os.environ.get("RUN_LIVE_CLOUDINARY_TESTS") != "1" or not settings.cloudinary_url,
        reason="opt-in: set RUN_LIVE_CLOUDINARY_TESTS=1 and CLOUDINARY_URL",
    ),
]


def _tiny_jpeg() -> bytes:
    output = BytesIO()
    Image.new("RGB", (10, 10), (10, 20, 30)).save(output, "JPEG")
    return output.getvalue()


def test_a_real_upload_can_be_fetched_and_then_is_gone_after_delete() -> None:
    storage = CloudinaryStorage(settings.cloudinary_url or "")
    name = "0123456789abcdef0123456789abcdef.jpg"

    storage.save(name, _tiny_jpeg())
    try:
        url = storage.url_for(name)
        with urllib.request.urlopen(url, timeout=15) as response:
            assert response.status == 200
            assert response.headers.get("Content-Type", "").startswith("image/")
    finally:
        storage.delete(name)

    # Asked of Cloudinary's own records, not fetched through its CDN: the CDN can keep serving a
    # cached copy for a while after a delete, so that would not reliably show the delete happened.
    with pytest.raises(cloudinary.exceptions.NotFound):
        cloudinary.api.resource(name.removesuffix(".jpg"), resource_type="image")
