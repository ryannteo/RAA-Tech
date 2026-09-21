"""Agent implementations consume contracts, never the entire graph state."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Generic, TypeVar

from app.schemas.dispute import AgentLogEntry

Input = TypeVar("Input")
Output = TypeVar("Output")


class BaseAgent(ABC, Generic[Input, Output]):
    name: str = "base_agent"

    @abstractmethod
    async def run(self, context: Input) -> Output:
        ...

    def log(self, message: str) -> AgentLogEntry:
        return AgentLogEntry(
            agent=self.name, message=message, timestamp=datetime.now(timezone.utc),
        )
