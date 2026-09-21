"""Integration contracts, not LLM-quality evaluations."""
from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.agents import graph
from app.agents.escalation_agent import route_ruling
from app.api import routes
from app.config import Settings
from app.db.store import InMemoryDisputeStore
from app.main import app
from app.schemas.dispute import (
    AdvocateCase, AdvocateInput, DisputeCategory, DisputeResult,
    DisputeSubmission, EvidenceItem, ResolutionStatus, Ruling,
)
from app.services.scenarios import (
    SCENARIO_FILES, ScenarioMismatchError, UnknownScenarioError,
    create_dispute, list_scenarios, load_evidence, load_policy, load_scenario,
)

SCENARIOS = [
    ("route_deviation_001", "route_deviation", "resolved"),
    ("no_show_001", "no_show", "needs_review"),
]


def submission(scenario_id="route_deviation_001", category="route_deviation", **kwargs):
    return DisputeSubmission(scenario_id=scenario_id, category=category, **kwargs)


def ruling_data(confidence=0.85):
    return {
        "decision": "partial_refund", "amount": 2.5, "currency": "SGD",
        "reasoning": "Test fixture ruling.", "confidence": confidence, "source": "stub",
    }


@pytest.fixture(autouse=True)
def isolated_settings_and_store(monkeypatch):
    monkeypatch.setattr(graph, "get_settings", lambda: SimpleNamespace(judge_confidence_threshold=0.75))
    monkeypatch.setattr(routes, "store", InMemoryDisputeStore())


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("statements", [
    {}, {"rider_statement": "Rider account."}, {"driver_statement": "Driver account."},
    {"rider_statement": "Rider account.", "driver_statement": "Driver account."},
    {"rider_statement": None, "driver_statement": None},
    {"rider_statement": "  ", "driver_statement": ""},
])
def test_optional_statements_through_api(client, statements):
    payload = {"scenario_id": "route_deviation_001", "category": "route_deviation", **statements}
    response = client.post("/disputes", json=payload)
    assert response.status_code == 200
    dispute = response.json()["dispute"]
    for side in ("rider", "driver"):
        value = statements.get(f"{side}_statement")
        assert dispute[f"{side}_statement"] == (value.strip() or None if value else None)


@pytest.mark.parametrize("category", ["unknown", "property_damage", "safety_incident", "", None, 7])
def test_category_validation(client, category):
    response = client.post("/disputes", json={"scenario_id": "route_deviation_001", "category": category})
    assert response.status_code == 422


def test_scenario_category_mismatch(client):
    response = client.post("/disputes", json={"scenario_id": "route_deviation_001", "category": "no_show"})
    assert response.status_code == 422
    assert "requires category route_deviation" in response.json()["detail"]


def test_exactly_two_scenarios(client):
    expected = {"route_deviation_001", "no_show_001"}
    assert set(SCENARIO_FILES) == expected
    assert {item.scenario_id for item in list_scenarios()} == expected
    response = client.get("/disputes/scenarios")
    assert response.status_code == 200
    assert {item["scenario_id"] for item in response.json()} == expected


@pytest.mark.parametrize("scenario_id,category,status", SCENARIOS)
def test_deterministic_evidence_and_policy(scenario_id, category, status):
    fixture = load_scenario(scenario_id)
    dispute = create_dispute(submission(scenario_id, category))
    assert fixture == load_scenario(scenario_id)
    assert load_evidence(dispute) == fixture.evidence
    policy = load_policy(category)
    assert policy == load_policy(DisputeCategory(category))
    assert policy.category == dispute.category
    assert policy.is_mock
    assert policy.rules
    evidence = fixture.evidence
    assert evidence.gps_data.data.points
    assert evidence.gps_data.data.events
    assert evidence.chat_logs.data
    assert evidence.fare_data.data.charged_total > 0
    assert evidence.user_history.data.rider.completed_trips > 0


