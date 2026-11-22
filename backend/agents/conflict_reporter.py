"""Agent 4: Conflict Reporter.

Collects screening evidence from other agents, ranks candidate matches,
generates structured explanations, and produces JSON-compatible report
data. Supports both Gemini-powered and deterministic explanations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from backend.core.config import settings


@dataclass
class MatchReport:
    """A single candidate match for the report."""
    trademark_id: str
    mark_name: str
    textual_similarity: float
    phonetic_similarity: float
    goods_overlap: float
    combined_score: float
    priority: str
    requires_human_review: bool
    explanation: str
    evidence: dict = field(default_factory=dict)
    nice_classes: list[int] = field(default_factory=list)
    jurisdiction: str = ""


@dataclass
class ScreeningReport:
    """Full screening report."""
    screening_id: str
    proposed_mark: str
    jurisdiction: str
    goods_description: str
    nice_classes: list[int]
    status: str
    search_completeness: str
    matches: list[MatchReport]
    screening_date: str
    data_sources: list[str]
    warnings: list[str] = field(default_factory=list)
    report_available: bool = True

    def to_dict(self) -> dict:
        return {
            "screening_id": self.screening_id,
            "proposed_mark": self.proposed_mark,
            "jurisdiction": self.jurisdiction,
            "goods_description": self.goods_description,
            "nice_classes": self.nice_classes,
            "status": self.status,
            "search_completeness": self.search_completeness,
            "matches": [
                {
                    "trademark_id": m.trademark_id,
                    "mark_name": m.mark_name,
                    "textual_similarity": round(m.textual_similarity, 1),
                    "phonetic_similarity": round(m.phonetic_similarity, 1),
                    "goods_overlap": round(m.goods_overlap, 1),
                    "combined_score": round(m.combined_score, 1),
                    "priority": m.priority,
                    "requires_human_review": m.requires_human_review,
                    "explanation": m.explanation,
                    "evidence": m.evidence,
                    "nice_classes": m.nice_classes,
                    "jurisdiction": m.jurisdiction,
                }
                for m in self.matches
            ],
            "screening_date": self.screening_date,
            "data_sources": self.data_sources,
            "search_completeness": self.search_completeness,
            "warnings": self.warnings,
            "report_available": self.report_available,
        }


class ConflictReporter:
    """Collects evidence, ranks matches, and generates reports."""

    def __init__(self):
        self.weight_phonetic = settings.weight_phonetic
        self.weight_textual = settings.weight_textual
        self.weight_goods = settings.weight_goods
        self.threshold_high = settings.threshold_high
        self.threshold_medium = settings.threshold_medium
        self.threshold_low = settings.threshold_low

    def calculate_combined_score(
        self,
        phonetic: float,
        textual: float,
        goods: float,
    ) -> float:
        """Calculate S = wP*P + wT*T + wG*G."""
        return (
            self.weight_phonetic * phonetic
            + self.weight_textual * textual
            + self.weight_goods * goods
        )

    def determine_priority(self, score: float) -> str:
        """Determine screening priority from combined score."""
        if score >= self.threshold_high:
            return "high"
        elif score >= self.threshold_medium:
            return "medium"
        elif score >= self.threshold_low:
            return "low"
        else:
            return "insufficient"

    def should_escalate(self, score: float, priority: str) -> bool:
        """Determine if human review is needed."""
        return priority == "high" or score >= 70

    def generate_explanation(
        self,
        proposed: str,
        candidate: str,
        textual: float,
        phonetic: float,
        goods: float,
        combined: float,
        priority: str,
        phonetic_signals: list[str] | None = None,
        goods_explanation: str = "",
    ) -> str:
        """Generate a deterministic explanation of the screening result.

        This is the fallback when Gemini is unavailable. It uses the actual
        computed similarity scores — no values are invented.
        """
        lines = [
            f'Screening analysis for "{proposed}" against "{candidate}":',
            "",
            f"  Textual similarity:  {textual:.1f}/100",
            f"  Phonetic similarity: {phonetic:.1f}/100",
            f"  Goods/services overlap: {goods:.1f}/100",
            f"  Combined screening score: {combined:.1f}/100",
            f"  Priority: {priority.upper()}",
            "",
        ]

        # Textual interpretation
        if textual >= 85:
            lines.append(f'  The names "{proposed}" and "{candidate}" are textually very similar.')
        elif textual >= 60:
            lines.append(f'  The names show moderate textual similarity.')
        else:
            lines.append(f'  The names are textually distinct.')

        # Phonetic interpretation
        if phonetic >= 85:
            lines.append(f'  The marks are likely to sound very similar when spoken.')
        elif phonetic >= 60:
            lines.append(f'  The marks have some phonetic resemblance.')

        # Goods interpretation
        if goods >= 80:
            lines.append(f'  The goods/services are in the same or closely related categories.')
        elif goods >= 50:
            lines.append(f'  There is some overlap in goods/services categories.')

        if phonetic_signals:
            lines.append(f"  Matching signals: {', '.join(phonetic_signals)}")

        if goods_explanation:
            lines.append(f"  Goods analysis: {goods_explanation}")

        # Disclaimer
        lines.extend([
            "",
            "  DISCLAIMER: This is an automated preliminary screening result.",
            "  It is not legal advice and does not constitute a formal trademark",
            "  clearance opinion. Consult a qualified trademark attorney for",
            "  definitive guidance.",
        ])

        return "\n".join(lines)

    async def generate_gemini_explanation(
        self,
        proposed: str,
        candidate: str,
        textual: float,
        phonetic: float,
        goods: float,
        combined: float,
        priority: str,
    ) -> str | None:
        """Attempt to use Gemini API for explanation generation.

        Returns None if Gemini is unavailable, allowing fallback.
        The prompt provides the computed scores so Gemini cannot invent them.
        """
        if not settings.has_gemini:
            return None

        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""You are a trademark screening assistant. Based on the COMPUTED similarity 
scores below, provide a brief, professional explanation. Do NOT invent any scores, 
registry IDs, legal citations, or trademark registrations. Only explain the provided data.

Proposed mark: "{proposed}"
Existing mark: "{candidate}"
Textual similarity: {textual:.1f}/100
Phonetic similarity: {phonetic:.1f}/100
Goods/services overlap: {goods:.1f}/100
Combined screening score: {combined:.1f}/100
Priority level: {priority}

Provide a 2-3 sentence explanation of why these marks may or may not conflict.
End with a note that this is automated screening, not legal advice."""

            response = await model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=300,
                    temperature=0.3,
                ),
            )
            return response.text
        except Exception:
            return None

    def rank_matches(self, matches: list[MatchReport]) -> list[MatchReport]:
        """Rank matches by combined score, highest first."""
        return sorted(matches, key=lambda m: m.combined_score, reverse=True)

    def build_report(
        self,
        screening_id: str,
        proposed_mark: str,
        jurisdiction: str,
        goods_description: str,
        nice_classes: list[int],
        matches: list[MatchReport],
        warnings: list[str] | None = None,
    ) -> ScreeningReport:
        """Build a complete screening report."""
        ranked = self.rank_matches(matches)

        # Determine overall status
        has_high = any(m.priority == "high" for m in ranked)
        status = "awaiting_review" if has_high else "completed"

        return ScreeningReport(
            screening_id=screening_id,
            proposed_mark=proposed_mark,
            jurisdiction=jurisdiction,
            goods_description=goods_description,
            nice_classes=nice_classes,
            status=status,
            search_completeness="complete_for_sample_dataset",
            matches=ranked[:20],  # Top 20 matches
            screening_date=datetime.now(timezone.utc).isoformat(),
            data_sources=["synthetic_demo_dataset"],
            warnings=warnings or [],
        )


# Module-level singleton
conflict_reporter = ConflictReporter()
