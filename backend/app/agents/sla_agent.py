# SLA & Routing Manager - prioritizes disputes; runs at intake AND after escalation
# (registered as two graph nodes pointing at the same agent - see graph.py).
# Writes: priority = "urgent" | "high" | "normal"
# TODO: real prioritization (safety_incident, high fare amounts, repeat-flagged users).
from app.agents.base import BaseAgent
from app.agents.state import DisputeState


class SLARoutingAgent(BaseAgent):
    name = "sla_routing"

    async def run(self, state: DisputeState) -> DisputeState:
        self.log(state, "Assigning priority / routing queue...")

        state["priority"] = "urgent" if state.get("category") == "safety_incident" else "normal"

        self.log(state, f"Priority set to '{state['priority']}'.")
        return state


sla_routing_agent = SLARoutingAgent()
