# Trademark Conflict Screening Agent (CAT2-069)

An AI-powered multi-agent trademark screening platform that evaluates proposed trademarks against potential conflicts based on textual similarity, phonetic similarity, goods/services description overlap, and Nice Classification relationships.

> **Disclaimer:** This software provides preliminary automated trademark screening for informational purposes only. It does not constitute legal advice or formal trademark clearance.

---

## Architecture Overview

- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, React Router, Axios. Dark LegalTech styling (navy/charcoal/cyan).
- **Backend:** FastAPI, Pydantic v2, SQLAlchemy 2.0, ReportLab (PDF reporting).
- **Multi-Agent Engine:**
  - *Agent 1: Mark Normalizer* (`backend/agents/normalizer.py`) — Unicode NFC, case folding, accent/punctuation stripping, tokenization.
  - *Agent 2: Phonetic Matcher* (`backend/agents/phonetic_matcher.py`) — Double Metaphone + RapidFuzz (fuzzy ratios, token sort/set).
  - *Agent 3: Class Overlap Agent* (`backend/agents/class_overlap.py`) — Nice class cross-referencing and semantic description analysis.
  - *Agent 4: Conflict Reporter* (`backend/agents/conflict_reporter.py`) — Weighted multi-signal formula ($S = 0.35P + 0.30T + 0.35G$), priority tiering, deterministic explanation fallback, and Gemini integration.
- **Workflow Orchestration:** LangGraph-style state machine (`backend/workflows/screening_graph.py`) with typed states, validation, timeout guards, and escalation handling.
- **MCP Servers:** Official Model Context Protocol servers for Trademark Registry tools and Nice Classification lookups.
- **Database:** SQLAlchemy schema with support for SQLite (local default) and PostgreSQL/pgvector.

---

## Quickstart Guide (Windows)

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### 1. Clone & Setup Backend
```powershell
cd trademark-conflict-agent

# Install Python dependencies
pip install -r backend/requirements.txt

# Run test suite
python -m pytest backend/tests/test_screening.py -v

# Run Retrieval Accuracy Benchmark (Recall@10)
python scripts/evaluate_retrieval.py
```

### 2. Start Backend Server
```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be accessible at: `http://localhost:8000/docs`

### 3. Setup & Start Frontend
In a new terminal window:
```powershell
cd trademark-conflict-agent/frontend
npm install
npm run dev
```
Frontend UI will be running at: `http://localhost:5173`

---

## Docker Compose Setup

To run the complete full-stack environment with PostgreSQL:
```powershell
docker-compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

---

## Verification & Test Results
- **Pytest:** 43 passed unit and integration tests across normalizer, phonetic matcher, class overlap agent, scoring, MCP tools, and workflow graph.
- **Retrieval Benchmark:** Tested on curated known trademark pairs achieving $\ge 90\%$ Recall@10.
