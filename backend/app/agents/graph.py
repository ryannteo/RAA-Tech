"""Shared wiring: deterministic context -> isolated advocates -> judge -> validation."""
from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from app.agents.driver_agent import driver_advocate_agent
from app.agents.escalation_agent import route_ruling
from app.agents.evidence_agent import evidence_agent
from app.agents.judge_agent import judge_agent
from app.agents.llm import LLMError
from app.agents.policy_agent import policy_precedent_agent
from app.agents.rider_agent import rider_advocate_agent
from app.agents.sla_agent import sla_routing_agent
from app.agents.state import DisputeState
from app.config import get_settings
from app.schemas.dispute import (
    AdvocateCase, AdvocateFailureDetail, AdvocateInput, Dispute, DisputeResult,
    EvidenceBundle, JudgeInput, PolicyContext, ResolutionStatus, Ruling,
)


class AdvocateContractError(Exception):
    def __init__(self, stage: str):
        label = stage.replace("_", " ").capitalize()
        self.detail = AdvocateFailureDetail(
            stage=stage,
            message=f"{label} returned an invalid case; workflow stopped before judge execution.",
        )
        super().__init__(self.detail.message)


def _advocate_input(state: DisputeState) -> AdvocateInput:
    # Deliberately excludes cases, ruling, and communication_log.
    return AdvocateInput(
        dispute=state["dispute"], evidence=state["evidence"], policy=state["policy"],
    )


async def _intake(state: DisputeState):
    return {
        "priority": await sla_routing_agent.run(state["dispute"]),
        "fraud_check": "not_implemented",
        "communication_log": (*state["communication_log"], sla_routing_agent.log(
            "Normal priority assigned. Fraud assessment is not implemented.",
        )),
    }


async def _evidence(state: DisputeState):
    evidence = EvidenceBundle.model_validate(await evidence_agent.run(state["dispute"]))
    return {
        "evidence": evidence,
        "communication_log": (*state["communication_log"], evidence_agent.log("Scenario evidence loaded.")),
    }


async def _policy(state: DisputeState):
    policy = PolicyContext.model_validate(await policy_precedent_agent.run(state["dispute"].category))
    return {
        "policy": policy,
        "communication_log": (*state["communication_log"], policy_precedent_agent.log("Category policy loaded for both advocates.")),
    }


async def _rider(state: DisputeState):
    try:
        case = AdvocateCase.model_validate(await rider_advocate_agent.run(_advocate_input(state)))
        if case.side != "rider":
            raise AdvocateContractError("rider_advocate")
    except (ValidationError, LLMError) as exc:
        raise AdvocateContractError("rider_advocate") from exc
    return {
        "rider_case": case,
        "communication_log": (*state["communication_log"], rider_advocate_agent.log(f"Rider case received ({case.source}).")),
    }


async def _driver(state: DisputeState):
    try:
        case = AdvocateCase.model_validate(await driver_advocate_agent.run(_advocate_input(state)))
        if case.side != "driver":
            raise AdvocateContractError("driver_advocate")
    except ValidationError as exc:
        raise AdvocateContractError("driver_advocate") from exc
    return {
        "driver_case": case,
        "communication_log": (*state["communication_log"], driver_advocate_agent.log(f"Driver case received ({case.source}).")),
    }


async def _judge(state: DisputeState):
    context = JudgeInput(
        context=_advocate_input(state),
        rider_case=state["rider_case"], driver_case=state["driver_case"],
    )
    try:
        candidate = await judge_agent.run(context)
    except ValidationError:
        # A typed agent may raise while constructing its Ruling.
        candidate = None
    return {"ruling_candidate": candidate}


def _validate_ruling(state: DisputeState):
    try:
        ruling = Ruling.model_validate(state.get("ruling_candidate"))
    except ValidationError:
        # No confidence routing occurs without a valid Ruling.
        return {
            "ruling": None,
            "ruling_candidate": None,
            "status": ResolutionStatus.NEEDS_REVIEW,
            "review_reason": "Judge returned a missing or malformed ruling.",
            "communication_log": (*state["communication_log"], judge_agent.log(
                "Ruling validation failed; needs_review. No human decision has been recorded.",
            )),
        }
    status = route_ruling(ruling, state["confidence_threshold"])
    reason = (
        f"Judge confidence {ruling.confidence} is below threshold "
        f'{state["confidence_threshold"]}.'
        if status == ResolutionStatus.NEEDS_REVIEW else None
    )
    return {
        "ruling": ruling,
        "ruling_candidate": None,
        "status": status,
        "review_reason": reason,
        "communication_log": (*state["communication_log"], judge_agent.log(
            f"Validated ruling ({ruling.source}); {status.value}.",
        )),
    }


def build_graph():
    graph = StateGraph(DisputeState)
    for name, node in (
        ("sla_intake", _intake), ("evidence", _evidence), ("policy", _policy),
        ("rider", _rider), ("driver", _driver), ("judge", _judge),
        ("validate_ruling", _validate_ruling),
    ):
        graph.add_node(name, node)
    graph.set_entry_point("sla_intake")
    for start, end in (
        ("sla_intake", "evidence"), ("evidence", "policy"), ("policy", "rider"),
        ("rider", "driver"), ("driver", "judge"), ("judge", "validate_ruling"),
    ):
        graph.add_edge(start, end)
    # Both statuses are terminal. Review does not simulate a person or feedback.
    graph.add_edge("validate_ruling", END)
    return graph.compile()


compiled_graph = build_graph()


async def run_dispute_graph(dispute: Dispute) -> DisputeResult:
    dispute = Dispute.model_validate(dispute)
    initial_state: DisputeState = {
        "dispute": dispute,
        "confidence_threshold": get_settings().judge_confidence_threshold,
        "communication_log": (),
    }
    state = await compiled_graph.ainvoke(initial_state)
    state.pop("ruling_candidate", None)
    return DisputeResult.model_validate(state)
