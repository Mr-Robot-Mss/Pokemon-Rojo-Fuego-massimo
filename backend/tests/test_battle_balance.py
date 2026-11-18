"""Pruebas de dificultad: la tabla de tipos y los turnos no cambian."""
import unittest
from unittest.mock import patch
from app.battle_balance import nivel_rival, vida_rival, dano_rival
from app.battle_effects import efectividad
from app.pokemon_progression import estadisticas_a_nivel

class TestEquilibrioCombate(unittest.TestCase):
    def test_niveles_iniciales_de_rivales(self):
        with patch('app.battle_balance.random.choice', return_value=2):
            self.assertEqual(nivel_rival(5), 3)
            self.assertEqual(nivel_rival(10), 8)
            self.assertEqual(nivel_rival(20), 18)

    def test_vida_salvaje_reducida_solo_en_niveles_bajos(self):
        self.assertEqual(vida_rival(20, 5), 16)
        self.assertEqual(vida_rival(20, 15), 18)
        self.assertEqual(vida_rival(20, 20), 20)

    def test_rock_slide_no_oneshot_charmander_nivel_5(self):
        vida=estadisticas_a_nivel(1, 5)['ps']
        self.assertEqual(efectividad('Roca', {'tipos':['Fuego'], 'tipo':'Fuego'}), 2)
        self.assertLess(dano_rival(999, vida, 5), vida // 2)
        self.assertGreater(vida - dano_rival(999, vida, 5), 0)

    def test_ataque_fallido_no_produce_dano(self):
        self.assertEqual(dano_rival(0, 20, 5), 0)

    def test_escalado_fuerte_a_nivel_alto(self):
        vida=70
        self.assertLess(dano_rival(35, vida, 5), dano_rival(35, vida, 15))
        self.assertLess(dano_rival(35, vida, 15), dano_rival(35, vida, 30))

if __name__ == '__main__':unittest.main()
