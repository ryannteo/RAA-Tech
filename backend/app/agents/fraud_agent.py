# Fraud / Bad-Faith Detection Agent - flags suspicious patterns, feeds risk signal to Judge.
# Reads: user_history
# Writes: risk_signals = {rider_risk_score, driver_risk_score, flags}
# TODO: replace placeholder with real behavioral heuristics over user_history.
from app.agents.base import BaseAgent
from app.agents.state import DisputeState


class FraudDetectionAgent(BaseAgent):
    name = "fraud_detection"

    async def run(self, state: DisputeState) -> DisputeState:
        self.log(state, "Scanning dispute history for risk signals...")

        state["risk_signals"] = {"rider_risk_score": 0.0, "driver_risk_score": 0.0, "flags": []}

        self.log(state, "Risk assessment complete.", data=state["risk_signals"])
        return state


fraud_detection_agent = FraudDetectionAgent()
