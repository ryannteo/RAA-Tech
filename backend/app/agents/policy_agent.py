"""Category-based policy lookup; no precedent search or reasoning."""
from app.agents.base import BaseAgent
from app.schemas.dispute import DisputeCategory, PolicyContext
from app.services.scenarios import load_policy


class PolicyPrecedentAgent(BaseAgent[DisputeCategory, PolicyContext]):
    name = "policy_lookup"

    async def run(self, context: DisputeCategory) -> PolicyContext:
        return load_policy(context)


policy_precedent_agent = PolicyPrecedentAgent()
