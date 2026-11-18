"""Reglas de combates y movimientos. Los tiempos de animación pertenecen a Angular.

Tabla de tipos: Gen III. Los conjuntos de cuatro movimientos son personalizados
según lo solicitado; algunos movimientos originales tienen más mecánicas de las
que este RPG simplificado soporta (no clima, objetos, captura ni PP).
"""
import random
from math import floor

# nombre / potencia Gen III aproximada / tipo / efecto / precisión
MOVES = {
 1: [('Arañazo',40,'Normal'),('Ascuas',40,'Fuego','quemar_ocasional'),('Gruñido',0,'Normal','bajar_ataque'),('Pantalla de Humo',0,'Normal','bajar_precision')],
 14:[('Arañazo',40,'Normal'),('Lanzallamas',95,'Fuego','quemar_ocasional'),('Garra Dragón',80,'Dragón'),('Furia',20,'Normal','furia')],
 15:[('Lanzallamas',95,'Fuego','quemar_ocasional'),('Vuelo',70,'Volador','vuelo',0.95),('Garra Dragón',80,'Dragón'),('Movimiento Sísmico',1,'Lucha','mov_sismico')],
 3: [('Placaje',35,'Normal'),('Latigazo',35,'Planta'),('Drenadoras',0,'Planta','drenadoras',0.9),('Somnífero',0,'Planta','dormir',0.75)],
 16:[('Placaje',35,'Normal'),('Hojas Navaja',55,'Planta','critico_alto',0.95),('Polvo Veneno',0,'Veneno','envenenar',0.75),('Síntesis',0,'Planta','recuperar')],
 17:[('Rayo Solar',120,'Planta','rayo_solar'),('Bomba Lodo',90,'Veneno','envenenar_ocasional'),('Somnífero',0,'Planta','dormir',0.75),('Síntesis',0,'Planta','recuperar')],
 2: [('Placaje',35,'Normal'),('Pistola Agua',40,'Agua'),('Refugio',0,'Agua','subir_defensa'),('Látigo',0,'Normal','bajar_defensa')],
 18:[('Pistola Agua',40,'Agua'),('Giro Rápido',20,'Normal','giro_rapido'),('Mordisco',60,'Siniestro','retroceso_ocasional'),('Protección',0,'Normal','proteccion')],
 19:[('Hidrobomba',120,'Agua','',0.8),('Surf',95,'Agua'),('Rayo Hielo',95,'Hielo','congelar_ocasional'),('Giro Rápido',20,'Normal','giro_rapido')],
 4: [('Rayo',95,'Eléctrico','paralizar_ocasional'),('Trueno',120,'Eléctrico','paralizar_ocasional',0.7),('Ataque Rápido',40,'Normal'),('Onda Trueno',0,'Eléctrico','paralizar')],
 5: [('Golpe Cuerpo',85,'Normal','paralizar_ocasional'),('Terremoto',100,'Tierra'),('Descanso',0,'Psíquico','descanso'),('Ronquido',40,'Normal','ronquido')],
 6: [('Bola Sombra',80,'Fantasma'),('Bomba Lodo',90,'Veneno','envenenar_ocasional'),('Rayo',95,'Eléctrico','paralizar_ocasional'),('Hipnosis',0,'Psíquico','dormir',0.6)],
 7: [('Garra Dragón',80,'Dragón'),('Rayo Hielo',95,'Hielo','congelar_ocasional'),('Terremoto',100,'Tierra'),('Velocidad Extrema',80,'Normal')],
 8: [('Cascada',80,'Agua'),('Terremoto',100,'Tierra'),('Triturar',80,'Siniestro'),('Danza Dragón',0,'Dragón','danza_dragon')],
 9: [('Psíquico',90,'Psíquico'),('Bola Sombra',80,'Fantasma'),('Rayo',95,'Eléctrico','paralizar_ocasional'),('Recuperación',0,'Normal','recuperar')],
 10:[('Lanzallamas',95,'Fuego','quemar_ocasional'),('Velocidad Extrema',80,'Normal'),('Triturar',80,'Siniestro'),('Pulso Dragón',90,'Dragón')],
 11:[('Demolición',75,'Lucha'),('Avalancha',75,'Roca'),('Terremoto',100,'Tierra'),('Corpulencia',0,'Lucha','corpulencia')],
 12:[('Surf',95,'Agua'),('Rayo Hielo',95,'Hielo','congelar_ocasional'),('Rayo',95,'Eléctrico','paralizar_ocasional'),('Rayo Confuso',0,'Fantasma','confundir')],
 13:[('Psíquico',90,'Psíquico'),('Rayo',95,'Eléctrico','paralizar_ocasional'),('Lanzallamas',95,'Fuego','quemar_ocasional'),('Recuperación',0,'Normal','recuperar')],
}

def movimientos(pokemon_id):
    return [dict(nombre=x[0],potencia=x[1],tipo=x[2],efecto=x[3] if len(x)>3 else '',
                 precision=x[4] if len(x)>4 else 1.0) for x in MOVES.get(pokemon_id,[])]

