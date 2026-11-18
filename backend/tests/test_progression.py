"""Pruebas de progresión sin servicios externos.
Ejecutar desde backend/: python -m unittest discover -s tests -v
"""
import unittest
from app.pokemon_progression import (
    BASE,EVOLUCIONES,experiencia_total_para_nivel,EXPERIENCIA_INICIAL,
    nivel_desde_experiencia,experiencia_progreso,especie_evolucionada,
    estadisticas_a_nivel,experiencia_ganada,pokemon_a_nivel,
)
from app.battle_effects import movimientos,daño,default_state,efectividad

class TestProgresion(unittest.TestCase):
    def test_levels_start_at_five(self):
        self.assertEqual(nivel_desde_experiencia(0),5)
        self.assertEqual(EXPERIENCIA_INICIAL,135)
        self.assertEqual(experiencia_total_para_nivel(10),560)
        self.assertEqual(experiencia_total_para_nivel(20),5460)
    def test_evolutions_exact_levels(self):
        for initial,mid,final in ((1,14,15),(2,18,19),(3,16,17)):
            self.assertEqual(especie_evolucionada(initial,5),initial)
            self.assertEqual(especie_evolucionada(initial,9),initial)
            self.assertEqual(especie_evolucionada(initial,10),mid)
            self.assertEqual(especie_evolucionada(initial,19),mid)
            self.assertEqual(especie_evolucionada(initial,20),final)
        for lvl in (10,20):
            xp=experiencia_total_para_nivel(lvl)-EXPERIENCIA_INICIAL
            self.assertEqual(nivel_desde_experiencia(xp),lvl)
    def test_real_base_stats_all_species(self):
        self.assertEqual(len(BASE),19)
        self.assertEqual(BASE[1][:6],(39,52,43,60,50,65))
        self.assertEqual(BASE[14][:6],(58,64,58,80,65,80))
        self.assertEqual(BASE[15][:6],(78,84,78,109,85,100))
        self.assertEqual(BASE[17][:6],(80,82,83,100,100,80))
        self.assertEqual(BASE[19][:6],(79,83,100,85,105,78))
    def test_hp_scales_with_level(self):
        self.assertLess(estadisticas_a_nivel(1,5)['ps'],estadisticas_a_nivel(14,10)['ps'])
        self.assertLess(estadisticas_a_nivel(14,10)['ps'],estadisticas_a_nivel(15,20)['ps'])
    def test_all_species_four_attacks(self):
        for ident in BASE:
            moves=movimientos(ident)
            self.assertEqual(len(moves),4,ident)
            self.assertEqual(len(set(m['nombre'] for m in moves)),4,ident)
    def test_starters_moves(self):
        expected={
            1:['Arañazo','Ascuas','Gruñido','Pantalla de Humo'],
            14:['Arañazo','Lanzallamas','Garra Dragón','Furia'],
            15:['Lanzallamas','Vuelo','Garra Dragón','Movimiento Sísmico'],
            3:['Placaje','Latigazo','Drenadoras','Somnífero'],
            16:['Placaje','Hojas Navaja','Polvo Veneno','Síntesis'],
            17:['Rayo Solar','Bomba Lodo','Somnífero','Síntesis'],
            2:['Placaje','Pistola Agua','Refugio','Látigo'],
            18:['Pistola Agua','Giro Rápido','Mordisco','Protección'],
            19:['Hidrobomba','Surf','Rayo Hielo','Giro Rápido'],
        }
        for i,moves in expected.items():self.assertEqual([m['nombre'] for m in movimientos(i)],moves)
    def test_more_exp_for_higher_enemy_level(self):
        enemy={'id':4}
        self.assertLess(experiencia_ganada(enemy,5),experiencia_ganada(enemy,20))
        self.assertGreater(experiencia_ganada({'id':13},20),experiencia_ganada(enemy,20))
    def test_battle_damage_scaled_by_level(self):
        move=movimientos(1)[1]
        player={'id':1,'tipo':'Fuego','tipos':['Fuego'],'nivel':5,'estadisticas':estadisticas_a_nivel(1,5)}
        high={'id':15,'tipo':'Fuego','tipos':['Fuego','Volador'],'nivel':20,'estadisticas':estadisticas_a_nivel(15,20)}
        target={'id':3,'tipo':'Planta','tipos':['Planta','Veneno'],'nivel':5,'estadisticas':estadisticas_a_nivel(3,5)}
        states=default_state()
        self.assertGreater(daño(move,target,states['jugador'],states['enemigo'],high)[0],
                           daño(move,target,states['jugador'],states['enemigo'],player)[0])

if __name__=='__main__':unittest.main()