def test_no_show_fixture_timing_and_fee_are_consistent():
    evidence = load_scenario("no_show_001").evidence
    gps = evidence.gps_data.data
    chat = evidence.chat_logs.data
    fare = evidence.fare_data.data
    arrival_at = gps.events[1].timestamp
    cancellation_at = gps.events[-1].timestamp
    latest_rider_message_at = max(message.timestamp for message in chat if message.sender == "rider")

    assert cancellation_at - arrival_at == timedelta(minutes=gps.waiting_minutes)
    assert latest_rider_message_at < cancellation_at
    assert fare.charged_total == fare.cancellation_fee


def test_route_deviation_fixture_fare_delta_is_sgd_4_60():
    fare = load_scenario("route_deviation_001").evidence.fare_data.data

    assert fare.currency == "SGD"
    assert round(fare.charged_total - fare.quoted_total, 2) == 4.60


@pytest.mark.parametrize("scenario_id", ["missing", "../policies/no_show", "trip-1"])
def test_unknown_scenario_is_clear(client, scenario_id):
    with pytest.raises(UnknownScenarioError, match="Unknown scenario"):
        load_scenario(scenario_id)
    response = client.post("/disputes", json={"scenario_id": scenario_id, "category": "no_show"})
    assert response.status_code == 404
    assert "Unknown scenario" in response.json()["detail"]


def test_wrong_trip_cannot_load_another_scenarios_evidence():
    dispute = create_dispute(submission()).model_copy(update={"trip_id": "wrong-trip"})
    with pytest.raises(ScenarioMismatchError):
        load_evidence(dispute)
    with pytest.raises(ValueError):
        load_policy("unsupported")


def test_zero_empty_and_unavailable_are_distinct():
    evidence = load_scenario("no_show_001").evidence
    assert evidence.gps_data.data.actual_route_km == 0
    assert evidence.fare_data.data.distance_charge == 0
    assert evidence.fare_data.data.tolls == 0
    assert evidence.user_history.data.rider.prior_disputes == 0
    assert evidence.user_history.data.driver.prior_cancellations is None
    available_zero = EvidenceItem[int](availability="available", data=0)
    available_empty = EvidenceItem[tuple[str, ...]](availability="available", data=())
    unavailable = EvidenceItem[int](availability="unavailable", data=None, reason="Source unavailable.")
    assert available_zero.model_dump()["data"] == 0
    assert available_empty.model_dump(mode="json")["data"] == []
    assert unavailable.model_dump()["data"] is None


@pytest.mark.parametrize("data", [
    {"availability": "available", "data": None},
    {"availability": "unavailable", "data": 0, "reason": "Missing"},
    {"availability": "unavailable", "data": None},
    {"availability": "available", "data": 0, "reason": "Missing"},
])
def test_invalid_availability_contract(data):
    with pytest.raises(ValidationError):
        EvidenceItem[int].model_validate(data)


@pytest.mark.parametrize("confidence", [-0.01, 1.01, float("nan"), float("inf"), float("-inf"), None, "0.9", True])
def test_invalid_confidence(confidence):
    with pytest.raises(ValidationError):
        Ruling.model_validate(ruling_data(confidence))


@pytest.mark.parametrize("confidence,expected", [
    (0.0, "needs_review"), (0.7499, "needs_review"),
    (0.75, "resolved"), (0.7501, "resolved"), (1.0, "resolved"),
])
def test_confidence_routing(confidence, expected):
    ruling = Ruling.model_validate(ruling_data(confidence))
    assert route_ruling(ruling, 0.75) == expected


@pytest.mark.parametrize("threshold", [-0.1, 1.1, float("nan"), float("inf")])
def test_threshold_validation(threshold):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, judge_confidence_threshold=threshold)
    with pytest.raises(ValueError):
        route_ruling(Ruling.model_validate(ruling_data()), threshold)


