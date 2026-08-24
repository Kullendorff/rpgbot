"""
Registreringstest för EON-kommandona — src/eon/commands.py.

Bygger EonCommands offline (ingen Discord-uppkoppling, temporär
databas — ALDRIG data/rolls.db) och verifierar att kommandonamnen
är exakt de sex eon_*-namnen efter modulariseringen och namnbytet.

Kör som skript: python tests/test_eon_commands_registration.py
(ALDRIG python -m unittest — känd tests-paketkrock, se CLAUDE.md.)
"""

import asyncio
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import discord
from discord.ext import commands as dc

from color_handler import ColorHandler
from roll_tracker import RollTracker
from core.embed_factory import EmbedFactory
from eon import CombatManager
from eon.commands import EonCommands

FÖRVÄNTAT = {"eon_hugg", "eon_stick", "eon_kross", "eon_fummel",
             "eon_regel", "eon_hoj"}


class TestEonRegistrering(unittest.TestCase):
    """EonCommands exponerar exakt de sex eon_*-kommandona."""

    def test_kommandonamn(self):
        async def bygg():
            bot = dc.Bot(command_prefix="!", intents=discord.Intents.default())
            ch = ColorHandler()
            ef = EmbedFactory(ch)
            rt = RollTracker(db_path=os.path.join(tempfile.mkdtemp(), "t.db"))
            return EonCommands(bot, CombatManager(), rt, ch, ef)

        cog = asyncio.run(bygg())
        namn = {c.name for c in cog.get_app_commands()}
        self.assertEqual(namn, FÖRVÄNTAT)

    def test_antal_kommandon(self):
        async def bygg():
            bot = dc.Bot(command_prefix="!", intents=discord.Intents.default())
            ch = ColorHandler()
            ef = EmbedFactory(ch)
            rt = RollTracker(db_path=os.path.join(tempfile.mkdtemp(), "t.db"))
            return EonCommands(bot, CombatManager(), rt, ch, ef)

        cog = asyncio.run(bygg())
        self.assertEqual(len(cog.get_app_commands()), 6)


if __name__ == '__main__':
    unittest.main()
