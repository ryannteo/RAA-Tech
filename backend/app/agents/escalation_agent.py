# Escalation Protocol + Human Review + Learning Feedback Loop.
# Only runs when JudgeAgent's confidence < Settings.judge_confidence_threshold
# (see the conditional edge in graph.py). Grouped in one file: they're one flow.
#
# TODO for whoever picks this up:
# - EscalationAgent: build a real case summary for the human reviewer.
# - HumanReviewAgent: currently auto-mocks a decision. Replace with a real pause -
#   LangGraph's interrupt() can stop the graph until the frontend posts a decision.
# - FeedbackLoopAgent: persist overrides (once Tencent DB is wired) and feed them
#   back into PolicyPrecedentAgent's knowledge base.
from app.agents.base import BaseAgent
from app.agents.state import DisputeState


class EscalationAgent(BaseAgent):
    name = "escalation"

    async def run(self, state: DisputeState) -> DisputeState:
        state["escalated"] = True
        state["escalation_reason"] = f"Judge confidence {state.get('confidence')} below threshold."
        self.log(state, "Escalating to human review.", data={"reason": state["escalation_reason"]})
        return state


class HumanReviewAgent(BaseAgent):
    name = "human_reviewer"

    async def run(self, state: DisputeState) -> DisputeState:
        self.log(state, "Waiting for human reviewer... (auto-mocked for now)")

        state["human_decision"] = {
            "decision": state.get("ruling", {}).get("decision", "no_action"),
            "notes": "Placeholder auto-approval - wire up a real reviewer UI.",
        }

        self.log(state, "Human decision recorded.", data=state["human_decision"])
        return state


class FeedbackLoopAgent(BaseAgent):
    name = "feedback_loop"

    async def run(self, state: DisputeState) -> DisputeState:
        ai_decision = state.get("ruling", {}).get("decision")
        human_decision = state.get("human_decision", {}).get("decision")
        overridden = ai_decision != human_decision

        self.log(
            state,
            "Comparing AI ruling to human decision..." + (" (override)" if overridden else " (agreed)"),
            data={"ai_decision": ai_decision, "human_decision": human_decision, "overridden": overridden},
        )
        # TODO: persist correction + update PolicyPrecedentAgent's knowledge base
        return state


escalation_agent = EscalationAgent()
human_review_agent = HumanReviewAgent()
feedback_loop_agent = FeedbackLoopAgent()
