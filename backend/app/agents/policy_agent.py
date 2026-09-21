# Policy & Precedent Agent - retrieves company policy + past rulings for the Judge (RAG).
# Writes: policy_context = [{title, excerpt}, ...]
# TODO: load backend/app/data/policies.json, embed it, similarity-search against
# state["category"] / the advocates' claims. Stretch: index past rulings as precedent.
from app.agents.base import BaseAgent
from app.agents.state import DisputeState


class PolicyPrecedentAgent(BaseAgent):
    name = "policy_precedent"

    async def run(self, state: DisputeState) -> DisputeState:
        self.log(state, f"Looking up policy for category '{state.get('category')}'...")

        state["policy_context"] = [
            {"title": "Placeholder Policy", "excerpt": "Replace with real policy retrieval."}
        ]

        self.log(state, "Policy context attached.")
        return state


policy_precedent_agent = PolicyPrecedentAgent()
