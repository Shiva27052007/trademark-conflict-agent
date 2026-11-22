"""SQLAlchemy ORM models for the trademark screening system."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Boolean,
    ForeignKey, JSON, Index, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum

from backend.database.engine import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ScreeningStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    FAILED = "failed"
    AWAITING_REVIEW = "awaiting_review"


class ReviewDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MORE_INFO = "needs_more_info"
    ESCALATED = "escalated"


class Priority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


# ─── Trademark Records ───────────────────────────────────────────────────────

class Trademark(Base):
    __tablename__ = "trademarks"

    id = Column(String, primary_key=True, default=gen_uuid)
    trademark_id = Column(String, unique=True, nullable=False, index=True)
    mark_name = Column(String, nullable=False, index=True)
    normalized_name = Column(String, nullable=False, index=True)
    jurisdiction = Column(String, nullable=False, index=True)
    registration_status = Column(String, default="sample_record")
    source = Column(String, default="synthetic_demo")
    source_type = Column(String, default="synthetic")
    data_timestamp = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    goods_services = relationship("TrademarkGoodsService", back_populates="trademark", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_trademarks_normalized_jurisdiction", "normalized_name", "jurisdiction"),
    )


class TrademarkGoodsService(Base):
    __tablename__ = "trademark_goods_services"

    id = Column(String, primary_key=True, default=gen_uuid)
    trademark_id = Column(String, ForeignKey("trademarks.id"), nullable=False)
    nice_class = Column(Integer, nullable=False, index=True)
    description = Column(Text, nullable=False)

    trademark = relationship("Trademark", back_populates="goods_services")


class NiceClass(Base):
    __tablename__ = "nice_classes"

    id = Column(Integer, primary_key=True)
    class_number = Column(Integer, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    example_goods = Column(JSON, default=list)
    related_classes = Column(JSON, default=list)


# ─── Screening ───────────────────────────────────────────────────────────────

class Screening(Base):
    __tablename__ = "screenings"

    id = Column(String, primary_key=True, default=gen_uuid)
    screening_id = Column(String, unique=True, nullable=False, index=True)
    proposed_mark = Column(String, nullable=False)
    normalized_mark = Column(String, nullable=False)
    goods_description = Column(Text, nullable=False)
    nice_classes = Column(JSON, default=list)
    jurisdiction = Column(String, nullable=False)
    status = Column(SAEnum(ScreeningStatus), default=ScreeningStatus.PENDING)
    search_completeness = Column(String, default="complete_for_sample_dataset")
    total_candidates = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    matches = relationship("ScreeningMatch", back_populates="screening", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="screening", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("HumanReview", back_populates="screening", cascade="all, delete-orphan")
    workflow_events = relationship("WorkflowEvent", back_populates="screening", cascade="all, delete-orphan")


class ScreeningMatch(Base):
    __tablename__ = "screening_matches"

    id = Column(String, primary_key=True, default=gen_uuid)
    screening_id = Column(String, ForeignKey("screenings.id"), nullable=False)
    trademark_id = Column(String, nullable=False)
    mark_name = Column(String, nullable=False)
    textual_similarity = Column(Float, default=0.0)
    phonetic_similarity = Column(Float, default=0.0)
    goods_overlap = Column(Float, default=0.0)
    combined_score = Column(Float, default=0.0)
    priority = Column(SAEnum(Priority), default=Priority.LOW)
    requires_human_review = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)
    evidence = Column(JSON, default=dict)
    nice_classes = Column(JSON, default=list)
    jurisdiction = Column(String, nullable=True)

    screening = relationship("Screening", back_populates="matches")

    __table_args__ = (
        Index("ix_screening_matches_score", "combined_score"),
    )


# ─── Reports ────────────────────────────────────────────────────────────────

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=gen_uuid)
    screening_id = Column(String, ForeignKey("screenings.id"), nullable=False, unique=True)
    file_path = Column(String, nullable=True)
    generated_at = Column(DateTime, default=utcnow)
    report_data = Column(JSON, default=dict)

    screening = relationship("Screening", back_populates="report")


# ─── Human Review ───────────────────────────────────────────────────────────

class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(String, primary_key=True, default=gen_uuid)
    screening_id = Column(String, ForeignKey("screenings.id"), nullable=False)
    reviewer = Column(String, nullable=False)
    decision = Column(SAEnum(ReviewDecision), nullable=False)
    notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=utcnow)

    screening = relationship("Screening", back_populates="reviews")


# ─── Workflow Events ────────────────────────────────────────────────────────

class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id = Column(String, primary_key=True, default=gen_uuid)
    screening_id = Column(String, ForeignKey("screenings.id"), nullable=False)
    node_name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # started, completed, failed, skipped
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    screening = relationship("Screening", back_populates="workflow_events")
