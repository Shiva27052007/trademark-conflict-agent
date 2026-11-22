"""Screening service: orchestrates the screening workflow."""

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.database.models import (
    Screening, ScreeningMatch, ScreeningStatus, Priority, Trademark,
    TrademarkGoodsService, WorkflowEvent,
)
from backend.agents.normalizer import normalizer
from backend.agents.phonetic_matcher import phonetic_matcher
from backend.agents.class_overlap import class_overlap_agent
from backend.agents.conflict_reporter import conflict_reporter, MatchReport


class ScreeningService:
    """Runs the trademark screening pipeline."""

    def run_screening(
        self,
        db: Session,
        proposed_mark: str,
        goods_description: str,
        nice_classes: list[int],
        jurisdiction: str,
    ) -> dict:
        """Execute the full screening pipeline.

        1. Validate input
        2. Normalize the proposed mark
        3. Retrieve candidate trademarks
        4. Calculate similarity scores
        5. Rank and report results
        6. Persist to database
        """
        screening_id = f"SCR-{uuid.uuid4().hex[:8].upper()}"
        start_time = datetime.now(timezone.utc)

        # Create screening record
        norm_result = normalizer.normalize(proposed_mark)
        screening = Screening(
            screening_id=screening_id,
            proposed_mark=proposed_mark,
            normalized_mark=norm_result.normalized,
            goods_description=goods_description,
            nice_classes=nice_classes,
            jurisdiction=jurisdiction,
            status=ScreeningStatus.PROCESSING,
        )
        db.add(screening)
        db.flush()

        self._log_event(db, screening.id, "validate_input", "completed")
        self._log_event(db, screening.id, "normalize_mark", "completed")

        try:
            # Retrieve candidates
            candidates = self._retrieve_candidates(db, norm_result.normalized, jurisdiction, nice_classes)
            self._log_event(db, screening.id, "retrieve_candidates", "completed",
                            output_data={"count": len(candidates)})

            # Score each candidate
            match_reports: list[MatchReport] = []
            for candidate in candidates:
                # Phonetic + textual
                phonetic_result = phonetic_matcher.compare(
                    norm_result.normalized,
                    candidate["normalized_name"],
                )

                # Class overlap
                class_result = class_overlap_agent.compare(
                    nice_classes,
                    candidate["nice_classes"],
                    goods_description,
                    candidate["goods_description"],
                )

                # Combined score
                textual = phonetic_result.textual_similarity
                phonetic = phonetic_result.phonetic_similarity
                goods = class_result.combined_goods_score

                combined = conflict_reporter.calculate_combined_score(
                    phonetic, textual, goods
                )
                priority = conflict_reporter.determine_priority(combined)
                needs_review = conflict_reporter.should_escalate(combined, priority)

                explanation = conflict_reporter.generate_explanation(
                    proposed=proposed_mark,
                    candidate=candidate["mark_name"],
                    textual=textual,
                    phonetic=phonetic,
                    goods=goods,
                    combined=combined,
                    priority=priority,
                    phonetic_signals=phonetic_result.matching_signals,
                    goods_explanation=class_result.explanation,
                )

                match_reports.append(MatchReport(
                    trademark_id=candidate["trademark_id"],
                    mark_name=candidate["mark_name"],
                    textual_similarity=textual,
                    phonetic_similarity=phonetic,
                    goods_overlap=goods,
                    combined_score=combined,
                    priority=priority,
                    requires_human_review=needs_review,
                    explanation=explanation,
                    evidence={
                        "phonetic_codes_query": list(phonetic_result.phonetic_codes_query),
                        "phonetic_codes_candidate": list(phonetic_result.phonetic_codes_candidate),
                        "matching_signals": phonetic_result.matching_signals,
                        "overlapping_classes": class_result.overlapping_classes,
                        "related_classes": class_result.related_classes,
                    },
                    nice_classes=candidate["nice_classes"],
                    jurisdiction=candidate.get("jurisdiction", ""),
                ))

            self._log_event(db, screening.id, "calculate_similarity", "completed")

            # Build report
            report = conflict_reporter.build_report(
                screening_id=screening_id,
                proposed_mark=proposed_mark,
                jurisdiction=jurisdiction,
                goods_description=goods_description,
                nice_classes=nice_classes,
                matches=match_reports,
            )
            self._log_event(db, screening.id, "generate_report", "completed")

            # Persist matches
            for m in report.matches:
                db_match = ScreeningMatch(
                    screening_id=screening.id,
                    trademark_id=m.trademark_id,
                    mark_name=m.mark_name,
                    textual_similarity=m.textual_similarity,
                    phonetic_similarity=m.phonetic_similarity,
                    goods_overlap=m.goods_overlap,
                    combined_score=m.combined_score,
                    priority=Priority(m.priority),
                    requires_human_review=m.requires_human_review,
                    explanation=m.explanation,
                    evidence=m.evidence,
                    nice_classes=m.nice_classes,
                    jurisdiction=m.jurisdiction,
                )
                db.add(db_match)

            # Update screening status
            screening.status = ScreeningStatus(report.status)
            screening.total_candidates = len(match_reports)
            screening.completed_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(screening)

            return report.to_dict()

        except Exception as e:
            screening.status = ScreeningStatus.FAILED
            screening.error_message = str(e)
            self._log_event(db, screening.id, "screening_pipeline", "failed",
                            error_message=str(e))
            db.commit()
            raise

    def _retrieve_candidates(
        self,
        db: Session,
        normalized_query: str,
        jurisdiction: str,
        nice_classes: list[int],
    ) -> list[dict]:
        """Retrieve candidate trademarks from the database."""
        from rapidfuzz import fuzz as rfuzz
        from metaphone import doublemetaphone

        q_codes = doublemetaphone(normalized_query)

        # Query all trademarks in the jurisdiction (or all if jurisdiction is broad)
        query = db.query(Trademark)
        if jurisdiction:
            query = query.filter(Trademark.jurisdiction == jurisdiction)

        all_marks = query.all()

        candidates = []
        for tm in all_marks:
            # Fuzzy string comparison
            ratio = rfuzz.ratio(normalized_query, tm.normalized_name)
            partial = rfuzz.partial_ratio(normalized_query, tm.normalized_name)

            # Phonetic match check during retrieval
            tm_codes = doublemetaphone(tm.normalized_name)
            phonetic_match = False
            if q_codes[0] and tm_codes[0]:
                if q_codes[0] == tm_codes[0] or (q_codes[1] and q_codes[1] == tm_codes[0]) or (tm_codes[1] and q_codes[0] == tm_codes[1]):
                    phonetic_match = True

            # Get goods/services
            goods_list = db.query(TrademarkGoodsService).filter(
                TrademarkGoodsService.trademark_id == tm.id
            ).all()

            tm_classes = [gs.nice_class for gs in goods_list]
            tm_description = "; ".join(gs.description for gs in goods_list)

            # Class overlap
            class_overlap = bool(set(nice_classes) & set(tm_classes)) if nice_classes else False

            # Include if any textual, phonetic, or category similarity signal is present
            if ratio >= 28 or partial >= 50 or phonetic_match or class_overlap:
                candidates.append({
                    "trademark_id": tm.trademark_id,
                    "mark_name": tm.mark_name,
                    "normalized_name": tm.normalized_name,
                    "nice_classes": tm_classes,
                    "goods_description": tm_description,
                    "jurisdiction": tm.jurisdiction,
                    "status": tm.registration_status,
                })

        return candidates

    def _log_event(
        self,
        db: Session,
        screening_id: str,
        node_name: str,
        status: str,
        input_data: dict | None = None,
        output_data: dict | None = None,
        error_message: str | None = None,
    ):
        event = WorkflowEvent(
            screening_id=screening_id,
            node_name=node_name,
            status=status,
            input_data=input_data,
            output_data=output_data,
            error_message=error_message,
        )
        db.add(event)
        db.flush()


# Module-level singleton
screening_service = ScreeningService()
