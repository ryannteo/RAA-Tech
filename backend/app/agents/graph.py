# LangGraph wiring - mirrors the team's flowchart. This is shared glue;
# individual agents (in this folder) are owned/implemented independently.
from langgraph.graph import END, StateGraph

from app.agents.escalation_agent import escalation_agent, feedback_loop_agent, human_review_agent
from app.agents.evidence_agent import evidence_agent
from app.agents.fraud_agent import fraud_detection_agent
from app.agents.driver_agent import driver_advocate_agent
from app.agents.judge_agent import judge_agent
from app.agents.policy_agent import policy_precedent_agent
from app.agents.rider_agent import rider_advocate_agent
from app.agents.sla_agent import sla_routing_agent
from app.agents.state import DisputeState
from app.config import get_settings


def _route_after_judge(state: DisputeState) -> str:
    settings = get_settings()
    confidence = state.get("confidence", 0.0)
    return "resolved" if confidence >= settings.judge_confidence_threshold else "escalate"


def build_graph():
    graph = StateGraph(DisputeState)

    graph.add_node("sla_intake", sla_routing_agent.run)
    graph.add_node("evidence", evidence_agent.run)
    graph.add_node("fraud", fraud_detection_agent.run)
    graph.add_node("rider", rider_advocate_agent.run)
    graph.add_node("driver", driver_advocate_agent.run)
    graph.add_node("policy", policy_precedent_agent.run)
    graph.add_node("judge", judge_agent.run)
    graph.add_node("escalate", escalation_agent.run)
    graph.add_node("sla_escalation_routing", sla_routing_agent.run)
    graph.add_node("human_review", human_review_agent.run)
    graph.add_node("feedback_loop", feedback_loop_agent.run)

    graph.set_entry_point("sla_intake")
    graph.add_edge("sla_intake", "evidence")
    graph.add_edge("evidence", "fraud")

    # Diagram shows Rider/Driver running in parallel off the same evidence.
    # Wired sequentially here for simplicity - swap for asyncio.gather in a
    # wrapper node if you want true concurrency.
    graph.add_edge("fraud", "rider")
    graph.add_edge("rider", "driver")
    graph.add_edge("driver", "policy")

    graph.add_edge("policy", "judge")
    graph.add_conditional_edges("judge", _route_after_judge, {"resolved": END, "escalate": "escalate"})

    graph.add_edge("escalate", "sla_escalation_routing")
    graph.add_edge("sla_escalation_routing", "human_review")
    graph.add_edge("human_review", "feedback_loop")
    graph.add_edge("feedback_loop", END)

    return graph.compile()


compiled_graph = build_graph()


async def run_dispute_graph(initial_state: DisputeState) -> DisputeState:
    return await compiled_graph.ainvoke(initial_state)
