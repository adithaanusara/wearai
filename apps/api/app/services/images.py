"""Checks and cleans an uploaded image. The file is treated as hostile.

Nothing about the upload is trusted: not its name, its content type or its extension. The bytes are
decoded with Pillow and, if they really are a supported image, drawn again into a new file. That
drops metadata (such as GPS position) and anything hidden inside or after the image data.
"""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.services.admin import AdminError

MAX_BYTES = 5 * 1024 * 1024
MIN_SIDE = 200
MAX_SIDE = 8000
MAX_PIXELS = 25_000_000
# Stored images are shrunk to this on the long edge, so a phone photo does not cost megabytes.
STORED_LONG_EDGE = 2000

# Pillow reports many phone JPEGs as "MPO" (a JPEG that can hold several pictures); the first is
# used.
_FORMATS = {"JPEG": ".jpg", "MPO": ".jpg", "PNG": ".png", "WEBP": ".webp"}


@dataclass(frozen=True)
class ProcessedImage:
    data: bytes
    extension: str


def _reject(message: str, code: str = "invalid_image", status: int = 422) -> AdminError:
    return AdminError(status, message, code=code)


def process_upload(data: bytes) -> ProcessedImage:
    if len(data) > MAX_BYTES:
        raise _reject("The image is too large (at most 5 MB).", "image_too_large", 413)
    if not data:
        raise _reject("This file is empty.")

    try:
        image = Image.open(BytesIO(data))
        extension = _FORMATS.get(image.format or "")
        if extension is None:
            raise _reject("Only JPEG, PNG and WebP images are accepted.")

        # Only the header has been read so far, so oversized images are turned away before any
        # pixel is decoded.
        width, height = image.size
        if min(width, height) < MIN_SIDE:
            raise _reject(f"The image must be at least {MIN_SIDE} pixels on each side.")
        if max(width, height) > MAX_SIDE or width * height > MAX_PIXELS:
            raise _reject(
                "The image is too large: at most 8,000 pixels on a side and 25 megapixels."
            )
        if image.format != "MPO" and getattr(image, "n_frames", 1) > 1:
            raise _reject("Animated images are not supported.")

        image.load()
    except AdminError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError, SyntaxError):
        raise _reject("This file is not a valid image.") from None

    # Turn the picture the right way up first, because the orientation note is dropped below.
    image = ImageOps.exif_transpose(image)
    image.thumbnail((STORED_LONG_EDGE, STORED_LONG_EDGE), Image.Resampling.LANCZOS)

    output = BytesIO()
    if extension == ".jpg":
        image.convert("RGB").save(output, "JPEG", quality=85, optimize=True, progressive=True)
    else:
        has_alpha = image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info
        image = image.convert("RGBA" if has_alpha else "RGB")
        if extension == ".png":
            image.save(output, "PNG", optimize=True)
        else:
            image.save(output, "WEBP", quality=85)
    return ProcessedImage(output.getvalue(), extension)
