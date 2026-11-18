
from datetime import datetime, timezone

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    JSON
)

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ==========================================
# ESTADÍSTICAS POR ENTRENADOR
# ==========================================

class EstadisticaKafka(Base):

    __tablename__ = "kafka_estadisticas"

    jugador_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    victorias: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    derrotas: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    ataques_jugador: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    ataques_enemigo: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    dano_causado: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    dano_recibido: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# ==========================================
# HISTORIAL DE EVENTOS PROCESADOS
# ==========================================

class EventoProcesadoKafka(Base):

    __tablename__ = "kafka_eventos_procesados"

    event_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True
    )

    topic: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    player_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    procesado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
