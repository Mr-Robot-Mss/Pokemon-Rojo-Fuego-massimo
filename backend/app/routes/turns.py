"""Combate por turnos: respeta el contrato de eventos de Angular y el Outbox Kafka.
La API calcula el turno en una sola transacción. Angular conserva sus esperas.
"""
import random
from copy import deepcopy

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Jugador, Combate, CombateTurno, EstadoCombate, POKEMONS
from app.battle_effects import (movimientos, efectividad, default_state, daño,
                                actualizar_stage, puede_actuar, factor_stat)
from app.pokemon_progression import (nivel_desde_experiencia, especie_evolucionada,
                                     pokemon_a_nivel, experiencia_ganada)
from app.battle_balance import nivel_rival, vida_rival, dano_rival
from app.messaging.rabbitmq import publicar_recompensa
from app.messaging.kafka_outbox import crear_evento_outbox, guardar_evento_outbox
from app.messaging.kafka_config import TOPIC_BATTLES, TOPIC_EVENTS

router = APIRouter(prefix='/battles', tags=['Combates por turnos'])

class IniciarCombate(BaseModel):
    jugador_id: int = Field(gt=0)
    pokemon_salvaje_id: int | None = None  # Ignorado: siempre se selecciona al azar.

class EjecutarAtaque(BaseModel):
    movimiento: str = Field(min_length=1, max_length=40)
    turno_esperado: int = Field(gt=0)


def buscar_pokemon(ident):
    return next((p for p in POKEMONS if p['id']==ident), None)


def stats_de(combate, datos):
    n_j=int(datos.get('nivel_jugador',5))
    n_e=int(datos.get('nivel_enemigo',5))
    aliado=pokemon_a_nivel(buscar_pokemon(combate.pokemon_jugador_id),n_j)
    enemigo=pokemon_a_nivel(buscar_pokemon(combate.pokemon_salvaje_id),n_e)
    # Los combates históricos pueden tener PS mayores que los nuevos máximos por nivel.
    return aliado,enemigo


def serializar_combate(combate, meta=None):
    meta=meta or {}
    aliado,enemigo=stats_de(combate,meta)
    return {
        'combate_id':combate.id,'jugador_id':combate.jugador_id,
        'pokemon_jugador':aliado,'pokemon_enemigo':enemigo,
        'nivel_jugador':aliado['nivel'],'nivel_enemigo':enemigo['nivel'],
        'ps_jugador':combate.ps_jugador,'ps_enemigo':combate.ps_enemigo,
        'ps_max_jugador':int(meta.get('ps_max_jugador',max(aliado['vida'],combate.ps_jugador))),
        'ps_max_enemigo':int(meta.get('ps_max_enemigo',max(enemigo['vida'],combate.ps_enemigo))),
        'turno':combate.turno,'estado':combate.estado,
        'mensaje':combate.ultimo_mensaje,'resultado_id':combate.resultado_id,
        'movimientos':movimientos(aliado['id']),
    }


def registrar_evento(db, topic, player_id, event_type, data):
    ev=crear_evento_outbox(player_id=player_id,event_type=event_type,data=data)
    guardar_evento_outbox(db=db,topic=topic,evento=ev)


