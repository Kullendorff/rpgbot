"""
In-memory TTL cache för senast utförda SAN-check per agent.

Används av /dgsan (skriver) och /dgproject (läser) så att spelaren kan
"projicera" på en Bond inom ett tidsfönster utan att behöva ange förlusten
manuellt igen. Detta är RAM-endast — omstart nollställer. Det är avsiktligt:
projection är en snabb, narrativ reaktion, inte en flerveckors bokföring.
"""

import time
import logging
import threading
from dataclasses import dataclass
from typing import Optional, Dict

logger = logging.getLogger(__name__)


@dataclass
class SanCheckEntry:
    """En färsk SAN-check som kandidat för projection."""
    user_id: str
    san_loss: int              # Faktisk förlust i senaste SAN-check
    san_before: int            # SAN innan förlusten (för rollback-beräkningar)
    san_after: int             # SAN efter förlusten
    timestamp: float           # Unix-tidsstämpel
    channel_id: Optional[str] = None
    ti_triggered: bool = False
    consumed: bool = False     # True efter lyckad projection, hindrar dubbel-användning


class SanCheckCache:
    """
    Enkel per-user TTL-cache för senaste SAN-förlusten.

    En användare har högst en aktiv post åt gången — nya SAN-check skriver
    över äldre oavsett om de var consumed eller inte. `ttl_seconds` styr
    hur länge en post är kandidat för projection (default 15 min).

    Thread-safe via en intern lock, även om Discord.py-eventloopen gör
    racing osannolik.
    """

    def __init__(self, ttl_seconds: int = 900):
        self.ttl_seconds = ttl_seconds
        self._entries: Dict[str, SanCheckEntry] = {}
        self._lock = threading.Lock()

    # --- write ---

    def record(
        self,
        user_id: str,
        san_loss: int,
        san_before: int,
        san_after: int,
        channel_id: Optional[str] = None,
        ti_triggered: bool = False,
    ) -> SanCheckEntry:
        """Spara en färsk SAN-check. Skriver över tidigare post för samma användare."""
        entry = SanCheckEntry(
            user_id=str(user_id),
            san_loss=san_loss,
            san_before=san_before,
            san_after=san_after,
            timestamp=time.time(),
            channel_id=str(channel_id) if channel_id else None,
            ti_triggered=ti_triggered,
            consumed=False,
        )
        with self._lock:
            self._entries[str(user_id)] = entry
        logger.debug(
            f"SAN-check cached: {user_id} lost {san_loss} "
            f"({san_before} -> {san_after}, ti={ti_triggered})"
        )
        return entry

    # --- read ---

    def get_fresh(self, user_id: str) -> Optional[SanCheckEntry]:
        """
        Hämta en färsk, icke-förbrukad post för användaren.

        Returnerar None om posten saknas, har gått ut, eller redan är
        förbrukad. Läsaren ska inte mutera returnerad entry — markera
        som consumed via `mark_consumed()`.
        """
        user_id = str(user_id)
        with self._lock:
            entry = self._entries.get(user_id)
            if entry is None:
                return None
            if entry.consumed:
                return None
            if time.time() - entry.timestamp > self.ttl_seconds:
                # Städa bort gammalt
                del self._entries[user_id]
                return None
            return entry

    def mark_consumed(self, user_id: str) -> bool:
        """Markera användarens senaste post som förbrukad. Returnerar True om det fanns något att markera."""
        user_id = str(user_id)
        with self._lock:
            entry = self._entries.get(user_id)
            if entry is None or entry.consumed:
                return False
            entry.consumed = True
            return True

    def clear(self, user_id: Optional[str] = None) -> None:
        """Töm cachen — hela, eller bara en användare."""
        with self._lock:
            if user_id is None:
                self._entries.clear()
            else:
                self._entries.pop(str(user_id), None)
