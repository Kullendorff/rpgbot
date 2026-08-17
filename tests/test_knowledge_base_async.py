"""
Tester för KnowledgeBase.ensure_ready() — den icke-blockerande, race-säkra
varianten av initialize_knowledge_base() (src/core/knowledge_base.py).

Bakgrund: initialize_knowledge_base() var tidigare synkron och anropades
direkt i on_ready(), vilket blockerade botens event-loop i ~6 sekunder vid
varje omstart och gjorde att interaktioner som kom in under tiden dog med
"404 Unknown Interaction". ensure_ready() kör samma laddning via
asyncio.to_thread bakom ett asyncio.Lock. Dessa tester bevisar låsbeteendet
och att event-loopen faktiskt förblir responsiv under laddningen — utan
riktiga API-nycklar eller att faktiskt ladda en SentenceTransformer-modell.
"""

import os
import sys
import time
import asyncio
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.knowledge_base import KnowledgeBase


class FakeKnowledgeBase(KnowledgeBase):
    """
    Ersätter den tunga, blockerande initialize_knowledge_base() med en kort
    time.sleep + räknare, så vi kan testa ensure_ready()'s lås- och
    trådbeteende isolerat.
    """

    def __init__(self, sleep_seconds: float = 0.2, should_succeed: bool = True):
        super().__init__()
        self.sleep_seconds = sleep_seconds
        self.should_succeed = should_succeed
        self.call_count = 0

    def initialize_knowledge_base(self) -> bool:
        self.call_count += 1
        time.sleep(self.sleep_seconds)
        if self.should_succeed:
            self.pc = object()
            self.embedding_model = object()
            self.claude_client = object()
        return self.should_succeed


class TestEnsureReady(unittest.IsolatedAsyncioTestCase):
    async def test_skips_when_already_ready(self):
        kb = FakeKnowledgeBase()
        kb.pc = object()
        kb.embedding_model = object()
        kb.claude_client = object()

        result = await kb.ensure_ready()

        self.assertTrue(result)
        self.assertEqual(kb.call_count, 0)

    async def test_loads_once_when_not_ready(self):
        kb = FakeKnowledgeBase(sleep_seconds=0.1)

        result = await kb.ensure_ready()

        self.assertTrue(result)
        self.assertEqual(kb.call_count, 1)
        self.assertTrue(kb.is_ready)

    async def test_concurrent_calls_load_only_once(self):
        # Simulerar racet mellan bakgrundsjobbet i on_ready och ett
        # kommando (t.ex. /ask) som triggar ensure_ready() samtidigt.
        kb = FakeKnowledgeBase(sleep_seconds=0.2)

        results = await asyncio.gather(
            kb.ensure_ready(), kb.ensure_ready(), kb.ensure_ready(),
        )

        self.assertTrue(all(results))
        self.assertEqual(kb.call_count, 1, "flera samtidiga anrop laddade mer än en gång")

    async def test_failure_is_reported_and_can_retry(self):
        kb = FakeKnowledgeBase(sleep_seconds=0.05, should_succeed=False)

        result = await kb.ensure_ready()
        self.assertFalse(result)
        self.assertEqual(kb.call_count, 1)
        self.assertFalse(kb.is_ready)

        # "Fixa API-nyckeln" och försök igen — ska ladda på nytt, inte
        # fastna permanent efter ett första misslyckande.
        kb.should_succeed = True
        result2 = await kb.ensure_ready()
        self.assertTrue(result2)
        self.assertEqual(kb.call_count, 2)

    async def test_event_loop_is_not_blocked_during_load(self):
        """
        Bevisar själva poängen med fixen: medan ensure_ready() väntar på
        asyncio.to_thread (som kör en blockerande time.sleep i en annan
        tråd), ska en oberoende coroutine fortsätta tick:a på loopen. Med
        det gamla synkrona anropet hade räknaren stått helt still tills
        laddningen var klar.
        """
        kb = FakeKnowledgeBase(sleep_seconds=0.3)
        ticks = 0
        stop = False

        async def ticker():
            nonlocal ticks
            while not stop:
                ticks += 1
                await asyncio.sleep(0.01)

        ticker_task = asyncio.create_task(ticker())
        await kb.ensure_ready()
        stop = True
        await ticker_task

        # ~0.3s laddning / 0.01s tick-intervall borde ge minst ~10 tick.
        self.assertGreater(ticks, 5, "event-loopen verkar ha blockerats under laddningen")


if __name__ == '__main__':
    unittest.main()
