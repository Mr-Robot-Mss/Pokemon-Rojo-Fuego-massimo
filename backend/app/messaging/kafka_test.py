
from app.messaging.kafka_producer import (
    publicar_combate_terminado,
    publicar_ataque
)


def ejecutar_prueba():

    print("\n===================================")
    print(" POKEMON ROJO MASSIMO - TEST KAFKA")
    print("===================================")

    print("\n[1] Publicando ataque...")

    ataque = publicar_ataque(
        player_id=1,
        battle_id=100,
        turn=1,
        pokemon="Charmander",
        movement="Ascuas",
        damage=18,
        remaining_hp=27
    )

    print(
        "[OK] Evento publicado:",
        ataque["event_id"]
    )

    print("\n[2] Publicando combate...")

    combate = publicar_combate_terminado(
        player_id=1,
        battle_id=100,
        winner="jugador",
        experience_gained=10,
        pokemon_player="Charmander",
        pokemon_enemy="Bulbasaur"
    )

    print(
        "[OK] Evento publicado:",
        combate["event_id"]
    )

    print("\n===================================")
    print(" PRUEBA DE PUBLICACIÓN COMPLETADA")
    print("===================================\n")


if __name__ == "__main__":

    ejecutar_prueba()
