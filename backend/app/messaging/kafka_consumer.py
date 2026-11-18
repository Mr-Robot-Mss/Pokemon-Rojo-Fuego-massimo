
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from confluent_kafka import Consumer
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.database import (
    SessionLocal,
    engine
)

from app.messaging.kafka_config import (
    CONSUMER_CONFIG,
    TOPIC_BATTLES,
    TOPIC_EVENTS
)

from app.messaging.kafka_outbox import KafkaOutbox

from app.messaging.kafka_analytics import (
    EstadisticaKafka,
    EventoProcesadoKafka
)


# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("pokemon.kafka.analytics")


# ==========================================
# CONFIGURACIÓN DEL CONSUMIDOR
# ==========================================

CONFIG = CONSUMER_CONFIG.copy()

CONFIG.update({
    "group.id": "pokemon-massimo-analytics-v1",
    "client.id": "pokemon-analytics-consumer",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
    "enable.auto.offset.store": False
})


# ==========================================
# VALIDAR MENSAJES
# ==========================================

def validar_evento(evento, topic):

    if not isinstance(evento, dict):
        raise ValueError("Evento JSON inválido")

    campos = [
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "player_id",
        "data"
    ]

    for campo in campos:
        if campo not in evento:
            raise ValueError(f"Falta el campo: {campo}")

    UUID(str(evento["event_id"]))

    if type(evento["event_version"]) is not int:
        raise ValueError("Versión inválida")

    if evento["event_version"] != 1:
        raise ValueError("Versión no soportada")

    if (
        type(evento["player_id"]) is not int
        or evento["player_id"] <= 0
    ):
        raise ValueError("Jugador inválido")

    if not isinstance(evento["data"], dict):
        raise ValueError("Datos inválidos")

    if not isinstance(evento["occurred_at"], str):
        raise ValueError("Fecha inválida")

    datetime.fromisoformat(evento["occurred_at"])

    tipos = {
        TOPIC_EVENTS: "AttackExecuted",
        TOPIC_BATTLES: "BattleCompleted"
    }

    if evento["event_type"] != tipos.get(topic):
        raise ValueError("Tipo de evento incorrecto")


# ==========================================
# CALCULAR ESTADÍSTICAS
# ==========================================

def calcular_cambios(evento):

    tipo = evento["event_type"]
    datos = evento["data"]

    cambios = {
        "victorias": 0,
        "derrotas": 0,
        "ataques_jugador": 0,
        "ataques_enemigo": 0,
        "dano_causado": 0,
        "dano_recibido": 0
    }

    if tipo == "BattleCompleted":

        if datos.get("winner") == "jugador":
            cambios["victorias"] = 1

        elif datos.get("winner") == "salvaje":
            cambios["derrotas"] = 1

        else:
            raise ValueError("Resultado desconocido")

    elif tipo == "AttackExecuted":

        actor = datos.get("actor")
        dano = datos.get("damage")

        if type(dano) is not int or dano < 0:
            raise ValueError("Daño inválido")

        if actor == "jugador":

            cambios["ataques_jugador"] = 1
            cambios["dano_causado"] = dano

        elif actor == "enemigo":

            cambios["ataques_enemigo"] = 1
            cambios["dano_recibido"] = dano

        else:
            raise ValueError("Actor desconocido")

    else:
        raise ValueError("Evento desconocido")

    return cambios


# ==========================================
# GUARDAR ESTADÍSTICAS
# ==========================================

def actualizar_estadisticas(db, jugador_id, cambios):

    tabla = EstadisticaKafka

    ahora = datetime.now(timezone.utc)

    sentencia = insert(tabla).values(
        jugador_id=jugador_id,
        actualizado_en=ahora,
        **cambios
    )

    incrementos = {
        campo: getattr(tabla, campo) + valor
        for campo, valor in cambios.items()
    }

    incrementos["actualizado_en"] = ahora

    sentencia = sentencia.on_conflict_do_update(
        index_elements=[tabla.jugador_id],
        set_=incrementos
    )

    db.execute(sentencia)


# ==========================================
# PROCESAR EVENTO CON IDEMPOTENCIA
# ==========================================

