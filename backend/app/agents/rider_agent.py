"""Isolated, grounded Rider Advocate with explicit offline mock mode."""
import logging
import re

from app.agents.base import BaseAgent
from app.agents.llm import LLMClient, LLMConfigurationError, LLMOutputError, llm_client
from app.agents.rider_prompt import EVIDENCE_IDS, RIDER_SYSTEM_PROMPT, rider_user_message
from app.schemas.dispute import AdvocateCase, AdvocateInput

logger = logging.getLogger(__name__)


def _validate_case(case: AdvocateCase, context: AdvocateInput) -> AdvocateCase:
    if case.side != "rider" or case.source != "llm" or not case.supporting_points:
        raise LLMOutputError("Expected a nonempty LLM Rider Advocate case.")
    allowed = {f"evidence:{key}" for key in EVIDENCE_IDS}
    allowed.update(f"policy:{rule.rule_id}" for rule in context.policy.rules)
    citations = set()
    for text in (case.claim, *case.supporting_points):
        citations.update(re.findall(r"\[([^\[\]]*)\]", text))
        remainder = re.sub(r"\[[^\[\]]*\]", "", text)
        if "[" in remainder or "]" in remainder:
            raise LLMOutputError("Malformed Rider Advocate citation.")
    if citations - allowed:
        raise LLMOutputError("Rider Advocate cited an unknown evidence or policy ID.")
    if not any(c.startswith("evidence:") for c in citations) or not any(c.startswith("policy:") for c in citations):
        raise LLMOutputError("Rider Advocate must cite supplied evidence and policy.")
    return case


class RiderAdvocateAgent(BaseAgent[AdvocateInput, AdvocateCase]):
    name = "rider_advocate"

    def __init__(self, client: LLMClient | None = None) -> None:
        self._client = client if client is not None else llm_client

    async def run(self, context: AdvocateInput) -> AdvocateCase:
        context = AdvocateInput.model_validate(context)
        if self._client.is_mock:
            # Intentional offline behavior, never a fallback after an LLM failure.
            return AdvocateCase(
                side="rider",
                claim=context.dispute.rider_statement or "No rider statement supplied.",
                supporting_points=("Stub: LLM_PROVIDER=mock; no Rider Advocate reasoning was performed.",),
                requested_outcome="undetermined",
                source="stub",
            )
        try:
            raw = await self._client.complete(
                RIDER_SYSTEM_PROMPT, rider_user_message(context), response_model=AdvocateCase,
            )
        except LLMConfigurationError as exc:
            logger.error("Rider Advocate configuration error: %s", exc)
            raise
        case = AdvocateCase.model_validate_json(raw)
        return _validate_case(case, context)


rider_advocate_agent = RiderAdvocateAgent()
