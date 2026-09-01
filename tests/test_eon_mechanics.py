"""
Unit tests för EON-mekaniken — src/eon/ (hit_tables, damage_tables,
fumble_tables, combat_manager).

Täcker paketfasaden (import eon + __all__), träfftabellernas
fullständighet för slag 1-100, effektkodsparsning på verkliga koder
ur skadetabellerna och fummeltabellernas täckning 1-20 för alla
vapenalias.

Kör som skript: python tests/test_eon_mechanics.py
(ALDRIG python -m unittest — känd tests-paketkrock, se CLAUDE.md.)
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import eon
from eon import (
    WeaponType,
    AttackLevel,
    get_hit_location,
    parse_effect_code,
    FUMBLE_TABLES,
    WEAPON_TYPE_ALIASES,
)


class TestPaketfasad(unittest.TestCase):
    """import eon fungerar och allt i __all__ är importerbart."""

    def test_all_importerbart(self):
        for namn in eon.__all__:
            self.assertTrue(hasattr(eon, namn), f"eon.{namn} saknas")

    def test_antal_symboler(self):
        # Paketfasaden re-exponerar 12 mekaniksymboler
        self.assertEqual(len(eon.__all__), 12)


class TestTrafftabeller(unittest.TestCase):
    """get_hit_location täcker slag 1..100 för alla vapentyper × nivåer."""

    def test_alla_slag_1_till_100(self):
        for weapon in WeaponType:
            for level in AttackLevel:
                for roll in range(1, 101):
                    resultat = get_hit_location(weapon, level, roll)
                    # (huvudområde, delområde, områdeskod)
                    self.assertEqual(len(resultat), 3,
                                     f"{weapon}/{level}/slag {roll}: {resultat!r}")
                    for del_ in resultat:
                        self.assertIsInstance(del_, str)


class TestEffektkoder(unittest.TestCase):
    """parse_effect_code på verkliga effektkoder ur HUGG_DAMAGE_TABLE."""

    def test_enkel_kod(self):
        resultat = parse_effect_code("T+1, S+3, B+1", 10)
        self.assertIsInstance(resultat, dict)

    def test_komplex_kod(self):
        resultat = parse_effect_code("T*2, S*2, B/2", 10)
        self.assertIsInstance(resultat, dict)

    def test_tom_kod(self):
        resultat = parse_effect_code("", 10)
        self.assertIsInstance(resultat, dict)


class TestFummeltabeller(unittest.TestCase):
    """FUMBLE_TABLES[WEAPON_TYPE_ALIASES[k]][n] finns för alla alias × n 1..20."""

    def test_alla_alias_1_till_20(self):
        self.assertTrue(WEAPON_TYPE_ALIASES)
        for alias, fulltnamn in WEAPON_TYPE_ALIASES.items():
            self.assertIn(fulltnamn, FUMBLE_TABLES,
                          f"alias {alias!r} -> {fulltnamn!r} saknas i FUMBLE_TABLES")
            tabell = FUMBLE_TABLES[fulltnamn]
            for n in range(1, 21):
                self.assertIn(n, tabell, f"{fulltnamn}[{n}] saknas")


if __name__ == '__main__':
    unittest.main()
