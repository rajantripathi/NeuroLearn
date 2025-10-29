"""
Focus Sprint Module
Handles timed focus sessions with countdown and completion tracking.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Callable

from config import DEFAULT_SPRINT_DURATION, MIN_SPRINT_DURATION, MAX_SPRINT_DURATION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FocusSprint:
    """Manages timed focus sprint sessions."""
    
    def __init__(self, duration_minutes: int = DEFAULT_SPRINT_DURATION):
        """
        Initialize a focus sprint.
        
        Args:
            duration_minutes: Sprint duration in minutes
        """
        self.duration_minutes = max(
            MIN_SPRINT_DURATION,
            min(duration_minutes, MAX_SPRINT_DURATION)
        )
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.is_active = False
        self.is_completed = False
        self.task_description = ""
    
    def start(self, task_description: str = "") -> bool:
        """
        Start the sprint timer.
        
        Args:
            task_description: Optional description of what to work on
            
        Returns:
            True if started successfully
        """
        if self.is_active:
            logger.warning("Sprint already active")
            return False
        
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=self.duration_minutes)
        self.is_active = True
        self.is_completed = False
        self.task_description = task_description
        
        logger.info(f"Sprint started: {self.duration_minutes} min - {task_description}")
        return True
    
    def get_remaining_time(self) -> Optional[timedelta]:
        """
        Get remaining time in the sprint.
        
        Returns:
            Timedelta of remaining time, or None if not active
        """
        if not self.is_active or not self.end_time:
            return None
        
        remaining = self.end_time - datetime.now()
        if remaining.total_seconds() <= 0:
            return timedelta(0)
        
        return remaining
    
    def get_elapsed_time(self) -> Optional[timedelta]:
        """
        Get elapsed time since sprint start.
        
        Returns:
            Timedelta of elapsed time, or None if not started
        """
        if not self.start_time:
            return None
        
        return datetime.now() - self.start_time
    
    def is_finished(self) -> bool:
        """
        Check if sprint time is up.
        
        Returns:
            True if time has elapsed
        """
        if not self.is_active or not self.end_time:
            return False
        
        return datetime.now() >= self.end_time
    
    def complete(self, successful: bool = True) -> bool:
        """
        Mark sprint as completed.
        
        Args:
            successful: Whether the sprint was successful
            
        Returns:
            True if marked successfully
        """
        if not self.is_active:
            logger.warning("No active sprint to complete")
            return False
        
        self.is_active = False
        self.is_completed = True
        
        logger.info(f"Sprint completed. Success: {successful}")
        return True
    
    def cancel(self) -> bool:
        """
        Cancel the active sprint.
        
        Returns:
            True if cancelled successfully
        """
        if not self.is_active:
            return False
        
        self.is_active = False
        self.is_completed = False
        logger.info("Sprint cancelled")
        return True
    
    def get_progress_percentage(self) -> float:
        """
        Get sprint completion progress as percentage.
        
        Returns:
            Percentage complete (0-100)
        """
        if not self.is_active or not self.start_time or not self.end_time:
            return 0.0
        
        total_seconds = (self.end_time - self.start_time).total_seconds()
        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        
        progress = min(100.0, (elapsed_seconds / total_seconds) * 100)
        return progress
    
    def get_status_message(self) -> str:
        """
        Get a friendly status message about the sprint.
        
        Returns:
            Status string
        """
        if not self.is_active:
            if self.is_completed:
                return "Sprint completed! 🎉"
            return "No active sprint"
        
        remaining = self.get_remaining_time()
        if not remaining:
            return "Sprint finished!"
        
        if remaining.total_seconds() <= 0:
            return "Time's up! Ready to log your progress?"
        
        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        
        return f"⏱️ {minutes}:{seconds:02d} remaining"
    
    def format_time_remaining(self) -> str:
        """
        Format remaining time as MM:SS string.
        
        Returns:
            Formatted time string
        """
        remaining = self.get_remaining_time()
        if not remaining:
            return "00:00"
        
        total_seconds = max(0, int(remaining.total_seconds()))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        return f"{minutes:02d}:{seconds:02d}"
    
    @staticmethod
    def get_recommended_duration(focus_state: str) -> int:
        """
        Get recommended sprint duration based on focus state.
        
        Args:
            focus_state: Current focus state
            
        Returns:
            Recommended duration in minutes
        """
        recommendations = {
            "overwhelmed": 5,
            "distracted": 10,
            "neutral": 15,
            "focused": 20
        }
        
        return recommendations.get(focus_state, DEFAULT_SPRINT_DURATION)

