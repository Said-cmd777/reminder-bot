# handlers/__init__.py
"""Handlers package for Telegram bot."""
# Note: register_handlers is in handlers.py (the main file), not in this package
# To import it, use: import handlers as handlers_module; register_handlers = handlers_module.register_handlers
# Or change the import in bot.py to import directly from handlers.py

# Export BotHandlers for new code
from .base import BotHandlers

__all__ = ['BotHandlers']

