"""Agent 3: Class Overlap Agent.

Compares Nice classification codes and goods/services descriptions
to identify commercial overlap between trademarks. Uses semantic
similarity via sentence embeddings when available, with a TF-IDF
fallback for environments without the model installed.
"""

from dataclasses import dataclass, field
import re
import math
from collections import Counter

# Nice Classification data (key classes)
NICE_CLASSES: dict[int, dict] = {
    1: {"title": "Chemicals", "related": [2, 5, 17]},
    2: {"title": "Paints", "related": [1, 17, 19]},
    3: {"title": "Cosmetics and cleaning preparations", "related": [5, 21, 44]},
    4: {"title": "Industrial oils and greases", "related": [1, 19]},
    5: {"title": "Pharmaceuticals", "related": [3, 10, 44]},
    6: {"title": "Common metals", "related": [7, 19, 20]},
    7: {"title": "Machines and machine tools", "related": [6, 8, 11, 12]},
    8: {"title": "Hand tools", "related": [7, 21]},
    9: {"title": "Scientific and electronic apparatus", "related": [42, 38, 35]},
    10: {"title": "Medical apparatus", "related": [5, 44]},
    11: {"title": "Environmental control apparatus", "related": [7, 9, 21]},
    12: {"title": "Vehicles", "related": [7, 37, 39]},
    13: {"title": "Firearms", "related": [28]},
    14: {"title": "Precious metals and jewellery", "related": [26, 35]},
    15: {"title": "Musical instruments", "related": [9, 41]},
    16: {"title": "Paper goods and printed matter", "related": [35, 41]},
    17: {"title": "Rubber goods", "related": [1, 6, 19]},
    18: {"title": "Leather goods", "related": [25, 26]},
    19: {"title": "Non-metallic building materials", "related": [6, 17, 37]},
    20: {"title": "Furniture", "related": [6, 21, 24]},
    21: {"title": "Housewares", "related": [3, 8, 11, 20]},
    22: {"title": "Cordage and fibers", "related": [23, 24]},
    23: {"title": "Yarns and threads", "related": [22, 24, 25, 26]},
    24: {"title": "Fabrics", "related": [22, 23, 25]},
    25: {"title": "Clothing", "related": [18, 23, 24, 26, 35]},
    26: {"title": "Lace and embroidery", "related": [23, 24, 25]},
    27: {"title": "Floor coverings", "related": [19, 20, 24]},
    28: {"title": "Toys and sporting goods", "related": [25, 41]},
    29: {"title": "Meats and processed foods", "related": [30, 31, 32, 43]},
    30: {"title": "Staple foods", "related": [29, 31, 32, 43]},
    31: {"title": "Natural agricultural products", "related": [29, 30, 44]},
    32: {"title": "Light beverages", "related": [29, 30, 33, 43]},
    33: {"title": "Wines and spirits", "related": [32, 43]},
    34: {"title": "Smokers' articles", "related": [4]},
    35: {"title": "Advertising and business", "related": [9, 16, 25, 36, 42]},
    36: {"title": "Insurance and financial", "related": [35, 37]},
    37: {"title": "Building construction and repair", "related": [6, 12, 19, 36]},
    38: {"title": "Telecommunications", "related": [9, 35, 42]},
    39: {"title": "Transportation and storage", "related": [12, 35]},
    40: {"title": "Treatment of materials", "related": [1, 7, 37]},
    41: {"title": "Education and entertainment", "related": [9, 15, 16, 28, 35]},
    42: {"title": "Computer and scientific services", "related": [9, 35, 38, 45]},
    43: {"title": "Hotels and restaurants", "related": [29, 30, 32, 33]},
    44: {"title": "Medical, beauty, and agricultural", "related": [3, 5, 10, 31]},
    45: {"title": "Legal and social services", "related": [35, 36, 42]},
}


