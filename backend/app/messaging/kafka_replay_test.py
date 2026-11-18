
from sqlalchemy import select, func

from app import models
from app.database import SessionLocal

from app.messaging.kafka_outbox import KafkaOutbox
from app.messaging.kafka_analytics import (
    EstadisticaKafka,
    EventoProcesadoKafka
)
from app.messaging.kafka_producer import publicar_evento


def obtener_estadisticas(db, jugador_id):

    estadistica = db.get(
        EstadisticaKafka,
        jugador_id
    )

    if estadistica is None:
        return None

    return {
        "victorias": estadistica.victorias,
        "derrotas": estadistica.derrotas,
        "ataques_jugador": estadistica.ataques_jugador,
        "ataques_enemigo": estadistica.ataques_enemigo,
        "dano_causado": estadistica.dano_causado,
        "dano_recibido": estadistica.dano_recibido
    }


def ejecutar_prueba():

    print("\n===================================")
    print(" POKEMON ROJO MASSIMO")
    print(" TEST DE IDEMPOTENCIA KAFKA")
    print("===================================\n")

    with SessionLocal() as db:

        consulta = (
            select(KafkaOutbox)
            .join(
                EventoProcesadoKafka,
                EventoProcesadoKafka.event_id
                == KafkaOutbox.id
            )
            .order_by(
                KafkaOutbox.created_at.desc()
            )
            .limit(1)
        )

        registro = db.scalar(consulta)

        if registro is None:

            print(
                "[ERROR] No hay eventos reales "
                "procesados para repetir."
            )

            return

        topic = registro.topic
        evento = registro.payload
        jugador_id = registro.player_id
        event_id = registro.id

        antes = obtener_estadisticas(
            db,
            jugador_id
        )

        total_antes = db.scalar(
            select(
                func.count(
                    EventoProcesadoKafka.event_id
                )
            )
        )

        print("[1] Evento seleccionado")
        print("Topic:", topic)
        print("Event ID:", event_id)
        print("Jugador:", jugador_id)

        print("\n[2] Estadísticas actuales:")
        print(antes)

        print(
            "\n[3] Total de eventos procesados:",
            total_antes
        )

        print(
            "\n[4] Republicando el MISMO evento..."
        )

        resultado = publicar_evento(
            topic,
            evento
        )

        print("\n[OK] Publicación confirmada")
        print("Partición:", resultado["partition"])
        print("Offset:", resultado["offset"])

        print("\n===================================")
        print(" EVENTO DUPLICADO ENVIADO")
        print("===================================\n")

        print(
            "Revisa la terminal del consumidor."
        )
        print(
            "Debe aparecer: DUPLICADO IGNORADO"
        )


if __name__ == "__main__":
    ejecutar_prueba()
