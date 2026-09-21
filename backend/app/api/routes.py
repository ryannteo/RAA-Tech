import uuid

from fastapi import APIRouter, HTTPException

from app.agents.graph import run_dispute_graph
from app.db.store import store
from app.schemas.dispute import DisputeSubmission

router = APIRouter(prefix="/disputes", tags=["disputes"])


@router.post("")
async def submit_dispute(payload: DisputeSubmission):
    initial_state = {
        "dispute_id": str(uuid.uuid4()),
        "category": payload.category,
        "trip_id": payload.trip_id,
        "rider_id": payload.rider_id,
        "driver_id": payload.driver_id,
        "rider_statement": payload.rider_statement,
        "driver_statement": payload.driver_statement,
        "escalated": False,
        "communication_log": [],
    }

    final_state = await run_dispute_graph(initial_state)
    store.save(final_state)
    return final_state


@router.get("")
async def list_disputes():
    return store.list()


@router.get("/{dispute_id}")
async def get_dispute(dispute_id: str):
    dispute = store.get(dispute_id)
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute
