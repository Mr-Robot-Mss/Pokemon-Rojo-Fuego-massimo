"""Dificultad progresiva del modo historia de Pokémon Rojo Massimo.

Solo ajusta encuentros SALVAJES. Conserva las estadísticas base reales,
los tipos, movimientos, estados, EXP y el orden jugador -> enemigo.
El objetivo es evitar KO de un golpe a los iniciales de nivel bajo.
"""
import random
from math import floor


def nivel_rival(nivel_jugador: int) -> int:
    """Los salvajes empiezan ligeramente por debajo del entrenador."""
    nivel = max(5, min(100, int(nivel_jugador)))
    if nivel < 10:
        diferencia = random.choice((1, 2, 2, 3))
    elif nivel < 20:
        diferencia = random.choice((0, 1, 2, 2))
    else:
        diferencia = random.choice((-1, 0, 1, 2))
    return max(3, min(100, nivel - diferencia))


def vida_rival(vida_original: int, nivel_jugador: int) -> int:
    """Ajusta SOLO los PS del encuentro, no las estadísticas de la Pokédex."""
    nivel = int(nivel_jugador)
    factor = 0.78 if nivel < 10 else (0.88 if nivel < 20 else 1.0)
    return max(1, min(int(vida_original), round(vida_original * factor)))


def dano_rival(dano_original: int, ps_max_jugador: int, nivel_jugador: int) -> int:
    """Suaviza la IA y evita OHKO incluso cuando un ataque es supereficaz.

    El tipo se calcula ANTES en battle_effects.daño. Así Avalancha
    sigue mostrando «Es súper eficaz» contra Charmander, pero ya no
    lo derrota de un golpe al principio. Solo se aplica al enemigo.
    """
    dano = max(0, int(dano_original))
    if dano == 0:
        return 0
    nivel = int(nivel_jugador)
    factor = 0.65 if nivel < 10 else (0.80 if nivel < 20 else 0.95)
    proporcion_max = 0.30 if nivel < 10 else (0.40 if nivel < 20 else 0.55)
    limite = max(1, floor(int(ps_max_jugador) * proporcion_max))
    return min(limite, max(1, round(dano * factor)))
