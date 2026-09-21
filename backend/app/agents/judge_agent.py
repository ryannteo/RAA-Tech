# Judge Agent - impartial arbitrator, weighs both cases + policy + risk, issues a ruling.
# Reads: rider_case, driver_case, policy_context, risk_signals
# Writes: ruling = {decision, amount, reasoning}, confidence (0-1, drives escalation)
# TODO: replace placeholder with a real LLM prompt returning structured JSON -
# parse defensively, this node is what the whole demo hinges on.
from app.agents.base import BaseAgent
from app.agents.state import DisputeState


class JudgeAgent(BaseAgent):
    name = "judge"

    async def run(self, state: DisputeState) -> DisputeState:
        self.log(state, "Weighing rider and driver cases against policy...")

        state["ruling"] = {
            "decision": "partial_refund",
            "amount": 3.25,
            "reasoning": "Placeholder ruling - replace with LLM-generated reasoning.",
        }
        state["confidence"] = 0.85

        self.log(state, "Ruling issued.", data={**state["ruling"], "confidence": state["confidence"]})
        return state


judge_agent = JudgeAgent()
