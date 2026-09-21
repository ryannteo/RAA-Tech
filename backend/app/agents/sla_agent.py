"""Minimal deterministic priority assignment; no queues or SLA simulation."""
from typing import Literal

from app.agents.base import BaseAgent
from app.schemas.dispute import Dispute


class SLARoutingAgent(BaseAgent[Dispute, Literal["normal"]]):
    name = "sla_routing"

    async def run(self, context: Dispute) -> Literal["normal"]:
        return "normal"


sla_routing_agent = SLARoutingAgent()
