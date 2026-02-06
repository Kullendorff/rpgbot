"""
Delta Green Session Manager.

Tracks active sessions and failed skill checks for skill improvement.
Sessions are per-channel, all players in channel are included.
"""

import json
import os
import logging
import random
from typing import Dict, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages Delta Green sessions and skill improvement tracking."""

    def __init__(self, data_dir: str = "data/deltagreen/sessions"):
        self.data_dir = data_dir
        self._ensure_data_dir()
        self.active_sessions: Dict[str, Dict] = {}  # channel_id -> session data
        self._load_active_sessions()

    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "completed"), exist_ok=True)
        logger.info(f"Session data directory: {self.data_dir}")

    def _load_active_sessions(self):
        """Load active sessions from disk."""
        try:
            active_file = os.path.join(self.data_dir, "active_sessions.json")
            if os.path.exists(active_file):
                with open(active_file, 'r', encoding='utf-8') as f:
                    self.active_sessions = json.load(f)
                logger.info(f"Loaded {len(self.active_sessions)} active sessions")
        except Exception as e:
            logger.error(f"Failed to load active sessions: {e}")
            self.active_sessions = {}

    def _save_active_sessions(self):
        """Save active sessions to disk."""
        try:
            active_file = os.path.join(self.data_dir, "active_sessions.json")
            with open(active_file, 'w', encoding='utf-8') as f:
                json.dump(self.active_sessions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save active sessions: {e}")

    def start_session(self, channel_id: str, session_name: str, gm_name: str) -> bool:
        """
        Start a new session for a channel.

        Args:
            channel_id: Discord channel ID
            session_name: Name of the session
            gm_name: GM's display name

        Returns:
            True if started, False if session already active
        """
        channel_id = str(channel_id)

        if channel_id in self.active_sessions:
            logger.warning(f"Session already active in channel {channel_id}")
            return False

        self.active_sessions[channel_id] = {
            "session_name": session_name,
            "channel_id": channel_id,
            "gm_name": gm_name,
            "started_at": datetime.utcnow().isoformat(),
            "failed_checks": {}  # user_id -> {skill_name: count}
        }

        self._save_active_sessions()
        logger.info(f"Started session '{session_name}' in channel {channel_id}")
        return True

    def is_session_active(self, channel_id: str) -> bool:
        """Check if a session is active in this channel."""
        return str(channel_id) in self.active_sessions

    def get_session(self, channel_id: str) -> Optional[Dict]:
        """Get active session for channel."""
        return self.active_sessions.get(str(channel_id))

    def record_failed_check(self, channel_id: str, user_id: str, skill_name: str):
        """
        Record a failed skill check.

        Args:
            channel_id: Discord channel ID
            user_id: Discord user ID
            skill_name: Name of the skill that failed
        """
        channel_id = str(channel_id)
        user_id = str(user_id)

        if channel_id not in self.active_sessions:
            return

        session = self.active_sessions[channel_id]
        failed_checks = session["failed_checks"]

        if user_id not in failed_checks:
            failed_checks[user_id] = {}

        if skill_name not in failed_checks[user_id]:
            failed_checks[user_id][skill_name] = 0

        failed_checks[user_id][skill_name] += 1
        self._save_active_sessions()

        logger.debug(f"Recorded failed check: {user_id} - {skill_name} (channel {channel_id})")

    def end_session(
        self,
        channel_id: str,
        agent_manager
    ) -> Optional[Dict]:
        """
        End session and perform skill improvement.

        Args:
            channel_id: Discord channel ID
            agent_manager: AgentManager instance

        Returns:
            Dict with improvement results, or None if no session active
        """
        channel_id = str(channel_id)

        if channel_id not in self.active_sessions:
            return None

        session = self.active_sessions[channel_id]
        failed_checks = session["failed_checks"]

        # Process skill improvements
        improvements = {}

        for user_id, skills in failed_checks.items():
            agent = agent_manager.get_agent(user_id)
            if not agent:
                logger.warning(f"Agent not found for user {user_id}, skipping improvement")
                continue

            agent_improvements = {}

            for skill_name, fail_count in skills.items():
                current_skill = agent_manager.get_skill_value(user_id, skill_name)
                if current_skill is None:
                    logger.warning(f"Skill '{skill_name}' not found for user {user_id}")
                    continue

                # Roll for improvement
                improvement_roll = random.randint(1, 100)

                if improvement_roll > current_skill:
                    # Success! Improve skill by 1d4
                    improvement = random.randint(1, 4)
                    new_skill = min(99, current_skill + improvement)

                    # Update agent
                    agent_manager.set_skill_value(user_id, skill_name, new_skill)

                    agent_improvements[skill_name] = {
                        "old_value": current_skill,
                        "new_value": new_skill,
                        "improvement": improvement,
                        "roll": improvement_roll,
                        "failed_count": fail_count
                    }

                    logger.info(f"Improved {skill_name}: {current_skill} -> {new_skill} (+{improvement})")
                else:
                    # Failed to improve
                    agent_improvements[skill_name] = {
                        "old_value": current_skill,
                        "new_value": current_skill,
                        "improvement": 0,
                        "roll": improvement_roll,
                        "failed_count": fail_count
                    }

                    logger.info(f"No improvement for {skill_name} (rolled {improvement_roll} vs {current_skill})")

            if agent_improvements:
                improvements[user_id] = {
                    "agent": agent,
                    "improvements": agent_improvements
                }

        # Save completed session
        session["ended_at"] = datetime.utcnow().isoformat()
        session["improvements"] = improvements
        self._save_completed_session(session)

        # Remove from active sessions
        del self.active_sessions[channel_id]
        self._save_active_sessions()

        logger.info(f"Ended session '{session['session_name']}' with {len(improvements)} agents improved")
        return session

    def _save_completed_session(self, session: Dict):
        """Save completed session to file."""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{timestamp}_{session['session_name'].replace(' ', '_')}.json"
            filepath = os.path.join(self.data_dir, "completed", filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved completed session to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save completed session: {e}")

    def export_to_trip19(
        self,
        session: Dict,
        output_dir: str = os.getenv("DG_TRIP19_DIR", "data/deltagreen/exports")
    ) -> Optional[str]:
        """
        Export session improvements to Trip19 folder.

        Args:
            session: Completed session data
            output_dir: Path to Trip19 folder

        Returns:
            Path to exported file, or None if failed
        """
        try:
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"skill_improvements_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)

            # Create export data
            export_data = {
                "session_name": session["session_name"],
                "started_at": session["started_at"],
                "ended_at": session["ended_at"],
                "gm": session["gm_name"],
                "agents": []
            }

            improvements = session.get("improvements", {})
            for user_id, data in improvements.items():
                agent = data["agent"]
                agent_export = {
                    "callsign": agent["callsign"],
                    "name": agent["name"],
                    "discord_id": user_id,
                    "skill_changes": []
                }

                for skill_name, improvement_data in data["improvements"].items():
                    if improvement_data["improvement"] > 0:
                        agent_export["skill_changes"].append({
                            "skill": skill_name,
                            "old_value": improvement_data["old_value"],
                            "new_value": improvement_data["new_value"],
                            "improvement": improvement_data["improvement"],
                            "improvement_roll": improvement_data["roll"]
                        })

                if agent_export["skill_changes"]:
                    export_data["agents"].append(agent_export)

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported session improvements to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to export to Trip19: {e}")
            return None
