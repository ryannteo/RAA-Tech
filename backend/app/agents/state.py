# Shared state contract passed between every agent in the graph.
# Add fields here first if an agent needs something new, so everyone stays synced.
from typing import Any, Optional, TypedDict


class AgentLogEntry(TypedDict):
    agent: str
    message: str
    timestamp: str
    data: Optional[dict[str, Any]]


class DisputeState(TypedDict, total=False):
    # Intake
    dispute_id: str
    category: str  # route_deviation | no_show | property_damage | safety_incident
    trip_id: str
    rider_id: str
    driver_id: str
    rider_statement: str
    driver_statement: Optional[str]
    priority: Optional[str]  # set by SLARoutingAgent

    # Evidence (set by EvidenceAgent)
    gps_data: Optional[dict]
    chat_logs: Optional[list]
    fare_data: Optional[dict]
    user_history: Optional[dict]

    # Risk (set by FraudDetectionAgent)
    risk_signals: Optional[dict]

    # Cases (set by the advocate agents)
    rider_case: Optional[dict]
    driver_case: Optional[dict]

    # Policy context (set by PolicyPrecedentAgent)
    policy_context: Optional[list]

    # Ruling (set by JudgeAgent)
    ruling: Optional[dict]
    confidence: Optional[float]

    # Escalation path
    escalated: bool
    escalation_reason: Optional[str]
    human_decision: Optional[dict]

    # Powers the frontend's live agent timeline
    communication_log: list[AgentLogEntry]
