"""
Integration tests for the end-to-end "Projecting Onto a Bond" flow.

These tests bypass Discord by invoking the three layers in the same order
as the /dgproject command: SanCheckCache read → project_onto_bond() →
AgentManager mutations. The goal is to catch glue bugs where the
individual units pass their own tests but their composition breaks
invariants (WP/SAN/Bond net-effect, unconscious flag, cache consumption,
breaking-point interaction, etc.).
"""

import os
import sys
import shutil
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.deltagreen.agent_manager import AgentManager
from src.deltagreen.san_check_cache import SanCheckCache
from src.deltagreen.dice_functions import project_onto_bond


def _make_agent(wp=10, san=50, bp=30, bonds=None):
    return {
        "owner_id": "u1",
        "callsign": "Trench",
        "name": "Test",
        "stats": {},
        "derived": {
            "hp": {"current": 11, "max": 11},
            "wp": {"current": wp, "max": 10},
            "san": {"current": san, "max": 99},
            "breaking_point": bp,
        },
        "skills": {},
        "bonds": bonds if bonds is not None else [
            {"name": "Sandra", "relation": "Daughter", "value": 8},
            {"name": "Mike",   "relation": "Partner",  "value": 6},
        ],
    }


def _apply_projection(agent_mgr, cache, user_id, bond_name, d4_override=None):
    """
    Replikerar glue-logiken i /dgproject för testbarhet.

    Returnerar (projection, bond_modify_result, san_refund).
    """
    entry = cache.get_fresh(user_id)
    assert entry is not None, "test setup error: no fresh cache entry"

    agent = agent_mgr.get_agent(user_id)
    wp_before = agent['derived']['wp']['current']

    # Hitta bond
    bond_val = next(b['value'] for b in agent['bonds'] if b['name'] == bond_name)

    # Kör projektion (ev. tvinga D4)
    if d4_override is not None:
        with patch('src.deltagreen.dice_functions.random.randint', return_value=d4_override):
            proj = project_onto_bond(wp_before, entry.san_loss, bond_val)
    else:
        proj = project_onto_bond(wp_before, entry.san_loss, bond_val)

    # Applicera state
    agent_mgr.modify_wp(user_id, -proj.d4_roll)

    bond_result = None
    san_refund = 0
    if proj.projection_succeeded:
        san_refund = entry.san_loss - proj.san_loss_reduced
        if san_refund > 0:
            agent_mgr.modify_san(user_id, san_refund)
        bond_result = agent_mgr.modify_bond(user_id, bond_name, -proj.d4_roll)

    cache.mark_consumed(user_id)
    return proj, bond_result, san_refund


class TestProjectingFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="dg_project_flow_")
        self.mgr = AgentManager(data_dir=self.tmp)
        self.cache = SanCheckCache(ttl_seconds=900)
        self.user_id = "u1"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # --- Happy path: TI avoided ---

    def test_successful_projection_avoids_ti(self):
        """Lost 6 SAN, D4=3 → net loss 3, WP -3, Bond -3, TI avoided."""
        self.mgr.create_agent(self.user_id, _make_agent(wp=10, san=44))
        # Simulate /dgsan having just logged a 6-SAN loss
        self.cache.record(self.user_id, san_loss=6, san_before=50, san_after=44, ti_triggered=True)

        proj, bond_result, refund = _apply_projection(
            self.mgr, self.cache, self.user_id, "Sandra", d4_override=3
        )

        self.assertTrue(proj.projection_succeeded)
        self.assertTrue(proj.ti_avoided)
        self.assertEqual(proj.san_loss_reduced, 3)
        self.assertEqual(refund, 3)

        agent = self.mgr.get_agent(self.user_id)
        self.assertEqual(agent['derived']['wp']['current'], 7)
        self.assertEqual(agent['derived']['san']['current'], 47)   # 44 + 3 refund
        self.assertFalse(agent['conditions']['unconscious'])
        sandra = next(b for b in agent['bonds'] if b['name'] == "Sandra")
        self.assertEqual(sandra['value'], 5)   # 8 - 3
        self.assertFalse(sandra['broken'])

    # --- Failure: WP drained ---

    def test_failed_projection_knocks_unconscious(self):
        """Lost 6 SAN, WP=3, D4=4 → projection fails, agent unconscious."""
        self.mgr.create_agent(self.user_id, _make_agent(wp=3, san=44))
        self.cache.record(self.user_id, san_loss=6, san_before=50, san_after=44)

        proj, bond_result, refund = _apply_projection(
            self.mgr, self.cache, self.user_id, "Sandra", d4_override=4
        )

        self.assertFalse(proj.projection_succeeded)
        self.assertTrue(proj.unconscious)
        self.assertEqual(refund, 0)
        self.assertIsNone(bond_result)

        agent = self.mgr.get_agent(self.user_id)
        self.assertEqual(agent['derived']['wp']['current'], 0)
        self.assertEqual(agent['derived']['san']['current'], 44)   # unchanged
        self.assertTrue(agent['conditions']['unconscious'])
        sandra = next(b for b in agent['bonds'] if b['name'] == "Sandra")
        self.assertEqual(sandra['value'], 8)   # unchanged
        self.assertFalse(sandra['broken'])

    # --- Bond broken ---

    def test_projection_breaks_bond(self):
        self.mgr.create_agent(self.user_id, _make_agent(
            wp=10, san=44,
            bonds=[{"name": "Fragile", "relation": "x", "value": 2}],
        ))
        self.cache.record(self.user_id, san_loss=5, san_before=50, san_after=45)

        proj, bond_result, _ = _apply_projection(
            self.mgr, self.cache, self.user_id, "Fragile", d4_override=4
        )

        self.assertTrue(proj.projection_succeeded)
        self.assertEqual(proj.bond_after, 0)
        self.assertTrue(proj.bond_broken)
        self.assertTrue(bond_result.just_broke)

        agent = self.mgr.get_agent(self.user_id)
        fragile = agent['bonds'][0]
        self.assertEqual(fragile['value'], 0)
        self.assertTrue(fragile['broken'])

    # --- Cache consumption ---

    def test_cache_consumed_after_projection(self):
        self.mgr.create_agent(self.user_id, _make_agent(wp=10, san=44))
        self.cache.record(self.user_id, san_loss=3, san_before=47, san_after=44)

        _apply_projection(self.mgr, self.cache, self.user_id, "Sandra", d4_override=2)

        # Cache ska vara förbrukad — inga dubbla projektioner
        self.assertIsNone(self.cache.get_fresh(self.user_id))

    # --- Breaking point interaction ---

    def test_projection_does_not_un_trigger_breaking_point(self):
        """
        Om /dgsan redan triggade breaking point så ska en refund inte magiskt
        "avbryta" den störningen. Refund höjer bara SAN-värdet; BP-flaggan är
        narrativ och hanteras av SL separat.
        """
        self.mgr.create_agent(self.user_id, _make_agent(wp=10, san=28, bp=30))
        # Simulera att /dgsan just dragit 4 och tog SAN från 32 → 28 (under BP=30)
        self.cache.record(self.user_id, san_loss=4, san_before=32, san_after=28)

        proj, _, refund = _apply_projection(
            self.mgr, self.cache, self.user_id, "Sandra", d4_override=3
        )

        self.assertTrue(proj.projection_succeeded)
        self.assertEqual(refund, 3)

        agent = self.mgr.get_agent(self.user_id)
        # SAN är nu 31 — över BP — men Handbooken säger att en utlöst BP kvarstår.
        # Boten mekaniserar inte "avreagera BP" automatiskt, så vi testar bara
        # att SAN-värdet är korrekt återställt. (Breaking-point-flaggan är
        # narrativ, inte fältbaserad, i nuvarande datamodell.)
        self.assertEqual(agent['derived']['san']['current'], 31)


if __name__ == '__main__':
    unittest.main()
