# Ryde Dispute Resolution — Tencent Cloud Hackathon 2026

Multi-agent autonomous dispute resolution system for Ryde's Digital Native
Track challenge. See `docs/ARCHITECTURE.md` for the agent graph and
`TASKS.md` for the 3-person work split.

## Stack

- **Agents/backend:** Python, FastAPI, LangGraph
- **Frontend:** React + TypeScript + Vite + Tailwind
- **DB:** Tencent Cloud PostgreSQL (placeholder for now — see below)
- **LLM:** any OpenAI-compatible endpoint (defaults to a mock, no key needed)

## Repo layout

```
backend/
  app/
    agents/     # one file per agent + shared state.py, base.py, graph.py
    api/        # FastAPI routes
    db/         # store.py (in-memory, used today) + models.py (Tencent DB schema, placeholder)
    data/       # sample fixtures for evidence/policies
  tests/
frontend/
  src/
    components/ # Header, DisputeForm, AgentTimeline, RulingCard
    assets/brand/  # drop real Ryde brand assets here
docs/
  ARCHITECTURE.md
TASKS.md
```

## Getting started

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # (Windows) or `source .venv/bin/activate`
pip install -r requirements.txt
copy .env.example .env      # (Windows) or `cp .env.example .env`
uvicorn app.main:app --reload
```

API runs at `http://localhost:8000`. `GET /health` should return `{"status": "ok"}`.

Run tests: `pytest` (from `backend/`).

### Frontend

```bash
cd frontend
npm install
copy .env.example .env      # (Windows) or `cp .env.example .env`
npm run dev
```

App runs at `http://localhost:5173`.

## How the agent graph works

`backend/app/agents/graph.py` wires every agent into a LangGraph state
machine matching the team's flowchart: SLA routing → evidence → fraud check
→ rider/driver advocates → policy lookup → judge → (resolved, or escalate →
human review → feedback loop).

All agents share one `DisputeState` dict (`agents/state.py`) and implement
`BaseAgent.run(state) -> state` (`agents/base.py`). Every agent currently
returns placeholder data so the full pipeline already runs end-to-end —
each teammate can replace the placeholder logic in their own agent file(s)
independently. Anything logged via `self.log(...)` shows up in the
frontend's live agent-communication timeline.

## Tencent Cloud DB

Not wired up yet on purpose — `backend/app/db/store.py` is an in-memory
store so no one needs real credentials to start building. `backend/.env.example`
has placeholder `TENCENT_DB_*` vars and `backend/app/db/models.py` has the
schema ready to go once the team provisions an instance.