@pytest.mark.parametrize("candidate", [
    None, {}, {"confidence": 1.0}, {"ruling": None, "confidence": 1.0},
    {**ruling_data(), "reasoning": ""},
    ruling_data(1.1), ruling_data("0.99"),
    {**ruling_data(), "decision": "auto_approve"},
    {**ruling_data(), "amount": -1},
    "not JSON", '{"confidence": 1.0}',
    Ruling.model_construct(**ruling_data(9.0)),
])
async def test_invalid_ruling_ends_in_review_without_routing(monkeypatch, candidate):
    async def bad_judge(context):
        return candidate

    def forbidden_route(*args):
        pytest.fail("Confidence routing must never receive an invalid ruling")

    monkeypatch.setattr(graph.judge_agent, "run", bad_judge)
    monkeypatch.setattr(graph, "route_ruling", forbidden_route)
    # A zero threshold must not turn a missing confidence into a resolved outcome.
    monkeypatch.setattr(graph, "get_settings", lambda: SimpleNamespace(judge_confidence_threshold=0.0))
    result = await graph.run_dispute_graph(create_dispute(submission()))
    assert result.status == ResolutionStatus.NEEDS_REVIEW
    assert result.ruling is None
    assert "missing or malformed" in result.review_reason
    assert "human_decision" not in result.model_dump()
    assert "ruling_candidate" not in result.model_dump()


async def test_judge_validation_error_is_review(monkeypatch):
    async def invalid_typed_judge(context):
        return Ruling.model_validate(ruling_data(-1))
    monkeypatch.setattr(graph.judge_agent, "run", invalid_typed_judge)
    result = await graph.run_dispute_graph(create_dispute(submission()))
    assert result.status == ResolutionStatus.NEEDS_REVIEW
    assert result.ruling is None


def invalid_advocate_case(side, failure):
    if failure == "none":
        return None
    if failure == "malformed":
        return {"side": side, "claim": "Missing required fields."}
    if failure == "wrong_side":
        return AdvocateCase(
            side="driver" if side == "rider" else "rider",
            claim="Wrong-side case.", supporting_points=(),
            requested_outcome="undetermined", source="stub",
        )
    return AdvocateCase.model_validate({"side": side, "claim": ""})


@pytest.mark.parametrize("side", ["rider", "driver"])
@pytest.mark.parametrize("failure", ["none", "malformed", "wrong_side", "validation_error"])
async def test_advocate_contract_failure_stops_before_judge(monkeypatch, side, failure):
    async def bad_advocate(context):
        return invalid_advocate_case(side, failure)

    async def forbidden_judge(context):
        pytest.fail("Judge must not run after an advocate contract failure")

    monkeypatch.setattr(getattr(graph, f"{side}_advocate_agent"), "run", bad_advocate)
    monkeypatch.setattr(graph.judge_agent, "run", forbidden_judge)

    with pytest.raises(graph.AdvocateContractError) as caught:
        await graph.run_dispute_graph(create_dispute(submission()))

    assert caught.value.detail.code == "advocate_contract_failure"
    assert caught.value.detail.stage == f"{side}_advocate"


@pytest.mark.parametrize("side", ["rider", "driver"])
def test_api_returns_structured_advocate_failure(client, monkeypatch, side):
    async def bad_advocate(context):
        return None

    async def forbidden_judge(context):
        pytest.fail("Judge must not run after an advocate contract failure")

    monkeypatch.setattr(getattr(graph, f"{side}_advocate_agent"), "run", bad_advocate)
    monkeypatch.setattr(graph.judge_agent, "run", forbidden_judge)

    response = client.post("/disputes", json={
        "scenario_id": "route_deviation_001", "category": "route_deviation",
    })

    assert response.status_code == 502
    assert response.json() == {"detail": {
        "code": "advocate_contract_failure",
        "stage": f"{side}_advocate",
        "message": (
            f"{side.capitalize()} advocate returned an invalid case; "
            "workflow stopped before judge execution."
        ),
    }}
    assert client.get("/disputes").json() == []


