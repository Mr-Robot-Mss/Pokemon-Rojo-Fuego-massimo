from datetime import datetime, timezone
import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from confluent_kafka import Consumer, TopicPartition
from confluent_kafka.admin import AdminClient

from app.database import SessionLocal
from app.messaging.kafka_config import KAFKA_BOOTSTRAP_SERVERS

router = APIRouter(prefix="/kafka", tags=["Kafka: monitoreo"])
logger = logging.getLogger(__name__)
TOPICS = ("pokemon.events", "pokemon.battles")
GROUP = "pokemon-massimo-analytics-v1"


def _partitions_and_offsets(metadata):
    broker_ids = sorted(metadata.brokers.keys())
    group_consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP,
        "enable.auto.commit": False,
        "broker.address.family": "v4",
        "socket.timeout.ms": 4000,
    })
    try:
        requested = [
            TopicPartition(topic, partition)
            for topic in TOPICS
            if topic in metadata.topics
            for partition in metadata.topics[topic].partitions
        ]
        committed = {}
        try:
            for item in group_consumer.committed(requested, timeout=4.0):
                committed[(item.topic, item.partition)] = (
                    item.offset if item.offset is not None and item.offset >= 0 else None
                )
        except Exception:
            pass
        topics = []
        for topic in TOPICS:
            meta = metadata.topics.get(topic)
            if not meta or meta.error:
                topics.append({"name": topic, "partitions": []})
                continue
            partitions = []
            for pid, part in sorted(meta.partitions.items()):
                current = committed.get((topic, pid))
                high = None
                try:
                    _, high = group_consumer.get_watermark_offsets(
                        TopicPartition(topic, pid), timeout=2.0, cached=False
                    )
                except Exception:
                    pass
                partitions.append({
                    "id": pid,
                    "leader": part.leader if part.leader >= 0 else None,
                    "replicas": list(part.replicas),
                    "isr": list(part.isrs),
                    "offset_actual": current,
                    "offset_final": high,
                    "lag": max(0, high - current) if current is not None and high is not None else None,
                })
            topics.append({"name": topic, "partitions": partitions})
        return broker_ids, topics
    finally:
        group_consumer.close()


@router.get("/overview")
def kafka_overview():
    result = {
        "available": False,
        "brokers": [],
        "topics": [],
        "consumer_group": GROUP,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        metadata = AdminClient({
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "broker.address.family": "v4",
            "socket.timeout.ms": 4000,
        }).list_topics(timeout=4.0)
        ids, topics = _partitions_and_offsets(metadata)
        result.update(available=bool(ids), brokers=ids, topics=topics)
    except Exception as exc:
        result["error"] = str(exc)[:220]
    return result


@router.get("/stats/{player_id}")
def kafka_player_stats(player_id: int):
    if player_id <= 0:
        raise HTTPException(status_code=422, detail="ID inválido")
    with SessionLocal() as db:
        try:
            row = db.execute(text("""
                SELECT jugador_id, victorias, derrotas, ataques_jugador,
                       ataques_enemigo, dano_causado, dano_recibido, actualizado_en
                FROM kafka_estadisticas WHERE jugador_id = :player_id
            """), {"player_id": player_id}).mappings().first()
            if row is None:
                raise HTTPException(status_code=404, detail="Sin estadísticas procesadas")
            return dict(row)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=503, detail="Tabla de estadísticas no disponible")


@router.get("/activity")
def kafka_activity():
    with SessionLocal() as db:
        try:
            rows = db.execute(text("""
                SELECT id AS event_id,
                       payload->>'event_type' AS event_type,
                       topic, player_id, status, created_at, "partition", "offset"
                FROM kafka_outbox
                ORDER BY created_at DESC, id DESC LIMIT 30
            """)).mappings().all()
            return [dict(row) for row in rows]
        except Exception:
            logger.exception("Error al consultar la tabla kafka_outbox")
            raise HTTPException(status_code=503, detail="No se pudo consultar Kafka Outbox")
