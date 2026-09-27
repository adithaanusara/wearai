from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.main import app
from app.models import AuditLog, ProductImage
from app.storage import LocalStorage, get_storage
from tests.test_admin_api import ADMIN_PREFIX, WEB_ORIGIN, make_user, signed_in

pytestmark = pytest.mark.usefixtures("catalogue")

TEE = "w-tee-01"
MEDIA = "/api/v1/media"


@pytest.fixture(autouse=True)
def storage(client: TestClient, tmp_path: Path) -> LocalStorage:
    """Uploads go to a temporary folder, never to the real one."""
    local = LocalStorage(tmp_path / "uploads")
    app.dependency_overrides[get_storage] = lambda: local
    return local


@pytest.fixture
def admin(client: TestClient, db: Session) -> TestClient:
    make_user(db, "admin@example.com", "admin")
    return signed_in("admin@example.com")


@pytest.fixture
def staff(client: TestClient, db: Session) -> TestClient:
    make_user(db, "staff@example.com", "staff")
    return signed_in("staff@example.com")


def picture(fmt: str = "JPEG", size: tuple[int, int] = (400, 500), **save) -> bytes:
    output = BytesIO()
    Image.new("RGB", size, (200, 120, 40)).save(output, fmt, **save)
    return output.getvalue()


def files_on_disk(storage: LocalStorage) -> list[str]:
    return sorted(p.name for p in storage.root.glob("*")) if storage.root.exists() else []


def read(browser: TestClient, product_id: str = TEE) -> dict:
    response = browser.get(f"{ADMIN_PREFIX}/products/{product_id}")
    assert response.status_code == 200
    return response.json()


def upload(
    browser: TestClient,
    data: bytes,
    filename: str = "photo.jpg",
    content_type: str = "image/jpeg",
    product_id: str = TEE,
    version: str | None = None,
    origin: str = WEB_ORIGIN,
):
    version = version or read(browser, product_id)["updatedAt"]
    return browser.post(
        f"{ADMIN_PREFIX}/products/{product_id}/images",
        data={"updatedAt": version},
        files={"file": (filename, data, content_type)},
        headers={"Origin": origin},
    )


def remove(browser: TestClient, image_id: int, product_id: str = TEE, version: str | None = None):
    version = version or read(browser, product_id)["updatedAt"]
    return browser.delete(
        f"{ADMIN_PREFIX}/products/{product_id}/images/{image_id}",
        params={"updatedAt": version},
        headers={"Origin": WEB_ORIGIN},
    )


def reorder(browser: TestClient, ids: list[int], product_id: str = TEE, version: str | None = None):
    version = version or read(browser, product_id)["updatedAt"]
    return browser.put(
        f"{ADMIN_PREFIX}/products/{product_id}/images/order",
        json={"updatedAt": version, "imageIds": ids},
        headers={"Origin": WEB_ORIGIN},
    )


def stored_name(url: str) -> str:
    assert url.startswith(f"{MEDIA}/")
    return url.removeprefix(f"{MEDIA}/")


# ---------- who may upload ----------


def test_staff_cannot_change_images(staff: TestClient, storage: LocalStorage) -> None:
    version = read(staff)["updatedAt"]

    assert upload(staff, picture(), version=version).status_code == 403
    assert remove(staff, 1, version=version).status_code == 403
    assert reorder(staff, [1, 2], version=version).status_code == 403
    assert files_on_disk(storage) == []


def test_an_upload_from_an_untrusted_origin_is_refused(
    admin: TestClient, storage: LocalStorage
) -> None:
    assert upload(admin, picture(), origin="https://evil.example").status_code == 403
    assert files_on_disk(storage) == []


# ---------- good uploads ----------


