"""Creates the Groq chat models (lazily) and turns provider errors into friendly AppErrors."""

import logging
from functools import lru_cache

from app.config import get_settings
from app.utils.errors import (
    AppError,
    RateLimitedError,
    ServiceUnavailableError,
    UpstreamError,
)

logger = logging.getLogger(__name__)


def require_api_key() -> None:
    if not get_settings().ai_configured:
        raise ServiceUnavailableError(
            "The AI assistant is not configured. Add your GROQ_API_KEY to backend/.env and restart the server.",
            code="ai_not_configured",
        )


@lru_cache
def get_chat_model():
    """Text model used by the shopping agent (needs tool-calling support)."""
    require_api_key()
    from langchain_groq import ChatGroq  # imported here so the app starts even without the AI packages

    # The Groq API key is read from the GROQ_API_KEY environment variable (loaded from .env).
    return ChatGroq(model=get_settings().groq_model, temperature=0)


@lru_cache
def get_vision_model():
    """Vision model used to read uploaded product photos."""
    require_api_key()
    from langchain_groq import ChatGroq

    return ChatGroq(model=get_settings().groq_vision_model, temperature=0)


def translate_llm_error(exc: Exception) -> AppError:
    """Map an exception from Groq/LangChain to a clear message for the user.

    We log only the exception type and message, never request headers or keys.
    """
    if isinstance(exc, AppError):
        return exc

    status = getattr(exc, "status_code", None)
    text = str(exc).lower()
    kind = type(exc).__name__
    logger.warning("AI request failed (%s): %s", kind, str(exc)[:300])

    if status == 429 or "rate_limit" in text or "rate limit" in text or "quota" in text:
        return RateLimitedError(
            "The AI service is rate limited or the Groq quota is used up. Wait a minute and try again, "
            "or check your usage at console.groq.com.",
            code="ai_rate_limited",
        )
    if status in (401, 403) or "invalid_api_key" in text or "invalid api key" in text:
        return ServiceUnavailableError(
            "Groq rejected the API key. Check GROQ_API_KEY in backend/.env.", code="ai_bad_key"
        )
    if (
        status == 404
        or "decommissioned" in text
        or "model_not_found" in text
        or "does not exist" in text
        or "model_not_active" in text
    ):
        return ServiceUnavailableError(
            "Groq does not offer the configured model any more. Update GROQ_MODEL / GROQ_VISION_MODEL in "
            "backend/.env (see console.groq.com/docs/models).",
            code="ai_model_unavailable",
        )
    if "tool_use_failed" in text or "failed_generation" in text:
        return UpstreamError(
            "The AI model produced an invalid tool call. Please try rephrasing your request.",
            code="ai_tool_call_failed",
        )
    if "connection" in kind.lower() or "timeout" in kind.lower() or "connect" in text:
        return ServiceUnavailableError(
            "Could not reach the Groq API. Check your internet connection and try again.", code="ai_unreachable"
        )
    return UpstreamError("The AI model request failed. Please try again.", code="ai_upstream_error")
