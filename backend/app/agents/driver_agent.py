"""Isolated, grounded Driver Advocate with explicit offline mock mode."""
import logging
import re

from app.agents.base import BaseAgent
from app.agents.llm import LLMClient, LLMConfigurationError, LLMOutputError, llm_client
from app.agents.driver_prompt import EVIDENCE_IDS, DRIVER_SYSTEM_PROMPT, driver_user_message
from app.schemas.dispute import AdvocateCase, AdvocateInput

logger = logging.getLogger(__name__)


def _validate_case(case: AdvocateCase, context: AdvocateInput) -> AdvocateCase:
    if case.side != "driver" or case.source != "llm" or not case.supporting_points:
        raise LLMOutputError("Expected a nonempty LLM Driver Advocate case.")
    allowed = {f"evidence:{key}" for key in EVIDENCE_IDS}
    allowed.update(f"policy:{rule.rule_id}" for rule in context.policy.rules)
    citations = set()
    for text in (case.claim, *case.supporting_points):
        citations.update(re.findall(r"\[([^\[\]]*)\]", text))
        remainder = re.sub(r"\[[^\[\]]*\]", "", text)
        if "[" in remainder or "]" in remainder:
            raise LLMOutputError("Malformed Driver Advocate citation.")
    if citations - allowed:
        raise LLMOutputError("Driver Advocate cited an unknown evidence or policy ID.")
    if not any(c.startswith("evidence:") for c in citations) or not any(c.startswith("policy:") for c in citations):
        raise LLMOutputError("Driver Advocate must cite supplied evidence and policy.")
    return case


class DriverAdvocateAgent(BaseAgent[AdvocateInput, AdvocateCase]):
    name = "driver_advocate"

    def __init__(self, client: LLMClient | None = None) -> None:
        self._client = client if client is not None else llm_client

    async def run(self, context: AdvocateInput) -> AdvocateCase:
        context = AdvocateInput.model_validate(context)
        if self._client.is_mock:
            # Intentional offline behavior, never a fallback after an LLM failure.
            return AdvocateCase(
                side="driver",
                claim=context.dispute.driver_statement or "No driver statement supplied.",
                supporting_points=("Stub: LLM_PROVIDER=mock; no Driver Advocate reasoning was performed.",),
                requested_outcome="undetermined",
                source="stub",
            )
        try:
            raw = await self._client.complete(
                DRIVER_SYSTEM_PROMPT, driver_user_message(context), response_model=AdvocateCase,
            )
        except LLMConfigurationError as exc:
            logger.error("Driver Advocate configuration error: %s", exc)
            raise
        case = AdvocateCase.model_validate_json(raw)
        return _validate_case(case, context)


driver_advocate_agent = DriverAdvocateAgent()
