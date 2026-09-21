# Ryde Dispute Resolution — Tencent Cloud Hackathon 2026

A contract-hardened demo skeleton for Ryde's Digital Native Track challenge.
It runs without LLM keys or database credentials. The Rider Advocate, Driver
Advocate, and Judge are **typed stubs**, ready for independent implementation.

See [architecture](docs/ARCHITECTURE.md), [task ownership](TASKS.md), and
[development rules](AGENTS.md).

## Stack and layout

- Backend: Python 3.11+, FastAPI, Pydantic 2, LangGraph.
- Frontend: React, TypeScript, Vite, Tailwind (Node 22+ recommended).
- Storage: process-local in-memory results; lost on restart.
- LLM: unused by the current graph.

```text
backend/
  app/
    agents/       # typed agents, graph adapters, state and routing
    schemas/      # shared validated domain and API contracts
    services/     # deterministic evidence/scenario and policy loaders
    data/
      scenarios/  # exactly two mock scenarios
      policies/   # mock policy by category
    api/          # submission, scenario catalog, result reads
    db/           # active in-memory store; dormant SQLAlchemy scaffold
  tests/
frontend/src/
  components/     # existing design + evidence/case/policy views
  types.ts        # backend contract mirrored for the UI
docs/
  ARCHITECTURE.md
```

## Run locally

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On macOS/Linux, activate with `source .venv/bin/activate`.
Optionally copy `backend/.env.example` to `backend/.env` to set
`JUDGE_CONFIDENCE_THRESHOLD` (default 0.75, valid range 0–1).
The existing LLM/database variables are dormant placeholders.

API: http://localhost:8000; API documentation: http://localhost:8000/docs.
`GET /health` returns `{"status": "ok"}`.

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

UI: http://localhost:5173. Optionally copy `frontend/.env.example` to
`frontend/.env` to change `VITE_API_BASE_URL`.

## Stable scenarios

The selector loads its catalog from `GET /disputes/scenarios`.
Both statements may be omitted, null, or blank; blank input becomes null.
Trip and account IDs come from the selected fixture.

| Scenario | Competing evidence | Preset judge output at threshold 0.75 |
| --- | --- | --- |
| `route_deviation_001` | Extra distance/fare and unclear consent versus a roadworks advisory; incomplete GPS | 0.85 confidence → `resolved` |
| `no_show_001` | Five-minute timer/contact attempt versus different entrances, uncertain location, and timely rider reply | 0.60 confidence → `needs_review` |

All policy is fictional demo policy. Preset rulings demonstrate routing, do
not adjudicate the evidence, and do not change with submitted statements.
No money is transferred and no human review is simulated.

Submit a dispute:

```http
POST /disputes
Content-Type: application/json

{
  "scenario_id": "route_deviation_001",
  "category": "route_deviation",
  "driver_statement": "I diverted because of roadworks."
}
```

The response contains `dispute`, `evidence`, `policy`, `rider_case`,
`driver_case`, `ruling`, `status`, `review_reason`, the applied threshold,
and the completed execution log. Confidence exists only inside `ruling`.
`GET /disputes` lists results; `GET /disputes/{dispute_id}` retrieves one.
Unknown scenarios return 404; unsupported categories and scenario/category
mismatches return 422.

## Validation

```bash
cd backend
python -m pytest -q
```

```bash
cd frontend
npm run build
```

The integration suite covers optional statements, validated categories,
both deterministic loaders, missing versus zero data, isolated advocate
inputs, confidence boundaries, malformed/missing rulings, and API smoke
tests for both scenarios.

No RAG, embeddings, database integration, real fraud detection, multimodal
analysis, human-review workflow, learning loops, queues, or streaming are
implemented in this pass.
