import asyncio
import logging

from fastapi import APIRouter

from app.agent.shopping_agent import run_agent
from app.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """Send the conversation to the AI shopping agent.

    The agent runs in a worker thread (it makes slow network calls) so the server can keep serving other requests.
    If the AI provider fails, the matching error status (429 / 502 / 503) is returned; we never fake an answer.
    """
    messages = [m.model_dump() for m in body.messages]
    result = await asyncio.to_thread(run_agent, messages, body.image_id)
    return result
