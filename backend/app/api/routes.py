from fastapi import APIRouter, HTTPException

from app.agents.graph import AdvocateContractError, run_dispute_graph
from app.db.store import store
from app.schemas.dispute import DisputeResult, DisputeSubmission, ScenarioSummary
from app.services.scenarios import (
    ScenarioMismatchError, UnknownScenarioError, create_dispute, list_scenarios,
)

router = APIRouter(prefix="/disputes", tags=["disputes"])


@router.get("/scenarios", response_model=tuple[ScenarioSummary, ...])
async def get_scenarios():
    return list_scenarios()


@router.post("", response_model=DisputeResult)
async def submit_dispute(payload: DisputeSubmission):
    try:
        dispute = create_dispute(payload)
        result = await run_dispute_graph(dispute)
    except UnknownScenarioError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ScenarioMismatchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AdvocateContractError as exc:
        raise HTTPException(status_code=502, detail=exc.detail.model_dump()) from exc
    store.save(result)
    return result


@router.get("", response_model=list[DisputeResult])
async def list_disputes():
    return store.list()


@router.get("/{dispute_id}", response_model=DisputeResult)
async def get_dispute(dispute_id: str):
    dispute = store.get(dispute_id)
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute
