# Driver Advocate Agent - mirror of RiderAdvocateAgent, argues driver-favorable outcome.
# Reads: driver_statement (may be None), gps_data, chat_logs, fare_data, user_history, risk_signals
# Writes: driver_case = {claim, supporting_points, requested_outcome}
# TODO: replace placeholder with a real llm_client.complete() prompt; keep output
# shape identical to RiderAdvocateAgent so JudgeAgent can compare fairly.
from app.agents.base import BaseAgent
from app.agents.state import DisputeState


class DriverAdvocateAgent(BaseAgent):
    name = "driver_advocate"

    async def run(self, state: DisputeState) -> DisputeState:
        self.log(state, "Reviewing evidence to build the driver's case...")

        state["driver_case"] = {
            "claim": "Placeholder: driver defends the charge/route taken.",
            "supporting_points": ["Placeholder evidence point from GPS/chat/fare data."],
            "requested_outcome": "no_action",
        }

        self.log(state, "Driver case ready.", data=state["driver_case"])
        return state


driver_advocate_agent = DriverAdvocateAgent()
