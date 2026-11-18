import json
import os

import pika

from dotenv import load_dotenv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

RABBITMQ_URL = os.getenv("RABBITMQ_URL")

if not RABBITMQ_URL:
    raise RuntimeError("Falta RABBITMQ_URL en .env")


EXCHANGE = "pokemon.events.direct"
DLX = "pokemon.events.dlx"

REWARD_QUEUE = "pokemon.rewards.queue"
REWARD_ROUTING_KEY = "battle.reward"

DLQ = "pokemon.rewards.dlq"
DLQ_ROUTING_KEY = "battle.reward.failed"


def obtener_conexion():

    parametros = pika.URLParameters(RABBITMQ_URL)

    parametros.heartbeat = 60
    parametros.blocked_connection_timeout = 30

    return pika.BlockingConnection(parametros)


def declarar_infraestructura(channel):

    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type="direct",
        durable=True
    )

    channel.exchange_declare(
        exchange=DLX,
        exchange_type="direct",
        durable=True
    )

    channel.queue_declare(
        queue=DLQ,
        durable=True
    )

    channel.queue_bind(
        queue=DLQ,
        exchange=DLX,
        routing_key=DLQ_ROUTING_KEY
    )

    channel.queue_declare(
        queue=REWARD_QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": DLX,
            "x-dead-letter-routing-key": DLQ_ROUTING_KEY
        }
    )

    channel.queue_bind(
        queue=REWARD_QUEUE,
        exchange=EXCHANGE,
        routing_key=REWARD_ROUTING_KEY
    )


def publicar_recompensa(
    battle_id: int,
    operation_id: str
):

    mensaje = {
        "operation_id": operation_id,
        "battle_id": battle_id,
        "task_type": "battle_reward",
        "amount": 5
    }

    conexion = obtener_conexion()

    try:
        channel = conexion.channel()

        declarar_infraestructura(channel)

        channel.confirm_delivery()

        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=REWARD_ROUTING_KEY,
            body=json.dumps(mensaje),
            mandatory=True,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
                message_id=operation_id,
                headers={"retry_count": 0}
            )
        )

        print(
            f"[RABBITMQ] Tarea publicada: {operation_id}"
        )

    finally:
        if conexion.is_open:
            conexion.close()