@dataclass
class ClassOverlapResult:
    """Result of goods/services overlap analysis."""
    query_classes: list[int]
    candidate_classes: list[int]
    class_overlap_score: float  # 0-100
    description_similarity: float  # 0-100
    combined_goods_score: float  # 0-100
    overlapping_classes: list[int] = field(default_factory=list)
    related_classes: list[int] = field(default_factory=list)
    explanation: str = ""
    uncertain: bool = False

    def to_dict(self) -> dict:
        return {
            "query_classes": self.query_classes,
            "candidate_classes": self.candidate_classes,
            "class_overlap_score": round(self.class_overlap_score, 1),
            "description_similarity": round(self.description_similarity, 1),
            "combined_goods_score": round(self.combined_goods_score, 1),
            "overlapping_classes": self.overlapping_classes,
            "related_classes": self.related_classes,
            "explanation": self.explanation,
            "uncertain": self.uncertain,
        }


def _tokenize(text: str) -> list[str]:
    """Tokenizer with simple stemming/lemmatization for goods descriptions."""
    raw = re.findall(r'[a-z]+', text.lower())
    stems = []
    for w in raw:
        # Handle plurals/suffixes simply
        if w.endswith("ies") and len(w) > 4:
            stems.append(w[:-3] + "y")
        elif w.endswith("es") and len(w) > 3:
            stems.append(w[:-2])
        elif w.endswith("s") and len(w) > 2:
            stems.append(w[:-1])
        else:
            stems.append(w)
        # Also decompose compound words if detected like skincare -> skin, care
        if "skin" in w and len(w) > 4:
            stems.extend(["skin", w.replace("skin", "")])
    return [s for s in stems if len(s) > 1]


def _cosine_tfidf(text_a: str, text_b: str) -> float:
    """Token-overlap and fuzzy substring similarity fallback."""
    from rapidfuzz import fuzz

    # Direct fuzzy partial / token set match between full descriptions
    ratio = fuzz.token_set_ratio(text_a, text_b)

    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return float(ratio)

    stop = {"and", "or", "the", "a", "an", "of", "for", "in", "on", "to", "is", "it"}
    tokens_a = [t for t in tokens_a if t not in stop]
    tokens_b = [t for t in tokens_b if t not in stop]

    if not tokens_a or not tokens_b:
        return float(ratio)

    all_tokens = set(tokens_a) | set(tokens_b)
    tf_a = Counter(tokens_a)
    tf_b = Counter(tokens_b)

    dot = sum(tf_a.get(t, 0) * tf_b.get(t, 0) for t in all_tokens)
    mag_a = math.sqrt(sum(v * v for v in tf_a.values()))
    mag_b = math.sqrt(sum(v * v for v in tf_b.values()))

    token_overlap = (dot / (mag_a * mag_b) * 100) if (mag_a and mag_b) else 0.0

    # Max or weighted combination
    return float(max(token_overlap, ratio))


GOODS_BY_CLASS: dict[int, list[str]] = {
    3: ["Cosmetics and skincare products", "Beauty and cosmetic products", "Hair care preparations"],
    5: ["Pharmaceutical preparations", "Dietary supplements", "Medical nutrition products"],
    9: ["Computer software and applications", "Electronic devices and accessories", "Mobile phone accessories"],
    25: ["Clothing and apparel", "Footwear", "Headwear and hats"],
    29: ["Processed meats and poultry", "Dairy products", "Preserved fruits and vegetables"],
    30: ["Rice and grains", "Flour and cereals", "Bread and bakery products"],
    32: ["Non-alcoholic beverages", "Fruit juices and drinks", "Mineral and aerated waters"],
    35: ["Advertising and marketing services", "Business management consulting", "Retail services"],
    42: ["Software development services", "IT consulting", "Cloud computing services"],
}


