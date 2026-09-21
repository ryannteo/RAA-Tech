# Task split (3 people)

Shared foundation is already in place: `DisputeState` contract, `BaseAgent`
interface, graph wiring, API skeleton, frontend skeleton. Every agent
currently returns placeholder data, so the whole pipeline already runs
end-to-end — pick a track and replace the placeholder logic in your files
without touching anyone else's.

## Track A — Advocate agents
- [ ] `backend/app/agents/rider_agent.py`
- [ ] `backend/app/agents/driver_agent.py`
- [ ] `backend/app/agents/evidence_agent.py` (feeds both advocates — load real data from `backend/app/data/`)

## Track B — Judge & knowledge
- [ ] `backend/app/agents/judge_agent.py`
- [ ] `backend/app/agents/policy_agent.py` (RAG over company policy)
- [ ] `backend/app/data/policies.json` (write the sample policy corpus)

## Track C — Ops agents & escalation
- [ ] `backend/app/agents/sla_agent.py`
- [ ] `backend/app/agents/fraud_agent.py`
- [ ] `backend/app/agents/escalation_agent.py` (Escalation + Human Review + Feedback Loop)

## Shared / cross-cutting (whoever has bandwidth)
- [ ] Frontend: wire up `frontend/src/assets/brand/` once real Ryde assets arrive
- [ ] Tencent Cloud DB: fill in `backend/.env` and wire `backend/app/db/models.py`, replacing `db/store.py`
- [ ] LLM: pick a provider, fill in `LLM_*` vars in `backend/.env`
- [ ] Demo prep: make sure at least 2 dispute categories work end-to-end (route deviation + no-show is the easiest pair)
- [ ] Architecture diagram for submission (starting point in `docs/ARCHITECTURE.md`)

## Ground rules
- Don't edit `state.py`, `base.py`, or `graph.py` without a quick heads-up in
  the group chat — they're the shared contract everyone's agent depends on.
- If your agent needs a new field on `DisputeState`, add it in `state.py` and
  say so, don't just stuff it into the dict.