def procesar_evento(topic, evento):

    event_id = evento["event_id"]
    jugador_id = evento["player_id"]

    with SessionLocal() as db:

        try:

            # Solo procesar eventos generados
            # por nuestro juego mediante Outbox.
            origen = db.scalar(
                select(KafkaOutbox.id).where(
                    KafkaOutbox.id == event_id,
                    KafkaOutbox.topic == topic,
                    KafkaOutbox.player_id == jugador_id
                )
            )

            if origen is None:

                logger.warning(
                    "EVENTO DE PRUEBA OMITIDO | %s",
                    event_id
                )

                db.rollback()
                return "omitido"

            cambios = calcular_cambios(evento)

            # Registrar el evento antes de
            # incrementar estadísticas.
            sentencia = insert(
                EventoProcesadoKafka
            ).values(
                event_id=event_id,
                topic=topic,
                event_type=evento["event_type"],
                player_id=jugador_id,
                payload=evento,
                procesado_en=datetime.now(timezone.utc)
            ).on_conflict_do_nothing(
                index_elements=[
                    EventoProcesadoKafka.event_id
                ]
            )

            resultado = db.execute(sentencia)

            if resultado.rowcount == 0:

                logger.info(
                    "DUPLICADO IGNORADO | %s",
                    event_id
                )

                db.rollback()
                return "duplicado"

            actualizar_estadisticas(
                db,
                jugador_id,
                cambios
            )

            # Historial y contadores se
            # confirman en la misma transacción.
            db.commit()

            logger.info(
                "ESTADISTICA ACTUALIZADA | "
                "jugador=%s | evento=%s",
                jugador_id,
                evento["event_type"]
            )

            return "procesado"

        except Exception:

            db.rollback()
            logger.exception(
                "Error procesando evento %s",
                event_id
            )
            raise


# ==========================================
# CONSUMIDOR PRINCIPAL
# ==========================================

def iniciar_consumidor():

    print("\n===================================")
    print(" POKEMON ROJO MASSIMO")
    print(" KAFKA ANALYTICS CONSUMER V2")
    print("===================================\n")

    # Las tablas deben existir antes de iniciar.
    # No modificamos el esquema automáticamente.
    with engine.connect() as conexion:
        from sqlalchemy import text
        conexion.execute(text(
            "SELECT 1 FROM kafka_estadisticas LIMIT 1"
        ))
        conexion.execute(text(
            "SELECT 1 FROM kafka_eventos_procesados LIMIT 1"
        ))

    logger.info(
        "Tablas de estadísticas verificadas"
    )

    consumer = Consumer(CONFIG)

    consumer.subscribe([
        TOPIC_EVENTS,
        TOPIC_BATTLES
    ])

    logger.info(
        "Grupo: %s",
        CONFIG["group.id"]
    )

    logger.info(
        "Escuchando: %s, %s",
        TOPIC_EVENTS,
        TOPIC_BATTLES
    )

    try:

        while True:

            mensaje = consumer.poll(1.0)

            if mensaje is None:
                continue

            if mensaje.error():
                raise RuntimeError(str(mensaje.error()))

            evento = json.loads(
                mensaje.value().decode("utf-8")
            )

            validar_evento(
                evento,
                mensaje.topic()
            )

            logger.info(
                "RECIBIDO | topic=%s | "
                "partition=%s | offset=%s",
                mensaje.topic(),
                mensaje.partition(),
                mensaje.offset()
            )

            estado = procesar_evento(
                mensaje.topic(),
                evento
            )

            # Confirmar solo después de
            # terminar el procesamiento.
            consumer.commit(
                message=mensaje,
                asynchronous=False
            )

            logger.info(
                "OFFSET CONFIRMADO | "
                "offset=%s | estado=%s",
                mensaje.offset(),
                estado
            )

    except KeyboardInterrupt:

        logger.info(
            "Consumidor detenido"
        )

    except Exception:

        logger.exception(
            "Error del consumidor. "
            "El último offset no fue confirmado."
        )
        raise

    finally:

        consumer.close()
        engine.dispose()

        logger.info(
            "Conexiones cerradas"
        )


if __name__ == "__main__":
    iniciar_consumidor()
