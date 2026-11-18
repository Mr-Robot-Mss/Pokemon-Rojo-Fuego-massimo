import json
import time

import pika

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import Combate, Recompensa

from app.messaging.rabbitmq import (
    obtener_conexion,
    declarar_infraestructura,
    EXCHANGE,
    REWARD_QUEUE,
    REWARD_ROUTING_KEY
)


MAX_RETRIES = 2


def procesar_recompensa(mensaje):

    operation_id = mensaje["operation_id"]
    battle_id = int(mensaje["battle_id"])
    amount = int(mensaje["amount"])

    if amount != 5:
        raise ValueError(
            "Importe de recompensa no válido"
        )

    with SessionLocal() as db:

        recompensa_existente = db.scalar(
            select(Recompensa).where(
                Recompensa.operation_id == operation_id
            )
        )

        if recompensa_existente:
            print(
                f"[IDEMPOTENCIA] {operation_id} ya procesada"
            )
            return

        combate = db.get(Combate, battle_id)

        if combate is None:
            raise ValueError(
                f"Combate {battle_id} no existe"
            )

        if combate.ganador != "jugador":
            raise ValueError(
                "El combate no fue ganado"
            )

        recompensa = Recompensa(
            operation_id=operation_id,
            combate_id=combate.id,
            jugador_id=combate.jugador_id,
            monedas=amount
        )

        db.add(recompensa)

        try:
            db.commit()

        except IntegrityError:
            db.rollback()

            # Una restricción UNIQUE puede haber detectado
            # una recompensa creada por otro worker.
            existente = db.scalar(
                select(Recompensa).where(
                    Recompensa.combate_id == battle_id
                )
            )

            if existente:
                print(
                    f"[IDEMPOTENCIA] Combate {battle_id}"
                    " ya recompensado"
                )
                return

            raise

        print(
            f"[RECOMPENSA] Combate {battle_id}: "
            f"+{amount} monedas"
        )


def procesar_mensaje(
    channel,
    method,
    properties,
    body
):

    tag = method.delivery_tag

    try:
        mensaje = json.loads(body)

        if not isinstance(mensaje, dict):
            raise ValueError("El mensaje debe ser un objeto")

        retries = (
            properties.headers or {}
        ).get("retry_count", 0)

        retries = int(retries)

        print(
            f"[WORKER] Recibido: {mensaje}"
        )

        procesar_recompensa(mensaje)

        # Confirmamos solo después del commit
        channel.basic_ack(
            delivery_tag=tag
        )

        print("[ACK] Mensaje confirmado")

    except (ValueError, KeyError, TypeError) as error:

        # Datos inválidos: no conviene reintentarlos.
        print(f"[ERROR PERMANENTE] {error}")

        channel.basic_nack(
            delivery_tag=tag,
            requeue=False
        )

        print("[DLQ] Mensaje rechazado")

    except Exception as error:

        print(f"[ERROR] {error}")

        retries = int(
            (properties.headers or {}).get(
                "retry_count", 0
            )
        )

        if retries >= MAX_RETRIES:

            channel.basic_nack(
                delivery_tag=tag,
                requeue=False
            )

            print("[DLQ] Reintentos agotados")
            return

        # Enviar una nueva copia con el contador aumentado.
        # Primero confirmamos la nueva publicación y
        # después confirmamos el mensaje original.
        try:
            nuevos_headers = dict(
                properties.headers or {}
            )

            nuevos_headers["retry_count"] = retries + 1

            time.sleep(1)

            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=REWARD_ROUTING_KEY,
                body=body,
                mandatory=True,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                    message_id=properties.message_id,
                    headers=nuevos_headers
                )
            )

            channel.basic_ack(
                delivery_tag=tag
            )

            print(
                f"[REINTENTO] {retries + 1}/{MAX_RETRIES}"
            )

        except Exception:
            # No confirmamos la tarea original si
            # no pudimos publicar el reintento.
            # Al cerrarse la conexión, RabbitMQ podrá
            # volver a entregar el mensaje pendiente.
            raise


def main():

    while True:

        try:
            conexion = obtener_conexion()
            channel = conexion.channel()

            declarar_infraestructura(channel)

            # Confirmar las republicaciones
            channel.confirm_delivery()

            # Procesar un mensaje a la vez
            channel.basic_qos(
                prefetch_count=1
            )

            channel.basic_consume(
                queue=REWARD_QUEUE,
                on_message_callback=procesar_mensaje,
                auto_ack=False
            )

            print("[WORKER] Esperando recompensas...")

            channel.start_consuming()

        except KeyboardInterrupt:
            print("[WORKER] Detenido")
            break

        except Exception as error:
            print(
                f"[WORKER] Conexión interrumpida: {error}"
            )
            time.sleep(5)

        finally:
            if "conexion" in locals() and conexion.is_open:
                conexion.close()


if __name__ == "__main__":
    main()