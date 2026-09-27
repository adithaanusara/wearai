"""Serves the uploaded product images. Public, read only.

Only names this store made are served (32 hex characters and a known extension), so a request can
never reach another file. Browsers are told the exact type and not to guess it, and to keep the
image for a year: a file's name never changes, because every upload gets a new random one.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.storage import CONTENT_TYPES, LocalStorage, get_storage

router = APIRouter(tags=["media"])


@router.get("/media/{name}")
def get_media(name: str, storage: Annotated[LocalStorage, Depends(get_storage)]) -> FileResponse:
    path = storage.path_for(name)
    if path is None or not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(
        path,
        media_type=CONTENT_TYPES[path.suffix],
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "public, max-age=31536000, immutable",
            # If a file were ever opened as a page, it may load or run nothing.
            "Content-Security-Policy": "default-src 'none'; sandbox",
        },
    )
