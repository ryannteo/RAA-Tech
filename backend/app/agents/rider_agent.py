"""Typed stub. Replace run() with reasoning without changing its contract."""
from app.agents.base import BaseAgent
from app.schemas.dispute import AdvocateCase, AdvocateInput


class RiderAdvocateAgent(BaseAgent[AdvocateInput, AdvocateCase]):
    name = "rider_advocate"

    async def run(self, context: AdvocateInput) -> AdvocateCase:
        return AdvocateCase(
            side="rider",
            claim=context.dispute.rider_statement or "No rider statement supplied.",
            supporting_points=("Stub: evidence and policy received; argument generation is pending.",),
            requested_outcome="undetermined",
            source="stub",
        )


rider_advocate_agent = RiderAdvocateAgent()
