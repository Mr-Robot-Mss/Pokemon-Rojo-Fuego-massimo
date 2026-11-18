from pydantic import BaseModel, Field
from typing import Literal


class JugadorCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=50)
    pokemon_id: int


class CombateCrear(BaseModel):
    jugador_id: int
    pokemon_salvaje_id: int


class ResultadoCombate(BaseModel):
    combate_id: int
    jugador: str
    pokemon_jugador: str
    pokemon_salvaje: str
    ganador: Literal["jugador", "salvaje"]
    experiencia_ganada: int