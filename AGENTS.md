# Repository guidance

## Architecture
- Preserve the FastAPI / LangGraph backend and React / TypeScript / Vite UI.
- Shared domain contracts live in `backend/app/schemas/dispute.py`; mirror public fields in `frontend/src/types.ts`. Reject extra fields and validate at API, service, agent-output, and final-result boundaries.
- `agents/state.py` is graph transport only. Agents implement `BaseAgent[Input, Output].run` and receive their declared contract, never the complete graph state.
- Both advocates receive the same immutable `AdvocateInput` (dispute, evidence, policy). Neither sees the other advocate's case or the execution log. Only `JudgeInput` includes both cases.
- Evidence comes from allowlisted scenario fixtures; policy lookup is by validated category. Unknown scenarios fail explicitly. Never substitute generic evidence.
- Missing evidence is unavailable/null with an explanation; measured zero and recorded empty collections remain data.
- Validate a complete `Ruling` before comparing confidence. Confidence >= threshold is `resolved`; below it is `needs_review`. Missing/malformed output terminates as `needs_review` with no ruling.

## Current MVP
Dispute -> deterministic evidence + policy -> Rider Advocate -> Driver Advocate -> Judge -> validate ruling -> resolved / needs_review.
The two scenarios are `route_deviation_001` and `no_show_001`. Rider Advocate uses Tencent TokenHub / Hy3 through the shared OpenAI-compatible adapter in real mode, with an explicit offline mock stub. Driver Advocate and Judge remain typed stubs. Rider output is validated as the existing AdvocateCase, including inline citations; provider or output failures stop before Driver/Judge through the controlled advocate-error path. SLA priority is normal; fraud is bypassed. Review is terminal, with no fabricated human decision or feedback.

## Development
- Keep agent implementation changes local to their modules. Coordinate shared contract/graph changes across consumers in the same change; update frontend types and contract tests together.
- Preserve the current UI design and in-memory store. Do not add RAG, embeddings, databases, multimodal analysis, learning loops, queues, streaming, or real fraud detection to this MVP.
- Mock policy and stub outputs must be labelled. Account history alone is not a fraud assessment.
- Run backend `python -m pytest -q` and frontend `npm run build` after relevant changes. Tests validate deterministic contracts and routing, not LLM prose.
- No commit, push, deployment, or external messages unless requested.
