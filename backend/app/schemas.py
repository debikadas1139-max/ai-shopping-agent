"""Pydantic models: they validate incoming requests and shape outgoing responses.

The React app uses exactly these field names.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------- products
class ProductOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    price: float
    description: str = ""
    is_organic: bool
    average_rating: float
    review_count: int
    reason: Optional[str] = None  # filled by recommendations
    matched_on: Optional[str] = None  # filled by image search


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int


class ReviewOut(BaseModel):
    id: int
    product_id: int
    rating: float
    reviewer_name: Optional[str] = None
    review_text: Optional[str] = None


class CategoryOut(BaseModel):
    category: str
    product_count: int


# ---------------------------------------------------------------- compare
class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_ids: list[int] = Field(min_length=2, max_length=4)


class ComparisonHighlights(BaseModel):
    cheapest_id: int
    highest_rated_id: int
    most_reviewed_id: int
    price_difference: float
    same_category: bool
    organic_ids: list[int]


class ComparisonOut(BaseModel):
    products: list[ProductOut]
    highlights: ComparisonHighlights


# ---------------------------------------------------------------- cart and orders
class CartItemIn(BaseModel):
    """The browser sends only an id and a quantity. Prices are never accepted from the client."""

    model_config = ConfigDict(extra="forbid")
    product_id: int = Field(gt=0)
    quantity: int = Field(default=1, ge=1, le=99)


class CartValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[CartItemIn] = Field(min_length=1, max_length=50)


class CartLineOut(BaseModel):
    product_id: int
    name: str
    category: Optional[str] = None
    is_organic: bool
    unit_price: float
    quantity: int
    line_total: float


class CartOut(BaseModel):
    items: list[CartLineOut]
    total: float
    item_count: int


class OrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[CartItemIn] = Field(min_length=1, max_length=50)
    confirmed: bool
    confirmed_total: float = Field(ge=0)
    idempotency_key: str = Field(min_length=8, max_length=100)


class OrderItemOut(BaseModel):
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    line_total: float


class OrderOut(BaseModel):
    id: int
    created_at: str
    status: str
    total_amount: float
    item_count: int
    items: list[OrderItemOut]
    duplicate_request: bool = False


# ---------------------------------------------------------------- chat
class ShownProduct(BaseModel):
    id: int
    name: str


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)
    shown_products: list[ShownProduct] = Field(default_factory=list, max_length=12)


class ChatRequest(BaseModel):
    messages: list[ChatMessageIn] = Field(min_length=1, max_length=40)
    image_id: Optional[str] = Field(default=None, pattern=r"^[a-f0-9]{32}$")

    @field_validator("messages")
    @classmethod
    def last_message_is_from_user(cls, messages):
        if messages[-1].role != "user":
            raise ValueError("The last message must be from the user.")
        return messages


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductOut] = Field(default_factory=list)
    comparison: Optional[ComparisonOut] = None
    order_proposal: Optional[CartOut] = None
    tools_used: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------- image search
class ImageAnalysis(BaseModel):
    """What the vision model says it sees. Validated so bad model output can't crash the app."""

    product_type: str = Field(min_length=1, max_length=80)
    search_keywords: list[str] = Field(default_factory=list)
    is_organic: Optional[bool] = None
    visual_characteristics: list[str] = Field(default_factory=list)
    description: str = ""

    @field_validator("product_type", mode="before")
    @classmethod
    def clean_type(cls, value):
        return str(value).strip().lower()[:80] or "unknown"

    @field_validator("search_keywords", "visual_characteristics", mode="before")
    @classmethod
    def clean_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        return [str(v).strip().lower()[:60] for v in value if str(v).strip()][:6]

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value):
        return str(value or "").strip()[:300]


class ImageSearchOut(BaseModel):
    image_id: str
    analysis: ImageAnalysis
    matches: list[ProductOut]
    note: str


# ---------------------------------------------------------------- health
class HealthOut(BaseModel):
    status: str
    database: str
    ai_configured: bool
    demo_store: bool = True
    message: str