class ClassOverlapAgent:
    """Analyzes Nice class and goods/services overlap."""

    def __init__(self):
        self._model = None
        self._model_loaded = False

    def _try_load_model(self):
        """Attempt to load sentence-transformers model. Falls back to TF-IDF."""
        if self._model_loaded:
            return
        self._model_loaded = True
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            self._model = None

    def _semantic_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate semantic similarity between two descriptions."""
        self._try_load_model()
        if self._model is not None:
            try:
                embeddings = self._model.encode([text_a, text_b])
                # Cosine similarity
                from numpy import dot
                from numpy.linalg import norm
                cosine = dot(embeddings[0], embeddings[1]) / (
                    norm(embeddings[0]) * norm(embeddings[1])
                )
                return float(max(0, cosine) * 100)
            except Exception:
                pass
        # Fallback: TF-IDF cosine
        return _cosine_tfidf(text_a, text_b)

    def compare(
        self,
        query_classes: list[int],
        candidate_classes: list[int],
        query_description: str,
        candidate_description: str,
    ) -> ClassOverlapResult:
        """Compare Nice classes and goods/services descriptions.

        Args:
            query_classes: Nice classes for the proposed mark.
            candidate_classes: Nice classes of the existing mark.
            query_description: Goods/services description for the proposed mark.
            candidate_description: Goods/services description for the existing mark.

        Returns:
            ClassOverlapResult with overlap scores and explanation.
        """
        query_set = set(query_classes)
        candidate_set = set(candidate_classes)

        # ── Direct class overlap ────────────────────────────────────────
        overlapping = sorted(query_set & candidate_set)

        # ── Related classes ─────────────────────────────────────────────
        related = []
        for qc in query_classes:
            class_info = NICE_CLASSES.get(qc, {})
            related_list = class_info.get("related", [])
            for cc in candidate_classes:
                if cc in related_list and cc not in overlapping:
                    related.append(cc)
        related = sorted(set(related))

        # Class overlap score
        if not query_classes or not candidate_classes:
            class_score = 0.0
            uncertain = True
        elif overlapping:
            # Exact overlap: high score
            class_score = min(100, (len(overlapping) / max(len(query_set), 1)) * 100)
            uncertain = False
        elif related:
            # Related classes: moderate score
            class_score = min(70, (len(related) / max(len(query_set), 1)) * 50)
            uncertain = False
        else:
            class_score = 0.0
            uncertain = False

        # ── Description similarity ──────────────────────────────────────
        desc_score = 0.0
        if query_description and candidate_description:
            desc_score = self._semantic_similarity(
                query_description, candidate_description
            )
        elif not query_description or not candidate_description:
            uncertain = True

        # ── Combined score ──────────────────────────────────────────────
        # 50% class overlap + 50% description similarity
        combined = 0.50 * class_score + 0.50 * desc_score

        # Boost if both class and description match strongly
        if class_score >= 80 and desc_score >= 70:
            combined = min(100, combined * 1.1)

        # ── Explanation ─────────────────────────────────────────────────
        explanation = self._build_explanation(
            query_classes, candidate_classes, overlapping, related,
            class_score, desc_score, combined, uncertain,
            query_description, candidate_description,
        )

        return ClassOverlapResult(
            query_classes=query_classes,
            candidate_classes=candidate_classes,
            class_overlap_score=class_score,
            description_similarity=desc_score,
            combined_goods_score=combined,
            overlapping_classes=overlapping,
            related_classes=related,
            explanation=explanation,
            uncertain=uncertain,
        )

    def _build_explanation(
        self, q_classes, c_classes, overlapping, related,
        class_score, desc_score, combined, uncertain,
        q_desc, c_desc,
    ) -> str:
        parts = [
            f"Nice classes: query={q_classes}, candidate={c_classes}",
        ]
        if overlapping:
            parts.append(f"  Direct overlap in classes: {overlapping}")
        if related:
            parts.append(f"  Related classes: {related}")
        if not overlapping and not related:
            parts.append("  No class overlap or related classes found.")
        parts.append(f"  Class overlap score: {class_score:.1f}/100")
        parts.append(f"  Description similarity: {desc_score:.1f}/100")
        parts.append(f"  Combined goods score: {combined:.1f}/100")
        if uncertain:
            parts.append("  ⚠ Classification uncertain — missing or incomplete data.")
        return "\n".join(parts)


# Module-level singleton
class_overlap_agent = ClassOverlapAgent()
