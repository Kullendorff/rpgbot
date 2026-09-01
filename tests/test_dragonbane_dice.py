"""
Unit tests for Dragonbane skill-check stapling av fördel/nackdel
(src/dragonbane/dice.py::dragonbane_skill_check).

House rule beslutad i dragonbane-stapling-av-f-rdelar-nackdelar.json:
varje extra instans av fördel/nackdel lägger till ytterligare ett T20
utöver grundslaget (t.ex. nackdel med antal=3 -> 4T20, behåll högsta).
Officiella regler stödjer inte stapling; se docstring i dice.py.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.dragonbane.dice import dragonbane_skill_check


class SequenceRandom:
    """Returnerar förutbestämda tärningsvärden i tur och ordning."""

    def __init__(self, values):
        self.values = list(values)

    def randint(self, a, b):
        return self.values.pop(0)


class TestDragonbaneSkillCheckAntal(unittest.TestCase):
    def test_normal_mode_default_antal_slar_en_tarning(self):
        result = dragonbane_skill_check(skill=10, mode="normal", rng=SequenceRandom([7]))
        self.assertEqual(result.antal, 1)
        self.assertEqual(result.rolls, [7])
        self.assertEqual(result.chosen_roll, 7)

    def test_fordel_antal_1_slar_tva_tarningar_behaller_lagst(self):
        result = dragonbane_skill_check(
            skill=10, mode="fördel", antal=1, rng=SequenceRandom([15, 3])
        )
        self.assertEqual(result.rolls, [15, 3])
        self.assertEqual(result.chosen_roll, 3)

    def test_nackdel_antal_1_slar_tva_tarningar_behaller_hogst(self):
        result = dragonbane_skill_check(
            skill=10, mode="nackdel", antal=1, rng=SequenceRandom([5, 19])
        )
        self.assertEqual(result.rolls, [5, 19])
        self.assertEqual(result.chosen_roll, 19)

    def test_fordel_stapling_antal_3_slar_fyra_tarningar(self):
        result = dragonbane_skill_check(
            skill=10, mode="fördel", antal=3, rng=SequenceRandom([15, 3, 18, 7])
        )
        self.assertEqual(len(result.rolls), 4)
        self.assertEqual(result.chosen_roll, 3)

    def test_nackdel_stapling_antal_2_slar_tre_tarningar(self):
        result = dragonbane_skill_check(
            skill=10, mode="nackdel", antal=2, rng=SequenceRandom([5, 19, 12])
        )
        self.assertEqual(len(result.rolls), 3)
        self.assertEqual(result.chosen_roll, 19)

    def test_draksslag_lyckas_alltid_oavsett_stapling(self):
        result = dragonbane_skill_check(
            skill=1, mode="nackdel", antal=5, rng=SequenceRandom([1] + [10] * 5)
        )
        self.assertEqual(result.chosen_roll, 10)
        self.assertIsNone(result.critical)
        # chosen_roll är max av [1,10,10,10,10,10] = 10, inte draksslag.
        # Verifiera separat att en etta bland de VALDA tärningarna ger draksslag:
        result2 = dragonbane_skill_check(
            skill=1, mode="fördel", antal=5, rng=SequenceRandom([1] + [10] * 5)
        )
        self.assertEqual(result2.chosen_roll, 1)
        self.assertEqual(result2.critical, "dragon")
        self.assertTrue(result2.success)

    def test_demonslag_misslyckas_alltid_oavsett_stapling(self):
        result = dragonbane_skill_check(
            skill=30, mode="nackdel", antal=5, rng=SequenceRandom([1] + [20] * 5)
        )
        self.assertEqual(result.chosen_roll, 20)
        self.assertEqual(result.critical, "demon")
        self.assertFalse(result.success)

    def test_antal_noll_ger_valueerror(self):
        with self.assertRaises(ValueError):
            dragonbane_skill_check(skill=10, mode="fördel", antal=0)

    def test_antal_over_99_ger_valueerror(self):
        with self.assertRaises(ValueError):
            dragonbane_skill_check(skill=10, mode="fördel", antal=100)

    def test_normal_med_antal_over_1_ger_valueerror(self):
        with self.assertRaises(ValueError):
            dragonbane_skill_check(skill=10, mode="normal", antal=2)

    def test_ogiltigt_lage_ger_valueerror(self):
        with self.assertRaises(ValueError):
            dragonbane_skill_check(skill=10, mode="ogiltigt")


if __name__ == "__main__":
    unittest.main()
