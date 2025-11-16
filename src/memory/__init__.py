"""
Memory and Session Management for Research Concierge
Implements ADK's InMemorySessionService and MemoryBank
"""

from google.genai.types import LiveConnectConfig
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryBank:
    """
    Custom MemoryBank implementation for storing research context
    Stores user preferences, research findings, and agent state
    """

    def __init__(self):
        self.storage: Dict[str, Any] = {
            "user_preferences": {},
            "research_context": {},
            "source_cache": [],
            "fact_checks": [],
            "iterations": []
        }
        logger.info("MemoryBank initialized")

    def store_user_preferences(self, preferences: Dict[str, Any]):
        """
        Store user research preferences

        Args:
            preferences: Dictionary containing topic, scope, style, etc.
        """
        self.storage["user_preferences"] = {
            **preferences,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Stored user preferences: {preferences.get('topic', 'unknown')}")

    def get_user_preferences(self) -> Dict[str, Any]:
        """Retrieve user preferences"""
        return self.storage["user_preferences"]

    def add_source(self, source: Dict[str, Any]):
        """
        Add a research source to cache

        Args:
            source: Source summary with claim, evidence, URL, etc.
        """
        self.storage["source_cache"].append({
            **source,
            "added_at": datetime.now().isoformat()
        })
        logger.info(f"Added source: {source.get('source_url', 'unknown')}")

    def get_sources(self) -> List[Dict[str, Any]]:
        """Retrieve all cached sources"""
        return self.storage["source_cache"]

    def add_fact_check(self, fact_check: Dict[str, Any]):
        """Store fact check result"""
        self.storage["fact_checks"].append(fact_check)
        logger.info(f"Added fact check: {fact_check.get('claim', '')[:50]}...")

    def get_fact_checks(self) -> List[Dict[str, Any]]:
        """Retrieve all fact checks"""
        return self.storage["fact_checks"]

    def add_iteration(self, iteration_data: Dict[str, Any]):
        """Store quality loop iteration data"""
        self.storage["iterations"].append({
            **iteration_data,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Added iteration {len(self.storage['iterations'])}")

    def get_iterations(self) -> List[Dict[str, Any]]:
        """Retrieve all iterations"""
        return self.storage["iterations"]

    def update_research_context(self, key: str, value: Any):
        """
        Update research context with key-value pair

        Args:
            key: Context key
            value: Context value
        """
        self.storage["research_context"][key] = value
        logger.info(f"Updated research context: {key}")

    def get_research_context(self, key: Optional[str] = None) -> Any:
        """
        Get research context

        Args:
            key: Specific key to retrieve, or None for all context
        """
        if key:
            return self.storage["research_context"].get(key)
        return self.storage["research_context"]

    def clear(self):
        """Clear all stored data"""
        self.storage = {
            "user_preferences": {},
            "research_context": {},
            "source_cache": [],
            "fact_checks": [],
            "iterations": []
        }
        logger.info("MemoryBank cleared")

    def export_to_json(self, file_path: str):
        """
        Export memory to JSON file

        Args:
            file_path: Path to save JSON
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.storage, f, indent=2, ensure_ascii=False)
            logger.info(f"Memory exported to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export memory: {str(e)}")

    def import_from_json(self, file_path: str):
        """
        Import memory from JSON file

        Args:
            file_path: Path to JSON file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.storage = json.load(f)
            logger.info(f"Memory imported from {file_path}")
        except Exception as e:
            logger.error(f"Failed to import memory: {str(e)}")

    def get_summary(self) -> Dict[str, int]:
        """Get summary statistics of stored data"""
        return {
            "total_sources": len(self.storage["source_cache"]),
            "total_fact_checks": len(self.storage["fact_checks"]),
            "total_iterations": len(self.storage["iterations"]),
            "has_preferences": bool(self.storage["user_preferences"])
        }


class SessionManager:
    """
    Session management for long-running research operations
    Implements pause/resume functionality for ADK
    """

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.active_session_id: Optional[str] = None
        logger.info("SessionManager initialized")

    def create_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Create a new session

        Args:
            session_id: Unique session identifier
            metadata: Optional session metadata
        """
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "metadata": metadata or {},
            "state": {},
            "memory": MemoryBank()
        }
        self.active_session_id = session_id
        logger.info(f"Created session: {session_id}")

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session by ID"""
        return self.sessions.get(session_id)

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """Get currently active session"""
        if self.active_session_id:
            return self.sessions.get(self.active_session_id)
        return None

    def pause_session(self, session_id: str):
        """
        Pause a session (for long-running operations)

        Args:
            session_id: Session to pause
        """
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "paused"
            self.sessions[session_id]["paused_at"] = datetime.now().isoformat()
            logger.info(f"Paused session: {session_id}")

    def resume_session(self, session_id: str):
        """
        Resume a paused session

        Args:
            session_id: Session to resume
        """
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "active"
            self.sessions[session_id]["resumed_at"] = datetime.now().isoformat()
            self.active_session_id = session_id
            logger.info(f"Resumed session: {session_id}")

    def save_session_state(self, session_id: str, state: Dict[str, Any]):
        """
        Save session state for pause/resume

        Args:
            session_id: Session ID
            state: State data to save
        """
        if session_id in self.sessions:
            self.sessions[session_id]["state"] = state
            logger.info(f"Saved state for session: {session_id}")

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session state"""
        session = self.sessions.get(session_id)
        if session:
            return session.get("state")
        return None

    def close_session(self, session_id: str):
        """
        Close a session

        Args:
            session_id: Session to close
        """
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "closed"
            self.sessions[session_id]["closed_at"] = datetime.now().isoformat()
            if self.active_session_id == session_id:
                self.active_session_id = None
            logger.info(f"Closed session: {session_id}")

    def list_sessions(self) -> List[str]:
        """List all session IDs"""
        return list(self.sessions.keys())


# Global instances
memory_bank = MemoryBank()
session_manager = SessionManager()
