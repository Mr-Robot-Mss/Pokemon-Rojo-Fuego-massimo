
import json
import logging

from datetime import datetime, timezone
from uuid import uuid4

from confluent_kafka import Producer

from app.messaging.kafka_config import (
    PRODUCER_CONFIG,
    TOPIC_BATTLES,
    TOPIC_EVENTS
)


# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("pokemon.kafka.producer")


# ==========================================
# PRODUCTOR KAFKA
# ==========================================

producer = Producer(PRODUCER_CONFIG)


# ==========================================
# CREAR EVENTO ESTRUCTURADO
# ==========================================

def crear_evento(
    event_type: str,
    player_id: int,
    data: dict
) -> dict:

    if not event_type.strip():
        raise ValueError("event_type es obligatorio")

    if player_id <= 0:
        raise ValueError("player_id debe ser positivo")

    if not isinstance(data, dict):
        raise ValueError("data debe ser un diccionario")

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
# PUBLICAR Y CONFIRMAR ENTREGA
# ==========================================

def publicar_evento(
    topic: str,
    evento: dict
) -> dict:

    if topic not in (TOPIC_BATTLES, TOPIC_EVENTS):
        raise ValueError(
            f"Tópico no permitido: {topic}"
        )

    # Usamos player_id como clave para
    # conservar orden por entrenador
    # dentro de una partición.
    player_id = evento.get("player_id")

    if not isinstance(player_id, int) or player_id <= 0:
        raise ValueError("player_id inválido")

    payload = json.dumps(
        evento,
        ensure_ascii=False
    ).encode("utf-8")

    resultado = {
        "entregado": False,
        "error": None,
        "topic": topic,
        "partition": None,
        "offset": None
    }

    def confirmar_entrega(error, mensaje):

        if error is not None:

            resultado["error"] = str(error)

            logger.error(
                "Error publicando evento: %s",
                error
            )

            return

        resultado["entregado"] = True
        resultado["partition"] = mensaje.partition()
        resultado["offset"] = mensaje.offset()

        logger.info(
            "Evento entregado | topic=%s | "
            "partition=%s | offset=%s",
            mensaje.topic(),
            mensaje.partition(),
            mensaje.offset()
        )

    try:

        producer.produce(
            topic=topic,
            key=str(player_id).encode("utf-8"),
            value=payload,
            callback=confirmar_entrega
        )

        # Para esta primera versión esperamos
        # la confirmación antes de responder.
        pendientes = producer.flush(timeout=20)

        if pendientes > 0:
            raise RuntimeError(
                "Kafka no confirmó todos los mensajes"
            )

        if not resultado["entregado"]:
            raise RuntimeError(
                resultado["error"]
                or "No se confirmó la entrega"
            )

        return resultado

    except Exception:

        logger.exception(
            "Falló la publicación en Kafka"
        )

        raise


# ==========================================
# EVENTO: COMBATE TERMINADO
# ==========================================

def publicar_combate_terminado(
    player_id: int,
    battle_id: int,
    winner: str,
    experience_gained: int,
    pokemon_player: str,
    pokemon_enemy: str
) -> dict:

    evento = crear_evento(
        event_type="BattleCompleted",
        player_id=player_id,
        data={
            "battle_id": battle_id,
            "winner": winner,
            "experience_gained": experience_gained,
            "pokemon_player": pokemon_player,
            "pokemon_enemy": pokemon_enemy
        }
    )

    publicar_evento(
        TOPIC_BATTLES,
        evento
    )

    return evento


# ==========================================
# EVENTO: ATAQUE EJECUTADO
# ==========================================

def publicar_ataque(
    player_id: int,
    battle_id: int,
    turn: int,
    pokemon: str,
    movement: str,
    damage: int,
    remaining_hp: int
) -> dict:

    evento = crear_evento(
        event_type="AttackExecuted",
        player_id=player_id,
        data={
            "battle_id": battle_id,
            "turn": turn,
            "pokemon": pokemon,
            "movement": movement,
            "damage": damage,
            "remaining_hp": remaining_hp
        }
    )

    publicar_evento(
        TOPIC_EVENTS,
        evento
    )

    return evento
