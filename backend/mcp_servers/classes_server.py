"""MCP Server: Nice Classification.

Provides tools for looking up Nice classification codes and
finding related classes for goods/services descriptions.
"""

import json
import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.agents.class_overlap import NICE_CLASSES, GOODS_BY_CLASS


# ─── Tool definitions ────────────────────────────────────────────────────────

TOOLS = {
    "get_class_for_goods": {
        "name": "get_class_for_goods",
        "description": "Suggest the most likely Nice classification class(es) for a given goods/services description.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goods_description": {
                    "type": "string",
                    "description": "Description of the goods or services to classify.",
                },
            },
            "required": ["goods_description"],
        },
    },
    "get_related_classes": {
        "name": "get_related_classes",
        "description": "Get related Nice classification classes for a given class number.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "nice_class": {
                    "type": "integer",
                    "description": "Nice class number (1-45).",
                    "minimum": 1,
                    "maximum": 45,
                },
            },
            "required": ["nice_class"],
        },
    },
}


def get_class_for_goods(goods_description: str) -> dict:
    """Suggest Nice classes for a goods description using keyword matching."""
    if not goods_description:
        return {"error": "Empty goods description", "suggestions": []}

    desc_lower = goods_description.lower()

    # Keyword-to-class mapping
    keyword_classes: dict[str, list[int]] = {
        "cosmetic": [3], "beauty": [3], "skincare": [3], "makeup": [3],
        "perfume": [3], "fragrance": [3], "soap": [3], "shampoo": [3],
        "hair": [3], "nail": [3], "lotion": [3],
        "pharma": [5], "medical": [5, 10], "drug": [5], "vitamin": [5],
        "supplement": [5], "health": [5, 44], "medicine": [5],
        "software": [9, 42], "computer": [9, 42], "electronic": [9],
        "mobile": [9], "app": [9, 42], "device": [9], "tech": [9, 42],
        "clothing": [25], "apparel": [25], "footwear": [25], "fashion": [25],
        "wear": [25], "garment": [25], "textile": [24],
        "food": [29, 30], "meat": [29], "dairy": [29], "fruit": [29, 31],
        "vegetable": [29, 31], "grain": [30], "cereal": [30], "bread": [30],
        "spice": [30], "tea": [30], "coffee": [30], "chocolate": [30],
        "beverage": [32], "juice": [32], "drink": [32], "water": [32],
        "wine": [33], "spirit": [33], "alcohol": [33], "beer": [32],
        "advertising": [35], "marketing": [35], "business": [35],
        "consulting": [35, 42], "retail": [35],
        "insurance": [36], "financial": [36], "banking": [36],
        "construction": [37], "repair": [37],
        "telecom": [38], "communication": [38],
        "transport": [39], "logistics": [39], "shipping": [39],
        "education": [41], "entertainment": [41], "gaming": [41],
        "restaurant": [43], "hotel": [43], "catering": [43],
        "legal": [45], "security": [45],
    }

    matches: dict[int, int] = {}
    for keyword, classes in keyword_classes.items():
        if keyword in desc_lower:
            for cls in classes:
                matches[cls] = matches.get(cls, 0) + 1

    suggestions = []
    for cls, score in sorted(matches.items(), key=lambda x: -x[1]):
        class_info = NICE_CLASSES.get(cls, {})
        suggestions.append({
            "class_number": cls,
            "title": class_info.get("title", "Unknown"),
            "confidence": min(1.0, score / 3),
            "match_count": score,
        })

    if not suggestions:
        suggestions.append({
            "class_number": 0,
            "title": "No matching class found",
            "confidence": 0,
            "match_count": 0,
            "note": "Consider manual classification or consulting a trademark attorney.",
        })

    return {
        "goods_description": goods_description,
        "suggestions": suggestions[:5],
    }


def get_related_classes(nice_class: int) -> dict:
    """Get related Nice classes for a given class number."""
    if nice_class < 1 or nice_class > 45:
        return {"error": f"Invalid Nice class: {nice_class}. Must be 1-45."}

    class_info = NICE_CLASSES.get(nice_class, {})
    related = class_info.get("related", [])

    related_details = []
    for rc in related:
        rc_info = NICE_CLASSES.get(rc, {})
        related_details.append({
            "class_number": rc,
            "title": rc_info.get("title", "Unknown"),
        })

    return {
        "class_number": nice_class,
        "title": class_info.get("title", "Unknown"),
        "related_classes": related_details,
        "total_related": len(related_details),
    }


# MCP handler
TOOL_HANDLERS = {
    "get_class_for_goods": get_class_for_goods,
    "get_related_classes": get_related_classes,
}


def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    """Handle an MCP tool call."""
    if tool_name not in TOOL_HANDLERS:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return TOOL_HANDLERS[tool_name](**arguments)
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("=== get_class_for_goods test ===")
    result = get_class_for_goods("Cosmetics and skincare products")
    print(json.dumps(result, indent=2))

    print("\n=== get_related_classes test ===")
    result = get_related_classes(3)
    print(json.dumps(result, indent=2))
