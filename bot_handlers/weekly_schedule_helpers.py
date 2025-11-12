# bot_handlers/weekly_schedule_helpers.py
"""Helper functions for weekly schedule keyboards."""
from typing import Optional, Dict, Any
from telebot import types
from constants import CALLBACK_WEEKLY_SCHEDULE_LOCATION


def class_entry_keyboard(entry: Dict[str, Any], group_number: str = "", day: str = "") -> Optional[types.InlineKeyboardMarkup]:
    """
    Create keyboard for a single class entry.
    Shows "موقع الحجرة" button if location has a map URL.
    """
    from weekly_schedule import has_location_map, get_location_map_url
    
    location = entry.get("location", "")
    
    # Only show location button if not online
    if has_location_map(location):
        kb = types.InlineKeyboardMarkup()
        map_url = get_location_map_url(location)
        kb.add(types.InlineKeyboardButton("📍 موقع الحجرة", url=map_url))
        return kb
    
    return None

