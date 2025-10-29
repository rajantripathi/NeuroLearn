"""
State Manager Module
Handles loading, saving, and updating user session data.
All data stored locally in JSON format.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from config import SESSIONS_DIR, DEFAULT_SESSION_FILENAME, FOCUS_STATES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StateManager:
    """Manages user session state with local JSON persistence."""
    
    def __init__(self, user_id: str = "default_user"):
        """
        Initialize state manager for a specific user.
        
        Args:
            user_id: Identifier for the user session
        """
        self.user_id = user_id
        self.session_file = SESSIONS_DIR / f"{user_id}_{DEFAULT_SESSION_FILENAME}"
        self.state = self._load_or_create_session()
    
    def _load_or_create_session(self) -> Dict[str, Any]:
        """
        Load existing session or create a new one.
        
        Returns:
            Dictionary containing session state
        """
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    logger.info(f"Loaded session for user: {self.user_id}")
                    return state
            except json.JSONDecodeError as e:
                logger.error(f"Error loading session: {e}. Creating new session.")
        
        # Create new session
        new_state = {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "focus_state": "neutral",
            "current_environment": "home",
            "focus_rating_history": [],
            "sprint_count": 0,
            "successful_sprints": 0,
            "total_focus_time_minutes": 0,
            "conversation_history": [],
            "preferences": {
                "preferred_tone": "supportive",
                "successful_strategies": []
            },
            "current_sprint": None
        }
        logger.info(f"Created new session for user: {self.user_id}")
        return new_state
    
    def save(self) -> bool:
        """
        Persist current state to JSON file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.state["last_updated"] = datetime.now().isoformat()
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            logger.info(f"Session saved for user: {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False
    
    def update_focus_state(self, focus_state: str) -> bool:
        """
        Update the user's current focus state.
        
        Args:
            focus_state: One of FOCUS_STATES
            
        Returns:
            True if successful
        """
        if focus_state not in FOCUS_STATES:
            logger.warning(f"Invalid focus state: {focus_state}")
            return False
        
        self.state["focus_state"] = focus_state
        logger.info(f"Focus state updated to: {focus_state}")
        return self.save()
    
    def update_environment(self, environment: str) -> bool:
        """
        Update the user's current study environment.
        
        Args:
            environment: Study location (home, library, cafe, etc.)
            
        Returns:
            True if successful
        """
        self.state["current_environment"] = environment
        logger.info(f"Environment updated to: {environment}")
        return self.save()
    
    def add_focus_rating(self, rating: int, what_helped: Optional[str] = None) -> bool:
        """
        Record a focus rating after a session or sprint.
        
        Args:
            rating: Focus rating from 1-5
            what_helped: Optional note about what worked
            
        Returns:
            True if successful
        """
        if not 1 <= rating <= 5:
            logger.warning(f"Invalid rating: {rating}")
            return False
        
        rating_entry = {
            "timestamp": datetime.now().isoformat(),
            "rating": rating,
            "what_helped": what_helped,
            "environment": self.state.get("current_environment"),
            "focus_state_before": self.state.get("focus_state")
        }
        
        self.state["focus_rating_history"].append(rating_entry)
        
        # Update focus state based on rating
        if rating >= 4:
            self.state["focus_state"] = "focused"
        elif rating <= 2:
            self.state["focus_state"] = "overwhelmed"
        else:
            self.state["focus_state"] = "neutral"
        
        logger.info(f"Focus rating added: {rating}/5")
        return self.save()
    
    def start_sprint(self, duration_minutes: int, task_description: str = "") -> bool:
        """
        Start a focus sprint session.
        
        Args:
            duration_minutes: Sprint duration
            task_description: Optional description of the task
            
        Returns:
            True if successful
        """
        self.state["current_sprint"] = {
            "start_time": datetime.now().isoformat(),
            "duration_minutes": duration_minutes,
            "task_description": task_description,
            "completed": False
        }
        
        self.state["sprint_count"] = self.state.get("sprint_count", 0) + 1
        logger.info(f"Sprint started: {duration_minutes} minutes")
        return self.save()
    
    def complete_sprint(self, successful: bool = True) -> bool:
        """
        Mark current sprint as completed.
        
        Args:
            successful: Whether the sprint was completed successfully
            
        Returns:
            True if successful
        """
        if not self.state.get("current_sprint"):
            logger.warning("No active sprint to complete")
            return False
        
        sprint = self.state["current_sprint"]
        sprint["completed"] = True
        sprint["successful"] = successful
        sprint["end_time"] = datetime.now().isoformat()
        
        if successful:
            self.state["successful_sprints"] = self.state.get("successful_sprints", 0) + 1
            self.state["total_focus_time_minutes"] = (
                self.state.get("total_focus_time_minutes", 0) + 
                sprint["duration_minutes"]
            )
        
        # Archive sprint
        if "past_sprints" not in self.state:
            self.state["past_sprints"] = []
        self.state["past_sprints"].append(sprint)
        
        self.state["current_sprint"] = None
        logger.info(f"Sprint completed. Success: {successful}")
        return self.save()
    
    def add_conversation_turn(self, user_message: str, bot_response: str, 
                             intent: Optional[str] = None) -> bool:
        """
        Record a conversation exchange.
        
        Args:
            user_message: User's input
            bot_response: Bot's response
            intent: Detected intent category
            
        Returns:
            True if successful
        """
        turn = {
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "bot": bot_response,
            "intent": intent,
            "focus_state": self.state.get("focus_state")
        }
        
        self.state["conversation_history"].append(turn)
        
        # Keep only recent conversation (last 50 turns)
        if len(self.state["conversation_history"]) > 50:
            self.state["conversation_history"] = self.state["conversation_history"][-50:]
        
        return self.save()
    
    def get_recent_successful_strategies(self, limit: int = 5) -> list:
        """
        Get strategies that have been rated highly in the past.
        
        Args:
            limit: Maximum number of strategies to return
            
        Returns:
            List of successful strategy names
        """
        ratings = self.state.get("focus_rating_history", [])
        successful = [
            r.get("what_helped") 
            for r in ratings 
            if r.get("rating", 0) >= 4 and r.get("what_helped")
        ]
        return list(set(successful))[-limit:]
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current state for context.
        
        Returns:
            Dictionary with key state information
        """
        return {
            "focus_state": self.state.get("focus_state"),
            "environment": self.state.get("current_environment"),
            "sprint_count": self.state.get("sprint_count", 0),
            "successful_sprints": self.state.get("successful_sprints", 0),
            "total_focus_time": self.state.get("total_focus_time_minutes", 0),
            "recent_successful_strategies": self.get_recent_successful_strategies(),
            "has_active_sprint": self.state.get("current_sprint") is not None
        }

