# handlers/base.py
"""Base classes and state management for bot handlers."""
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from collections import defaultdict
from time import time

import telebot

logger = logging.getLogger(__name__)


class StateType(Enum):
    """Types of user states."""
    ADD_HOMEWORK = "add_hw"
    MANUAL_REMINDER = "manual_reminder"
    NICKNAME = "nickname"


@dataclass
class UserState:
    """Represents a user's current state in a multi-step process."""
    state_type: StateType
    step: str
    data: Dict[str, Any] = field(default_factory=dict)


class StateManager:
    """Thread-safe state manager for user interactions."""
    
    def __init__(self):
        self._states: Dict[int, UserState] = {}
        self._lock = threading.Lock()
    
    def start(self, chat_id: int, state_type: StateType, initial_data: Optional[Dict[str, Any]] = None):
        """Start a new state for a user."""
        with self._lock:
            self._states[chat_id] = UserState(
                state_type=state_type,
                step="initial",
                data=initial_data or {}
            )
            logger.debug(f"Started {state_type.value} state for chat {chat_id}")
    
    def get(self, chat_id: int) -> Optional[UserState]:
        """Get current state for a user."""
        with self._lock:
            return self._states.get(chat_id)
    
    def update(self, chat_id: int, step: Optional[str] = None, **kwargs):
        """Update state data."""
        with self._lock:
            state = self._states.get(chat_id)
            if state:
                if step:
                    state.step = step
                for key, value in kwargs.items():
                    state.data[key] = value
                logger.debug(f"Updated state for chat {chat_id}: step={step}, data={kwargs}")
            else:
                logger.warning(f"Attempted to update non-existent state for chat {chat_id}")
    
    def clear(self, chat_id: int):
        """Clear state for a user."""
        with self._lock:
            state = self._states.pop(chat_id, None)
            if state:
                logger.debug(f"Cleared {state.state_type.value} state for chat {chat_id}")
    
    def is_active(self, chat_id: int, state_type: Optional[StateType] = None) -> bool:
        """Check if user has an active state."""
        with self._lock:
            state = self._states.get(chat_id)
            if not state:
                return False
            if state_type:
                return state.state_type == state_type
            return True


class RateLimiter:
    """Rate limiter to prevent abuse."""
    
    def __init__(self, max_calls: int = 5, period: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self._calls: Dict[int, list] = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to make a call."""
        with self._lock:
            now = time()
            # Remove old calls
            self._calls[user_id] = [
                t for t in self._calls[user_id]
                if now - t < self.period
            ]
            
            if len(self._calls[user_id]) >= self.max_calls:
                return False
            
            self._calls[user_id].append(now)
            return True
    
    def reset(self, user_id: int):
        """Reset rate limit for a user."""
        with self._lock:
            self._calls.pop(user_id, None)


class CallbackRouter:
    """Router for callback queries."""
    
    def __init__(self):
        self._handlers: Dict[str, callable] = {}
        self._prefix_handlers: Dict[str, callable] = {}
    
    def register(self, callback_data: str, exact_match: bool = True):
        """
        Register a callback handler.
        
        Args:
            callback_data: Callback data string or prefix
            exact_match: If True, requires exact match; if False, matches prefix
        """
        def decorator(func):
            if exact_match:
                self._handlers[callback_data] = func
            else:
                self._prefix_handlers[callback_data] = func
            return func
        return decorator
    
    def route(self, callback_query) -> bool:
        """
        Route callback query to appropriate handler.
        
        Returns:
            True if handler was found and called, False otherwise
        """
        data = callback_query.data
        
        # Try exact match first
        if data in self._handlers:
            try:
                self._handlers[data](callback_query)
                return True
            except Exception as e:
                logger.exception(f"Error in callback handler for {data}: {e}")
                return False
        
        # Try prefix match
        for prefix, handler in self._prefix_handlers.items():
            if data.startswith(prefix):
                try:
                    handler(callback_query)
                    return True
                except Exception as e:
                    logger.exception(f"Error in prefix callback handler for {prefix}: {e}")
                    return False
        
        logger.warning(f"No handler found for callback: {data}")
        return False


class BotHandlers:
    """Main handler class for bot operations."""
    
    def __init__(self, bot: telebot.TeleBot, sch_mgr):
        """
        Initialize bot handlers.
        
        Args:
            bot: TeleBot instance
            sch_mgr: SchedulerManager instance
        """
        self.bot = bot
        self.sch_mgr = sch_mgr
        self.state_mgr = StateManager()
        self.rate_limiter = RateLimiter(max_calls=5, period=60)
        self.callback_router = CallbackRouter()
        
        # Store bot reference for scheduled jobs (APScheduler needs module-level function)
        # We'll use a closure approach for scheduled jobs
        self._setup_scheduled_jobs()
    
    def _setup_scheduled_jobs(self):
        """Setup scheduled job functions that can access bot instance."""
        # These will be registered with APScheduler using string references
        # The actual functions will be created as closures
        pass
    
    def register_all(self):
        """Register all handlers."""
        from .commands import register_command_handlers
        from .callbacks import register_callback_handlers
        from .homework import register_homework_handlers
        from .manual_reminder import register_manual_reminder_handlers
        
        register_command_handlers(self)
        register_callback_handlers(self)
        register_homework_handlers(self)
        register_manual_reminder_handlers(self)
        
        logger.info("All handlers registered successfully")