@router.post('/start', status_code=201)
def iniciar_combate(datos:IniciarCombate,db:Session=Depends(get_db)):
    jugador=db.get(Jugador,datos.jugador_id)
    if not jugador:raise HTTPException(404,'Entrenador no encontrado')
    if jugador.pokemon_id not in (1,2,3):
        raise HTTPException(422,'El entrenador debe tener uno de los 3 Pokémon iniciales')
    n_j=nivel_desde_experiencia(jugador.experiencia)
    evo=especie_evolucionada(jugador.pokemon_id,n_j)
    n_e=nivel_rival(n_j)
    rival=random.choice([p for p in POKEMONS if p.get('rival')])
    aliado=pokemon_a_nivel(buscar_pokemon(evo),n_j)
    enemigo=pokemon_a_nivel(rival,n_e)
    # El rival mantiene sus estadísticas reales; solo se equilibra la vida
    # del encuentro para que los iniciales tengan oportunidades de ganar.
    ps_rival=vida_rival(enemigo['vida'],n_j)
    combate=CombateTurno(jugador_id=jugador.id,pokemon_jugador_id=evo,
        pokemon_salvaje_id=rival['id'],ps_jugador=aliado['vida'],ps_enemigo=ps_rival,
        turno=1,estado='activo',ultimo_mensaje=f'¡Un {enemigo["nombre"]} salvaje de nivel {n_e} apareció!')
    meta={**default_state(),'nivel_jugador':n_j,'nivel_enemigo':n_e,
          'ps_max_jugador':aliado['vida'],'ps_max_enemigo':ps_rival}
    try:
        db.add(combate);db.flush()
        db.add(EstadoCombate(combate_id=combate.id,datos=meta))
        db.commit();db.refresh(combate)
        return serializar_combate(combate,meta)
    except Exception:
        db.rollback();raise


@router.get('/{combate_id}')
def consultar_combate(combate_id:int,db:Session=Depends(get_db)):
    combate=db.get(CombateTurno,combate_id)
    if not combate:raise HTTPException(404,'Combate no encontrado')
    record=db.get(EstadoCombate,combate_id)
    return serializar_combate(combate,record.datos if record else {})


