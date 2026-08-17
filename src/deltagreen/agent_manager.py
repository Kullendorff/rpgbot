"""
Delta Green Agent Manager.

Manages agent data with per-user ownership and JSON persistence.
"""

import json
import os
import logging
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime
from difflib import get_close_matches
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BondModifyResult:
    """Result of modifying a Bond's value."""
    bond_name: str
    old_value: int
    new_value: int
    broken: bool               # True iff bond just hit 0 (or was already 0 and stays)
    just_broke: bool           # True iff this change broke it (old > 0, new == 0)


class AgentManager:
    """Manages Delta Green agent data with per-user ownership."""

    def __init__(self, data_dir: str = "data/deltagreen/agents"):
        self.data_dir = data_dir
        self._ensure_data_dir()
        self.cache: Dict[str, Dict] = {}  # user_id -> agent data

    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
        logger.info(f"Agent data directory: {self.data_dir}")

    def _get_agent_path(self, user_id: str) -> str:
        """Get file path for user's agent."""
        return os.path.join(self.data_dir, f"{user_id}.json")

    @staticmethod
    def _ensure_defaults(agent: Dict) -> Dict:
        """
        Lazy-inject newer fields into legacy agent dicts.

        Mutates `agent` in place and returns it. Safe to call on already-migrated
        agents. Called from `get_agent()` so both cached and freshly-loaded
        agents get consistent shape.

        Injects:
          - conditions.unconscious = False      (root)
          - bond['broken']         = False      (on every bond)
        """
        # Root-level conditions block
        if 'conditions' not in agent or not isinstance(agent.get('conditions'), dict):
            agent['conditions'] = {}
        agent['conditions'].setdefault('unconscious', False)

        # Per-bond 'broken' flag
        bonds = agent.get('bonds')
        if isinstance(bonds, list):
            for b in bonds:
                if isinstance(b, dict):
                    b.setdefault('broken', False)

        return agent

    def get_agent(self, user_id: str) -> Optional[Dict]:
        """
        Get agent for user.

        Args:
            user_id: Discord user ID

        Returns:
            Agent data dict, or None if no agent exists
        """
        user_id = str(user_id)

        # Check cache first
        if user_id in self.cache:
            return self._ensure_defaults(self.cache[user_id])

        # Load from disk
        path = self._get_agent_path(user_id)
        if not os.path.exists(path):
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                agent = json.load(f)
                self._ensure_defaults(agent)
                self.cache[user_id] = agent
                logger.debug(f"Loaded agent for {user_id}: {agent.get('callsign')}")
                return agent
        except Exception as e:
            logger.error(f"Failed to load agent for {user_id}: {e}")
            return None

    def save_agent(self, user_id: str, agent: Dict) -> bool:
        """
        Save agent data to disk.

        Args:
            user_id: Discord user ID
            agent: Agent data dict

        Returns:
            True if successful
        """
        user_id = str(user_id)

        try:
            # Update timestamps
            agent['last_updated'] = datetime.utcnow().isoformat()
            if 'created_at' not in agent:
                agent['created_at'] = agent['last_updated']

            # Ensure owner_id matches
            agent['owner_id'] = user_id

            # Write to disk
            path = self._get_agent_path(user_id)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(agent, f, indent=2, ensure_ascii=False)

            # Update cache
            self.cache[user_id] = agent
            logger.info(f"Saved agent for {user_id}: {agent.get('callsign')}")
            return True

        except Exception as e:
            logger.error(f"Failed to save agent for {user_id}: {e}")
            return False

    def create_agent(self, user_id: str, agent_data: Dict) -> bool:
        """
        Create new agent for user.

        Args:
            user_id: Discord user ID
            agent_data: Initial agent data

        Returns:
            True if successful
        """
        user_id = str(user_id)

        # Check if agent already exists
        if self.get_agent(user_id):
            logger.warning(f"Agent already exists for {user_id}")
            return False

        return self.save_agent(user_id, agent_data)

    def delete_agent(self, user_id: str) -> bool:
        """
        Delete user's agent.

        Args:
            user_id: Discord user ID

        Returns:
            True if successful
        """
        user_id = str(user_id)

        try:
            path = self._get_agent_path(user_id)
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Deleted agent for {user_id}")

            # Remove from cache
            if user_id in self.cache:
                del self.cache[user_id]

            return True

        except Exception as e:
            logger.error(f"Failed to delete agent for {user_id}: {e}")
            return False

    def get_skill_value(self, user_id: str, skill_name: str) -> Optional[int]:
        """
        Get skill value with fuzzy matching.

        Args:
            user_id: Discord user ID
            skill_name: Skill name (fuzzy matched)

        Returns:
            Skill value (0-99), or None if not found
        """
        agent = self.get_agent(str(user_id))
        if not agent:
            return None

        skills = agent.get('skills', {})

        # Exact match first
        if skill_name in skills:
            return skills[skill_name]

        # Fuzzy match
        matches = get_close_matches(skill_name, skills.keys(), n=1, cutoff=0.6)
        if matches:
            matched_skill = matches[0]
            logger.debug(f"Fuzzy matched '{skill_name}' to '{matched_skill}'")
            return skills[matched_skill]

        return None

    def set_skill_value(self, user_id: str, skill_name: str, value: int) -> bool:
        """
        Set a skill value.

        Args:
            user_id: Discord user ID
            skill_name: Skill name
            value: New skill value (0-99)

        Returns:
            True if successful
        """
        agent = self.get_agent(str(user_id))
        if not agent:
            return False

        agent['skills'][skill_name] = max(0, min(99, value))
        return self.save_agent(user_id, agent)

    def modify_hp(self, user_id: str, delta: int) -> Optional[Tuple[int, int]]:
        """
        Modify HP by delta.

        Args:
            user_id: Discord user ID
            delta: Amount to change (negative for damage)

        Returns:
            Tuple of (old_hp, new_hp), or None if failed
        """
        agent = self.get_agent(str(user_id))
        if not agent:
            return None

        old_hp = agent['derived']['hp']['current']
        max_hp = agent['derived']['hp']['max']
        new_hp = max(0, min(max_hp, old_hp + delta))

        agent['derived']['hp']['current'] = new_hp
        self.save_agent(user_id, agent)

        logger.info(f"Agent {agent['callsign']} HP: {old_hp} -> {new_hp}")
        return (old_hp, new_hp)

    def set_hp(self, user_id: str, hp: int) -> Optional[Tuple[int, int]]:
        """
        Set HP to a specific value.

        Args:
            user_id: Discord user ID
            hp: New HP value

        Returns:
            Tuple of (old_hp, new_hp), or None if failed
        """
        agent = self.get_agent(str(user_id))
        if not agent:
            return None

        old_hp = agent['derived']['hp']['current']
        max_hp = agent['derived']['hp']['max']
        new_hp = max(0, min(max_hp, hp))

        agent['derived']['hp']['current'] = new_hp
        self.save_agent(user_id, agent)

        logger.info(f"Agent {agent['callsign']} HP set: {old_hp} -> {new_hp}")
        return (old_hp, new_hp)

    def modify_wp(self, user_id: str, delta: int) -> Optional[Tuple[int, int]]:
        """
        Modify WP by delta.

        Globally enforces the "WP 0 = unconscious" rule: whenever WP hits 0
        from any source (projection cost, exertion, GM override), the agent's
        conditions.unconscious flag is set to True. WP rising above 0 does
        NOT auto-clear the flag — waking up is its own narrative beat.

        Args:
            user_id: Discord user ID
            delta: Amount to change

        Returns:
            Tuple of (old_wp, new_wp), or None if failed
        """
        agent = self.get_agent(str(user_id))
        if not agent:
            return None

        old_wp = agent['derived']['wp']['current']
        max_wp = agent['derived']['wp']['max']
        new_wp = max(0, min(max_wp, old_wp + delta))

        agent['derived']['wp']['current'] = new_wp

        # Global unconscious trigger
        if new_wp <= 0:
            agent.setdefault('conditions', {})['unconscious'] = True
            logger.info(f"Agent {agent['callsign']} is now UNCONSCIOUS (WP=0)")

        self.save_agent(user_id, agent)

        logger.info(f"Agent {agent['callsign']} WP: {old_wp} -> {new_wp}")
        return (old_wp, new_wp)

    def modify_san(self, user_id: str, delta: int) -> Optional[Tuple[int, int, bool]]:
        """
        Modify SAN by delta.

        Args:
            user_id: Discord user ID
            delta: Amount to change (negative for loss)

        Returns:
            Tuple of (old_san, new_san, hit_breaking_point), or None if failed
        """
        agent = self.get_agent(str(user_id))
        if not agent:
            return None

        old_san = agent['derived']['san']['current']
        max_san = agent['derived']['san']['max']
        breaking_point = agent['derived']['breaking_point']

        new_san = max(0, min(max_san, old_san + delta))
        hit_breaking_point = new_san <= breaking_point and old_san > breaking_point

        agent['derived']['san']['current'] = new_san
        self.save_agent(user_id, agent)

        logger.info(f"Agent {agent['callsign']} SAN: {old_san} -> {new_san} (BP: {breaking_point})")
        return (old_san, new_san, hit_breaking_point)

    # ------------------------------------------------------------------
    # Bonds
    # ------------------------------------------------------------------

    def _find_bond(self, agent: Dict, bond_name: str) -> Optional[Dict]:
        """
        Locate a bond on an agent by name. Exact match first, then fuzzy.

        Returns the bond dict itself (mutating the return value mutates the
        agent) or None if no reasonable match.
        """
        bonds = agent.get('bonds')
        if not isinstance(bonds, list):
            return None

        # Exact (case-insensitive) match
        lc = bond_name.lower()
        for b in bonds:
            if isinstance(b, dict) and b.get('name', '').lower() == lc:
                return b

        # Fuzzy match on name field
        names = [b.get('name', '') for b in bonds if isinstance(b, dict)]
        matches = get_close_matches(bond_name, names, n=1, cutoff=0.6)
        if matches:
            matched = matches[0]
            for b in bonds:
                if isinstance(b, dict) and b.get('name') == matched:
                    logger.debug(f"Fuzzy matched bond '{bond_name}' to '{matched}'")
                    return b

        return None

    def get_active_bonds(self, user_id: str) -> List[Dict]:
        """
        Return all non-broken bonds for autocomplete / selection.

        Args:
            user_id: Discord user ID

        Returns:
            List of bond dicts with `broken == False` and `value > 0`.
            Empty list if agent/bonds missing.
        """
        agent = self.get_agent(str(user_id))
        if not agent:
            return []

        bonds = agent.get('bonds')
        if not isinstance(bonds, list):
            return []

        return [
            b for b in bonds
            if isinstance(b, dict)
            and not b.get('broken', False)
            and b.get('value', 0) > 0
        ]

    def modify_bond(
        self,
        user_id: str,
        bond_name: str,
        delta: int,
    ) -> Optional[BondModifyResult]:
        """
        Adjust a bond's value (use a negative delta to reduce it).

        Clamps at 0. Sets `broken = True` and persists it the moment the
        bond's value reaches 0. Once broken, it stays broken (per DG RAW).

        Args:
            user_id: Discord user ID
            bond_name: Bond name (exact or fuzzy)
            delta: Amount to add to value (usually negative)

        Returns:
            BondModifyResult, or None if agent/bond not found.
        """
        agent = self.get_agent(str(user_id))
        if not agent:
            return None

        bond = self._find_bond(agent, bond_name)
        if bond is None:
            logger.warning(f"Bond '{bond_name}' not found on agent {user_id}")
            return None

        old_value = int(bond.get('value', 0))
        new_value = max(0, old_value + delta)
        already_broken = bool(bond.get('broken', False)) or old_value == 0

        bond['value'] = new_value
        if new_value == 0:
            bond['broken'] = True

        just_broke = new_value == 0 and old_value > 0 and not already_broken
        broken = bool(bond.get('broken', False))

        self.save_agent(user_id, agent)

        logger.info(
            f"Agent {agent.get('callsign')} Bond '{bond.get('name')}': "
            f"{old_value} -> {new_value} (broken={broken}, just_broke={just_broke})"
        )

        return BondModifyResult(
            bond_name=bond.get('name', bond_name),
            old_value=old_value,
            new_value=new_value,
            broken=broken,
            just_broke=just_broke,
        )

    # ------------------------------------------------------------------
    # Conditions
    # ------------------------------------------------------------------

    def set_condition(self, user_id: str, key: str, value: Any) -> bool:
        """
        Set a value in the agent's `conditions` block.

        Generic helper so future state flags (unconscious, disoriented,
        in_shock, ...) don't each need their own mutator.

        Args:
            user_id: Discord user ID
            key: Condition key (e.g. 'unconscious')
            value: New value (typically bool)

        Returns:
            True on success, False if agent not found.
        """
        agent = self.get_agent(str(user_id))
        if not agent:
            return False

        conditions = agent.setdefault('conditions', {})
        conditions[key] = value
        self.save_agent(user_id, agent)
        logger.info(f"Agent {agent.get('callsign')} condition '{key}' set to {value}")
        return True

    def list_all_agents(self) -> List[Tuple[str, str]]:
        """
        List all agents (for GM).

        Returns:
            List of (user_id, callsign) tuples
        """
        agents = []
        try:
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    user_id = filename[:-5]  # Remove .json
                    agent = self.get_agent(user_id)
                    if agent:
                        agents.append((user_id, agent.get('callsign', 'Unknown')))
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")

        return agents

    def get_all_skills(self, user_id: str) -> List[str]:
        """
        Get list of all skill names for autocomplete.

        Args:
            user_id: Discord user ID

        Returns:
            List of skill names
        """
        agent = self.get_agent(str(user_id))
        if not agent:
            return []

        return list(agent.get('skills', {}).keys())
