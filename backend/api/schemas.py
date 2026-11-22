"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field
from datetime import datetime


# ─── Request Schemas ─────────────────────────────────────────────────────────

class ScreeningRequest(BaseModel):
    brand_name: str = Field(..., min_length=1, max_length=200, description="The proposed trademark")
    goods: str = Field(..., min_length=1, max_length=1000, description="Goods/services description")
    nice_class: int | None = Field(None, ge=1, le=45, description="Primary Nice class")
    nice_classes: list[int] = Field(default_factory=list, description="Additional Nice classes")
    jurisdiction: str = Field("IN", min_length=2, max_length=10, description="Jurisdiction code")


class ReviewRequest(BaseModel):
    reviewer: str = Field(..., min_length=1, max_length=100)
    decision: str = Field(..., pattern="^(approved|rejected|needs_more_info|escalated)$")
    notes: str | None = Field(None, max_length=2000)


# ─── Response Schemas ────────────────────────────────────────────────────────

class MatchResponse(BaseModel):
    trademark_id: str
    mark_name: str
    textual_similarity: float
    phonetic_similarity: float
    goods_overlap: float
    combined_score: float
    priority: str
    requires_human_review: bool
    explanation: str = ""
    evidence: dict = {}
    nice_classes: list[int] = []
    jurisdiction: str = ""


class ScreeningResponse(BaseModel):
    screening_id: str
    proposed_mark: str
    jurisdiction: str
    status: str
    search_completeness: str = "complete_for_sample_dataset"
    total_candidates: int = 0
    matches: list[MatchResponse] = []
    report_available: bool = False
    created_at: datetime | None = None
    completed_at: datetime | None = None


class ScreeningListItem(BaseModel):
    screening_id: str
    proposed_mark: str
    jurisdiction: str
    status: str
    total_candidates: int
    created_at: datetime | None = None


class HistoryResponse(BaseModel):
    items: list[ScreeningListItem]
    total: int
    page: int
    page_size: int


class TrademarkSearchResponse(BaseModel):
    trademarks: list[dict]
    total: int


class NiceClassResponse(BaseModel):
    class_number: int
    title: str
    description: str
    example_goods: list[str] = []
    related_classes: list[int] = []


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    database: str = "connected"
    timestamp: str = ""


class ReviewResponse(BaseModel):
    id: str
    screening_id: str
    reviewer: str
    decision: str
    notes: str | None = None
    reviewed_at: datetime | None = None


class ErrorResponse(BaseModel):
    detail: str
    error_code: str = "UNKNOWN_ERROR"
