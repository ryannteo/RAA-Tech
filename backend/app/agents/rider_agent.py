# Rider Advocate Agent - gathers rider-side evidence, argues rider-favorable outcome.
# Reads: rider_statement, gps_data, chat_logs, fare_data, user_history, risk_signals
# Writes: rider_case = {claim, supporting_points, requested_outcome}
# TODO: replace placeholder with a real llm_client.complete() prompt.
from app.agents.base import BaseAgent
from app.agents.state import DisputeState


class RiderAdvocateAgent(BaseAgent):
    name = "rider_advocate"

    async def run(self, state: DisputeState) -> DisputeState:
        self.log(state, "Reviewing evidence to build the rider's case...")

        state["rider_case"] = {
            "claim": "Placeholder: rider disputes the charge.",
            "supporting_points": ["Placeholder evidence point from GPS/chat/fare data."],
            "requested_outcome": "full_refund",
        }

        self.log(state, "Rider case ready.", data=state["rider_case"])
        return state


rider_advocate_agent = RiderAdvocateAgent()
