# Evidence Collection Agent - gathers GPS/telemetry, chat logs, fare, account history.
# Writes: gps_data, chat_logs, fare_data, user_history
# TODO: load from backend/app/data/*.json fixtures keyed by trip_id (or real APIs later).
from app.agents.base import BaseAgent
from app.agents.state import DisputeState


class EvidenceAgent(BaseAgent):
    name = "evidence_collector"

    async def run(self, state: DisputeState) -> DisputeState:
        self.log(state, f"Gathering evidence for trip {state.get('trip_id')}...")

        state["gps_data"] = {"actual_route_km": 0.0, "optimal_route_km": 0.0, "note": "placeholder"}
        state["chat_logs"] = []
        state["fare_data"] = {"total": 0.0, "note": "placeholder"}
        state["user_history"] = {"rider_past_disputes": 0, "driver_past_disputes": 0}

        self.log(state, "Evidence gathered.")
        return state


evidence_agent = EvidenceAgent()
