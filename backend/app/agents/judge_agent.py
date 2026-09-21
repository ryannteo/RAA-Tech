"""Fixed demo outputs exercise both routing paths; no LLM reasoning."""
from app.agents.base import BaseAgent
from app.schemas.dispute import DisputeCategory, JudgeInput, Ruling


class JudgeAgent(BaseAgent[JudgeInput, Ruling]):
    name = "judge"

    async def run(self, context: JudgeInput) -> Ruling:
        if context.context.dispute.category == DisputeCategory.ROUTE_DEVIATION:
            return Ruling(
                decision="partial_refund", amount=2.50, currency="SGD",
                confidence=0.85, source="stub",
                reasoning="Fixed demo ruling to exercise routing. The cases and policy have not been adjudicated.",
            )
        return Ruling(
            decision="no_action", amount=0.0, currency="SGD",
            confidence=0.60, source="stub",
            reasoning="Fixed demo ruling to exercise review routing. Pickup uncertainty has not been adjudicated.",
        )


judge_agent = JudgeAgent()
