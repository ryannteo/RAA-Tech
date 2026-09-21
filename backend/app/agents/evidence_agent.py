"""Compatibility adapter for deterministic evidence loading."""
from app.agents.base import BaseAgent
from app.schemas.dispute import Dispute, EvidenceBundle
from app.services.scenarios import load_evidence


class EvidenceAgent(BaseAgent[Dispute, EvidenceBundle]):
    name = "evidence_collector"

    async def run(self, context: Dispute) -> EvidenceBundle:
        return load_evidence(context)


evidence_agent = EvidenceAgent()