@pytest.mark.parametrize(
    ("fmt", "extension", "content_type"),
    [("JPEG", ".jpg", "image/jpeg"), ("PNG", ".png", "image/png"), ("WEBP", ".webp", "image/webp")],
)
def test_a_valid_image_is_stored_served_and_audited(
    admin: TestClient,
    storage: LocalStorage,
    db: Session,
    fmt: str,
    extension: str,
    content_type: str,
) -> None:
    before = read(admin)

    response = upload(
        admin, picture(fmt), filename=f"my photo{extension}", content_type=content_type
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["images"]) == len(before["images"]) + 1
    assert body["updatedAt"] != before["updatedAt"]
    name = stored_name(body["images"][-1]["url"])
    assert name.endswith(extension)
    assert files_on_disk(storage) == [name]

    served = TestClient(app).get(f"{MEDIA}/{name}")
    assert served.status_code == 200
    assert served.headers["content-type"] == content_type
    assert served.headers["x-content-type-options"] == "nosniff"
    assert "immutable" in served.headers["cache-control"]
    assert "default-src 'none'" in served.headers["content-security-policy"]
    assert Image.open(BytesIO(served.content)).format == fmt

    entry = db.scalars(select(AuditLog).where(AuditLog.action == "product.image_added")).one()
    assert entry.entity_id == TEE and entry.actor_email == "admin@example.com"


def test_the_shop_shows_the_new_image_last(admin: TestClient) -> None:
    url = upload(admin, picture()).json()["images"][-1]["url"]

    shop = TestClient(app).get("/api/v1/products/essential-fitted-tee").json()

    assert shop["images"][-1] == url


def test_the_stored_name_is_random_and_the_upload_name_is_ignored(
    admin: TestClient, storage: LocalStorage
) -> None:
    upload(admin, picture(), filename="../../../evil.php.png")
    upload(admin, picture(), filename="../../../evil.php.png")

    names = files_on_disk(storage)

    assert len(names) == 2 and len(set(names)) == 2
    assert all(len(n) == 36 and n.endswith(".jpg") for n in names)
    # Nothing was written anywhere else.
    assert list(storage.root.parent.glob("**/evil*")) == []


def test_metadata_is_stripped_and_the_picture_is_turned_upright(
    admin: TestClient, storage: LocalStorage
) -> None:
    image = Image.new("RGB", (400, 300), (10, 20, 30))
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90 degrees when displayed
    exif[0x010F] = "SecretCameraMaker"
    exif.get_ifd(0x8825)[0x0002] = (6.0, 55.0, 0.0)  # GPS latitude
    output = BytesIO()
    image.save(output, "JPEG", exif=exif)
    assert b"SecretCameraMaker" in output.getvalue()

    response = upload(admin, output.getvalue())

    assert response.status_code == 201
    stored = (storage.root / files_on_disk(storage)[0]).read_bytes()
    assert b"SecretCameraMaker" not in stored
    assert dict(Image.open(BytesIO(stored)).getexif()) == {}
    assert Image.open(BytesIO(stored)).size == (300, 400)


def test_a_polyglot_file_loses_its_hidden_tail(admin: TestClient, storage: LocalStorage) -> None:
    hidden = b"<script>alert(1)</script><?php system($_GET['c']); ?>"

    assert upload(admin, picture() + hidden).status_code == 201

    stored = (storage.root / files_on_disk(storage)[0]).read_bytes()
    assert b"<script" not in stored and b"<?php" not in stored


def test_large_pictures_are_shrunk(admin: TestClient, storage: LocalStorage) -> None:
    assert upload(admin, picture(size=(4000, 3000))).status_code == 201

    stored = Image.open(storage.root / files_on_disk(storage)[0])
    assert max(stored.size) == 2000


def test_a_png_keeps_its_transparency(admin: TestClient, storage: LocalStorage) -> None:
    output = BytesIO()
    Image.new("RGBA", (300, 300), (255, 0, 0, 0)).save(output, "PNG")

    assert upload(admin, output.getvalue(), "a.png", "image/png").status_code == 201

    stored = Image.open(storage.root / files_on_disk(storage)[0])
    assert stored.mode == "RGBA" and stored.getpixel((5, 5))[3] == 0


# ---------- hostile and broken files ----------


