"""CloudinaryStorage, tested against a fake `cloudinary.uploader` (no real network calls here).

A real, opt-in round trip against the actual API lives in test_storage_cloudinary_live.py.
"""

import cloudinary.exceptions
import cloudinary.uploader
import pytest

from app.config import settings
from app.storage import CloudinaryStorage, get_storage

VALID_URL = "cloudinary://key123:secret456@demo-cloud"


class FakeUploader:
    """Stands in for cloudinary.uploader: records what it was asked to do, does nothing real."""

    def __init__(self) -> None:
        self.uploaded: list[tuple[bytes, dict]] = []
        self.destroyed: list[tuple[str, dict]] = []
        self.fail_upload = False
        self.fail_destroy = False

    def upload(self, data, **options):
        if self.fail_upload:
            raise cloudinary.exceptions.GeneralError("simulated failure")
        self.uploaded.append((data, options))
        return {"public_id": options["public_id"], "format": "jpg", "secure_url": "https://x"}

    def destroy(self, public_id, **options):
        if self.fail_destroy:
            raise cloudinary.exceptions.GeneralError("simulated failure")
        self.destroyed.append((public_id, options))
        return {"result": "ok"}


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeUploader:
    fake_uploader = FakeUploader()
    monkeypatch.setattr(cloudinary.uploader, "upload", fake_uploader.upload)
    monkeypatch.setattr(cloudinary.uploader, "destroy", fake_uploader.destroy)
    return fake_uploader


def storage() -> CloudinaryStorage:
    return CloudinaryStorage(VALID_URL)


# ---------- configuration ----------


@pytest.mark.parametrize(
    "bad_url",
    [
        "CLOUDINARY_URL=cloudinary://key:secret@cloud",  # the exact real-world paste mistake
        "cloudinary://key@cloud",  # no secret
        "cloudinary://:secret@cloud",  # no key
        "cloudinary://key:secret@",  # no cloud name
        "http://key:secret@cloud",  # wrong scheme
        "",
    ],
)
def test_a_malformed_url_is_rejected_with_a_helpful_message(bad_url: str) -> None:
    with pytest.raises(ValueError, match="CLOUDINARY_URL must look like"):
        CloudinaryStorage(bad_url)


def test_a_well_formed_url_configures_the_sdk() -> None:
    created = storage()
    assert created.cloud_name == "demo-cloud"


# ---------- save, delete, url_for ----------


def test_save_uploads_with_the_extension_stripped_from_the_public_id(fake: FakeUploader) -> None:
    storage().save("abc123def456abc123def456abc123d.jpg", b"pretend-image-bytes")

    assert len(fake.uploaded) == 1
    data, options = fake.uploaded[0]
    assert data == b"pretend-image-bytes"
    assert options["public_id"] == "abc123def456abc123def456abc123d"
    assert options["resource_type"] == "image"
    assert options["overwrite"] is True
    assert options["unique_filename"] is False
    assert options["use_filename"] is False


@pytest.mark.parametrize("extension", [".jpg", ".png", ".webp"])
def test_save_strips_every_supported_extension(fake: FakeUploader, extension: str) -> None:
    storage().save(f"0123456789abcdef0123456789abcdef{extension}", b"x")

    assert fake.uploaded[0][1]["public_id"] == "0123456789abcdef0123456789abcdef"


def test_a_name_with_no_extension_is_left_alone(fake: FakeUploader) -> None:
    storage().save("already-bare-name", b"x")

    assert fake.uploaded[0][1]["public_id"] == "already-bare-name"


def test_delete_destroys_by_the_stripped_public_id(fake: FakeUploader) -> None:
    storage().delete("abc123def456abc123def456abc123d.png")

    assert fake.destroyed == [("abc123def456abc123def456abc123d", {"resource_type": "image"})]


def test_url_for_has_no_extension_and_asks_for_automatic_format_and_quality(
    fake: FakeUploader,
) -> None:
    url = storage().url_for("abc123def456abc123def456abc123d.webp")

    assert url == (
        "https://res.cloudinary.com/demo-cloud/image/upload/f_auto,q_auto/"
        "abc123def456abc123def456abc123d"
    )


def test_a_save_failure_propagates_and_nothing_is_recorded_as_uploaded(fake: FakeUploader) -> None:
    fake.fail_upload = True

    with pytest.raises(cloudinary.exceptions.Error):
        storage().save("abc123def456abc123def456abc123d.jpg", b"x")
    assert fake.uploaded == []


def test_a_delete_failure_propagates(fake: FakeUploader) -> None:
    fake.fail_destroy = True

    with pytest.raises(cloudinary.exceptions.Error):
        storage().delete("abc123def456abc123def456abc123d.jpg")


# ---------- name_for: the exact inverse of url_for ----------


def test_name_for_round_trips_a_url_this_class_built() -> None:
    made = storage()
    url = made.url_for("abc123def456abc123def456abc123d.jpg")

    assert made.name_for(url) == "abc123def456abc123def456abc123d"


@pytest.mark.parametrize(
    "foreign_url",
    [
        "/images/placeholder.svg",
        "/api/v1/media/abc123def456abc123def456abc123d.jpg",  # LocalStorage's own shape
        "https://res.cloudinary.com/other-cloud/image/upload/f_auto,q_auto/abc123",  # wrong cloud
        "https://res.cloudinary.com/demo-cloud/image/upload/abc123",  # missing the transform bit
        "https://evil.example/f_auto,q_auto/abc123",
        "",
    ],
)
def test_name_for_ignores_urls_it_did_not_build(foreign_url: str) -> None:
    assert storage().name_for(foreign_url) is None


def test_name_for_rejects_an_empty_public_id() -> None:
    made = storage()
    assert made.name_for(f"{made._url_prefix}") is None


# ---------- the factory ----------


def test_get_storage_returns_cloudinary_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.storage as storage_module

    monkeypatch.setattr(settings, "image_storage", "cloudinary")
    monkeypatch.setattr(settings, "cloudinary_url", VALID_URL)
    monkeypatch.setattr(storage_module, "_storage", None)

    made = get_storage()

    assert isinstance(made, CloudinaryStorage)


def test_get_storage_refuses_cloudinary_without_a_url(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.storage as storage_module

    monkeypatch.setattr(settings, "image_storage", "cloudinary")
    monkeypatch.setattr(settings, "cloudinary_url", None)
    monkeypatch.setattr(storage_module, "_storage", None)

    with pytest.raises(RuntimeError, match="CLOUDINARY_URL"):
        get_storage()


def test_get_storage_returns_local_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.storage as storage_module
    from app.storage import LocalStorage

    monkeypatch.setattr(settings, "image_storage", "local")
    monkeypatch.setattr(storage_module, "_storage", None)

    assert isinstance(get_storage(), LocalStorage)


# ---------- the /media route, once every upload goes to Cloudinary instead ----------


def test_the_local_media_route_serves_nothing_once_storage_is_cloudinary(client) -> None:
    from app.main import app
    from app.storage import get_storage

    app.dependency_overrides[get_storage] = storage
    try:
        response = client.get("/api/v1/media/abc123def456abc123def456abc123d.jpg")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_storage, None)
