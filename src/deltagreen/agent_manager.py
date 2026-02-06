"""
Delta Green Agent Manager.

Manages agent data with per-user ownership and JSON persistence.
"""

import json
import os
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from difflib import get_close_matches

logger = logging.getLogger(__name__)


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
            return self.cache[user_id]

        # Load from disk
        path = self._get_agent_path(user_id)
        if not os.path.exists(path):
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                agent = json.load(f)
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
