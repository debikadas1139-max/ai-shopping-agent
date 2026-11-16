import pytest

from app.config import get_settings
from app.services import image_service as img
from app.utils.errors import (
    BadRequestError,
    NotFoundError,
    PayloadTooLargeError,
    ServiceUnavailableError,
    UnsupportedMediaTypeError,
)

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 32
LIMIT = 3 * 1024 * 1024


def test_valid_images_are_accepted():
    assert img.validate_image("a.jpg", JPEG, LIMIT) == "image/jpeg"
    assert img.validate_image("a.JPEG", JPEG, LIMIT) == "image/jpeg"
    assert img.validate_image("a.png", PNG, LIMIT) == "image/png"
    assert img.validate_image("a.webp", WEBP, LIMIT) == "image/webp"


def test_wrong_extension_is_rejected():
    with pytest.raises(UnsupportedMediaTypeError):
        img.validate_image("a.gif", JPEG, LIMIT)
    with pytest.raises(UnsupportedMediaTypeError):
        img.validate_image("noextension", JPEG, LIMIT)


def test_fake_image_content_is_rejected():
    with pytest.raises(UnsupportedMediaTypeError):
        img.validate_image("evil.jpg", b"<script>alert(1)</script>", LIMIT)


def test_empty_and_oversized_files_are_rejected():
    with pytest.raises(BadRequestError):
        img.validate_image("a.jpg", b"", LIMIT)
    with pytest.raises(PayloadTooLargeError):
        img.validate_image("a.jpg", JPEG + b"\x00" * LIMIT, LIMIT)


def test_upload_storage_roundtrip_and_id_checks(tmp_path):
    image_id = img.save_upload(tmp_path, PNG, "image/png")
    data, mime = img.load_upload(tmp_path, image_id)
    assert data == PNG and mime == "image/png"
    with pytest.raises(BadRequestError):
        img.load_upload(tmp_path, "../../etc/passwd")
    with pytest.raises(NotFoundError):
        img.load_upload(tmp_path, "a" * 32)
    img.delete_upload(tmp_path, image_id)
    with pytest.raises(NotFoundError):
        img.load_upload(tmp_path, image_id)


def test_json_extraction_handles_fences_and_thinking():
    raw = '<think>hmm</think>\n```json\n{"product_type": "honey", "search_keywords": ["honey"]}\n```'
    assert img.extract_json_object(raw)["product_type"] == "honey"
    assert img.extract_json_object('Sure! {"a": 1} Hope that helps')["a"] == 1
    with pytest.raises(ValueError):
        img.extract_json_object("I cannot see an image")


def test_analysis_without_api_key_gives_a_clear_error(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")
    get_settings.cache_clear()
    try:
        with pytest.raises(ServiceUnavailableError) as info:
            img.analyze_image_bytes(JPEG, "image/jpeg")
        assert info.value.code == "ai_not_configured"
    finally:
        get_settings.cache_clear()


class FakeAnalysis:
    def __init__(self, product_type, keywords, is_organic=None):
        self.product_type, self.search_keywords, self.is_organic = product_type, keywords, is_organic


def test_catalog_matching_uses_keywords(db):
    matches, organic_used = img.find_matching_products(db, FakeAnalysis("honey", ["honey", "jar"], True))
    assert organic_used is True
    assert matches and all(m["is_organic"] for m in matches)
    assert matches[0]["matched_on"] == "honey"


def test_catalog_matching_with_unknown_product_returns_nothing(db):
    assert img.find_matching_products(db, FakeAnalysis("unknown", [])) == ([], False)
    matches, _ = img.find_matching_products(db, FakeAnalysis("spaceship", ["rocket"]))
    assert matches == []
