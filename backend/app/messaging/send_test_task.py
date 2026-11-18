import sys

from app.messaging.rabbitmq import (
    obtener_conexion,
    declarar_infraestructura,
    EXCHANGE,
    REWARD_ROUTING_KEY
)

import json
import pika


def enviar_mensaje(mensaje):

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
                delivery_mode=2,
                content_type="application/json",
                message_id=mensaje.get("operation_id", "test"),
                headers={"retry_count": 0}
            )
        )

        print("Mensaje enviado:", mensaje)

    finally:
        if conexion.is_open:
            conexion.close()


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            "Uso: python -m "
            "app.messaging.send_test_task "
            "duplicado|invalido"
        )
        sys.exit(1)

    tipo = sys.argv[1]

    if tipo == "invalido":

        # El combate no existe.
        enviar_mensaje({
            "operation_id": "test-invalido",
            "battle_id": -999,
            "task_type": "battle_reward",
            "amount": 5
        })

    elif tipo == "duplicado":

        if len(sys.argv) < 3:
            print(
                "Indica el ID de un combate ganado"
            )
            sys.exit(1)

        battle_id = int(sys.argv[2])

        # Usa el mismo operation_id que la API.
        mensaje = {
            "operation_id": f"reward-battle-{battle_id}",
            "battle_id": battle_id,
            "task_type": "battle_reward",
            "amount": 5
        }

        enviar_mensaje(mensaje)
        enviar_mensaje(mensaje)

    else:
        print("Tipo de prueba no reconocido")