"""
Unit tests for SanCheckCache.
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.deltagreen.san_check_cache import SanCheckCache, SanCheckEntry


class TestSanCheckCache(unittest.TestCase):
    def setUp(self):
        # Short TTL for tests so expiry is verifiable
        self.cache = SanCheckCache(ttl_seconds=1)

    def test_record_and_get_fresh(self):
        self.cache.record("u1", san_loss=3, san_before=50, san_after=47)
        entry = self.cache.get_fresh("u1")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.san_loss, 3)
        self.assertEqual(entry.san_before, 50)
        self.assertEqual(entry.san_after, 47)
        self.assertFalse(entry.consumed)

    def test_missing_user_returns_none(self):
        self.assertIsNone(self.cache.get_fresh("ghost"))

    def test_expired_entry_returns_none(self):
        self.cache.record("u1", san_loss=3, san_before=50, san_after=47)
        time.sleep(1.1)
        self.assertIsNone(self.cache.get_fresh("u1"))

    def test_overwrite_replaces_entry(self):
        self.cache.record("u1", san_loss=3, san_before=50, san_after=47)
        self.cache.record("u1", san_loss=5, san_before=47, san_after=42)
        entry = self.cache.get_fresh("u1")
        self.assertEqual(entry.san_loss, 5)
        self.assertEqual(entry.san_before, 47)

    def test_mark_consumed_hides_entry(self):
        self.cache.record("u1", san_loss=3, san_before=50, san_after=47)
        self.assertTrue(self.cache.mark_consumed("u1"))
        self.assertIsNone(self.cache.get_fresh("u1"))

    def test_mark_consumed_twice_is_idempotent_but_returns_false_second(self):
        self.cache.record("u1", san_loss=3, san_before=50, san_after=47)
        self.assertTrue(self.cache.mark_consumed("u1"))
        self.assertFalse(self.cache.mark_consumed("u1"))

    def test_clear_single_user(self):
        self.cache.record("u1", 3, 50, 47)
        self.cache.record("u2", 4, 60, 56)
        self.cache.clear("u1")
        self.assertIsNone(self.cache.get_fresh("u1"))
        self.assertIsNotNone(self.cache.get_fresh("u2"))

    def test_clear_all(self):
        self.cache.record("u1", 3, 50, 47)
        self.cache.record("u2", 4, 60, 56)
        self.cache.clear()
        self.assertIsNone(self.cache.get_fresh("u1"))
        self.assertIsNone(self.cache.get_fresh("u2"))

    def test_ti_triggered_preserved(self):
        self.cache.record("u1", 6, 50, 44, ti_triggered=True)
        entry = self.cache.get_fresh("u1")
        self.assertTrue(entry.ti_triggered)


if __name__ == '__main__':
    unittest.main()
