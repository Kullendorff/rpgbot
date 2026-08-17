"""
Unit tests for Delta Green "Projecting Onto a Bond" mechanic.

Tests cover:
- Normal successful projection
- WP-drained failure (unconscious)
- Bond reduced to 0 (broken)
- Temporary insanity avoidance
- All edge cases described in DG Agent's Handbook
"""

import sys
import os
import random
import unittest
from unittest.mock import patch

# Allow imports from src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.deltagreen.dice_functions import project_onto_bond, ProjectionResult


class TestProjectOntoBond(unittest.TestCase):
    """Tests for project_onto_bond()."""

    def _project_with_d4(self, d4_value, wp, san_loss, bond):
        """Helper: force a specific 1D4 value via randint mock."""
        with patch('src.deltagreen.dice_functions.random.randint', return_value=d4_value):
            return project_onto_bond(wp, san_loss, bond)

    # --- Successful projection ---

    def test_basic_success(self):
        """WP plenty, Bond plenty, full reduction applies."""
        r = self._project_with_d4(2, wp=10, san_loss=3, bond=8)
        self.assertTrue(r.projection_succeeded)
        self.assertFalse(r.unconscious)
        self.assertEqual(r.d4_roll, 2)
        self.assertEqual(r.wp_after, 8)
        self.assertEqual(r.san_loss_reduced, 1)
        self.assertEqual(r.bond_after, 6)
        self.assertFalse(r.bond_broken)

    def test_reduction_caps_at_zero_loss(self):
        """If D4 >= SAN loss, loss reduced to 0 (not negative)."""
        r = self._project_with_d4(4, wp=10, san_loss=2, bond=8)
        self.assertTrue(r.projection_succeeded)
        self.assertEqual(r.san_loss_reduced, 0)
        # Bond still takes the full 4 though
        self.assertEqual(r.bond_after, 4)

    def test_exactly_1_wp_remaining_succeeds(self):
        """wp_after == 1 is the boundary — should succeed per RAW."""
        r = self._project_with_d4(3, wp=4, san_loss=5, bond=8)
        self.assertEqual(r.wp_after, 1)
        self.assertTrue(r.projection_succeeded)
        self.assertFalse(r.unconscious)

    # --- Failure / unconscious ---

    def test_wp_drained_fails(self):
        """wp_after == 0 means projection fails AND unconscious."""
        r = self._project_with_d4(4, wp=4, san_loss=5, bond=8)
        self.assertEqual(r.wp_after, 0)
        self.assertFalse(r.projection_succeeded)
        self.assertTrue(r.unconscious)
        # No reduction, no bond damage
        self.assertEqual(r.san_loss_reduced, 5)
        self.assertEqual(r.bond_after, 8)
        self.assertFalse(r.bond_broken)

    def test_d4_exceeds_wp_fails(self):
        """wp_after would be negative, capped at 0, projection fails."""
        r = self._project_with_d4(4, wp=2, san_loss=5, bond=8)
        self.assertEqual(r.wp_after, 0)
        self.assertFalse(r.projection_succeeded)
        self.assertTrue(r.unconscious)

    # --- Bond edge cases ---

    def test_bond_reduced_to_zero_is_broken(self):
        """Bond hitting 0 is permanently broken."""
        r = self._project_with_d4(3, wp=10, san_loss=5, bond=3)
        self.assertTrue(r.projection_succeeded)
        self.assertEqual(r.bond_after, 0)
        self.assertTrue(r.bond_broken)

    def test_bond_exceeded_capped_at_zero_and_broken(self):
        """D4 > Bond value: Bond → 0, broken."""
        r = self._project_with_d4(4, wp=10, san_loss=5, bond=2)
        self.assertTrue(r.projection_succeeded)
        self.assertEqual(r.bond_after, 0)
        self.assertTrue(r.bond_broken)

    def test_bond_not_broken_when_still_positive(self):
        r = self._project_with_d4(1, wp=10, san_loss=3, bond=2)
        self.assertTrue(r.projection_succeeded)
        self.assertEqual(r.bond_after, 1)
        self.assertFalse(r.bond_broken)

    # --- Temporary Insanity interaction ---

    def test_ti_avoided_when_reduced_below_5(self):
        """Original loss 6, D4=2 → reduced to 4, TI avoided."""
        r = self._project_with_d4(2, wp=10, san_loss=6, bond=8)
        self.assertTrue(r.ti_originally_triggered)
        self.assertEqual(r.san_loss_reduced, 4)
        self.assertTrue(r.ti_avoided)

    def test_ti_still_triggers_when_not_reduced_enough(self):
        """Original loss 10, D4=2 → reduced to 8, TI still triggers."""
        r = self._project_with_d4(2, wp=10, san_loss=10, bond=8)
        self.assertTrue(r.ti_originally_triggered)
        self.assertEqual(r.san_loss_reduced, 8)
        self.assertFalse(r.ti_avoided)

    def test_no_ti_originally_no_ti_avoided(self):
        """If original loss < 5, TI was never triggered, never 'avoided'."""
        r = self._project_with_d4(2, wp=10, san_loss=3, bond=8)
        self.assertFalse(r.ti_originally_triggered)
        self.assertFalse(r.ti_avoided)

    def test_ti_not_avoided_on_failure(self):
        """Projection fails → original loss stands → TI stays triggered."""
        r = self._project_with_d4(4, wp=2, san_loss=10, bond=8)
        self.assertFalse(r.projection_succeeded)
        self.assertTrue(r.ti_originally_triggered)
        self.assertFalse(r.ti_avoided)
        self.assertEqual(r.san_loss_reduced, 10)

    # --- D4 range ---

    def test_d4_always_in_range(self):
        """Actual random 1D4 stays within [1, 4] across many rolls."""
        random.seed(42)
        for _ in range(500):
            r = project_onto_bond(current_wp=10, san_loss=5, bond_value=10)
            self.assertGreaterEqual(r.d4_roll, 1)
            self.assertLessEqual(r.d4_roll, 4)

    # --- Dataclass fields present ---

    def test_result_fields(self):
        """Spot-check that all fields are populated (no None/missing)."""
        r = self._project_with_d4(2, wp=5, san_loss=3, bond=5)
        self.assertIsInstance(r, ProjectionResult)
        self.assertEqual(r.wp_before, 5)
        self.assertEqual(r.san_loss_original, 3)
        self.assertEqual(r.bond_before, 5)


if __name__ == '__main__':
    unittest.main()
