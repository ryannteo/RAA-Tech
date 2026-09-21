# Tencent Cloud Postgres schema - placeholder, not wired up yet.
# API currently uses app/db/store.py (in-memory) so no one needs real
# credentials to develop. Once TENCENT_DB_* env vars are filled in:
#   1. Add an async engine/session using settings.database_url
#   2. Swap store.py calls in app/api/routes.py for real reads/writes
#   3. Add Alembic (or Base.metadata.create_all on startup) for migrations
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    category: Mapped[str] = mapped_column(String)
    trip_id: Mapped[str] = mapped_column(String)
    rider_id: Mapped[str] = mapped_column(String)
    driver_id: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    dispute_id: Mapped[str] = mapped_column(ForeignKey("disputes.id"))
    agent_name: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Ruling(Base):
    __tablename__ = "rulings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    dispute_id: Mapped[str] = mapped_column(ForeignKey("disputes.id"), unique=True)
    decision: Mapped[str] = mapped_column(String)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
