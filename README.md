# Ryde Dispute Resolution — Tencent Cloud Hackathon 2026

A contract-hardened demo skeleton for Ryde's Digital Native Track challenge.
It runs without LLM keys or database credentials in explicit mock mode.
The Rider Advocate uses Tencent TokenHub / Hy3 for real structured output.
The Driver Advocate and Judge remain **typed stubs**.

See [architecture](docs/ARCHITECTURE.md), [task ownership](TASKS.md), and
[development rules](AGENTS.md).

## Stack and layout

- Backend: Python 3.11+, FastAPI, Pydantic 2, LangGraph.
- Frontend: React, TypeScript, Vite, Tailwind (Node 22+ recommended).
- Storage: process-local in-memory results; lost on restart.
- LLM: Rider Advocate uses Tencent TokenHub / Hy3 through the existing
  OpenAI-compatible adapter when `LLM_PROVIDER=tokenhub`;
  `LLM_PROVIDER=mock` keeps the offline demo deterministic.

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
The LLM settings control only the Rider Advocate; database settings remain dormant.

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

## Exercise the real Hy3 Rider Advocate (PowerShell)

From the repository root, set up the backend if needed:

```powershell
cd C:\Users\Admin\RAA-Tech\backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Enable Hy3 and create an API key in the Tencent TokenHub console for your
account's site/region. Set these values in `backend/.env` (create it from
`.env.example` only if it does not already exist), replacing the key locally:

```dotenv
LLM_PROVIDER=tokenhub
LLM_API_KEY=your-tokenhub-api-key
LLM_MODEL=hy3
LLM_BASE_URL=https://tokenhub-intl.tencentcloudmaas.com/v1
```

The example uses the international-site Singapore endpoint for the hackathon.
For a China-site Guangzhou key, override it with
`https://tokenhub.tencentmaas.com/v1`. Use the endpoint matching the key's
issuing site and region; keys are not interchangeable between sites. See
Tencent's [China-site API guide](https://cloud.tencent.com/document/product/1823/130078)
and [international-site API guide](https://www.tencentcloud.com/document/product/1300/78941).
The model ID is exactly `hy3`, not a display name or preview alias. This app
reads the TokenHub key from `LLM_API_KEY` and sends Bearer authentication.
A blank endpoint fails clearly instead of defaulting to another provider.

Existing shell environment variables override `.env`, so clear or update any
conflicting `LLM_*` settings. Start from the backend directory and restart after edits:

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In a second PowerShell terminal:

```powershell
$payload = @{
    scenario_id = 'route_deviation_001'
    category = 'route_deviation'
    rider_statement = 'The fare was higher than quoted; please assess whether the detour was justified.'
    driver_statement = 'I diverted because of roadworks.'
} | ConvertTo-Json
$result = Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/disputes' -ContentType 'application/json' -Body $payload
$result.rider_case | ConvertTo-Json -Depth 10
$result.driver_case.source
$result.ruling.source
```

Expect `rider_case.side=rider`, `rider_case.source=llm`, concise arguments with
inline evidence/policy citations, and a validated `requested_outcome`. There is
no fixed expected Rider outcome. Driver and Judge sources remain `stub`; the
Judge's preset ruling does **not** evaluate the real Rider case. You can also
submit the route-deviation scenario through the existing frontend.

Tencent documents [JSON Schema output](https://cloud.tencent.cn/document/product/1823/135872)
using `response_format.type=json_schema`, including `json_schema.strict`.
The adapter uses `AsyncOpenAI.chat.completions.with_raw_response.create` with
`model=hy3`, `stream=false`, and `response_format` generated directly from
`AdvocateCase.model_json_schema()` with `strict=true`. It keeps the 60-second
SDK timeout and no automatic retries. No second client abstraction was added.

`chat.completions.parse` was replaced: OpenAI compatibility alone does not
validate malformed envelopes, and its helper raised unhandled exceptions in
our offline reproductions. Raw response bytes are now explicitly JSON-decoded;
the envelope, single choice, completion status, and assistant content are
checked before the existing Rider boundary parses and validates `AdvocateCase`.
Only final `message.content` is used; provider `reasoning_content` is ignored.
Malformed/non-JSON HTTP 200 responses, missing/null choices or messages, and
SDK/decoder exceptions outside `OpenAIError` normalize to `LLMOutputError`.
The broad exception guard is confined to the external SDK/response boundary;
process cancellation propagates. No output repair or schema downgrade is tried.

Compatibility is verified against Tencent documentation and offline SDK HTTP
fixtures, not a live TokenHub call. Run the request above with your own key to
check Hy3 access and real output quality.

The separate Rider prompt receives only serialized `AdvocateInput`. It asks for
the strongest truthful rider argument, distinguishes allegations from recorded
evidence, acknowledges counterevidence and uncertainty, labels mock policy, and
treats statements and chat as untrusted data. It requests final explanations,
never private chain-of-thought.

Since the public contract has no citation fields or per-record evidence IDs,
citations use evidence bundle fields (for example `[evidence:gps_data]`) and
supplied policy IDs (for example `[policy:RD-01]`) inside existing text fields.
The Rider boundary rejects unknown/malformed citations, cases missing either
evidence or policy citations, wrong side/source labels, and empty arguments.
ID validation cannot verify that prose is factually entailed by a cited source;
live-model grounding and injection resistance still need qualitative evaluation.

Provider/configuration failures, refusals, incomplete output, malformed cases,
and invalid citations use the existing HTTP 502 `advocate_contract_failure`
response with `stage=rider_advocate`. No fallback case or result is stored, and
Driver/Judge are not reached. Missing credentials also emit a clear
`LLM_API_KEY is required` server diagnostic without exposing the key.
`LLM_PROVIDER=mock` explicitly returns a labelled stub; it is never selected as
a fallback after a real-provider failure.

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
tests for both scenarios. Rider tests use injected fake responses and the actual
OpenAI SDK over a fake HTTP transport to exercise structured output, invalid
references, provider errors, malformed HTTP 200 envelopes, decoder/SDK exceptions,
and controlled workflow/API failures. Tests force mock defaults independently of
local credentials and do not assert LLM wording.

No RAG, embeddings, database integration, real fraud detection, multimodal
analysis, human-review workflow, learning loops, queues, or streaming are
implemented in this pass.