@pytest.mark.parametrize("scenario_id,category,status", SCENARIOS)
async def test_advocates_receive_same_isolated_context(monkeypatch, scenario_id, category, status):
    captured = {}

    def advocate(side):
        async def run(context):
            assert isinstance(context, AdvocateInput)
            assert set(AdvocateInput.model_fields) == {"dispute", "evidence", "policy"}
            assert context.policy.category == category
            assert context.evidence == load_scenario(scenario_id).evidence
            with pytest.raises(ValidationError):
                context.evidence.gps_data.data.actual_route_km = 999
            captured[side] = context.model_dump()
            return AdvocateCase(
                side=side, claim=f"{side} test case", supporting_points=(),
                requested_outcome="undetermined", source="stub",
            )
        return run

    async def judge(context):
        assert context.rider_case.claim == "rider test case"
        assert context.driver_case.claim == "driver test case"
        assert context.context.model_dump() == captured["rider"]
        return Ruling.model_validate(ruling_data())

    monkeypatch.setattr(graph.rider_advocate_agent, "run", advocate("rider"))
    monkeypatch.setattr(graph.driver_advocate_agent, "run", advocate("driver"))
    monkeypatch.setattr(graph.judge_agent, "run", judge)
    await graph.run_dispute_graph(create_dispute(submission(scenario_id, category)))
    assert captured["rider"] == captured["driver"]


@pytest.mark.parametrize("confidence,threshold,expected", [
    (0.75, 0.75, "resolved"), (0.7499, 0.75, "needs_review"),
    (0.0, 0.0, "resolved"), (1.0, 1.0, "resolved"),
])
async def test_graph_routes_valid_ruling(monkeypatch, confidence, threshold, expected):
    async def judge(context):
        return Ruling.model_validate(ruling_data(confidence))
    monkeypatch.setattr(graph.judge_agent, "run", judge)
    monkeypatch.setattr(graph, "get_settings", lambda: SimpleNamespace(judge_confidence_threshold=threshold))
    result = await graph.run_dispute_graph(create_dispute(submission()))
    assert result.status == expected
    assert (result.review_reason is not None) == (expected == "needs_review")


@pytest.mark.parametrize("scenario_id,category,status", SCENARIOS)
def test_api_smoke_both_scenarios(client, scenario_id, category, status):
    response = client.post("/disputes", json={"scenario_id": scenario_id, "category": category})
    assert response.status_code == 200
    body = response.json()
    result = DisputeResult.model_validate(body)
    assert result.status == status
    assert result.ruling.source == "stub"
    assert result.rider_case.source == result.driver_case.source == "stub"
    assert result.fraud_check == "not_implemented"
    assert [entry.agent for entry in result.communication_log] == [
        "sla_routing", "evidence_collector", "policy_lookup",
        "rider_advocate", "driver_advocate", "judge",
    ]
    assert "confidence" not in body  # Confidence has exactly one source: Ruling.
    assert "human_decision" not in body
    assert "risk_signals" not in body
    assert client.get(f"/disputes/{result.dispute.dispute_id}").json() == body
    assert client.get("/disputes").json() == [body]
    assert client.get("/disputes/does-not-exist").status_code == 404


def test_api_exposes_invalid_ruling_as_review(client, monkeypatch):
    async def bad_judge(context):
        return {"confidence": 1.0}
    monkeypatch.setattr(graph.judge_agent, "run", bad_judge)
    body = client.post("/disputes", json={
        "scenario_id": "no_show_001", "category": "no_show",
    }).json()
    assert body["status"] == "needs_review"
    assert body["ruling"] is None


async def test_result_contract_rejects_invalid_resolved_state():
    result = await graph.run_dispute_graph(create_dispute(submission()))
    body = result.model_dump()
    body["ruling"] = None
    with pytest.raises(ValidationError, match="Status must agree"):
        DisputeResult.model_validate(body)


@pytest.mark.parametrize("change", ["policy", "evidence", "side"])
async def test_result_rejects_mismatched_case_context(change):
    result = await graph.run_dispute_graph(create_dispute(submission()))
    body = result.model_dump()
    if change == "policy":
        body["policy"] = load_policy("no_show").model_dump()
    elif change == "evidence":
        body["evidence"] = load_scenario("no_show_001").evidence.model_dump()
    else:
        body["rider_case"]["side"] = "driver"
    with pytest.raises(ValidationError):
        DisputeResult.model_validate(body)
