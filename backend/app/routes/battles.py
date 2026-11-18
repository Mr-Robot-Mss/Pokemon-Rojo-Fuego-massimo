
import random

from fastapi import (
    APIRouter,
    HTTPException,
    Depends
)

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Jugador,
    Combate,
    POKEMONS
)

from app.schemas import (
    CombateCrear,
    ResultadoCombate
)

from app.messaging.rabbitmq import publicar_recompensa


# ==================================================
# CONFIGURACIÓN DEL ROUTER
# ==================================================

router = APIRouter(
    prefix="/battles",
    tags=["Combates"]
)


# ==================================================
# FUNCIÓN AUXILIAR: BUSCAR POKÉMON
# ==================================================

def buscar_pokemon(pokemon_id: int):

    return next(
        (
            pokemon
            for pokemon in POKEMONS
            if pokemon["id"] == pokemon_id
        ),
        None
    )


# ==================================================
# POST: CREAR COMBATE
# ==================================================

@router.post(
    "/",
    response_model=ResultadoCombate,
    status_code=201
)
def crear_combate(
    datos: CombateCrear,
    db: Session = Depends(get_db)
):

    # ----------------------------------------------
    # 1. BUSCAR JUGADOR EN POSTGRESQL
    # ----------------------------------------------

    jugador = db.get(
        Jugador,
        datos.jugador_id
    )

    if jugador is None:
        raise HTTPException(
            status_code=404,
            detail="Jugador no encontrado"
        )

    # ----------------------------------------------
    # 2. OBTENER POKÉMON DEL JUGADOR
    # ----------------------------------------------

    pokemon_jugador = buscar_pokemon(
        jugador.pokemon_id
    )

    if pokemon_jugador is None:
        raise HTTPException(
            status_code=404,
            detail="Pokemon del jugador no encontrado"
        )

    # ----------------------------------------------
    # 3. OBTENER POKÉMON SALVAJE
    # ----------------------------------------------

    pokemon_salvaje = buscar_pokemon(
        datos.pokemon_salvaje_id
    )

    if pokemon_salvaje is None:
        raise HTTPException(
            status_code=404,
            detail="Pokemon salvaje no encontrado"
        )

    # ----------------------------------------------
    # 4. CALCULAR PODER DE COMBATE
    # ----------------------------------------------

    poder_jugador = (
        pokemon_jugador["ataque"]
        + random.randint(1, 20)
    )

    poder_salvaje = (
        pokemon_salvaje["ataque"]
        + random.randint(1, 20)
    )

    # ----------------------------------------------
    # 5. DETERMINAR GANADOR
    # ----------------------------------------------

    if poder_jugador >= poder_salvaje:

        ganador = "jugador"
        experiencia = 10

    else:

        ganador = "salvaje"
        experiencia = 0

    # ----------------------------------------------
    # 6. CREAR REGISTRO DE COMBATE
    # ----------------------------------------------

    combate = Combate(
        jugador_id=jugador.id,
        pokemon_salvaje_id=pokemon_salvaje["id"],
        ganador=ganador,
        experiencia_ganada=experiencia
    )

    # ----------------------------------------------
    # 7. GUARDAR COMBATE Y EXPERIENCIA
    # ----------------------------------------------

    try:

        db.add(combate)

        # Incrementar experiencia del jugador
        db.execute(
            update(Jugador)
            .where(Jugador.id == jugador.id)
            .values(
                experiencia=Jugador.experiencia
                + experiencia
            )
        )

        # Guardar ambas operaciones juntas
        db.commit()

        # Recuperar ID generado por PostgreSQL
        db.refresh(combate)

    except Exception:

        db.rollback()
        raise

    # ----------------------------------------------
    # 8. PUBLICAR RECOMPENSA EN RABBITMQ
    # ----------------------------------------------

    estado_recompensa = "no_aplica"

    if ganador == "jugador":

        operation_id = f"reward-battle-{combate.id}"

        try:

            publicar_recompensa(
                battle_id=combate.id,
                operation_id=operation_id
            )

            estado_recompensa = "publicada"

            print(
                f"[RABBITMQ] Recompensa publicada "
                f"para combate {combate.id}"
            )

        except Exception as error:

            estado_recompensa = "publicacion_fallida"

            print(
                f"[RABBITMQ] Error publicando "
                f"recompensa: {error}"
            )

    # ----------------------------------------------
    # 9. DEVOLVER RESULTADO DEL COMBATE
    # ----------------------------------------------

    resultado = {
        "combate_id": combate.id,
        "jugador": jugador.nombre,
        "pokemon_jugador": pokemon_jugador["nombre"],
        "pokemon_salvaje": pokemon_salvaje["nombre"],
        "ganador": ganador,
        "experiencia_ganada": experiencia,
        "estado_recompensa": estado_recompensa
    }

    return resultado


# ==================================================
# GET: LISTAR COMBATES
# ==================================================

@router.get("/")
def listar_combates(
    db: Session = Depends(get_db)
):

    # Consultar combates desde PostgreSQL
    combates = db.scalars(
        select(Combate)
        .order_by(Combate.id)
    ).all()

    resultados = []

    for combate in combates:

        # Buscar jugador relacionado
        jugador = db.get(
            Jugador,
            combate.jugador_id
        )

        pokemon_jugador = buscar_pokemon(
            jugador.pokemon_id
        )

        pokemon_salvaje = buscar_pokemon(
            combate.pokemon_salvaje_id
        )

        resultado = {
            "combate_id": combate.id,
            "jugador": jugador.nombre,
            "pokemon_jugador": pokemon_jugador["nombre"],
            "pokemon_salvaje": pokemon_salvaje["nombre"],
            "ganador": combate.ganador,
            "experiencia_ganada": combate.experiencia_ganada
        }

        resultados.append(resultado)

    return resultados