@router.post('/{combate_id}/attack')
def atacar(combate_id:int,datos:EjecutarAtaque,db:Session=Depends(get_db)):
    # Anti doble click y protección de resultados, XP y recompensas duplicadas.
    combate=db.scalar(select(CombateTurno).where(CombateTurno.id==combate_id).with_for_update())
    if not combate:raise HTTPException(404,'Combate no encontrado')
    if combate.estado!='activo':raise HTTPException(409,'El combate ya terminó')
    if datos.turno_esperado!=combate.turno:raise HTTPException(409,'El turno ya fue procesado')
    record=db.scalar(select(EstadoCombate).where(EstadoCombate.combate_id==combate.id).with_for_update())
    if record is None:
        record=EstadoCombate(combate_id=combate.id,datos=default_state());db.add(record)
    meta=deepcopy(record.datos or {})
    for k,v in default_state().items():
        meta.setdefault(k,v)
        for key,value in v.items():meta[k].setdefault(key,value)
    jugador=db.scalar(select(Jugador).where(Jugador.id==combate.jugador_id).with_for_update())
    aliado,enemigo=stats_de(combate,meta)
    n_j,n_e=aliado['nivel'],enemigo['nivel']
    mov=next((m for m in movimientos(aliado['id']) if m['nombre'].casefold()==datos.movimiento.casefold()),None)
    if mov is None:raise HTTPException(422,'Movimiento no disponible')
    eventos=[]; numero_turno=combate.turno
    recompensa_pendiente=None
    # Los eventos de daño y ataque conservan sus campos para Angular.
    def mensaje(texto):eventos.append({'tipo':'estado','mensaje':texto})
    def vida(side):return combate.ps_jugador if side=='jugador' else combate.ps_enemigo
    def maxima(side):return int(meta.get('ps_max_'+side,aliado['vida'] if side=='jugador' else enemigo['vida']))
    def poner_vida(side,nuevo):
        nuevo=max(0,min(maxima(side),int(nuevo)))
        if side=='jugador':combate.ps_jugador=nuevo
        else:combate.ps_enemigo=nuevo
        return nuevo
    def herir(side,cantidad):
        anterior=vida(side);final=poner_vida(side,anterior-cantidad)
        golpe=anterior-final
        if golpe:eventos.append(dict(tipo='dano',objetivo=side,cantidad=golpe,ps_restantes=final))
        return golpe
    def curar(side,cantidad,nombre):
        anterior=vida(side);final=poner_vida(side,anterior+cantidad)
        eventos.append(dict(tipo='curacion',objetivo=side,ps_restantes=final,
                            mensaje=f'¡{nombre} recuperó {final-anterior} PS!'))

    def aplicar(actor,atacante,objetivo,ataque):
        destino='enemigo' if actor=='jugador' else 'jugador'
        stats=meta[actor];other=meta[destino]
        # Vuelo y Rayo Solar fuerzan el movimiento del segundo turno.
        if stats['cargando']:
            forced=next((m for m in movimientos(atacante['id']) if m['nombre']==stats['cargando']),None)
            if forced:ataque=forced
        despertar_rqu=False
        if ataque['nombre']=='Ronquido' and stats['estado']=='dormido':
            stats['dormido']=max(0,stats['dormido']-1)
            despertar_rqu=(stats['dormido']==0)
            permite=True
        else:
            permite=puede_actuar(stats,eventos,atacante['nombre'])
        if permite is False:return
        if permite=='confuso':
            herir(actor,max(1,atacante['vida']//12))
            return
        efecto=ataque.get('efecto','')
        eventos.append({'tipo':'ataque','actor':actor,'pokemon':atacante['nombre'],'movimiento':ataque['nombre']})
        daño_hecho=0;factor=1.
        if stats['cargando']:
            stats['cargando']=''
        elif efecto in ('vuelo','rayo_solar'):
            stats['cargando']=ataque['nombre']
            mensaje(f'¡{atacante["nombre"]} voló alto!' if efecto=='vuelo' else f'¡{atacante["nombre"]} absorbió luz solar!')
            return
        # Protección del jugador actúa antes del ataque del rival por orden del turno.
        if other['proteccion'] and ataque['potencia']>0:
            mensaje(f'¡{objetivo["nombre"]} se protegió!')
        elif other.get('cargando')=='Vuelo' and ataque['potencia']>0:
            mensaje(f'¡{objetivo["nombre"]} esquivó el ataque mientras volaba!')
        elif ataque['nombre']=='Ronquido' and stats['estado']!='dormido':
            mensaje(f'¡{atacante["nombre"]} debe estar dormido para usar Ronquido!')
        else:
            exactitud=max(.2,min(1.,ataque.get('precision',1.)*factor_stat(stats['precision'])))
            if random.random()>exactitud:
                mensaje(f'¡{atacante["nombre"]} falló el ataque!')
            elif ataque['potencia']>0:
                if efecto=='mov_sismico':
                    factor=efectividad('Lucha',objetivo)
                    golpe=atacante['nivel'] if factor else 0
                else:
                    golpe,factor=daño(ataque,objetivo,stats,other,atacante)
                    if stats['estado']=='quemado' and ataque['tipo'] not in ('Fuego','Agua','Planta','Eléctrico','Hielo','Psíquico','Dragón','Siniestro'):
                        golpe=max(1,golpe//2)
                    if efecto=='furia':golpe=round(golpe*(1+stats['furia']*.5))
                # SOLO los golpes del rival se suavizan; el jugador mantiene
                # el daño original y la efectividad de tipos.
                if actor=='enemigo':
                    golpe=dano_rival(golpe,maxima('jugador'),n_j)
                daño_hecho=herir(destino,golpe)
                if daño_hecho:
                    if factor>1:mensaje('¡Es súper eficaz!')
                    elif factor==0:mensaje(f'¡No afecta a {objetivo["nombre"]}!')
                    elif factor<1:mensaje('No es muy eficaz...')
                elif factor==0:mensaje(f'¡No afecta a {objetivo["nombre"]}!')
                if daño_hecho and other['furia']>0:
                    other['furia']=min(5,other['furia']+1)
                    mensaje(f'¡La Furia de {objetivo["nombre"]} aumentó!')
                if daño_hecho and efecto in ('paralizar_ocasional','envenenar_ocasional','quemar_ocasional','congelar_ocasional','retroceso_ocasional'):
                    probabilidades={'paralizar_ocasional':.10,'envenenar_ocasional':.30,'quemar_ocasional':.10,
                                    'congelar_ocasional':.10,'retroceso_ocasional':.30}
                    if random.random()<probabilidades[efecto]:
                        if efecto=='retroceso_ocasional':other['retroceso']=True;mensaje(f'¡{objetivo["nombre"]} retrocedió!')
                        else:
                            status={'paralizar_ocasional':'paralizado','envenenar_ocasional':'envenenado',
                                    'quemar_ocasional':'quemado','congelar_ocasional':'congelado'}[efecto]
                            if not other['estado'] and not(status=='envenenado' and any(t in objetivo['tipos'] for t in ('Veneno','Acero'))):
                                other['estado']=status;mensaje(f'¡{objetivo["nombre"]} quedó {status}!')
                if efecto=='giro_rapido' and stats['drenadoras']:
                    stats['drenadoras']=False;mensaje(f'¡{atacante["nombre"]} se liberó de Drenadoras!')
                if efecto=='furia':stats['furia']=max(1,stats['furia'])
            elif efecto in ('bajar_ataque','bajar_defensa','bajar_precision'):
                key={'bajar_ataque':'ataque','bajar_defensa':'defensa','bajar_precision':'precision'}[efecto]
                cambio=actualizar_stage(other,key,-1)
                mensaje(f'¡Bajó {key.replace("_"," ")} de {objetivo["nombre"]}!' if cambio else '¡Ese atributo no puede bajar más!')
            elif efecto in ('subir_defensa','corpulencia','danza_dragon'):
                if efecto=='subir_defensa':names=('defensa',)
                elif efecto=='corpulencia':names=('ataque','defensa')
                else:names=('ataque','velocidad')
                for key in names:actualizar_stage(stats,key,1)
                mensaje(f'¡{atacante["nombre"]} mejoró sus atributos!')
            elif efecto=='drenadoras':
                if 'Planta' in objetivo['tipos']:mensaje('¡Drenadoras no afectan a los Pokémon de Planta!')
                elif other['drenadoras']:mensaje('¡El rival ya tiene Drenadoras!')
                else:other['drenadoras']=True;mensaje(f'¡{objetivo["nombre"]} fue atrapado por Drenadoras!')
            elif efecto in ('envenenar','paralizar','dormir'):
                status={'envenenar':'envenenado','paralizar':'paralizado','dormir':'dormido'}[efecto]
                immune=(status=='envenenado' and any(t in objetivo['tipos'] for t in ('Veneno','Acero')))
                immune=immune or(status=='paralizado' and 'Tierra' in objetivo['tipos'] and ataque['tipo']=='Eléctrico')
                if immune:mensaje(f'¡No afecta a {objetivo["nombre"]}!')
                elif other['estado']:mensaje('¡El Pokémon ya tiene un estado alterado!')
                else:
                    other['estado']=status
                    if status=='dormido':other['dormido']=random.randint(1,3)
                    mensaje(f'¡{objetivo["nombre"]} quedó {status}!')
            elif efecto=='confundir':
                if other['confusion']:mensaje('¡El Pokémon ya está confundido!')
                else:other['confusion']=random.randint(2,4);mensaje(f'¡{objetivo["nombre"]} quedó confundido!')
            elif efecto in ('recuperar','descanso'):
                curar(actor,maxima(actor) if efecto=='descanso' else max(1,maxima(actor)//2),atacante['nombre'])
                if efecto=='descanso':
                    stats['estado']='dormido';stats['dormido']=2
                    mensaje(f'¡{atacante["nombre"]} está durmiendo para descansar!')
            elif efecto=='proteccion':
                stats['proteccion']=True;mensaje(f'¡{atacante["nombre"]} está protegido durante este turno!')
            else:
                mensaje('¡El movimiento no causó daño!')
        if despertar_rqu:
            stats['estado']=''
            mensaje(f'¡{atacante["nombre"]} despertó después de Ronquido!')
        registrar_evento(db,TOPIC_EVENTS,combate.jugador_id,'AttackExecuted',{
            'battle_id':combate.id,'turn':numero_turno,'actor':actor,
            'pokemon':atacante['nombre'],'movement':ataque['nombre'],
            'damage':daño_hecho,'remaining_hp':vida(destino), 'effectiveness':factor})

    # RESPECTO AL SISTEMA ANTERIOR: el jugador ataca primero y el enemigo después.
    aplicar('jugador',aliado,enemigo,mov)
    if combate.ps_enemigo>0 and combate.ps_jugador>0:
        rival=random.choice(movimientos(enemigo['id']))
        aplicar('enemigo',enemigo,aliado,rival)
    # El daño residual se aplica tras ambas acciones, conservando orden y logs.
    for side,pokemon in (('jugador',aliado),('enemigo',enemigo)):
        if vida(side)<=0:continue
        status=meta[side]
        if status['estado'] in ('envenenado','quemado'):
            chip=max(1,maxima(side)//8)
            herir(side,chip)
            mensaje(f'¡{pokemon["nombre"]} sufre daño por {status["estado"]}!')
        if status['drenadoras'] and vida(side)>0:
            chip=max(1,maxima(side)//8)
            perdido=herir(side,chip)
            quien='enemigo' if side=='jugador' else 'jugador'
            otro=enemigo if side=='jugador' else aliado
            if vida(quien)>0:curar(quien,perdido,otro['nombre'])
            mensaje(f'¡Drenadoras absorbe PS de {pokemon["nombre"]}!')
        status['proteccion']=False
    # Resultado único y premio de experiencia del rival al nivel generado.
    if combate.ps_enemigo<=0:
        combate.estado='victoria'
        eventos.append({'tipo':'debilitado','objetivo':'enemigo','mensaje':f'¡{enemigo["nombre"]} se debilitó!'})
        xp=experiencia_ganada(enemigo,n_e)
        nivel_antes=nivel_desde_experiencia(jugador.experiencia)
        evo_antes=especie_evolucionada(jugador.pokemon_id,nivel_antes)
        jugador.experiencia+=xp
        nivel_nuevo=nivel_desde_experiencia(jugador.experiencia)
        evo_nueva=especie_evolucionada(jugador.pokemon_id,nivel_nuevo)
        eventos.append({'tipo':'experiencia','cantidad':xp,
                        'mensaje':f'¡Ganaste {xp} EXP! Nivel {nivel_nuevo}.'})
        if evo_nueva!=evo_antes:
            anterior=buscar_pokemon(evo_antes)['nombre'];nuevo=buscar_pokemon(evo_nueva)['nombre']
            eventos.append({'tipo':'evolucion','anterior':anterior,'nuevo':nuevo,'nivel':nivel_nuevo,
                            'mensaje':f'¡{anterior} evolucionó a {nuevo} en el nivel {nivel_nuevo}!'})
    elif combate.ps_jugador<=0:
        combate.estado='derrota'
        xp=0
        eventos.append({'tipo':'debilitado','objetivo':'jugador','mensaje':f'¡{aliado["nombre"]} se debilitó!'})
    else:xp=0
    if combate.estado!='activo':
        ganador='jugador' if combate.estado=='victoria' else 'salvaje'
        resultado=Combate(jugador_id=combate.jugador_id,pokemon_salvaje_id=combate.pokemon_salvaje_id,
                          ganador=ganador,experiencia_ganada=xp)
        db.add(resultado);db.flush();combate.resultado_id=resultado.id
        if ganador=='jugador':recompensa_pendiente=resultado.id
        registrar_evento(db,TOPIC_BATTLES,combate.jugador_id,'BattleCompleted',{
            'battle_id':resultado.id,'turn_battle_id':combate.id,'winner':ganador,
            'experience_gained':xp,'pokemon_player':aliado['nombre'],'pokemon_enemy':enemigo['nombre']})
    combate.ultimo_mensaje='\n'.join(e.get('mensaje','') for e in eventos if e.get('mensaje')) or 'Turno completado'
    combate.turno+=1
    record.datos=meta
    db.commit();db.refresh(combate)
    estado_recompensa='no_aplica'
    if recompensa_pendiente is not None:
        try:
            publicar_recompensa(battle_id=recompensa_pendiente,
                               operation_id=f'reward-battle-{recompensa_pendiente}')
            estado_recompensa='publicada'
        except Exception as error:
            estado_recompensa='publicacion_fallida'
            print(f'[RABBITMQ] Error: {error}')
    respuesta=serializar_combate(combate,meta)
    respuesta['eventos']=eventos
    respuesta['estado_recompensa']=estado_recompensa
    return respuesta
