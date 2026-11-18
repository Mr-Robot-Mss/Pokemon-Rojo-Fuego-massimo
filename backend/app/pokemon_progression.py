"""Progresión Pokémon de Massimo: stats base de Gen III, nivel propio 5/10/20.

XP y niveles por entrenador persistidos en Jugador.experiencia (XP ganada desde nivel 5).
El identificador del inicial nunca cambia; especie evolucionada se calcula en cada consulta.
Esto evita migraciones destructivas y conserva entrenadores existentes.
"""
from __future__ import annotations
from math import floor

# HP, Ataque, Defensa, At. Especial, Def. Especial, Velocidad, XP base al derrotarlo.
# Formato Gen III; experiencia de combate de acuerdo al nivel del rival.
BASE = {
    1:(39,52,43,60,50,65,65),   # Charmander
    14:(58,64,58,80,65,80,142), # Charmeleon
    15:(78,84,78,109,85,100,209), # Charizard
    2:(44,48,65,50,64,43,66),  # Squirtle
    18:(59,63,80,65,80,58,143),# Wartortle
    19:(79,83,100,85,105,78,210),# Blastoise
    3:(45,49,49,65,65,45,64),  # Bulbasaur
    16:(60,62,63,80,80,60,141), # Ivysaur
    17:(80,82,83,100,100,80,208), # Venusaur
    4:(35,55,40,50,50,90,82), # Pikachu
    5:(160,110,65,65,110,30,154), # Snorlax
    6:(60,65,60,130,75,110,190), # Gengar
    7:(91,134,95,100,100,80,218), # Dragonite
    8:(95,125,79,60,100,81,214), # Gyarados
    9:(55,50,45,135,95,120,186), # Alakazam
    10:(90,110,80,100,80,95,213), # Arcanine
    11:(90,130,80,65,85,55,193), # Machamp
    12:(130,85,80,85,95,60,219), # Lapras
    13:(106,110,90,154,90,130,220), # Mewtwo
}
ESTADISTICAS = ('ps','ataque','defensa','ataque_especial','defensa_especial','velocidad')
# Tu progresión personalizada: 5 inicial / 10 segunda / 20 final.
EVOLUCIONES = {
    1: ((5,1),(10,14),(20,15)),
    2: ((5,2),(10,18),(20,19)),
    3: ((5,3),(10,16),(20,17)),
}

def experiencia_total_para_nivel(nivel:int)->int:
    """Curva Medium Slow, sin EVs: 6/5*n³ - 15*n² + 100*n - 140."""
    n=max(1,min(100,int(nivel)))
    return max(0, floor(6*n*n*n/5 -15*n*n+100*n-140))

EXPERIENCIA_INICIAL=experiencia_total_para_nivel(5)

def nivel_desde_experiencia(experiencia:int)->int:
    xp=EXPERIENCIA_INICIAL + max(0,int(experiencia or 0))
    nivel=5
    while nivel<100 and experiencia_total_para_nivel(nivel+1)<=xp:
        nivel+=1
    return nivel

def experiencia_progreso(experiencia:int)->dict:
    n=nivel_desde_experiencia(experiencia)
    total=EXPERIENCIA_INICIAL+max(0,int(experiencia or 0))
    piso=experiencia_total_para_nivel(n)
    techo=experiencia_total_para_nivel(min(100,n+1))
    return {'nivel':n,'experiencia':int(experiencia or 0),
            'xp_nivel':max(0,total-piso),'xp_siguiente_nivel':max(0,techo-piso),
            'xp_restante':max(0,techo-total)}

def especie_evolucionada(inicial_id:int,nivel:int)->int:
    stages=EVOLUCIONES.get(inicial_id)
    if stages is None:return inicial_id
    result=inicial_id
    for minimo, ident in stages:
        if nivel>=minimo:result=ident
    return result

def estadisticas_a_nivel(ident:int,nivel:int)->dict:
    """Fórmula clásica HP y stats con IV=15, naturaleza neutra y EV=0.
    Las stats base son los valores reales de especie; las de combate están escaladas.
    """
    l=max(1,min(100,int(nivel)))
    valores=BASE[ident]; iv=15
    hp=floor((2*valores[0]+iv)*l/100)+l+10
    otros=[floor((2*base+iv)*l/100)+5 for base in valores[1:6]]
    return dict(zip(ESTADISTICAS, (hp,*otros)))

def pokemon_a_nivel(catalogo:dict,nivel:int)->dict:
    clone=dict(catalogo)
    est=estadisticas_a_nivel(catalogo['id'],nivel)
    clone.update({'nivel':int(nivel),'vida':est['ps'],
                  'ataque':est['ataque'],'estadisticas':est,
                  'estadisticas_base':dict(zip(ESTADISTICAS,BASE[catalogo['id']][:6])),
                  'experiencia_base':BASE[catalogo['id']][6]})
    return clone

def experiencia_ganada(pokemon_rival:dict,nivel_rival:int)->int:
    """XP de Pokémon salvaje: base_exp * nivel / 7 (Gen III, sin bonus entrenador)."""
    return max(1,floor(BASE[pokemon_rival['id']][6]*max(1,nivel_rival)/7))
