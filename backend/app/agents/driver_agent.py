"""Typed stub; input cannot contain the rider advocate's output."""
from app.agents.base import BaseAgent
from app.schemas.dispute import AdvocateCase, AdvocateInput


class DriverAdvocateAgent(BaseAgent[AdvocateInput, AdvocateCase]):
    name = "driver_advocate"

    async def run(self, context: AdvocateInput) -> AdvocateCase:
        return AdvocateCase(
            side="driver",
            claim=context.dispute.driver_statement or "No driver statement supplied.",
            supporting_points=("Stub: evidence and policy received; argument generation is pending.",),
            requested_outcome="undetermined",
            source="stub",
        )


driver_advocate_agent = DriverAdvocateAgent()