TYPE_CHART = {
 'Normal': {'Roca':.5,'Acero':.5,'Fantasma':0},
 'Fuego': {'Planta':2,'Hielo':2,'Bicho':2,'Acero':2,'Agua':.5,'Roca':.5,'Fuego':.5,'Dragón':.5},
 'Agua': {'Fuego':2,'Tierra':2,'Roca':2,'Agua':.5,'Planta':.5,'Dragón':.5},
 'Planta': {'Agua':2,'Tierra':2,'Roca':2,'Fuego':.5,'Planta':.5,'Veneno':.5,'Volador':.5,'Bicho':.5,'Dragón':.5,'Acero':.5},
 'Eléctrico': {'Agua':2,'Volador':2,'Planta':.5,'Eléctrico':.5,'Dragón':.5,'Tierra':0},
 'Hielo': {'Planta':2,'Tierra':2,'Volador':2,'Dragón':2,'Agua':.5,'Hielo':.5,'Fuego':.5,'Acero':.5},
 'Lucha': {'Normal':2,'Hielo':2,'Roca':2,'Siniestro':2,'Acero':2,'Veneno':.5,'Volador':.5,'Psíquico':.5,'Bicho':.5,'Fantasma':0},
 'Veneno': {'Planta':2,'Bicho':2,'Veneno':.5,'Tierra':.5,'Roca':.5,'Fantasma':.5,'Acero':0},
 'Tierra': {'Fuego':2,'Eléctrico':2,'Veneno':2,'Roca':2,'Acero':2,'Planta':.5,'Bicho':.5,'Volador':0},
 'Volador': {'Planta':2,'Lucha':2,'Bicho':2,'Eléctrico':.5,'Roca':.5,'Acero':.5},
 'Psíquico': {'Lucha':2,'Veneno':2,'Psíquico':.5,'Acero':.5,'Siniestro':0},
 'Bicho': {'Planta':2,'Psíquico':2,'Siniestro':2,'Fuego':.5,'Lucha':.5,'Veneno':.5,'Volador':.5,'Fantasma':.5,'Acero':.5},
 'Roca': {'Fuego':2,'Hielo':2,'Volador':2,'Bicho':2,'Lucha':.5,'Tierra':.5,'Acero':.5},
 'Fantasma': {'Psíquico':2,'Fantasma':2,'Siniestro':.5,'Normal':0},
 'Dragón': {'Dragón':2,'Acero':.5},
 'Siniestro': {'Psíquico':2,'Fantasma':2,'Lucha':.5,'Siniestro':.5,'Acero':.5},
 'Acero': {'Hielo':2,'Roca':2,'Fuego':.5,'Agua':.5,'Eléctrico':.5,'Acero':.5},
}
# Gen III: la categoría física/especial la determina el TIPO, no el movimiento.
TIPOS_ESPECIALES={'Fuego','Agua','Planta','Eléctrico','Hielo','Psíquico','Dragón','Siniestro'}

def efectividad(tipo_ataque, pokemon_objetivo):
    factor=1.
    for t in pokemon_objetivo.get('tipos', [pokemon_objetivo['tipo']]):
        factor*=TYPE_CHART.get(tipo_ataque,{}).get(t,1)
    return factor

def default_state():
    return {side:dict(ataque=0,defensa=0,ataque_especial=0,defensa_especial=0,velocidad=0,
                      precision=0,estado='',dormido=0,confusion=0,drenadoras=False,
                      cargando='',proteccion=False,furia=0,retroceso=False)
            for side in ('jugador','enemigo')}

def factor_stat(stage):
    return (2+stage)/2 if stage>=0 else 2/(2-stage)

def daño(move,target,attacker_state,target_state,attacker=None):
    """Daño de Gen III con stats escalados cuando se provee atacante.
    Conserva firma usada en pruebas anteriores sin acceso a BD.
    """
    factor=efectividad(move['tipo'],target)
    if factor==0:return 0,0
    if attacker is None or 'estadisticas' not in attacker or 'estadisticas' not in target:
        raw=max(1,move['potencia']+random.randint(-2,3))
        raw*=factor_stat(attacker_state['ataque'])/factor_stat(target_state['defensa'])
        return max(1,round(raw*factor)),factor
    especial=move['tipo'] in TIPOS_ESPECIALES
    atkkey='ataque_especial' if especial else 'ataque'
    defkey='defensa_especial' if especial else 'defensa'
    a=attacker['estadisticas'][atkkey]*factor_stat(attacker_state[atkkey])
    d=target['estadisticas'][defkey]*factor_stat(target_state[defkey])
    base=floor((2*attacker['nivel']/5+2)*move['potencia']*a/max(1,d)/50)+2
    stab=1.5 if move['tipo'] in attacker.get('tipos',[attacker['tipo']]) else 1.
    crit=1.5 if move.get('efecto')=='critico_alto' and random.random()<.125 else 1.
    return max(1,floor(base*stab*factor*crit*random.uniform(.85,1))),factor

def actualizar_stage(state,key,step):
    previo=state.get(key,0)
    state[key]=max(-6,min(6,previo+step))
    return previo!=state[key]

def puede_actuar(state,events,pokemon):
    if state.pop('retroceso',False):
        events.append(dict(tipo='estado',mensaje=f'¡{pokemon} retrocedió y no pudo moverse!'))
        return False
    if state['estado']=='dormido':
        if state['dormido']>0:
            state['dormido']-=1
            events.append(dict(tipo='estado',mensaje=f'¡{pokemon} está dormido y no puede atacar!'))
            if state['dormido']==0:state['estado']=''
            return False
        state['estado']=''
    if state['estado']=='congelado':
        if random.random()<.2:
            state['estado']=''
            events.append(dict(tipo='estado',mensaje=f'¡{pokemon} se descongeló!'))
        else:
            events.append(dict(tipo='estado',mensaje=f'¡{pokemon} está congelado!'))
            return False
    if state['estado']=='paralizado' and random.random()<.25:
        events.append(dict(tipo='estado',mensaje=f'¡{pokemon} está paralizado y no puede moverse!'))
        return False
    if state['confusion']>0:
        state['confusion']-=1
        if random.random()<.33:
            events.append(dict(tipo='estado',mensaje=f'¡{pokemon} se golpeó por confusión!'))
            return 'confuso'
        if state['confusion']==0:
            events.append(dict(tipo='estado',mensaje=f'¡{pokemon} ya no está confundido!'))
    return True
