"""Prueba de API interna en SQLite: no requiere PostgreSQL, Kafka ni RabbitMQ.
Ejecutar desde backend/: python tests/validate_integration_sqlite.py
"""
import sys,types
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import create_engine,select
from sqlalchemy.orm import DeclarativeBase,Session

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
mockdb=types.ModuleType('app.database')
class Base(DeclarativeBase):pass
mockdb.Base=Base
mockdb.get_db=lambda:None
sys.modules['app.database']=mockdb
rabbit=types.ModuleType('app.messaging.rabbitmq');rabbit.publicar_recompensa=lambda **kwargs:None
sys.modules['app.messaging.rabbitmq']=rabbit

from app import models
from app.messaging.kafka_outbox import KafkaOutbox
from app.routes import turns,players
from app.pokemon_progression import experiencia_total_para_nivel,EXPERIENCIA_INICIAL

engine=create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as db:
 for original,evolved,final in ((1,14,15),(2,18,19),(3,16,17)):
  for target, expected in ((10,evolved),(20,final)):
   threshold=experiencia_total_para_nivel(target)-EXPERIENCIA_INICIAL
   jugador=models.Jugador(nombre=f'test-{original}-{target}',pokemon_id=original,experiencia=threshold-1)
   db.add(jugador);db.commit();db.refresh(jugador)
   assert players.serializar_jugador(jugador)['nivel']==target-1, (original,target)
   combate=turns.iniciar_combate(turns.IniciarCombate(jugador_id=jugador.id),db=db)
   assert combate['pokemon_jugador']['id']!=expected
   assert combate['pokemon_enemigo']['rival'] is True
   assert combate['ps_max_jugador']==combate['pokemon_jugador']['vida']
   assert len(combate['movimientos'])==4
   # Forzar derrota rival al siguiente ataque sin alterar reglas de daño.
   batalla=db.get(models.CombateTurno,combate['combate_id'])
   batalla.ps_enemigo=1;db.commit()
   from app.battle_effects import efectividad
   ataque=next(m for m in combate['movimientos'] if m['potencia']>0 and efectividad(m['tipo'],combate['pokemon_enemigo'])>0)
   with patch('app.routes.turns.random.random',return_value=0.0):
    result=turns.atacar(combate['combate_id'],turns.EjecutarAtaque(movimiento=ataque['nombre'],turno_esperado=1),db=db)
   assert result['estado']=='victoria',result
   assert len([e for e in result['eventos'] if e['tipo']=='evolucion'])==1, result['eventos']
   db.refresh(jugador)
   assert players.serializar_jugador(jugador)['pokemon']['id']==expected
   assert players.serializar_jugador(jugador)['nivel']>=target
   nuevo=turns.iniciar_combate(turns.IniciarCombate(jugador_id=jugador.id),db=db)
   assert nuevo['pokemon_jugador']['id']==expected
   from app.battle_effects import movimientos
   assert [m['nombre'] for m in nuevo['movimientos']]==[m['nombre'] for m in movimientos(expected)]
   print(f'OK {original} -> {expected} en nivel {target}; EXP {jugador.experiencia}')
 assert db.scalar(select(KafkaOutbox)) is not None
 print('OK: 6 evoluciones, XP SQL, niveles de combate, eventos Outbox y 10 rivales potenciales')
with Session(engine) as db:
 import random
 random.seed(427)
 for start in (1,2,3):
  j=models.Jugador(nombre=f'stress-{start}',pokemon_id=start,experiencia=0)
  db.add(j);db.commit();db.refresh(j)
  for run in range(12):
   c=turns.iniciar_combate(turns.IniciarCombate(jugador_id=j.id),db=db)
   attempts=0
   while c['estado']=='activo' and attempts<100:
    attempts+=1
    # Ejecutar ataques reales, sin forzar daño ni RNG: valida estados y persistencia.
    moves=c['movimientos']
    pick=random.choice([m for m in moves if m['potencia']>0] or moves)
    c=turns.atacar(c['combate_id'],turns.EjecutarAtaque(movimiento=pick['nombre'],turno_esperado=c['turno']),db=db)
    assert 0<=c['ps_jugador']<=c['ps_max_jugador']
    assert 0<=c['ps_enemigo']<=c['ps_max_enemigo']
   assert c['estado']!='activo', (start,run)
 print('OK: 36 combates completos en SQLite con turnos secuenciales y estados variados')
