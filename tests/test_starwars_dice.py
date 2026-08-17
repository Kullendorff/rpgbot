"""
Unit tests for the Star Wars D6 (WEG40120, 2nd Ed. Revised & Expanded)
dice engine — src/starwars/dice.py.

Regelkällor testfallen verifierar mot (se dice.py-docstring för detaljer):
  * Wild Die exploderar på 6, obegränsat (s. 20).
  * Wild Die-etta gäller ENDAST första slaget (s. 72-73).
  * Character Point-tärningar exploderar också på 6, men saknar
    1:e-specialregeln (s. 81, "Character Elements").
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.starwars import dice


class SequenceRandom:
    """Returnerar förutbestämda tärningsvärden i tur och ordning."""

    def __init__(self, values):
        self.values = list(values)

    def randint(self, a, b):
        return self.values.pop(0)


class AlwaysSixRandom:
    """Simulerar en trasig/oändligt exploderande tärning."""

    def randint(self, a, b):
        return 6


class TestParseDiceCode(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(str(dice.parse_dice_code("4D+2")), "4D+2")
        self.assertEqual(str(dice.parse_dice_code("4d+2")), "4D+2")
        self.assertEqual(str(dice.parse_dice_code("4D")), "4D")
        self.assertEqual(str(dice.parse_dice_code("4")), "4D")
        self.assertEqual(str(dice.parse_dice_code(" 4 D + 2 ")), "4D+2")

    def test_invalid_input_raises(self):
        with self.assertRaises(ValueError):
            dice.parse_dice_code("blaster")
        with self.assertRaises(ValueError):
            dice.parse_dice_code("")
        with self.assertRaises(ValueError):
            dice.parse_dice_code("4D+")
        with self.assertRaises(ValueError):
            dice.parse_dice_code(None)


class TestDiceCode(unittest.TestCase):
    def test_bounds_validation(self):
        with self.assertRaises(ValueError):
            dice.DiceCode(dice=0)
        with self.assertRaises(ValueError):
            dice.DiceCode(dice=1, pips=-1)
        with self.assertRaises(ValueError):
            dice.DiceCode(dice=dice.MAX_DICE + 1)

    def test_doubled_doubles_dice_and_pips(self):
        code = dice.DiceCode(dice=4, pips=2)
        self.assertEqual(code.doubled(), dice.DiceCode(dice=8, pips=4))

    def test_with_dice_delta(self):
        code = dice.DiceCode(dice=6, pips=1)
        self.assertEqual(code.with_dice_delta(-2), dice.DiceCode(dice=4, pips=1))


class TestWildDie(unittest.TestCase):
    def test_wild_die_explodes_regular_six_does_not(self):
        # regular: 3, 6, 3 ; wild-kedja: 6 -> 6 -> 4
        rng = SequenceRandom([3, 6, 3, 6, 6, 4])
        result = dice.roll(dice.DiceCode(dice=4, pips=0), rng=rng)

        self.assertEqual(result.regular_rolls, [3, 6, 3])
        self.assertEqual(result.wild.rolls, [6, 6, 4])
        self.assertEqual(result.wild.total, 16)
        self.assertTrue(result.wild.exploded)
        self.assertEqual(result.total, 3 + 6 + 3 + 16)

    def test_max_explosions_bounds_an_always_six_rng(self):
        rng = AlwaysSixRandom()
        result = dice.roll(dice.DiceCode(dice=1, pips=0), rng=rng)
        self.assertEqual(len(result.wild.rolls), dice.MAX_EXPLOSIONS)
        self.assertTrue(all(r == 6 for r in result.wild.rolls))

    def test_wild_die_one_all_three_outcomes(self):
        # regular: 3, 5, 2 ; wild: 1 (endast första slaget, ingen kedja)
        rng = SequenceRandom([3, 5, 2, 1])
        result = dice.roll(dice.DiceCode(dice=4, pips=2), rng=rng)

        self.assertTrue(result.wild.is_one)
        # Alt A: räkna in som vanligt
        self.assertEqual(result.total, 3 + 5 + 2 + 1 + 2)
        # Alt B: dra bort ettan och högsta andra tärningen (5)
        self.assertEqual(result.total_if_removed, result.total - 1 - 5)
        # Alt C har samma numeriska värde som Alt A, bara flaggad med komplikation.

    def test_wild_die_one_on_a_1d_pool_has_no_other_die(self):
        rng = SequenceRandom([1])
        result = dice.roll(dice.DiceCode(dice=1, pips=0), rng=rng)

        self.assertTrue(result.wild.is_one)
        self.assertEqual(result.total, 1)
        self.assertEqual(result.total_if_removed, 0)

    def test_chain_six_then_one_is_not_a_gm_choice(self):
        # "for the first roll only" — en etta efter en explosion är bara en etta.
        rng = SequenceRandom([2, 2, 2, 6, 1])
        result = dice.roll(dice.DiceCode(dice=4, pips=0), rng=rng)

        self.assertEqual(result.wild.rolls, [6, 1])
        self.assertFalse(result.wild.is_one)
        self.assertEqual(result.total, 2 + 2 + 2 + 7)


class TestMultipleActions(unittest.TestCase):
    def test_penalty_scales_with_actions(self):
        code = dice.DiceCode(dice=6, pips=1)
        self.assertEqual(dice.apply_multiple_actions(code, 1), code)
        self.assertEqual(dice.apply_multiple_actions(code, 2), dice.DiceCode(dice=5, pips=1))
        self.assertEqual(dice.apply_multiple_actions(code, 4), dice.DiceCode(dice=3, pips=1))

    def test_too_many_actions_raises(self):
        code = dice.DiceCode(dice=2, pips=0)
        with self.assertRaises(ValueError):
            dice.apply_multiple_actions(code, 3)

    def test_zero_actions_raises(self):
        code = dice.DiceCode(dice=4, pips=0)
        with self.assertRaises(ValueError):
            dice.apply_multiple_actions(code, 0)


class TestCharacterPointDice(unittest.TestCase):
    def test_stacks_and_explodes(self):
        rng = SequenceRandom([
            3, 5, 2, 4,   # bas: regular 3,5,2 ; wild 4 (ingen explosion)
            6, 4,         # första CP-tärningen: exploderar 6 -> 4
            2,            # andra CP-tärningen: vanlig 2:a
        ])
        result = dice.roll(dice.DiceCode(dice=4, pips=0), rng=rng)
        base_total = result.total
        self.assertEqual(base_total, 3 + 5 + 2 + 4)

        result = dice.add_character_point_die(result, rng=rng)
        self.assertEqual(result.cp_dice[0].rolls, [6, 4])
        self.assertEqual(result.cp_dice[0].total, 10)
        self.assertEqual(result.total, base_total + 10)

        result = dice.add_character_point_die(result, rng=rng)
        self.assertEqual(result.cp_dice[1].rolls, [2])
        self.assertEqual(result.total, base_total + 10 + 2)

    def test_cp_die_one_has_no_special_rule(self):
        rng = SequenceRandom([3, 5, 2, 4, 1])
        result = dice.roll(dice.DiceCode(dice=4, pips=0), rng=rng)
        result = dice.add_character_point_die(result, rng=rng)

        self.assertEqual(result.cp_dice[0].rolls, [1])
        self.assertEqual(result.cp_dice[0].total, 1)
        self.assertEqual(result.total, 3 + 5 + 2 + 4 + 1)

    def test_wild_and_cp_explode_independently(self):
        rng = SequenceRandom([
            3, 5, 2,      # regular
            6, 3,         # wild exploderar: 6 -> 3 (=9)
            6, 6, 2,      # CP-tärning exploderar två gånger: 6 -> 6 -> 2 (=14)
        ])
        result = dice.roll(dice.DiceCode(dice=4, pips=0), rng=rng)
        self.assertEqual(result.wild.total, 9)

        result = dice.add_character_point_die(result, rng=rng)
        self.assertEqual(result.cp_dice[0].total, 14)
        self.assertEqual(result.total, 3 + 5 + 2 + 9 + 14)


class TestDifficultyBand(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(dice.difficulty_band(1), "Very Easy")
        self.assertEqual(dice.difficulty_band(5), "Very Easy")
        self.assertEqual(dice.difficulty_band(6), "Easy")
        self.assertEqual(dice.difficulty_band(10), "Easy")
        self.assertEqual(dice.difficulty_band(11), "Moderate")
        self.assertEqual(dice.difficulty_band(15), "Moderate")
        self.assertEqual(dice.difficulty_band(16), "Difficult")
        self.assertEqual(dice.difficulty_band(20), "Difficult")
        self.assertEqual(dice.difficulty_band(21), "Very Difficult")
        self.assertEqual(dice.difficulty_band(30), "Very Difficult")
        self.assertEqual(dice.difficulty_band(31), "Heroic")
        self.assertEqual(dice.difficulty_band(500), "Heroic")


class TestOpposed(unittest.TestCase):
    def test_highest_wins(self):
        rng = SequenceRandom([5, 4, 3, 2])  # initiator 9, defender 5
        result = dice.opposed(dice.DiceCode(dice=2), dice.DiceCode(dice=2), rng=rng)
        self.assertEqual(result.winner, "initiator")
        self.assertFalse(result.tie)

    def test_tie_goes_to_initiator(self):
        rng = SequenceRandom([5, 4, 5, 4])  # båda 9
        result = dice.opposed(dice.DiceCode(dice=2), dice.DiceCode(dice=2), rng=rng)
        self.assertEqual(result.winner, "initiator")
        self.assertTrue(result.tie)

    def test_defender_can_win(self):
        rng = SequenceRandom([2, 2, 5, 4])  # initiator 4, defender 9
        result = dice.opposed(dice.DiceCode(dice=2), dice.DiceCode(dice=2), rng=rng)
        self.assertEqual(result.winner, "defender")
        self.assertFalse(result.tie)


if __name__ == '__main__':
    unittest.main()
