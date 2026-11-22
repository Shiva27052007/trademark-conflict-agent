"""MCP Server: Trademark Registry.

Provides structured tool schemas for searching and retrieving
trademark records from the synthetic dataset.
"""

import json
import sys
from pathlib import Path

# Ensure project root on path
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# ─── Tool definitions ────────────────────────────────────────────────────────

TOOLS = {
    "search_marks": {
        "name": "search_marks",
        "description": "Search for existing trademark records by query string, jurisdiction, and limit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term to match against trademark names.",
                },
                "jurisdiction": {
                    "type": "string",
                    "description": "Jurisdiction code (e.g., IN, US, GB). Empty for all.",
                    "default": "",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["query"],
        },
    },
    "get_mark_details": {
        "name": "get_mark_details",
        "description": "Get detailed information about a specific trademark by its ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "trademark_id": {
                    "type": "string",
                    "description": "The unique trademark identifier (e.g., DEMO0001).",
                },
            },
            "required": ["trademark_id"],
        },
    },
}


def search_marks(query: str, jurisdiction: str = "", limit: int = 20) -> dict:
    """Search trademarks in the database."""
    from backend.database.engine import SessionLocal
    from backend.database.models import Trademark, TrademarkGoodsService

    db = SessionLocal()
    try:
        q = db.query(Trademark)
        if query:
            q = q.filter(
                Trademark.mark_name.ilike(f"%{query}%")
                | Trademark.normalized_name.ilike(f"%{query}%")
            )
        if jurisdiction:
            q = q.filter(Trademark.jurisdiction == jurisdiction)

        results = q.limit(limit).all()

        return {
            "results": [
                {
                    "trademark_id": t.trademark_id,
                    "mark_name": t.mark_name,
                    "normalized_name": t.normalized_name,
                    "jurisdiction": t.jurisdiction,
                    "status": t.registration_status,
                    "source": t.source,
                    "nice_classes": [
                        gs.nice_class
                        for gs in db.query(TrademarkGoodsService)
                        .filter(TrademarkGoodsService.trademark_id == t.id)
                        .all()
                    ],
                }
                for t in results
            ],
            "total": len(results),
            "source": "synthetic_demo_dataset",
        }
    finally:
        db.close()


def get_mark_details(trademark_id: str) -> dict:
    """Get details for a specific trademark."""
    from backend.database.engine import SessionLocal
    from backend.database.models import Trademark, TrademarkGoodsService

    db = SessionLocal()
    try:
        tm = db.query(Trademark).filter(
            Trademark.trademark_id == trademark_id
        ).first()

        if not tm:
            return {"error": f"Trademark {trademark_id} not found", "found": False}

        goods = db.query(TrademarkGoodsService).filter(
            TrademarkGoodsService.trademark_id == tm.id
        ).all()

        return {
            "found": True,
            "trademark_id": tm.trademark_id,
            "mark_name": tm.mark_name,
            "normalized_name": tm.normalized_name,
            "jurisdiction": tm.jurisdiction,
            "registration_status": tm.registration_status,
            "source": tm.source,
            "source_type": tm.source_type,
            "data_timestamp": tm.data_timestamp.isoformat() if tm.data_timestamp else None,
            "goods_services": [
                {"nice_class": gs.nice_class, "description": gs.description}
                for gs in goods
            ],
            "disclaimer": "This is synthetic demonstration data, not an official registry result.",
        }
    finally:
        db.close()


# MCP server handler
TOOL_HANDLERS = {
    "search_marks": search_marks,
    "get_mark_details": get_mark_details,
}


def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    """Handle an MCP tool call."""
    if tool_name not in TOOL_HANDLERS:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        handler = TOOL_HANDLERS[tool_name]
        return handler(**arguments)
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Test the tools
    from backend.database.engine import init_db
    from backend.services.dataset_generator import seed_database

    init_db()
    seed_database()

    print("=== search_marks test ===")
    result = search_marks("Nykaa", "IN", 5)
    print(json.dumps(result, indent=2))

    print("\n=== get_mark_details test ===")
    if result["results"]:
        detail = get_mark_details(result["results"][0]["trademark_id"])
        print(json.dumps(detail, indent=2))
