"""Pruebas ejecutables sin Kafka ni base de datos: python -m unittest discover -s tests"""
import unittest
from app.battle_effects import movimientos,efectividad,default_state,actualizar_stage,daño

class TestBattleRules(unittest.TestCase):
 def test_10_enemies_have_four_moves(self):
  for pid in range(4,14):
   self.assertEqual(len(movimientos(pid)),4)
 def test_initials_have_four_moves(self):
  for pid in (1,2,3):self.assertEqual(len(movimientos(pid)),4)
 def test_double_weakness_electric_gyarados(self):
  self.assertEqual(efectividad('Eléctrico',{'tipo':'Agua','tipos':['Agua','Volador']}),4)
 def test_double_weakness_ice_dragonite(self):
  self.assertEqual(efectividad('Hielo',{'tipo':'Dragón','tipos':['Dragón','Volador']}),4)
 def test_electric_ground_immunity(self):
  self.assertEqual(efectividad('Eléctrico',{'tipo':'Tierra','tipos':['Tierra']}),0)
 def test_grunido_lowers_attack_and_damage(self):
  atacante=default_state()['jugador'];defensor=default_state()['enemigo']
  self.assertTrue(actualizar_stage(atacante,'ataque',-1))
  with_unbuffed=daño({'potencia':12,'tipo':'Normal'}, {'tipo':'Normal'},default_state()['jugador'],defensor)[0]
  self.assertTrue(atacante['ataque']<0)
  self.assertTrue(daño({'potencia':12,'tipo':'Normal'}, {'tipo':'Normal'},atacante,defensor)[0] <= with_unbuffed+3)

if __name__=='__main__':unittest.main()