def animated(fmt: str) -> bytes:
    frames = [Image.new("RGB", (300, 300), (i * 60, 0, 0)) for i in range(3)]
    output = BytesIO()
    frames[0].save(output, fmt, save_all=True, append_images=frames[1:], duration=100)
    return output.getvalue()


def other_format(fmt: str) -> bytes:
    output = BytesIO()
    Image.new("RGB", (400, 400), (1, 2, 3)).save(output, fmt)
    return output.getvalue()


HOSTILE = {
    "text renamed .png": b"this is not an image at all",
    "html renamed .jpg": b"<html><script>alert(1)</script></html>",
    "svg with a script": (
        b'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">'
        b"<script>alert(1)</script></svg>"
    ),
    "php": b"<?php system($_GET['c']); ?>",
    "empty": b"",
    "gif": other_format("GIF"),
    "bmp": other_format("BMP"),
    "tiff": other_format("TIFF"),
    "truncated jpeg": picture()[:200],
    "jpeg header then garbage": picture()[:30] + b"\x00" * 500,
    "animated webp": animated("WEBP"),
    "animated png": animated("PNG"),
    "too small": picture(size=(100, 100)),
    "one pixel wide": picture(size=(1, 900)),
}


@pytest.mark.parametrize("label", list(HOSTILE))
def test_hostile_or_unsupported_files_are_refused_and_leave_nothing(
    admin: TestClient, storage: LocalStorage, db: Session, label: str
) -> None:
    before = read(admin)

    response = upload(admin, HOSTILE[label], filename="innocent.png", content_type="image/png")

    assert response.status_code in (413, 422), label
    assert response.json()["detail"]["code"] in ("invalid_image", "image_too_large")
    assert files_on_disk(storage) == []
    after = read(admin)
    assert after["images"] == before["images"] and after["updatedAt"] == before["updatedAt"]
    assert db.scalars(select(AuditLog)).first() is None


def test_pixel_bombs_are_refused_from_the_header(admin: TestClient, storage: LocalStorage) -> None:
    # Tiny on disk, huge when decoded.
    output = BytesIO()
    Image.new("1", (6000, 5000)).save(output, "PNG")  # 30 megapixels
    assert len(output.getvalue()) < 100_000
    wide = BytesIO()
    Image.new("1", (9000, 300)).save(wide, "PNG")

    for data in (output.getvalue(), wide.getvalue()):
        response = upload(admin, data, "a.png", "image/png")
        assert response.status_code == 422
        assert "too large" in response.json()["detail"]["message"]
    assert files_on_disk(storage) == []


def test_a_file_over_five_megabytes_is_refused(admin: TestClient, storage: LocalStorage) -> None:
    response = upload(admin, b"\xff\xd8\xff" + b"0" * (5 * 1024 * 1024 + 10))

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "image_too_large"
    assert files_on_disk(storage) == []


def test_a_far_larger_body_is_refused_from_the_headers_alone(admin: TestClient) -> None:
    response = admin.post(
        f"{ADMIN_PREFIX}/products/{TEE}/images",
        content=b"x" * (6 * 1024 * 1024),
        headers={"Content-Type": "multipart/form-data; boundary=x", "Origin": WEB_ORIGIN},
    )

    assert response.status_code == 413


def test_an_upload_that_does_not_say_its_size_is_refused(admin: TestClient) -> None:
    def chunks():
        yield b"--x\r\n"
        yield b"--x--\r\n"

    response = admin.post(
        f"{ADMIN_PREFIX}/products/{TEE}/images",
        content=chunks(),
        headers={"Content-Type": "multipart/form-data; boundary=x", "Origin": WEB_ORIGIN},
    )

    assert response.status_code == 411


