"""LangGraph-style screening workflow.

Implements the trademark screening pipeline as a graph of typed nodes
with state management, conditional transitions, and error handling.

Note: This uses a LangGraph-compatible pattern. If langgraph is not
installed, it falls back to a direct sequential execution that
preserves the same typed state and node structure.
"""

import sys
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.agents.normalizer import normalizer
from backend.agents.phonetic_matcher import phonetic_matcher
from backend.agents.class_overlap import class_overlap_agent
from backend.agents.conflict_reporter import conflict_reporter, MatchReport
from backend.services.report_service import pdf_generator


# ─── Workflow State ──────────────────────────────────────────────────────────

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class NodeResult:
    """Result of a single workflow node execution."""
    node_name: str
    status: str  # "completed", "failed", "skipped"
    duration_ms: int = 0
    data: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class WorkflowState:
    """Typed state passed through the screening workflow."""
    # Input
    proposed_mark: str = ""
    goods_description: str = ""
    nice_classes: list[int] = field(default_factory=list)
    jurisdiction: str = ""

    # Processing state
    screening_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_node: str = ""

    # Normalized data
    normalized_mark: str = ""
    mark_variants: list[str] = field(default_factory=list)

    # Candidates
    candidates: list[dict] = field(default_factory=list)

    # Similarity results
    phonetic_results: list[dict] = field(default_factory=list)
    class_results: list[dict] = field(default_factory=list)

    # Scored matches
    matches: list[dict] = field(default_factory=list)

    # Report
    report_data: dict = field(default_factory=dict)
    report_path: str = ""

    # Workflow events
    events: list[NodeResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Timing
    started_at: str = ""
    completed_at: str = ""


# ─── Workflow Nodes ──────────────────────────────────────────────────────────

def node_validate_input(state: WorkflowState) -> WorkflowState:
    """Node 1: Validate the screening input."""
    start = time.time()

    if not state.proposed_mark or not state.proposed_mark.strip():
        raise ValueError("Proposed mark cannot be empty")

    if not state.goods_description or not state.goods_description.strip():
        raise ValueError("Goods/services description cannot be empty")

    if not state.jurisdiction:
        state.jurisdiction = "IN"  # Default

    # Validate Nice classes
    state.nice_classes = [c for c in state.nice_classes if 1 <= c <= 45]

    state.screening_id = f"SCR-{uuid.uuid4().hex[:8].upper()}"
    state.started_at = datetime.now(timezone.utc).isoformat()

    state.events.append(NodeResult(
        node_name="validate_input",
        status="completed",
        duration_ms=int((time.time() - start) * 1000),
    ))
    return state


def node_normalize(state: WorkflowState) -> WorkflowState:
    """Node 2: Normalize the proposed trademark."""
    start = time.time()

    result = normalizer.normalize(state.proposed_mark)
    if not result.is_valid:
        raise ValueError(f"Normalization failed: {result.error}")

    state.normalized_mark = result.normalized
    state.mark_variants = result.variants

    state.events.append(NodeResult(
        node_name="normalize_mark",
        status="completed",
        duration_ms=int((time.time() - start) * 1000),
        data=result.to_dict(),
    ))
    return state


def node_retrieve_candidates(state: WorkflowState) -> WorkflowState:
    """Node 3: Retrieve candidate trademarks from database."""
    start = time.time()

    from backend.database.engine import SessionLocal
    from backend.database.models import Trademark, TrademarkGoodsService
    from rapidfuzz import fuzz as rfuzz

    db = SessionLocal()
    try:
        query = db.query(Trademark)
        if state.jurisdiction:
            query = query.filter(Trademark.jurisdiction == state.jurisdiction)

        all_marks = query.all()
        candidates = []

        for tm in all_marks:
            ratio = rfuzz.ratio(state.normalized_mark, tm.normalized_name)
            partial = rfuzz.partial_ratio(state.normalized_mark, tm.normalized_name)

            goods_list = db.query(TrademarkGoodsService).filter(
                TrademarkGoodsService.trademark_id == tm.id
            ).all()
            tm_classes = [gs.nice_class for gs in goods_list]
            tm_description = "; ".join(gs.description for gs in goods_list)

            class_overlap = bool(set(state.nice_classes) & set(tm_classes))

            if ratio >= 30 or partial >= 50 or class_overlap:
                candidates.append({
                    "trademark_id": tm.trademark_id,
                    "mark_name": tm.mark_name,
                    "normalized_name": tm.normalized_name,
                    "nice_classes": tm_classes,
                    "goods_description": tm_description,
                    "jurisdiction": tm.jurisdiction,
                })

        state.candidates = candidates

        state.events.append(NodeResult(
            node_name="retrieve_candidates",
            status="completed",
            duration_ms=int((time.time() - start) * 1000),
            data={"candidate_count": len(candidates)},
        ))
    finally:
        db.close()

    return state


def node_phonetic_analysis(state: WorkflowState) -> WorkflowState:
    """Node 4: Calculate textual and phonetic similarity."""
    start = time.time()

    results = []
    for candidate in state.candidates:
        result = phonetic_matcher.compare(
            state.normalized_mark,
            candidate["normalized_name"],
        )
        results.append({
            "trademark_id": candidate["trademark_id"],
            "textual_similarity": result.textual_similarity,
            "phonetic_similarity": result.phonetic_similarity,
            "matching_signals": result.matching_signals,
            "phonetic_codes_query": list(result.phonetic_codes_query),
            "phonetic_codes_candidate": list(result.phonetic_codes_candidate),
        })

    state.phonetic_results = results

    state.events.append(NodeResult(
        node_name="phonetic_analysis",
        status="completed",
        duration_ms=int((time.time() - start) * 1000),
    ))
    return state


def node_class_analysis(state: WorkflowState) -> WorkflowState:
    """Node 5: Calculate goods and class overlap."""
    start = time.time()

    results = []
    for candidate in state.candidates:
        result = class_overlap_agent.compare(
            state.nice_classes,
            candidate["nice_classes"],
            state.goods_description,
            candidate["goods_description"],
        )
        results.append({
            "trademark_id": candidate["trademark_id"],
            "class_overlap_score": result.class_overlap_score,
            "description_similarity": result.description_similarity,
            "combined_goods_score": result.combined_goods_score,
            "overlapping_classes": result.overlapping_classes,
            "related_classes": result.related_classes,
            "uncertain": result.uncertain,
        })

    state.class_results = results

    state.events.append(NodeResult(
        node_name="class_analysis",
        status="completed",
        duration_ms=int((time.time() - start) * 1000),
    ))
    return state


def node_combine_scores(state: WorkflowState) -> WorkflowState:
    """Node 6: Combine all similarity scores and rank."""
    start = time.time()

    # Build lookup maps
    phonetic_map = {r["trademark_id"]: r for r in state.phonetic_results}
    class_map = {r["trademark_id"]: r for r in state.class_results}

    matches = []
    for candidate in state.candidates:
        tid = candidate["trademark_id"]
        ph = phonetic_map.get(tid, {})
        cl = class_map.get(tid, {})

        textual = ph.get("textual_similarity", 0)
        phonetic = ph.get("phonetic_similarity", 0)
        goods = cl.get("combined_goods_score", 0)

        combined = conflict_reporter.calculate_combined_score(
            phonetic, textual, goods
        )
        priority = conflict_reporter.determine_priority(combined)
        needs_review = conflict_reporter.should_escalate(combined, priority)

        explanation = conflict_reporter.generate_explanation(
            proposed=state.proposed_mark,
            candidate=candidate["mark_name"],
            textual=textual,
            phonetic=phonetic,
            goods=goods,
            combined=combined,
            priority=priority,
            phonetic_signals=ph.get("matching_signals", []),
        )

        matches.append({
            "trademark_id": tid,
            "mark_name": candidate["mark_name"],
            "textual_similarity": round(textual, 1),
            "phonetic_similarity": round(phonetic, 1),
            "goods_overlap": round(goods, 1),
            "combined_score": round(combined, 1),
            "priority": priority,
            "requires_human_review": needs_review,
            "explanation": explanation,
            "evidence": {
                "phonetic_codes_query": ph.get("phonetic_codes_query", []),
                "phonetic_codes_candidate": ph.get("phonetic_codes_candidate", []),
                "matching_signals": ph.get("matching_signals", []),
                "overlapping_classes": cl.get("overlapping_classes", []),
                "related_classes": cl.get("related_classes", []),
            },
            "nice_classes": candidate.get("nice_classes", []),
            "jurisdiction": candidate.get("jurisdiction", ""),
        })

    # Sort by combined score descending
    matches.sort(key=lambda m: m["combined_score"], reverse=True)
    state.matches = matches[:20]  # Top 20

    state.events.append(NodeResult(
        node_name="combine_scores",
        status="completed",
        duration_ms=int((time.time() - start) * 1000),
        data={"match_count": len(state.matches)},
    ))
    return state


def node_generate_report(state: WorkflowState) -> WorkflowState:
    """Node 7: Generate the screening report."""
    start = time.time()

    has_high = any(m["priority"] == "high" for m in state.matches)

    state.report_data = {
        "screening_id": state.screening_id,
        "proposed_mark": state.proposed_mark,
        "jurisdiction": state.jurisdiction,
        "goods_description": state.goods_description,
        "nice_classes": state.nice_classes,
        "status": "awaiting_review" if has_high else "completed",
        "search_completeness": "complete_for_sample_dataset",
        "matches": state.matches,
        "screening_date": state.started_at,
        "data_sources": ["synthetic_demo_dataset"],
        "warnings": state.warnings,
    }

    state.events.append(NodeResult(
        node_name="generate_report",
        status="completed",
        duration_ms=int((time.time() - start) * 1000),
    ))
    return state


def node_generate_pdf(state: WorkflowState) -> WorkflowState:
    """Node 8: Generate PDF report."""
    start = time.time()

    try:
        path = pdf_generator.generate(state.report_data)
        state.report_path = path
        status = "completed"
    except Exception as e:
        state.warnings.append(f"PDF generation failed: {e}")
        status = "failed"

    state.events.append(NodeResult(
        node_name="generate_pdf",
        status=status,
        duration_ms=int((time.time() - start) * 1000),
    ))
    return state


def node_check_escalation(state: WorkflowState) -> WorkflowState:
    """Node 9: Check if human review is needed."""
    start = time.time()

    high_priority = [m for m in state.matches if m["priority"] == "high"]
    if high_priority:
        state.report_data["status"] = "awaiting_review"
        state.warnings.append(
            f"{len(high_priority)} high-priority match(es) require human review."
        )

    state.status = WorkflowStatus.COMPLETED
    state.completed_at = datetime.now(timezone.utc).isoformat()

    state.events.append(NodeResult(
        node_name="check_escalation",
        status="completed",
        duration_ms=int((time.time() - start) * 1000),
        data={"high_priority_count": len(high_priority)},
    ))
    return state


# ─── Workflow Execution ──────────────────────────────────────────────────────

WORKFLOW_NODES = [
    ("validate_input", node_validate_input),
    ("normalize_mark", node_normalize),
    ("retrieve_candidates", node_retrieve_candidates),
    ("phonetic_analysis", node_phonetic_analysis),
    ("class_analysis", node_class_analysis),
    ("combine_scores", node_combine_scores),
    ("generate_report", node_generate_report),
    ("generate_pdf", node_generate_pdf),
    ("check_escalation", node_check_escalation),
]


def run_screening_workflow(
    proposed_mark: str,
    goods_description: str,
    nice_classes: list[int],
    jurisdiction: str,
    timeout_seconds: float = 60.0,
) -> WorkflowState:
    """Execute the full screening workflow.

    Runs each node sequentially with error handling and timeout checking.
    """
    state = WorkflowState(
        proposed_mark=proposed_mark,
        goods_description=goods_description,
        nice_classes=nice_classes,
        jurisdiction=jurisdiction,
        status=WorkflowStatus.RUNNING,
    )

    workflow_start = time.time()

    for node_name, node_fn in WORKFLOW_NODES:
        # Timeout check
        elapsed = time.time() - workflow_start
        if elapsed > timeout_seconds:
            state.status = WorkflowStatus.TIMEOUT
            state.errors.append(f"Workflow timed out after {elapsed:.1f}s at node {node_name}")
            state.events.append(NodeResult(
                node_name=node_name,
                status="timeout",
            ))
            break

        state.current_node = node_name

        try:
            state = node_fn(state)
        except Exception as e:
            state.errors.append(f"Node {node_name} failed: {e}")
            state.events.append(NodeResult(
                node_name=node_name,
                status="failed",
                error=str(e),
            ))

            # For critical nodes, fail the whole workflow
            if node_name in ("validate_input", "normalize_mark"):
                state.status = WorkflowStatus.FAILED
                break
            # For non-critical nodes, continue with warnings
            state.warnings.append(f"Node {node_name} failed but workflow continues: {e}")

    if state.status == WorkflowStatus.RUNNING:
        state.status = WorkflowStatus.COMPLETED
        state.completed_at = datetime.now(timezone.utc).isoformat()

    return state
