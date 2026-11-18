
import logging
import time

from datetime import datetime, timezone

from sqlalchemy import select

from app.database import SessionLocal, Base

# IMPORTANTE:
# Registrar todos los modelos antes de utilizar
# KafkaOutbox, incluyendo la tabla jugadores.
from app import models

from app.messaging.kafka_outbox import KafkaOutbox

from app.messaging.kafka_producer import publicar_evento


# ==========================================
# CONFIGURACIÓN DE LOGS
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
)

logger = logging.getLogger(
    "pokemon.kafka.outbox"
)


# ==========================================
# CONFIGURACIÓN DEL WORKER
# ==========================================

INTERVALO_SEGUNDOS = 2
TAMANO_LOTE = 20


# ==========================================
# VERIFICAR MODELOS SQLALCHEMY
# ==========================================

def verificar_modelos():

    tablas = Base.metadata.tables

    requeridas = [
        "jugadores",
        "combates",
        "combates_turnos",
        "recompensas",
        "kafka_outbox"
    ]

    for nombre in requeridas:

        if nombre not in tablas:

            raise RuntimeError(
                f"Modelo no registrado: {nombre}"
            )

    logger.info(
        "Modelos SQLAlchemy registrados correctamente"
    )


# ==========================================
# PROCESAR UN EVENTO
# ==========================================

def procesar_evento():

    with SessionLocal() as db:

        registro_id = None

        try:

            # Seleccionar un evento pendiente.
            # SKIP LOCKED evita que dos workers
            # procesen la misma fila a la vez.
            registro = db.scalar(
                select(KafkaOutbox)
                .where(KafkaOutbox.status == "pending")
                .order_by(
                    KafkaOutbox.created_at,
                    KafkaOutbox.id
                )
                .limit(1)
                .with_for_update(skip_locked=True)
            )

            if registro is None:

                db.rollback()

                return None

            # Guardar datos antes del commit
            # para evitar acceder a objetos
            # expirados tras un error.
            registro_id = registro.id
            topic = registro.topic
            payload = registro.payload

            logger.info(
                "Publicando %s | evento=%s",
                topic,
                registro_id
            )

            # Publicar y esperar confirmación Kafka.
            resultado = publicar_evento(
                topic,
                payload
            )

            # Marcar como enviado solamente si
            # Kafka confirmó correctamente.
            registro.status = "sent"

            registro.sent_at = datetime.now(
                timezone.utc
            )

            registro.partition = resultado[
                "partition"
            ]

            registro.offset = resultado[
                "offset"
            ]

            registro.last_error = None

            registro.attempts += 1

            # Confirmar en PostgreSQL.
            db.commit()

            logger.info(
                "EVENTO PUBLICADO | "
                "topic=%s | "
                "partition=%s | "
                "offset=%s | "
                "event_id=%s",
                topic,
                resultado["partition"],
                resultado["offset"],
                registro_id
            )

            return True

        except Exception as error:

            # PRIMERO recuperar la transacción.
            db.rollback()

            logger.error(
                "Error procesando evento %s: %s",
                registro_id,
                error
            )

            # Registrar el intento fallido.
            if registro_id is not None:

                try:

                    registro_error = db.get(
                        KafkaOutbox,
                        registro_id
                    )

                    if (
                        registro_error is not None
                        and registro_error.status == "pending"
                    ):

                        registro_error.attempts += 1

                        registro_error.last_error = str(
                            error
                        )[:4000]

                        db.commit()

                except Exception:

                    db.rollback()

                    logger.exception(
                        "No fue posible guardar "
                        "el error del evento"
                    )

            return False


# ==========================================
# PROCESAR LOTE DE EVENTOS
# ==========================================

def procesar_pendientes():

    enviados = 0

    for _ in range(TAMANO_LOTE):

        resultado = procesar_evento()

        # No hay eventos pendientes.
        if resultado is None:
            break

        # Si hubo un error, detenemos el lote.
        # Se reintentará en otro ciclo.
        if resultado is False:
            break

        enviados += 1

    return enviados


# ==========================================
# INICIAR WORKER
# ==========================================

def iniciar_worker():

    print("\n===================================")
    print(" POKEMON ROJO MASSIMO")
    print(" KAFKA OUTBOX WORKER V2")
    print("===================================\n")

    verificar_modelos()

    logger.info(
        "Worker Kafka iniciado correctamente"
    )

    logger.info(
        "Buscando eventos pendientes..."
    )

    try:

        while True:

            try:

                enviados = procesar_pendientes()

                if enviados > 0:

                    logger.info(
                        "Eventos enviados en este ciclo: %s",
                        enviados
                    )

            except Exception:

                logger.exception(
                    "Error durante el ciclo del worker"
                )

            time.sleep(
                INTERVALO_SEGUNDOS
            )

    except KeyboardInterrupt:

        logger.info(
            "Worker detenido manualmente"
        )

    finally:

        logger.info(
            "Kafka Outbox Worker finalizado"
        )


# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":

    iniciar_worker()