def test_a_missing_file_or_version_is_a_422(admin: TestClient) -> None:
    version = read(admin)["updatedAt"]
    headers = {"Origin": WEB_ORIGIN}

    no_file = admin.post(
        f"{ADMIN_PREFIX}/products/{TEE}/images", data={"updatedAt": version}, headers=headers
    )
    no_version = admin.post(
        f"{ADMIN_PREFIX}/products/{TEE}/images",
        files={"file": ("a.jpg", picture(), "image/jpeg")},
        headers=headers,
    )

    assert no_file.status_code == 422 and no_version.status_code == 422


# ---------- limits, versions and cleanup ----------


def test_a_product_can_have_at_most_eight_images(admin: TestClient, storage: LocalStorage) -> None:
    for _ in range(6):  # the product starts with two
        assert upload(admin, picture()).status_code == 201

    response = upload(admin, picture())

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "too_many_images"
    assert len(read(admin)["images"]) == 8
    assert len(files_on_disk(storage)) == 6


def test_a_stale_upload_is_refused_and_stores_nothing(
    admin: TestClient, storage: LocalStorage
) -> None:
    stale = read(admin)["updatedAt"]
    upload(admin, picture())

    response = upload(admin, picture(), version=stale)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "stale_product"
    assert len(files_on_disk(storage)) == 1


