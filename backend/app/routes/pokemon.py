from fastapi import APIRouter, HTTPException
from app.models import POKEMONS

router = APIRouter(
    prefix="/pokemon",
    tags=["Pokemon"]
)


@router.get("/")
def listar_pokemon():
    return POKEMONS


@router.get("/{pokemon_id}")
def obtener_pokemon(pokemon_id: int):

    for pokemon in POKEMONS:
        if pokemon["id"] == pokemon_id:
            return pokemon

    raise HTTPException(
        status_code=404,
        detail="Pokemon no encontrado"
    )