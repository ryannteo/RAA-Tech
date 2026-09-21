"""LangGraph transport only. Domain data lives in validated shared models."""
from typing import Literal, NotRequired, TypedDict

from app.schemas.dispute import (
    AdvocateCase, AgentLogEntry, Dispute, EvidenceBundle, PolicyContext,
    ResolutionStatus, Ruling,
)


class DisputeState(TypedDict):
    dispute: Dispute
    confidence_threshold: float
    communication_log: tuple[AgentLogEntry, ...]
    priority: NotRequired[Literal["normal"]]
    evidence: NotRequired[EvidenceBundle]
    policy: NotRequired[PolicyContext]
    rider_case: NotRequired[AdvocateCase]
    driver_case: NotRequired[AdvocateCase]
    # Untrusted only between the judge and validation nodes; never exposed by the API.
    ruling_candidate: NotRequired[object]
    ruling: NotRequired[Ruling | None]
    status: NotRequired[ResolutionStatus]
    review_reason: NotRequired[str | None]
    fraud_check: NotRequired[Literal["not_implemented"]]
