"""Validated public contracts. Keep frontend/src/types.ts in sync."""
from datetime import datetime
from enum import Enum
from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ScenarioId = Literal["route_deviation_001", "no_show_001"]
Text = Annotated[str, Field(min_length=1)]
NonNegative = Annotated[float, Field(ge=0, allow_inf_nan=False, strict=True)]
Count = Annotated[int, Field(ge=0, strict=True)]
Confidence = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False, strict=True)]


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, str_strip_whitespace=True,
        revalidate_instances="always",
    )


class DisputeCategory(str, Enum):
    ROUTE_DEVIATION = "route_deviation"
    NO_SHOW = "no_show"


class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    NEEDS_REVIEW = "needs_review"


class DisputeSubmission(Contract):
    scenario_id: Text
    category: DisputeCategory
    rider_statement: str | None = None
    driver_statement: str | None = None

    @field_validator("rider_statement", "driver_statement")
    @classmethod
    def normalize_statement(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class Dispute(DisputeSubmission):
    scenario_id: ScenarioId
    dispute_id: Text
    trip_id: Text
    rider_id: Text
    driver_id: Text


T = TypeVar("T")


class EvidenceItem(Contract, Generic[T]):
    """Unavailable data is null with a reason; zero and empty collections are data."""
    availability: Literal["available", "unavailable"]
    data: T | None
    reason: Text | None = None

    @model_validator(mode="after")
    def consistent_availability(self):
        if self.availability == "available":
            if self.data is None or self.reason is not None:
                raise ValueError("Available evidence requires data and no unavailable reason")
        elif self.data is not None or self.reason is None:
            raise ValueError("Unavailable evidence requires null data and a reason")
        return self


class GPSPoint(Contract):
    timestamp: datetime
    latitude: Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
    longitude: Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
    accuracy_m: NonNegative


class TelemetryEvent(Contract):
    timestamp: datetime
    source: Text
    description: Text


class GPSTelemetry(Contract):
    points: tuple[GPSPoint, ...]
    actual_route_km: NonNegative | None
    estimated_route_km: NonNegative | None
    waiting_minutes: NonNegative | None
    pickup_distance_m: NonNegative | None
    events: tuple[TelemetryEvent, ...]
    limitations: tuple[Text, ...]


class ChatMessage(Contract):
    timestamp: datetime
    sender: Literal["rider", "driver", "system"]
    message: Text
    delivered: bool | None


class FareData(Contract):
    currency: Literal["SGD"]
    quoted_total: NonNegative | None
    charged_total: NonNegative | None
    distance_charge: NonNegative | None
    cancellation_fee: NonNegative | None
    tolls: NonNegative | None
    limitations: tuple[Text, ...]


class AccountHistory(Contract):
    completed_trips: Count | None
    prior_disputes: Count | None
    prior_cancellations: Count | None


class UserHistory(Contract):
    rider: AccountHistory
    driver: AccountHistory
    limitations: tuple[Text, ...]


class EvidenceBundle(Contract):
    scenario_id: ScenarioId
    trip_id: Text
    gps_data: EvidenceItem[GPSTelemetry]
    chat_logs: EvidenceItem[tuple[ChatMessage, ...]]
    fare_data: EvidenceItem[FareData]
    user_history: EvidenceItem[UserHistory]


class PolicyRule(Contract):
    rule_id: Text
    title: Text
    text: Text


class PolicyContext(Contract):
    category: DisputeCategory
    version: Text
    is_mock: bool
    rules: Annotated[tuple[PolicyRule, ...], Field(min_length=1)]


class AdvocateInput(Contract):
    """Same immutable facts for each advocate; no cases or conversation log."""
    dispute: Dispute
    evidence: EvidenceBundle
    policy: PolicyContext

    @model_validator(mode="after")
    def matching_context(self):
        if (self.evidence.scenario_id != self.dispute.scenario_id
                or self.evidence.trip_id != self.dispute.trip_id
                or self.policy.category != self.dispute.category):
            raise ValueError("Evidence and policy must match the dispute")
        return self


Decision = Literal["full_refund", "partial_refund", "no_action"]


class AdvocateCase(Contract):
    side: Literal["rider", "driver"]
    claim: Text
    supporting_points: tuple[Text, ...]
    requested_outcome: Literal["full_refund", "partial_refund", "no_action", "undetermined"]
    source: Literal["stub", "llm"]


class AdvocateFailureDetail(Contract):
    code: Literal["advocate_contract_failure"] = "advocate_contract_failure"
    stage: Literal["rider_advocate", "driver_advocate"]
    message: Text


class JudgeInput(Contract):
    context: AdvocateInput
    rider_case: AdvocateCase
    driver_case: AdvocateCase

    @model_validator(mode="after")
    def correct_sides(self):
        if self.rider_case.side != "rider" or self.driver_case.side != "driver":
            raise ValueError("Judge requires one correctly labelled case from each side")
        return self


class Ruling(Contract):
    decision: Decision
    amount: NonNegative | None
    currency: Literal["SGD"]
    reasoning: Text
    confidence: Confidence
    source: Literal["stub", "llm"]


class AgentLogEntry(Contract):
    agent: Text
    message: Text
    timestamp: datetime


class ScenarioSummary(Contract):
    scenario_id: ScenarioId
    category: DisputeCategory
    title: Text
    description: Text


class Scenario(ScenarioSummary):
    trip_id: Text
    rider_id: Text
    driver_id: Text
    evidence: EvidenceBundle

    @model_validator(mode="after")
    def matching_evidence(self):
        if (self.evidence.scenario_id != self.scenario_id
                or self.evidence.trip_id != self.trip_id):
            raise ValueError("Scenario evidence identifiers do not match")
        return self


class DisputeResult(Contract):
    dispute: Dispute
    priority: Literal["normal"]
    evidence: EvidenceBundle
    policy: PolicyContext
    rider_case: AdvocateCase
    driver_case: AdvocateCase
    ruling: Ruling | None
    status: ResolutionStatus
    review_reason: Text | None
    confidence_threshold: Confidence
    fraud_check: Literal["not_implemented"]
    communication_log: tuple[AgentLogEntry, ...]

    @model_validator(mode="after")
    def consistent_result(self):
        JudgeInput(
            context=AdvocateInput(dispute=self.dispute, evidence=self.evidence, policy=self.policy),
            rider_case=self.rider_case, driver_case=self.driver_case,
        )
        if self.ruling is None:
            expected = ResolutionStatus.NEEDS_REVIEW
        else:
            expected = (ResolutionStatus.RESOLVED
                        if self.ruling.confidence >= self.confidence_threshold
                        else ResolutionStatus.NEEDS_REVIEW)
        if self.status != expected:
            raise ValueError("Status must agree with the validated ruling and threshold")
        if (self.status == ResolutionStatus.NEEDS_REVIEW) != (self.review_reason is not None):
            raise ValueError("Only needs_review results require a review reason")
        return self
