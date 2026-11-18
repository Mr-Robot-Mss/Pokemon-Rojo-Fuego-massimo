
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    JSON,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ==========================================
# MODELO DE EVENTOS PENDIENTES
# ==========================================

class KafkaOutbox(Base):

    __tablename__ = "kafka_outbox"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True
    )

    topic: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("jugadores.id"),
        nullable=False
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    partition: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    offset: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )


# ==========================================
# CONSTRUIR EVENTOS
# ==========================================

def crear_evento_outbox(
    player_id: int,
    event_type: str,
    data: dict
) -> dict:

    if player_id <= 0:
        raise ValueError("player_id inválido")

    if not event_type.strip():
        raise ValueError("event_type obligatorio")

    if not isinstance(data, dict):
        raise ValueError("data inválida")

    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "event_version": 1,
        "occurred_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "player_id": player_id,
        "data": data
    }


# ==========================================
# REGISTRAR EVENTO EN LA MISMA TRANSACCIÓN
# ==========================================

def guardar_evento_outbox(
    db,
    topic: str,
    evento: dict
):

    registro = KafkaOutbox(
        id=evento["event_id"],
        topic=topic,
        player_id=evento["player_id"],
        payload=evento,
        status="pending",
        attempts=0
    )

    db.add(registro)

    # IMPORTANTE:
    # No hacemos db.commit() aquí.
    # El combate y sus eventos se guardan
    # juntos cuando turns.py confirma
    # la transacción de PostgreSQL.

    return registro

