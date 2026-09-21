# Every agent implements this. Use self.log() for anything that should show
# up in the frontend's live agent-communication timeline.
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from app.agents.state import DisputeState


class BaseAgent(ABC):
    name: str = "base_agent"

    @abstractmethod
    async def run(self, state: DisputeState) -> DisputeState:
        ...

    def log(self, state: DisputeState, message: str, data: Optional[dict[str, Any]] = None) -> None:
        state.setdefault("communication_log", []).append(
            {
                "agent": self.name,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data,
            }
        )
