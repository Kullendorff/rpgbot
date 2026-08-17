"""
Unit tests for the new Delta Green AgentManager helpers:

- _ensure_defaults() — lazy field injection
- modify_wp() — global unconscious trigger at WP 0
- modify_bond() / get_active_bonds() — bond mutation & listing
- set_condition() — generic conditions-block mutator
"""

import os
import sys
import json
import shutil
import tempfile
import unittest

# Allow imports from src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.deltagreen.agent_manager import AgentManager, BondModifyResult


def _make_agent(callsign="Trench", wp_cur=10, wp_max=10, bonds=None):
    """Minimal agent dict matching the live JSON shape."""
    return {
        "owner_id": "user_1",
        "callsign": callsign,
        "name": "Testperson",
        "stats": {},
        "derived": {
            "hp": {"current": 11, "max": 11},
            "wp": {"current": wp_cur, "max": wp_max},
            "san": {"current": 50, "max": 99},
            "breaking_point": 40,
        },
        "skills": {"Firearms": 50},
        "bonds": bonds if bonds is not None else [
            {"name": "Sandra Novak", "relation": "Daughter", "value": 8},
            {"name": "Mike Reiner",  "relation": "Partner",  "value": 6},
        ],
    }


class TestAgentManagerBondsAndConditions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="dg_agent_test_")
        self.mgr = AgentManager(data_dir=self.tmp)
        self.user_id = "user_1"
        self.mgr.create_agent(self.user_id, _make_agent())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # --- _ensure_defaults ---

    def test_ensure_defaults_injects_conditions_and_broken(self):
        agent = self.mgr.get_agent(self.user_id)
        self.assertIn('conditions', agent)
        self.assertEqual(agent['conditions']['unconscious'], False)
        for b in agent['bonds']:
            self.assertIn('broken', b)
            self.assertFalse(b['broken'])

    def test_ensure_defaults_idempotent(self):
        """Calling twice doesn't clobber existing condition state."""
        self.mgr.set_condition(self.user_id, 'unconscious', True)
        agent = self.mgr.get_agent(self.user_id)
        self.assertTrue(agent['conditions']['unconscious'])
        # Simulate another load
        self.mgr.cache.clear()
        agent2 = self.mgr.get_agent(self.user_id)
        self.assertTrue(agent2['conditions']['unconscious'])

    # --- modify_wp global unconscious ---

    def test_modify_wp_sets_unconscious_at_zero(self):
        res = self.mgr.modify_wp(self.user_id, -10)
        self.assertEqual(res, (10, 0))
        agent = self.mgr.get_agent(self.user_id)
        self.assertTrue(agent['conditions']['unconscious'])

    def test_modify_wp_positive_change_does_not_auto_wake(self):
        """Per design: waking up is a narrative beat, not automatic."""
        self.mgr.modify_wp(self.user_id, -10)           # → 0, unconscious
        self.mgr.modify_wp(self.user_id, +3)            # → 3
        agent = self.mgr.get_agent(self.user_id)
        self.assertEqual(agent['derived']['wp']['current'], 3)
        self.assertTrue(agent['conditions']['unconscious'])

    def test_modify_wp_non_zero_does_not_set_unconscious(self):
        self.mgr.modify_wp(self.user_id, -5)
        agent = self.mgr.get_agent(self.user_id)
        self.assertEqual(agent['derived']['wp']['current'], 5)
        self.assertFalse(agent['conditions']['unconscious'])

    # --- modify_bond ---

    def test_modify_bond_reduces_value(self):
        r = self.mgr.modify_bond(self.user_id, "Sandra Novak", -3)
        self.assertIsInstance(r, BondModifyResult)
        self.assertEqual(r.old_value, 8)
        self.assertEqual(r.new_value, 5)
        self.assertFalse(r.broken)
        self.assertFalse(r.just_broke)

    def test_modify_bond_breaks_at_zero(self):
        r = self.mgr.modify_bond(self.user_id, "Sandra Novak", -8)
        self.assertEqual(r.new_value, 0)
        self.assertTrue(r.broken)
        self.assertTrue(r.just_broke)

        # Persisted on disk
        with open(os.path.join(self.tmp, f"{self.user_id}.json"), 'r') as f:
            data = json.load(f)
        sandra = next(b for b in data['bonds'] if b['name'] == "Sandra Novak")
        self.assertTrue(sandra['broken'])
        self.assertEqual(sandra['value'], 0)

    def test_modify_bond_caps_at_zero_not_negative(self):
        r = self.mgr.modify_bond(self.user_id, "Sandra Novak", -100)
        self.assertEqual(r.new_value, 0)
        self.assertTrue(r.broken)

    def test_modify_bond_already_broken_just_broke_false(self):
        self.mgr.modify_bond(self.user_id, "Sandra Novak", -8)  # break it
        r2 = self.mgr.modify_bond(self.user_id, "Sandra Novak", -1)  # re-hit
        self.assertTrue(r2.broken)
        self.assertFalse(r2.just_broke)

    def test_modify_bond_fuzzy_match(self):
        r = self.mgr.modify_bond(self.user_id, "Sandra", -1)
        self.assertIsNotNone(r)
        self.assertEqual(r.bond_name, "Sandra Novak")

    def test_modify_bond_unknown_returns_none(self):
        r = self.mgr.modify_bond(self.user_id, "Nobody", -1)
        self.assertIsNone(r)

    # --- get_active_bonds ---

    def test_get_active_bonds_excludes_broken(self):
        self.mgr.modify_bond(self.user_id, "Sandra Novak", -8)
        active = self.mgr.get_active_bonds(self.user_id)
        names = [b['name'] for b in active]
        self.assertNotIn("Sandra Novak", names)
        self.assertIn("Mike Reiner", names)

    def test_get_active_bonds_empty_for_missing_agent(self):
        self.assertEqual(self.mgr.get_active_bonds("ghost"), [])

    # --- set_condition ---

    def test_set_condition_persists(self):
        self.assertTrue(self.mgr.set_condition(self.user_id, 'unconscious', True))
        self.mgr.cache.clear()
        agent = self.mgr.get_agent(self.user_id)
        self.assertTrue(agent['conditions']['unconscious'])

    def test_set_condition_unknown_agent(self):
        self.assertFalse(self.mgr.set_condition("ghost", 'unconscious', True))


if __name__ == '__main__':
    unittest.main()
