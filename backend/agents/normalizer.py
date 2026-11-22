"""Agent 1: Mark Normalizer.

Responsible for normalizing trademark text for comparison while
preserving the original form. Handles Unicode, casing, punctuation,
and whitespace to produce comparison-friendly variants.
"""

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class NormalizerResult:
    """Structured output from the normalizer."""
    original: str
    normalized: str
    variants: list[str] = field(default_factory=list)
    tokens: list[str] = field(default_factory=list)
    is_valid: bool = True
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "original": self.original,
            "normalized": self.normalized,
            "variants": self.variants,
            "tokens": self.tokens,
            "is_valid": self.is_valid,
            "error": self.error,
        }


class MarkNormalizer:
    """Normalizes trademarks for comparison."""

    def normalize(self, mark: str) -> NormalizerResult:
        """Normalize a trademark, preserving the original.

        Args:
            mark: The proposed or existing trademark name.

        Returns:
            NormalizerResult with original, normalized form, and variants.
        """
        # Handle empty / invalid input
        if not mark or not mark.strip():
            return NormalizerResult(
                original=mark or "",
                normalized="",
                is_valid=False,
                error="Empty or whitespace-only trademark input",
            )

        original = mark.strip()

        # Unicode NFC normalization
        nfc = unicodedata.normalize("NFC", original)

        # Lowercase
        lower = nfc.lower()

        # Remove accents / diacritics for one variant
        nfkd = unicodedata.normalize("NFKD", lower)
        no_accents = "".join(
            ch for ch in nfkd if unicodedata.category(ch) != "Mn"
        )

        # Strip punctuation and special characters for the core normalized form
        alpha_only = re.sub(r"[^a-z0-9]", "", no_accents)

        # Generate variants
        variants: list[str] = []
        # Variant 1: lowered original (preserves hyphens/spaces)
        variants.append(lower)
        # Variant 2: accents removed but punctuation kept
        if no_accents != lower:
            variants.append(no_accents)
        # Variant 3: alpha-only
        if alpha_only != lower and alpha_only != no_accents:
            variants.append(alpha_only)
        # Variant 4: hyphen/space collapsed
        collapsed = re.sub(r"[\s\-_]+", "", lower)
        if collapsed not in variants:
            variants.append(collapsed)

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_variants: list[str] = []
        for v in variants:
            if v and v not in seen:
                seen.add(v)
                unique_variants.append(v)

        # Tokenize (split on non-alphanumeric)
        tokens = [t for t in re.split(r"[^a-z0-9]+", lower) if t]

        return NormalizerResult(
            original=original,
            normalized=alpha_only if alpha_only else lower,
            variants=unique_variants,
            tokens=tokens,
            is_valid=True,
        )

    def normalize_batch(self, marks: list[str]) -> list[NormalizerResult]:
        """Normalize a batch of trademarks."""
        return [self.normalize(m) for m in marks]


# Module-level singleton for convenience
normalizer = MarkNormalizer()
