# Task split (3 developers)

The shared contracts and deterministic demo flow are ready. Each developer
can implement one core reasoning component against a stable interface.
Actual LLM reasoning remains outside the current hardening pass.

| Track | Owned implementation | Stable interface |
| --- | --- | --- |
| A — Rider Advocate | `backend/app/agents/rider_agent.py` | `run(AdvocateInput) -> AdvocateCase` with side `rider` |
| B — Driver Advocate | `backend/app/agents/driver_agent.py` | `run(AdvocateInput) -> AdvocateCase` with side `driver` |
| C — Judge | `backend/app/agents/judge_agent.py` | `run(JudgeInput) -> Ruling` |

Both advocates receive the same dispute, evidence, and policy; neither
receives the other's output. The Judge receives both cases and the factual
context. Each component must return its validated model and identify
whether its output came from a stub or LLM.

Shared changes to `schemas/dispute.py`, `agents/state.py`, `agents/base.py`,
`agents/graph.py`, or `frontend/src/types.ts` should update all consumers and
contract tests together. Keep agent-only changes out of these shared files
where possible.

Evidence and policy services are deterministic and already implemented.
Do not replace them with LLM reasoning. The two stable scenarios must remain
usable without credentials. Provider integration should be coordinated as a
separate task when actual reasoning is authorized.

Before integrating work, run backend `python -m pytest -q` and frontend
`npm run build`. Read [AGENTS.md](AGENTS.md) and
[the architecture document](docs/ARCHITECTURE.md) for the current boundaries.

Fraud detection, RAG/embeddings, database integration, multimodal analysis,
human-review implementation, learning loops, queues, and streaming are
deferred. No automatic human decision or feedback should be introduced.
