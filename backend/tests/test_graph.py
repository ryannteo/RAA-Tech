import pytest

from app.agents.graph import run_dispute_graph


@pytest.mark.asyncio
async def test_graph_runs_end_to_end():
    initial_state = {
        "dispute_id": "test-1",
        "category": "route_deviation",
        "trip_id": "trip-1",
        "rider_id": "rider-1",
        "driver_id": "driver-1",
        "rider_statement": "Driver took a longer route and I was overcharged.",
        "escalated": False,
        "communication_log": [],
    }

    final_state = await run_dispute_graph(initial_state)

    assert "ruling" in final_state
    assert final_state["communication_log"], "expected agents to log their steps"
