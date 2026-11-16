"""Product-photo handling: validation, temporary storage, vision-model analysis, catalog matching.

IMPORTANT: image search here is TEXT-BASED. The vision model turns the photo into a
product type and keywords, and then we search the catalog with those words. It does not
compare pixels, so results are approximate.
"""

import base64
import json
import logging
import re
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.services import product_service
from app.services.llm import get_vision_model, require_api_key, translate_llm_error
from app.utils.errors import (
    AppError,
    BadRequestError,
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
    UpstreamError,
)

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
MIME_TO_EXTENSION = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
_IMAGE_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")
UPLOAD_MAX_AGE_SECONDS = 3600


# ---------------------------------------------------------------- validation
def detect_image_type(data: bytes) -> Optional[str]:
    """Identify JPEG/PNG/WebP from the first bytes of the file (the 'magic number')."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image(filename: str, data: bytes, max_bytes: int) -> str:
    """Return the real MIME type, or raise an AppError explaining what is wrong."""
    extension = Path(filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise UnsupportedMediaTypeError(
            "Unsupported file type. Please upload a JPG, JPEG, PNG or WebP image.", code="unsupported_image_type"
        )
    if not data:
        raise BadRequestError("The uploaded file is empty.", code="empty_file")
    if len(data) > max_bytes:
        raise PayloadTooLargeError(
            f"The image is too large. The maximum size is {max_bytes // (1024 * 1024)} MB.", code="image_too_large"
        )
    detected = detect_image_type(data)
    if detected is None:
        raise UnsupportedMediaTypeError(
            "The file is not a valid JPG, PNG or WebP image.", code="invalid_image_content"
        )
    return detected


# ---------------------------------------------------------------- temporary storage
def cleanup_old_uploads(upload_dir: Path, max_age_seconds: int = UPLOAD_MAX_AGE_SECONDS) -> None:
    if not upload_dir.exists():
        return
    cutoff = time.time() - max_age_seconds
    for path in upload_dir.iterdir():
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            logger.warning("Could not delete old upload %s", path.name)


def save_upload(upload_dir: Path, data: bytes, mime: str) -> str:
    """Save an upload under a random name and return its image_id. Old files are removed."""
    upload_dir.mkdir(parents=True, exist_ok=True)
    cleanup_old_uploads(upload_dir)
    image_id = uuid.uuid4().hex
    (upload_dir / f"{image_id}{MIME_TO_EXTENSION[mime]}").write_bytes(data)
    return image_id


def load_upload(upload_dir: Path, image_id: str) -> tuple:
    """Return (bytes, mime) for a saved upload. The id is strictly checked, so paths can't be injected."""
    if not isinstance(image_id, str) or not _IMAGE_ID_PATTERN.match(image_id):
        raise BadRequestError("Invalid image_id.", code="invalid_image_id")
    for extension, mime in (".jpg", "image/jpeg"), (".png", "image/png"), (".webp", "image/webp"):
        path = upload_dir / f"{image_id}{extension}"
        if path.is_file():
            return path.read_bytes(), mime
    raise NotFoundError("That image is no longer available. Please upload it again.", code="image_not_found")


def delete_upload(upload_dir: Path, image_id: str) -> None:
    for extension in MIME_TO_EXTENSION.values():
        try:
            (upload_dir / f"{image_id}{extension}").unlink()
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------- vision model
VISION_PROMPT = (
    "You help a grocery store search its catalog from a customer's photo. "
    "Look at the product in the image. The store sells honey, oils, nuts, seeds, grains, tea, coffee, snacks "
    "and dairy alternatives (plant milks). "
    "Reply with ONLY a JSON object, no other text, with these fields:\n"
    '- "product_type": short singular noun for what the product is (for example "honey", "olive oil", '
    '"almonds"), or "unknown" if the image is not a food or drink product\n'
    '- "search_keywords": up to 5 lowercase words that would appear in a product name or description\n'
    '- "is_organic": true if the label clearly says organic, false if it clearly does not, null if unclear\n'
    '- "visual_characteristics": up to 5 short phrases describing what you can actually see '
    '(container, colour, label text)\n'
    '- "description": one sentence describing the product\n'
    "Only describe what is visible. Do not guess brands or details you cannot see."
)


def extract_json_object(text: str) -> dict:
    """Pull the first JSON object out of a model reply (handles ```json fences and <think> blocks)."""
    cleaned = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found")
    value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("JSON is not an object")
    return value


def message_text(content) -> str:
    """LangChain message content can be a string or a list of blocks; return plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return str(content or "")


def analyze_image_bytes(data: bytes, mime: str):
    """Ask the vision model about the photo. Returns a validated ImageAnalysis (Pydantic model)."""
    require_api_key()  # fail early with a clear message if there is no Groq key

    from langchain_core.messages import HumanMessage
    from pydantic import ValidationError

    from app.schemas import ImageAnalysis

    encoded = base64.b64encode(data).decode()
    message = HumanMessage(
        content=[
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
            {"type": "text", "text": VISION_PROMPT},
        ]
    )
    try:
        response = get_vision_model().invoke([message])
    except AppError:
        raise
    except Exception as exc:  # network, quota, bad model name, ...
        raise translate_llm_error(exc)

    try:
        return ImageAnalysis.model_validate(extract_json_object(message_text(response.content)))
    except (ValueError, ValidationError) as exc:
        logger.warning("Vision model returned unusable output: %s", str(exc)[:200])
        raise UpstreamError(
            "The vision model's answer could not be understood. Try again or use a clearer photo.",
            code="ai_bad_output",
        )


# ---------------------------------------------------------------- catalog matching
def find_matching_products(conn: sqlite3.Connection, analysis, limit: int = 12) -> tuple:
    """Search the catalog with the analysis keywords.

    Returns (matches, organic_filter_used). Each match has a `matched_on` keyword.
    """
    terms = []
    for term in [analysis.product_type, *analysis.search_keywords]:
        term = (term or "").strip().lower()
        if len(term) >= 2 and term != "unknown" and term not in terms:
            terms.append(term)
    if not terms:
        return [], False

    attempts = [True, None] if analysis.is_organic is True else [None]
    for organic in attempts:
        found: dict = {}
        for term in terms:
            items, _ = product_service.list_products(conn, query=term, is_organic=organic, sort="rating_desc", limit=20)
            for product in items:
                found.setdefault(product["id"], {**product, "matched_on": term})
        if found:
            return list(found.values())[:limit], organic is True
    return [], False
