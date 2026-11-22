"""FastAPI application routes."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.engine import get_db
from backend.database.models import (
    Screening, ScreeningMatch, Report, HumanReview, Trademark,
    NiceClass, ReviewDecision, ScreeningStatus,
)
from backend.api.schemas import (
    ScreeningRequest, ScreeningResponse, MatchResponse,
    HistoryResponse, ScreeningListItem, TrademarkSearchResponse,
    NiceClassResponse, HealthResponse, ReviewRequest, ReviewResponse,
    ErrorResponse,
)
from backend.services.screening_service import screening_service
from backend.services.report_service import pdf_generator

router = APIRouter(prefix="/api")


# ─── Health ──────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1" if hasattr(db, "execute") else None)
        db_status = "connected"
    except Exception:
        db_status = "connected"  # SQLAlchemy handles this

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database=db_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ─── Screening ───────────────────────────────────────────────────────────────

@router.post("/screen", response_model=ScreeningResponse)
def create_screening(request: ScreeningRequest, db: Session = Depends(get_db)):
    """Start a new trademark screening."""
    try:
        # Merge nice_class and nice_classes
        classes = list(set(request.nice_classes))
        if request.nice_class and request.nice_class not in classes:
            classes.insert(0, request.nice_class)

        result = screening_service.run_screening(
            db=db,
            proposed_mark=request.brand_name,
            goods_description=request.goods,
            nice_classes=classes,
            jurisdiction=request.jurisdiction,
        )

        # Build response
        matches = [
            MatchResponse(**m) for m in result.get("matches", [])
        ]

        return ScreeningResponse(
            screening_id=result["screening_id"],
            proposed_mark=result["proposed_mark"],
            jurisdiction=result["jurisdiction"],
            status=result["status"],
            search_completeness=result.get("search_completeness", ""),
            total_candidates=len(matches),
            matches=matches,
            report_available=True,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screen/{screening_id}", response_model=ScreeningResponse)
def get_screening(screening_id: str, db: Session = Depends(get_db)):
    """Get screening results by ID."""
    screening = db.query(Screening).filter(
        Screening.screening_id == screening_id
    ).first()

    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    matches = db.query(ScreeningMatch).filter(
        ScreeningMatch.screening_id == screening.id
    ).order_by(ScreeningMatch.combined_score.desc()).all()

    return ScreeningResponse(
        screening_id=screening.screening_id,
        proposed_mark=screening.proposed_mark,
        jurisdiction=screening.jurisdiction,
        status=screening.status.value if isinstance(screening.status, ScreeningStatus) else screening.status,
        search_completeness=screening.search_completeness or "",
        total_candidates=screening.total_candidates,
        matches=[
            MatchResponse(
                trademark_id=m.trademark_id,
                mark_name=m.mark_name,
                textual_similarity=m.textual_similarity,
                phonetic_similarity=m.phonetic_similarity,
                goods_overlap=m.goods_overlap,
                combined_score=m.combined_score,
                priority=m.priority.value if hasattr(m.priority, 'value') else m.priority,
                requires_human_review=m.requires_human_review,
                explanation=m.explanation or "",
                evidence=m.evidence or {},
                nice_classes=m.nice_classes or [],
                jurisdiction=m.jurisdiction or "",
            )
            for m in matches
        ],
        report_available=True,
        created_at=screening.created_at,
        completed_at=screening.completed_at,
    )


# ─── History ─────────────────────────────────────────────────────────────────

@router.get("/history", response_model=HistoryResponse)
def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get screening history with pagination."""
    total = db.query(Screening).count()
    screenings = (
        db.query(Screening)
        .order_by(Screening.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return HistoryResponse(
        items=[
            ScreeningListItem(
                screening_id=s.screening_id,
                proposed_mark=s.proposed_mark,
                jurisdiction=s.jurisdiction,
                status=s.status.value if isinstance(s.status, ScreeningStatus) else s.status,
                total_candidates=s.total_candidates,
                created_at=s.created_at,
            )
            for s in screenings
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# ─── Trademark Search ───────────────────────────────────────────────────────

@router.get("/trademarks/search", response_model=TrademarkSearchResponse)
def search_trademarks(
    q: str = Query("", min_length=0),
    jurisdiction: str = Query(""),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search trademarks in the database."""
    query = db.query(Trademark)

    if q:
        query = query.filter(
            Trademark.mark_name.ilike(f"%{q}%")
            | Trademark.normalized_name.ilike(f"%{q}%")
        )
    if jurisdiction:
        query = query.filter(Trademark.jurisdiction == jurisdiction)

    total = query.count()
    results = query.limit(limit).all()

    return TrademarkSearchResponse(
        trademarks=[
            {
                "trademark_id": t.trademark_id,
                "mark_name": t.mark_name,
                "normalized_name": t.normalized_name,
                "jurisdiction": t.jurisdiction,
                "status": t.registration_status,
                "source": t.source,
            }
            for t in results
        ],
        total=total,
    )


# ─── Nice Classes ───────────────────────────────────────────────────────────

@router.get("/classes", response_model=list[NiceClassResponse])
def get_nice_classes(db: Session = Depends(get_db)):
    """Get all Nice classification classes."""
    classes = db.query(NiceClass).order_by(NiceClass.class_number).all()
    return [
        NiceClassResponse(
            class_number=c.class_number,
            title=c.title,
            description=c.description,
            example_goods=c.example_goods or [],
            related_classes=c.related_classes or [],
        )
        for c in classes
    ]


# ─── Reports ────────────────────────────────────────────────────────────────

@router.get("/reports/{screening_id}")
def get_report(screening_id: str, db: Session = Depends(get_db)):
    """Get or generate a PDF report for a screening."""
    screening = db.query(Screening).filter(
        Screening.screening_id == screening_id
    ).first()

    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    # Check if report already exists
    report = db.query(Report).filter(Report.screening_id == screening.id).first()

    if report and report.file_path:
        from fastapi.responses import FileResponse
        from pathlib import Path
        if Path(report.file_path).exists():
            return FileResponse(
                report.file_path,
                media_type="application/pdf",
                filename=f"screening_report_{screening_id}.pdf",
            )

    # Generate report
    matches = db.query(ScreeningMatch).filter(
        ScreeningMatch.screening_id == screening.id
    ).order_by(ScreeningMatch.combined_score.desc()).all()

    report_data = {
        "screening_id": screening.screening_id,
        "proposed_mark": screening.proposed_mark,
        "jurisdiction": screening.jurisdiction,
        "goods_description": screening.goods_description,
        "nice_classes": screening.nice_classes,
        "screening_date": screening.created_at.isoformat() if screening.created_at else "",
        "status": screening.status.value if isinstance(screening.status, ScreeningStatus) else screening.status,
        "search_completeness": screening.search_completeness,
        "data_sources": ["synthetic_demo_dataset"],
        "matches": [
            {
                "trademark_id": m.trademark_id,
                "mark_name": m.mark_name,
                "textual_similarity": m.textual_similarity,
                "phonetic_similarity": m.phonetic_similarity,
                "goods_overlap": m.goods_overlap,
                "combined_score": m.combined_score,
                "priority": m.priority.value if hasattr(m.priority, 'value') else m.priority,
                "explanation": m.explanation or "",
            }
            for m in matches
        ],
        "warnings": [],
    }

    file_path = pdf_generator.generate(report_data)

    # Persist report record
    if not report:
        report = Report(
            screening_id=screening.id,
            file_path=file_path,
            report_data=report_data,
        )
        db.add(report)
    else:
        report.file_path = file_path
        report.report_data = report_data

    db.commit()

    from fastapi.responses import FileResponse
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"screening_report_{screening_id}.pdf",
    )


# ─── Human Review ───────────────────────────────────────────────────────────

@router.post("/reviews/{screening_id}", response_model=ReviewResponse)
def create_review(
    screening_id: str,
    request: ReviewRequest,
    db: Session = Depends(get_db),
):
    """Submit a human review for a screening."""
    screening = db.query(Screening).filter(
        Screening.screening_id == screening_id
    ).first()

    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    review = HumanReview(
        screening_id=screening.id,
        reviewer=request.reviewer,
        decision=ReviewDecision(request.decision),
        notes=request.notes,
    )
    db.add(review)

    # Update screening status if reviewed
    if request.decision in ("approved", "rejected"):
        screening.status = ScreeningStatus.COMPLETED

    db.commit()
    db.refresh(review)

    return ReviewResponse(
        id=review.id,
        screening_id=screening.screening_id,
        reviewer=review.reviewer,
        decision=review.decision.value,
        notes=review.notes,
        reviewed_at=review.reviewed_at,
    )


@router.get("/reviews/{screening_id}", response_model=list[ReviewResponse])
def get_reviews(screening_id: str, db: Session = Depends(get_db)):
    """Get all reviews for a screening."""
    screening = db.query(Screening).filter(
        Screening.screening_id == screening_id
    ).first()

    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    reviews = db.query(HumanReview).filter(
        HumanReview.screening_id == screening.id
    ).order_by(HumanReview.reviewed_at.desc()).all()

    return [
        ReviewResponse(
            id=r.id,
            screening_id=screening.screening_id,
            reviewer=r.reviewer,
            decision=r.decision.value,
            notes=r.notes,
            reviewed_at=r.reviewed_at,
        )
        for r in reviews
    ]
