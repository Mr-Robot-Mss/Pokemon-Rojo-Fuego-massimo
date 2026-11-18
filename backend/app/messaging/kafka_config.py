
import os

from pathlib import Path
from dotenv import load_dotenv


# ==========================================
# CARGAR VARIABLES DE ENTORNO
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


# ==========================================
# CONEXIÓN KAFKA - WINDOWS / DOCKER
# ==========================================

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    (
        "127.0.0.1:19092,"
        "127.0.0.1:19093,"
        "127.0.0.1:19094"
    )
).replace("localhost", "127.0.0.1")


# ==========================================
# TÓPICOS
# ==========================================

TOPIC_BATTLES = "pokemon.battles"
TOPIC_EVENTS = "pokemon.events"


# ==========================================
# GRUPO DE CONSUMIDORES
# ==========================================

KAFKA_CONSUMER_GROUP = os.getenv(
    "KAFKA_CONSUMER_GROUP",
    "pokemon-massimo-events-v1"
)


# ==========================================
# CONFIGURACIÓN DEL PRODUCTOR
# ==========================================

PRODUCER_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "acks": "all",
    "enable.idempotence": True,
    "compression.type": "snappy",
    "message.timeout.ms": 15000,
    "client.id": "pokemon-massimo-producer",

    # Solo IPv4
    "broker.address.family": "v4"
}


# ==========================================
# CONFIGURACIÓN DEL CONSUMIDOR
# ==========================================

CONSUMER_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "group.id": KAFKA_CONSUMER_GROUP,
    "client.id": "pokemon-massimo-consumer",

    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
    "enable.auto.offset.store": False,
    "session.timeout.ms": 10000,

    # Solo IPv4
    "broker.address.family": "v4"
}
