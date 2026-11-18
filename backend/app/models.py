
from datetime import datetime, timezone

from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text
)

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ==================================================
# CATÁLOGO DE POKÉMON
# ==================================================

POKEMONS = [{'id': 1,
  'nombre': 'Charmander',
  'tipo': 'Fuego',
  'tipos': ['Fuego'],
  'vida': 39,
  'ataque': 52,
  'seleccionable': True,
  'rival': False},
 {'id': 2,
  'nombre': 'Squirtle',
  'tipo': 'Agua',
  'tipos': ['Agua'],
  'vida': 44,
  'ataque': 48,
  'seleccionable': True,
  'rival': False},
 {'id': 3,
  'nombre': 'Bulbasaur',
  'tipo': 'Planta',
  'tipos': ['Planta', 'Veneno'],
  'vida': 45,
  'ataque': 49,
  'seleccionable': True,
  'rival': False},
 {'id': 4,
  'nombre': 'Pikachu',
  'tipo': 'Eléctrico',
  'tipos': ['Eléctrico'],
  'vida': 35,
  'ataque': 55,
  'seleccionable': False,
  'rival': True},
 {'id': 5,
  'nombre': 'Snorlax',
  'tipo': 'Normal',
  'tipos': ['Normal'],
  'vida': 160,
  'ataque': 110,
  'seleccionable': False,
  'rival': True},
 {'id': 6,
  'nombre': 'Gengar',
  'tipo': 'Fantasma',
  'tipos': ['Fantasma', 'Veneno'],
  'vida': 60,
  'ataque': 65,
  'seleccionable': False,
  'rival': True},
 {'id': 7,
  'nombre': 'Dragonite',
  'tipo': 'Dragón',
  'tipos': ['Dragón', 'Volador'],
  'vida': 91,
  'ataque': 134,
  'seleccionable': False,
  'rival': True},
 {'id': 8,
  'nombre': 'Gyarados',
  'tipo': 'Agua',
  'tipos': ['Agua', 'Volador'],
  'vida': 95,
  'ataque': 125,
  'seleccionable': False,
  'rival': True},
 {'id': 9,
  'nombre': 'Alakazam',
  'tipo': 'Psíquico',
  'tipos': ['Psíquico'],
  'vida': 55,
  'ataque': 50,
  'seleccionable': False,
  'rival': True},
 {'id': 10,
  'nombre': 'Arcanine',
  'tipo': 'Fuego',
  'tipos': ['Fuego'],
  'vida': 90,
  'ataque': 110,
  'seleccionable': False,
  'rival': True},
 {'id': 11,
  'nombre': 'Machamp',
  'tipo': 'Lucha',
  'tipos': ['Lucha'],
  'vida': 90,
  'ataque': 130,
  'seleccionable': False,
  'rival': True},
 {'id': 12,
  'nombre': 'Lapras',
  'tipo': 'Agua',
  'tipos': ['Agua', 'Hielo'],
  'vida': 130,
  'ataque': 85,
  'seleccionable': False,
  'rival': True},
 {'id': 13,
  'nombre': 'Mewtwo',
  'tipo': 'Psíquico',
  'tipos': ['Psíquico'],
  'vida': 106,
  'ataque': 110,
  'seleccionable': False,
  'rival': True}]

# Evoluciones elegibles solo por progreso, nunca al crear entrenador.
POKEMONS.extend([
    dict(id=14,nombre='Charmeleon',tipo='Fuego',tipos=['Fuego'],vida=58,ataque=64,seleccionable=False,rival=False),
    dict(id=15,nombre='Charizard',tipo='Fuego',tipos=['Fuego','Volador'],vida=78,ataque=84,seleccionable=False,rival=False),
    dict(id=16,nombre='Ivysaur',tipo='Planta',tipos=['Planta','Veneno'],vida=60,ataque=62,seleccionable=False,rival=False),
    dict(id=17,nombre='Venusaur',tipo='Planta',tipos=['Planta','Veneno'],vida=80,ataque=82,seleccionable=False,rival=False),
    dict(id=18,nombre='Wartortle',tipo='Agua',tipos=['Agua'],vida=59,ataque=63,seleccionable=False,rival=False),
    dict(id=19,nombre='Blastoise',tipo='Agua',tipos=['Agua'],vida=79,ataque=83,seleccionable=False,rival=False),
])
from app.pokemon_progression import pokemon_a_nivel
# Catálogo de especies: stats BASE (no PS escalados), apropiado para Pokédex.
for _pokemon in POKEMONS:
    from app.pokemon_progression import BASE, ESTADISTICAS
    _pokemon['estadisticas_base']=dict(zip(ESTADISTICAS, BASE[_pokemon['id']][:6]))
    _pokemon['experiencia_base']=BASE[_pokemon['id']][6]


# ==================================================
# MODELO: JUGADORES
# ==================================================

class Jugador(Base):

    __tablename__ = "jugadores"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nombre: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    pokemon_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    experiencia: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )


# ==================================================
# MODELO: COMBATES
# ==================================================

class Combate(Base):

    __tablename__ = "combates"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    jugador_id: Mapped[int] = mapped_column(
        ForeignKey("jugadores.id"),
        nullable=False
    )

    pokemon_salvaje_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    ganador: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    experiencia_ganada: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# ==================================================
# MODELO: RECOMPENSAS RABBITMQ
# ==================================================

class Recompensa(Base):

    __tablename__ = "recompensas"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    operation_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    combate_id: Mapped[int] = mapped_column(
        ForeignKey("combates.id"),
        unique=True,
        nullable=False
    )

    jugador_id: Mapped[int] = mapped_column(
        ForeignKey("jugadores.id"),
        nullable=False
    )

    monedas: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )


# ==========================================
# MODELO: COMBATES POR TURNOS
# ==========================================

class CombateTurno(Base):

    __tablename__ = "combates_turnos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    jugador_id: Mapped[int] = mapped_column(
        ForeignKey("jugadores.id"),
        nullable=False
    )

    pokemon_jugador_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    pokemon_salvaje_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    ps_jugador: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    ps_enemigo: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    turno: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    estado: Mapped[str] = mapped_column(
        String(20),
        default="activo",
        nullable=False
    )

    ultimo_mensaje: Mapped[str] = mapped_column(
        Text,
        default="¡Comienza el combate!",
        nullable=False
    )

    resultado_id: Mapped[int | None] = mapped_column(
        ForeignKey("combates.id"),
        nullable=True,
        unique=True
    )


# Estado persistente de cada combate, aislado para no modificar tablas existentes.
from sqlalchemy import JSON

class EstadoCombate(Base):
    __tablename__ = "combates_efectos"
    combate_id: Mapped[int] = mapped_column(ForeignKey("combates_turnos.id"), primary_key=True)
    datos: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