def test_a_failed_save_leaves_no_file_and_no_row(
    admin: TestClient, storage: LocalStorage, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = read(admin)

    def broken(*args, **kwargs):
        raise RuntimeError("database went away")

    monkeypatch.setattr("app.services.admin_images.audit.record", broken)
    with pytest.raises(RuntimeError):
        upload(admin, picture())
    monkeypatch.undo()

    assert files_on_disk(storage) == []
    assert read(admin)["images"] == before["images"]


# ---------- removing ----------


def test_removing_an_upload_deletes_the_row_and_the_file(
    admin: TestClient, storage: LocalStorage, db: Session
) -> None:
    added = upload(admin, picture()).json()["images"][-1]
    assert len(files_on_disk(storage)) == 1

    response = remove(admin, added["id"])

    assert response.status_code == 200
    assert added["id"] not in [i["id"] for i in response.json()["images"]]
    assert files_on_disk(storage) == []
    assert TestClient(app).get(added["url"]).status_code == 404
    assert db.scalars(select(AuditLog).where(AuditLog.action == "product.image_removed")).one()


def test_removing_renumbers_so_a_later_upload_goes_last(admin: TestClient, db: Session) -> None:
    first, second = read(admin)["images"]
    added = upload(admin, picture()).json()["images"][-1]

    remove(admin, first["id"])
    newest = upload(admin, picture()).json()["images"][-1]

    positions = db.scalars(
        select(ProductImage.position)
        .where(ProductImage.product_id == TEE)
        .order_by(ProductImage.id)
    ).all()
    assert sorted(positions) == [0, 1, 2]  # no gaps and no two images in the same place
    shop = TestClient(app).get("/api/v1/products/essential-fitted-tee").json()
    assert shop["images"] == [second["url"], added["url"], newest["url"]]


def test_removing_a_placeholder_touches_no_files(admin: TestClient, storage: LocalStorage) -> None:
    placeholder = read(admin)["images"][0]

    assert remove(admin, placeholder["id"]).status_code == 200
    assert files_on_disk(storage) == []


def test_the_last_image_cannot_be_removed(admin: TestClient) -> None:
    first, second = read(admin)["images"]
    remove(admin, first["id"])

    response = remove(admin, second["id"])

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "last_image"
    assert len(read(admin)["images"]) == 1


def test_an_unknown_or_foreign_image_is_a_404(admin: TestClient) -> None:
    other = read(admin, "m-tee-01")["images"][0]

    assert remove(admin, 999999).status_code == 404
    assert remove(admin, other["id"], product_id=TEE).status_code == 404
    assert len(read(admin, "m-tee-01")["images"]) == 2


def test_a_stale_removal_is_refused(admin: TestClient) -> None:
    stale = read(admin)["updatedAt"]
    image = upload(admin, picture()).json()["images"][-1]

    response = remove(admin, image["id"], version=stale)

    assert response.status_code == 409
    assert len(read(admin)["images"]) == 3


def test_a_file_that_cannot_be_deleted_does_not_undo_the_removal(
    admin: TestClient, storage: LocalStorage, monkeypatch: pytest.MonkeyPatch
) -> None:
    added = upload(admin, picture()).json()["images"][-1]

    def failing(name: str) -> None:
        raise OSError("disk trouble")

    monkeypatch.setattr(storage, "delete", failing)

    assert remove(admin, added["id"]).status_code == 200
    assert added["id"] not in [i["id"] for i in read(admin)["images"]]


# ---------- reordering ----------


def test_reordering_changes_the_default_image(admin: TestClient, db: Session) -> None:
    first, second = read(admin)["images"]

    response = reorder(admin, [second["id"], first["id"]])

    assert response.status_code == 200
    assert [i["id"] for i in response.json()["images"]] == [second["id"], first["id"]]
    shop = TestClient(app).get("/api/v1/products/essential-fitted-tee").json()
    assert shop["images"][0] == second["url"]
    assert db.scalars(select(AuditLog).where(AuditLog.action == "product.images_reordered")).one()


def test_the_same_order_changes_nothing(admin: TestClient, db: Session) -> None:
    before = read(admin)

    response = reorder(admin, [i["id"] for i in before["images"]])

    assert response.status_code == 200
    assert response.json()["updatedAt"] == before["updatedAt"]
    assert db.scalars(select(AuditLog)).first() is None


@pytest.mark.parametrize("shape", ["duplicate", "missing", "extra", "foreign"])
def test_a_reorder_must_list_each_image_exactly_once(admin: TestClient, shape: str) -> None:
    first, second = [i["id"] for i in read(admin)["images"]]
    other = read(admin, "m-tee-01")["images"][0]["id"]
    ids = {
        "duplicate": [first, first],
        "missing": [first],
        "extra": [first, second, second + 1000],
        "foreign": [first, other],
    }[shape]

    assert reorder(admin, ids).status_code == 422
    assert [i["id"] for i in read(admin)["images"]] == [first, second]


def test_a_stale_reorder_is_refused(admin: TestClient) -> None:
    stale = read(admin)["updatedAt"]
    first, second = [i["id"] for i in read(admin)["images"]]
    upload(admin, picture())

    assert reorder(admin, [second, first], version=stale).status_code == 409


# ---------- serving files ----------


@pytest.mark.parametrize(
    "name",
    [
        "..%2F..%2F..%2Fetc%2Fpasswd",
        "%2e%2e%2f%2e%2e%2fsecret.png",
        "..",
        "a" * 32 + ".png",  # well formed but not there
        "A" * 32 + ".png",  # capitals are never generated
        "0" * 32 + ".svg",
        "0" * 32 + ".html",
        "0" * 32 + ".png/../x",
        "0" * 31 + ".png",
        "0" * 32 + ".PNG",
    ],
)
def test_media_only_serves_names_this_store_made(client: TestClient, name: str) -> None:
    assert client.get(f"{MEDIA}/{name}").status_code == 404


def test_media_will_not_serve_a_file_placed_under_another_name(
    client: TestClient, storage: LocalStorage
) -> None:
    storage.root.mkdir(parents=True)
    (storage.root / "secret.txt").write_text("private")
    (storage.root / ("0" * 32 + ".html")).write_text("<script>alert(1)</script>")

    assert client.get(f"{MEDIA}/secret.txt").status_code == 404
    assert client.get(f"{MEDIA}/{'0' * 32}.html").status_code == 404


def test_the_storage_refuses_bad_names_and_leaves_no_partial_files(
    storage: LocalStorage,
) -> None:
    with pytest.raises(ValueError):
        storage.save("../escape.png", b"x")
    with pytest.raises(ValueError):
        storage.save("secret.txt", b"x")

    storage.save("0" * 32 + ".png", b"data")
    storage.delete("../../etc/passwd")  # ignored, not an error

    assert files_on_disk(storage) == ["0" * 32 + ".png"]
