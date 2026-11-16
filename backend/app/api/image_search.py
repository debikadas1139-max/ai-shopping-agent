import asyncio
import logging
import sqlite3

from fastapi import APIRouter, Depends, File, UploadFile

from app.config import get_settings
from app.database import get_db
from app.schemas import ImageSearchOut
from app.services import image_service
from app.services.image_service import analyze_image_bytes
from app.utils.errors import AppError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["image-search"])

APPROXIMATE_NOTE = (
    "These matches are approximate. The photo is turned into a product type and keywords by an AI model, "
    "then the catalog is searched with those words. It is not a pixel-level visual similarity search."
)


@router.post("/image-search", response_model=ImageSearchOut)
async def image_search(file: UploadFile = File(...), conn: sqlite3.Connection = Depends(get_db)):
    """Upload a JPG/PNG/WebP photo (multipart/form-data, field name 'file')."""
    settings = get_settings()
    # Read at most max+1 bytes so a huge upload can't fill memory.
    data = await file.read(settings.max_image_bytes + 1)
    mime = image_service.validate_image(file.filename or "", data, settings.max_image_bytes)

    image_id = image_service.save_upload(settings.upload_dir, data, mime)
    try:
        analysis = await asyncio.to_thread(analyze_image_bytes, data, mime)
        matches, organic_used = image_service.find_matching_products(conn, analysis)
    except AppError:
        image_service.delete_upload(settings.upload_dir, image_id)
        raise

    note = APPROXIMATE_NOTE
    if not matches:
        note = "No catalog products matched this photo. Try a clearer photo, or browse the catalog. " + APPROXIMATE_NOTE
    elif analysis.is_organic and not organic_used:
        note = "No organic matches were found, so non-organic matches are shown. " + APPROXIMATE_NOTE
    return {"image_id": image_id, "analysis": analysis, "matches": matches, "note": note}
