"""Allowlisted fixture loading. Paths never come from user input."""
from pathlib import Path
from uuid import uuid4

from app.schemas.dispute import (
    Dispute, DisputeCategory, DisputeSubmission, EvidenceBundle,
    PolicyContext, Scenario, ScenarioSummary,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SCENARIO_FILES = {
    "route_deviation_001": "route_deviation_001.json",
    "no_show_001": "no_show_001.json",
}


class UnknownScenarioError(ValueError):
    pass


class ScenarioMismatchError(ValueError):
    pass


def load_scenario(scenario_id: str) -> Scenario:
    filename = SCENARIO_FILES.get(scenario_id)
    if filename is None:
        raise UnknownScenarioError(f"Unknown scenario: {scenario_id}")
    scenario = Scenario.model_validate_json(
        (DATA_DIR / "scenarios" / filename).read_text(encoding="utf-8")
    )
    if scenario.scenario_id != scenario_id:
        raise ScenarioMismatchError("Fixture scenario identifier does not match its key")
    return scenario


def list_scenarios() -> tuple[ScenarioSummary, ...]:
    return tuple(
        ScenarioSummary(**load_scenario(key).model_dump(include={
            "scenario_id", "category", "title", "description",
        }))
        for key in SCENARIO_FILES
    )


def create_dispute(submission: DisputeSubmission) -> Dispute:
    submission = DisputeSubmission.model_validate(submission)
    scenario = load_scenario(submission.scenario_id)
    if scenario.category != submission.category:
        raise ScenarioMismatchError(
            f"Scenario {scenario.scenario_id} requires category {scenario.category.value}"
        )
    return Dispute(
        **submission.model_dump(), dispute_id=str(uuid4()), trip_id=scenario.trip_id,
        rider_id=scenario.rider_id, driver_id=scenario.driver_id,
    )


def load_evidence(dispute: Dispute) -> EvidenceBundle:
    scenario = load_scenario(dispute.scenario_id)
    if (scenario.category, scenario.trip_id, scenario.rider_id, scenario.driver_id) != (
        dispute.category, dispute.trip_id, dispute.rider_id, dispute.driver_id,
    ):
        raise ScenarioMismatchError("Dispute identifiers/category do not match the scenario")
    return scenario.evidence


def load_policy(category: DisputeCategory | str) -> PolicyContext:
    category = DisputeCategory(category)
    policy = PolicyContext.model_validate_json(
        (DATA_DIR / "policies" / f"{category.value}.json").read_text(encoding="utf-8")
    )
    if policy.category != category:
        raise ScenarioMismatchError("Policy category does not match its lookup key")
    return policy
