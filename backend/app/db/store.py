# In-memory store used until Tencent Cloud DB is wired up (see models.py).
from app.agents.state import DisputeState


class InMemoryDisputeStore:
    def __init__(self) -> None:
        self._disputes: dict[str, DisputeState] = {}

    def save(self, state: DisputeState) -> None:
        self._disputes[state["dispute_id"]] = state

    def get(self, dispute_id: str) -> DisputeState | None:
        return self._disputes.get(dispute_id)

    def list(self) -> list[DisputeState]:
        return list(self._disputes.values())


store = InMemoryDisputeStore()
