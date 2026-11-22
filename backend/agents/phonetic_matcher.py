"""Agent 2: Phonetic Matcher.

Calculates textual and phonetic similarity between trademarks using
RapidFuzz for string similarity and Double Metaphone for phonetic
representations. Returns normalized similarity scores and explanations.

Limitations:
- Double Metaphone is optimized for English phonetics. Indian-language
  names, transliterations (e.g. Hindi, Tamil, Telugu), and non-Latin
  scripts may produce inaccurate phonetic codes.
- Transliteration variants (e.g. "Shri" vs "Sri") may not be fully captured.
- Tonal and aspirated distinctions in many Indian languages are not modeled.
"""

from dataclasses import dataclass, field
from rapidfuzz import fuzz
from metaphone import doublemetaphone


@dataclass
class PhoneticResult:
    """Result of phonetic matching between two marks."""
    query: str
    candidate: str
    textual_similarity: float  # 0-100
    phonetic_similarity: float  # 0-100
    phonetic_codes_query: tuple[str, str] = ("", "")
    phonetic_codes_candidate: tuple[str, str] = ("", "")
    matching_signals: list[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "candidate": self.candidate,
            "textual_similarity": round(self.textual_similarity, 1),
            "phonetic_similarity": round(self.phonetic_similarity, 1),
            "phonetic_codes_query": self.phonetic_codes_query,
            "phonetic_codes_candidate": self.phonetic_codes_candidate,
            "matching_signals": self.matching_signals,
            "explanation": self.explanation,
        }


class PhoneticMatcher:
    """Computes textual and phonetic similarity between trademark names."""

    def compare(self, query: str, candidate: str) -> PhoneticResult:
        """Compare two trademark names.

        Args:
            query: The proposed trademark (normalized).
            candidate: An existing trademark to compare against (normalized).

        Returns:
            PhoneticResult with similarity scores and explanation.
        """
        if not query or not candidate:
            return PhoneticResult(
                query=query or "",
                candidate=candidate or "",
                textual_similarity=0.0,
                phonetic_similarity=0.0,
                explanation="One or both marks are empty.",
            )

        q = query.lower().strip()
        c = candidate.lower().strip()

        # ── Textual similarity ──────────────────────────────────────────
        ratio = fuzz.ratio(q, c)
        partial = fuzz.partial_ratio(q, c)
        token_sort = fuzz.token_sort_ratio(q, c)
        token_set = fuzz.token_set_ratio(q, c)

        # Weighted combination of textual metrics
        textual = 0.40 * ratio + 0.20 * partial + 0.20 * token_sort + 0.20 * token_set

        # ── Phonetic similarity ─────────────────────────────────────────
        q_codes = doublemetaphone(q)
        c_codes = doublemetaphone(c)

        phonetic_score = self._phonetic_score(q_codes, c_codes)

        # ── Matching signals ────────────────────────────────────────────
        signals: list[str] = []
        if ratio >= 90:
            signals.append("Near-exact textual match")
        elif ratio >= 70:
            signals.append("High textual similarity")
        elif ratio >= 50:
            signals.append("Moderate textual similarity")

        if phonetic_score >= 90:
            signals.append("Identical phonetic representation")
        elif phonetic_score >= 70:
            signals.append("Similar pronunciation")
        elif phonetic_score >= 50:
            signals.append("Partially similar pronunciation")

        if partial >= 90 and ratio < 70:
            signals.append("One mark contains the other")

        if token_set >= 90 and ratio < 70:
            signals.append("Shared word tokens")

        # ── Explanation ─────────────────────────────────────────────────
        explanation = self._build_explanation(
            q, c, textual, phonetic_score, q_codes, c_codes, signals
        )

        return PhoneticResult(
            query=q,
            candidate=c,
            textual_similarity=textual,
            phonetic_similarity=phonetic_score,
            phonetic_codes_query=q_codes,
            phonetic_codes_candidate=c_codes,
            matching_signals=signals,
            explanation=explanation,
        )

    def _phonetic_score(
        self,
        codes_a: tuple[str, str],
        codes_b: tuple[str, str],
    ) -> float:
        """Calculate phonetic similarity from Double Metaphone codes.

        Compares primary and secondary codes from both marks.
        Returns a score between 0 and 100.
        """
        if not any(codes_a) or not any(codes_b):
            return 0.0

        scores: list[float] = []

        # Compare all code pairs
        pairs = []
        for ca in codes_a:
            for cb in codes_b:
                if ca and cb:
                    pairs.append((ca, cb))

        if not pairs:
            return 0.0

        for ca, cb in pairs:
            if ca == cb:
                scores.append(100.0)
            else:
                # Use fuzz.ratio on the metaphone codes themselves
                scores.append(fuzz.ratio(ca, cb))

        # Primary-primary match has the most weight
        primary_score = 0.0
        if codes_a[0] and codes_b[0]:
            primary_score = 100.0 if codes_a[0] == codes_b[0] else fuzz.ratio(codes_a[0], codes_b[0])

        best_cross = max(scores) if scores else 0.0

        # 70% weight on primary codes, 30% on best cross-match
        return 0.70 * primary_score + 0.30 * best_cross

    def _build_explanation(
        self,
        query: str,
        candidate: str,
        textual: float,
        phonetic: float,
        q_codes: tuple[str, str],
        c_codes: tuple[str, str],
        signals: list[str],
    ) -> str:
        """Build a human-readable explanation of the matching."""
        parts = [
            f'Comparison of "{query}" vs "{candidate}":',
            f"  Textual similarity: {textual:.1f}/100",
            f"  Phonetic similarity: {phonetic:.1f}/100",
            f"  Phonetic codes: {q_codes} vs {c_codes}",
        ]
        if signals:
            parts.append(f"  Signals: {', '.join(signals)}")
        else:
            parts.append("  No strong similarity signals detected.")

        return "\n".join(parts)

    def compare_batch(
        self,
        query: str,
        candidates: list[str],
    ) -> list[PhoneticResult]:
        """Compare a query against multiple candidates."""
        return [self.compare(query, c) for c in candidates]


# Module-level singleton
phonetic_matcher = PhoneticMatcher()
