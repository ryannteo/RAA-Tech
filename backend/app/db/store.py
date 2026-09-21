"""Process-local demo store. No external database is used."""
from app.schemas.dispute import DisputeResult


class InMemoryDisputeStore:
    def __init__(self) -> None:
        self._disputes: dict[str, DisputeResult] = {}

    def save(self, result: DisputeResult) -> None:
        result = DisputeResult.model_validate(result)
        self._disputes[result.dispute.dispute_id] = result

    def get(self, dispute_id: str) -> DisputeResult | None:
        return self._disputes.get(dispute_id)

    def list(self) -> list[DisputeResult]:
        return list(self._disputes.values())


store = InMemoryDisputeStore()
