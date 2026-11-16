"""The shopping agent: a LangChain agent (powered by a Groq model) that decides which tools to call.

Flow for one chat request:
  1. Build the message list (previous turns + the new user message).
  2. agent.invoke(...) lets the model call tools (search, compare, ...) until it can answer.
  3. We read the tool results to build product cards, then return the model's final text.

This file does not import LangChain at the top, so the rest of the app (and the unit tests)
work even if the AI packages or the API key are missing.
"""

import json
import logging
import re
from functools import lru_cache
from typing import Optional

from app.database import db_session
from app.services import product_service
from app.services.image_service import message_text
from app.services.llm import get_chat_model, require_api_key, translate_llm_error
from app.utils.errors import AppError, UpstreamError

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 12
MAX_CARDS = 8

SYSTEM_PROMPT = """You are the shopping assistant of a small DEMONSTRATION grocery store. \
The products and reviews are sample data; nothing is really sold or shipped.

Store categories: {categories}.

RULES
1. Use tools for every fact about products. Never invent products, ids, prices, ratings, review counts or \
stock. The store does not track stock, so never say anything is "in stock" or "out of stock".
2. Prices are in US dollars. Ratings are average stars out of 5 from real review rows.
3. If the user names a product type that is a store category, pass it as `category`. Use `is_organic`, \
`max_price`, `min_price` and `min_rating` for those constraints instead of putting them in the query text.
4. SEARCH: call search_products with the user's constraints. Ratings are included in its result and the \
min_rating filter is already applied. Product cards are shown to the user automatically, so in your text \
mention the best 1-3 products by name with price and rating and do not repeat every detail.
5. COMPARE: find the products with search_products, then call compare_products with their ids, then explain \
the real differences briefly (price, rating, review count, organic).
6. RECOMMEND: call recommend_products and explain using the "reason" field.
7. IMAGE: if the user's message says an image was attached, call analyze_product_image with that image_id, then \
search_products using the result. Say the matches are approximate because they come from keywords, not visual \
similarity. If the analysis returns an error, tell the user what the error says.
8. BUYING: you can NEVER place an order. If the user clearly wants to buy specific products, call prepare_order \
with the product ids (taken from earlier tool results or from "[Products shown ...]" notes) and quantities, then \
tell them to review and confirm the order summary shown below your message. Never say an order was placed. \
If it is unclear which product they want, ask. Do not call prepare_order just because they searched or compared.
9. If no products match, say so and suggest relaxing one filter. If a tool returns an error, explain it plainly.
10. Be brief and friendly. Plain text only: no markdown tables, no bold, no code blocks. Stay on topic (shopping)."""


@lru_cache
def get_agent():
    """Build the agent once. Imports LangChain here (lazily)."""
    from langchain.agents import create_agent

    from app.agent.tools import ALL_TOOLS

    with db_session() as conn:
        categories = ", ".join(c["category"] for c in product_service.list_categories(conn))
    return create_agent(
        model=get_chat_model(),
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT.format(categories=categories or "none yet"),
    )


def build_history(messages: list, image_id: Optional[str] = None) -> list:
    """Turn API messages into LangChain-style dicts.

    Product cards are shown by the website, not stored in the text, so we append a short note with the
    ids that were shown. That lets the model answer "order the second one" using real ids.
    """
    history = []
    for message in messages[-MAX_HISTORY_MESSAGES:]:
        content = message["content"]
        shown = message.get("shown_products") or []
        if message["role"] == "assistant" and shown:
            names = "; ".join(f"{p['name']} (ID:{p['id']})" for p in shown)
            content += f"\n[Products shown to the user with this message: {names}]"
        history.append({"role": message["role"], "content": content})
    if image_id and history and history[-1]["role"] == "user":
        history[-1]["content"] += f"\n[The user attached a product image. image_id={image_id}]"
    return history


def _clean_reply(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()


def build_result(agent_messages: list) -> dict:
    """Read the agent's message list and extract the reply, product cards and tool names (this turn only)."""
    last_human = max((i for i, m in enumerate(agent_messages) if getattr(m, "type", "") == "human"), default=-1)
    turn = agent_messages[last_human + 1 :]

    products, comparison, proposal, tools_used = [], None, None, []
    for message in turn:
        if getattr(message, "type", "") != "tool":
            continue
        name = getattr(message, "name", "") or ""
        tools_used.append(name)
        try:
            data = json.loads(message_text(message.content))
        except (TypeError, ValueError):
            continue
        if not isinstance(data, dict) or "error" in data:
            continue
        if name in ("search_products", "recommend_products"):
            products = data.get("products", [])
            comparison = None
        elif name == "compare_products":
            comparison = data
            products = []
        elif name == "prepare_order":
            proposal = data.get("summary")

    reply = ""
    for message in reversed(turn):
        if getattr(message, "type", "") == "ai":
            reply = _clean_reply(message_text(message.content))
            if reply:
                break
    if not reply:
        reply = "Here is what I found." if (products or comparison or proposal) else "Sorry, I could not produce an answer. Please try again."

    return {
        "reply": reply,
        "products": products[:MAX_CARDS],
        "comparison": comparison,
        "order_proposal": proposal,
        "tools_used": list(dict.fromkeys(tools_used)),
    }


def run_agent(messages: list, image_id: Optional[str] = None) -> dict:
    """Run the agent (blocking). The API calls this in a worker thread so the server stays responsive."""
    require_api_key()
    history = build_history(messages, image_id)
    try:
        result = get_agent().invoke({"messages": history}, config={"recursion_limit": 14})
    except AppError:
        raise
    except Exception as exc:
        if "recursion" in type(exc).__name__.lower():
            raise UpstreamError(
                "The assistant needed too many steps for that request. Try a simpler question.",
                code="ai_too_many_steps",
            )
        raise translate_llm_error(exc)
    return build_result(result["messages"])
