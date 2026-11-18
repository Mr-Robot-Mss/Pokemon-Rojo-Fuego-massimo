
from fastapi import (
    APIRouter,
    HTTPException,
    Depends
)

from sqlalchemy import (
    select,
    func
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Jugador,
    POKEMONS
)

from app.schemas import JugadorCrear
from app.pokemon_progression import (nivel_desde_experiencia, experiencia_progreso, especie_evolucionada, pokemon_a_nivel)


# ==========================================
# CONFIGURACIÓN DEL ROUTER
# ==========================================

router = APIRouter(
    prefix="/players",
    tags=["Jugadores"]
)


# ==========================================
# FUNCIÓN: BUSCAR POKÉMON
# ==========================================

def buscar_pokemon(pokemon_id: int):

    return next(
        (
            pokemon
            for pokemon in POKEMONS
            if pokemon["id"] == pokemon_id
        ),
        None
    )


# ==========================================
# FUNCIÓN: FORMATEAR JUGADOR
# ==========================================

def serializar_jugador(jugador: Jugador):
    progreso = experiencia_progreso(jugador.experiencia)
    nivel = progreso['nivel']
    evolucion_id = especie_evolucionada(jugador.pokemon_id, nivel)
    pokemon = buscar_pokemon(evolucion_id)
    return {
        'id': jugador.id,
        'nombre': jugador.nombre,
        'pokemon_id': jugador.pokemon_id, # Siempre el inicial de la elección
        'pokemon_actual_id': evolucion_id,
        'pokemon': pokemon_a_nivel(pokemon, nivel) if pokemon else None,
        **progreso,
        'siguiente_evolucion_nivel': (10 if nivel<10 else 20 if nivel<20 else None),
    }


# ==========================================
# POST: CREAR JUGADOR
# ==========================================

@router.post("/", status_code=201)
def crear_jugador(
    datos: JugadorCrear,
    db: Session = Depends(get_db)
):

    # --------------------------------------
    # VALIDAR NOMBRE
    # --------------------------------------

    nombre = " ".join(
        datos.nombre.split()
    )

    if len(nombre) < 2:

        raise HTTPException(
            status_code=400,
            detail=(
                "El nombre del entrenador debe "
                "tener al menos 2 caracteres."
            )
        )

    if len(nombre) > 50:

        raise HTTPException(
            status_code=400,
            detail=(
                "El nombre del entrenador no puede "
                "superar los 50 caracteres."
            )
        )

    # --------------------------------------
    # VALIDAR POKÉMON INICIAL
    # --------------------------------------

    pokemon = buscar_pokemon(
        datos.pokemon_id
    )

    if pokemon is None or datos.pokemon_id not in (1, 2, 3):

        raise HTTPException(
            status_code=422,
            detail="Solo puedes elegir Charmander, Squirtle o Bulbasaur como inicial."
        )

    # --------------------------------------
    # VERIFICAR NOMBRE DUPLICADO
    # --------------------------------------

    jugador_existente = db.scalar(
        select(Jugador).where(
            func.lower(
                func.trim(Jugador.nombre)
            ) == nombre.lower()
        )
    )

    if jugador_existente is not None:

        raise HTTPException(
            status_code=409,
            detail=(
                f"El nombre '{nombre}' ya está "
                "registrado. Elige otro nombre "
                "para tu entrenador."
            )
        )

    # --------------------------------------
    # CREAR ENTRENADOR
    # --------------------------------------

    nuevo_jugador = Jugador(
        nombre=nombre,
        pokemon_id=datos.pokemon_id,
        experiencia=0
    )

    # --------------------------------------
    # GUARDAR EN POSTGRESQL
    # --------------------------------------

    try:

        db.add(nuevo_jugador)

        db.commit()

        db.refresh(nuevo_jugador)

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                f"El nombre '{nombre}' ya está "
                "en uso. Por favor, selecciona "
                "otro nombre."
            )
        )

    # --------------------------------------
    # RESPUESTA
    # --------------------------------------

    return serializar_jugador(
        nuevo_jugador
    )


# ==========================================
# GET: LISTAR JUGADORES
# ==========================================

@router.get("/")
def listar_jugadores(
    db: Session = Depends(get_db)
):

    jugadores = db.scalars(
        select(Jugador)
        .order_by(Jugador.id)
    ).all()

    return [
        serializar_jugador(jugador)
        for jugador in jugadores
    ]


# ==========================================
# GET: OBTENER JUGADOR POR ID
# ==========================================

@router.get("/{jugador_id}")
def obtener_jugador(
    jugador_id: int,
    db: Session = Depends(get_db)
):

    jugador = db.get(
        Jugador,
        jugador_id
    )

    if jugador is None:

        raise HTTPException(
            status_code=404,
            detail="Entrenador no encontrado."
        )

    return serializar_jugador(
        jugador
    )
