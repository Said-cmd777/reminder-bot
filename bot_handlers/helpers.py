# handlers/helpers.py
"""Helper functions and utilities for handlers."""
import logging
from typing import Optional, Dict, Any

import telebot
from telebot import types

from config import ADMIN_IDS
from db_utils import safe_get
from constants import (
    CALLBACK_HW_DONE, CALLBACK_HW_UNDONE, CALLBACK_HW_PDF, CALLBACK_HW_EDIT_ID,
    CALLBACK_HW_DELETE_ID, CALLBACK_HW_BACK, CALLBACK_HW_LIST,
    CALLBACK_HW_ADD, CALLBACK_HW_EDIT, CALLBACK_HW_DELETE,
    CALLBACK_MANUAL_REMINDER, CALLBACK_HW_CANCEL,
    CALLBACK_CUSTOM_REMINDER, CALLBACK_CUSTOM_REMINDER_ADD, CALLBACK_CUSTOM_REMINDER_LIST,
    CALLBACK_CUSTOM_REMINDER_DELETE, CALLBACK_CUSTOM_REMINDER_CONFIRM_DELETE,
    CALLBACK_CUSTOM_REMINDER_DONE, CALLBACK_CUSTOM_REMINDER_UNDONE,
    CALLBACK_WEEKLY_SCHEDULE, CALLBACK_WEEKLY_SCHEDULE_GROUP_01, CALLBACK_WEEKLY_SCHEDULE_GROUP_02,
    CALLBACK_WEEKLY_SCHEDULE_GROUP_03, CALLBACK_WEEKLY_SCHEDULE_GROUP_04,
    CALLBACK_WEEKLY_SCHEDULE_TODAY, CALLBACK_WEEKLY_SCHEDULE_TOMORROW, CALLBACK_WEEKLY_SCHEDULE_WEEK,
    CALLBACK_WEEKLY_SCHEDULE_LOCATION,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN, CALLBACK_WEEKLY_SCHEDULE_ADMIN_GROUP, CALLBACK_WEEKLY_SCHEDULE_ADMIN_DAY,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN_VIEW, CALLBACK_WEEKLY_SCHEDULE_ADMIN_ADD, CALLBACK_WEEKLY_SCHEDULE_ADMIN_EDIT,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN_DELETE, CALLBACK_WEEKLY_SCHEDULE_ADMIN_CONFIRM_DELETE,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN_LOCATIONS, CALLBACK_WEEKLY_SCHEDULE_ADMIN_ALTERNATING,
    CALLBACK_NOTIFICATION_SETTINGS, CALLBACK_NOTIFICATION_DISABLE_HOMEWORK, CALLBACK_NOTIFICATION_ENABLE_HOMEWORK,
    CALLBACK_NOTIFICATION_DISABLE_MANUAL, CALLBACK_NOTIFICATION_ENABLE_MANUAL,
    CALLBACK_NOTIFICATION_DISABLE_CUSTOM, CALLBACK_NOTIFICATION_ENABLE_CUSTOM,
    CALLBACK_NOTIFICATION_DISABLE_ALL, CALLBACK_NOTIFICATION_ENABLE_ALL
)

logger = logging.getLogger(__name__)

MAIN_MENU_BUTTONS = ("Homeworks", "Weekly Schedule")


def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS


def format_homework_text(row: Dict[str, Any]) -> str:
    """Format homework row as display text."""
    target_info = f"ID:{safe_get(row, 'target_user_id')}" if safe_get(row, 'target_user_id') else 'الجميع'
    return (f"ID: {row['id']}\n"
            f"المادة: {row['subject']}\n"
            f"الموعد: {row['due_at']}\n"
            f"الوصف: {row['description']}\n"
            f"الشروط: {row['conditions'] or '-'}\n"
            f"مستهدف: {target_info}")


def main_menu_kb():
    """Create main menu keyboard."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for label in MAIN_MENU_BUTTONS:
        kb.row(label)
    return kb


def is_main_menu_button(text: Optional[str]) -> bool:
    """Check if text matches a main menu button label."""
    return (text or "").strip() in MAIN_MENU_BUTTONS


def registration_kb():
    """Create registration keyboard without main menu buttons."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.row("إلغاء")
    return kb


def cancel_inline_kb():
    """Create cancel inline keyboard."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("إلغاء", callback_data=CALLBACK_HW_CANCEL))
    return kb


def hw_item_kb(user_id: int, hw_id: int, is_done: bool = False):
    """
    Create homework item keyboard.
    
    Args:
        user_id: User ID for admin check
        hw_id: Homework ID
        is_done: Whether homework is marked as done
    """
    kb = types.InlineKeyboardMarkup()
    # Toggle button: "تم؟" if not done, "لم يتم؟" if done
    if is_done:
        kb.add(types.InlineKeyboardButton("❌ لم يتم؟", callback_data=f"{CALLBACK_HW_UNDONE}{hw_id}"))
    else:
        kb.add(types.InlineKeyboardButton("✅ تم؟", callback_data=f"{CALLBACK_HW_DONE}{hw_id}"))
    kb.add(types.InlineKeyboardButton("📎 ملف الواجب", callback_data=f"{CALLBACK_HW_PDF}{hw_id}"))
    if is_admin(user_id):
        kb.add(types.InlineKeyboardButton("✏️ تعديل", callback_data=f"{CALLBACK_HW_EDIT_ID}{hw_id}"))
        kb.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"{CALLBACK_HW_DELETE_ID}{hw_id}"))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_HW_BACK))
    return kb


def hw_main_kb(user_id: int):
    """Create homework main menu keyboard."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📋 قائمة الواجبات", callback_data=CALLBACK_HW_LIST))
    if is_admin(user_id):
        kb.add(types.InlineKeyboardButton("➕ إضافة واجب", callback_data=CALLBACK_HW_ADD))
        kb.add(types.InlineKeyboardButton("✏️ تعديل واجب", callback_data=CALLBACK_HW_EDIT))
        kb.add(types.InlineKeyboardButton("🗑️ حذف واجب", callback_data=CALLBACK_HW_DELETE))
        kb.add(types.InlineKeyboardButton("⏱️ Manual reminder", callback_data=CALLBACK_MANUAL_REMINDER))
        kb.add(types.InlineKeyboardButton("⚙️ إدارة الجداول الأسبوعية", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN))
    kb.add(types.InlineKeyboardButton("🔔 تذكيراتي المخصصة", callback_data=CALLBACK_CUSTOM_REMINDER))
    kb.add(types.InlineKeyboardButton("🔕 إعدادات الإشعارات", callback_data=CALLBACK_NOTIFICATION_SETTINGS))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_HW_BACK))
    return kb


def custom_reminder_main_kb():
    """Create custom reminders main menu keyboard."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("➕ إضافة تذكير مخصص", callback_data=CALLBACK_CUSTOM_REMINDER_ADD))
    kb.add(types.InlineKeyboardButton("📋 قائمة تذكيراتي", callback_data=CALLBACK_CUSTOM_REMINDER_LIST))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_HW_BACK))
    return kb


def custom_reminder_item_kb(reminder_id: int, is_done: bool = False):
    """Create custom reminder item keyboard."""
    kb = types.InlineKeyboardMarkup()
    if is_done:
        kb.add(types.InlineKeyboardButton("❌ لم يتم؟", callback_data=f"{CALLBACK_CUSTOM_REMINDER_UNDONE}{reminder_id}"))
    else:
        kb.add(types.InlineKeyboardButton("✅ تم؟", callback_data=f"{CALLBACK_CUSTOM_REMINDER_DONE}{reminder_id}"))
    kb.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"{CALLBACK_CUSTOM_REMINDER_DELETE}{reminder_id}"))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_CUSTOM_REMINDER_LIST))
    return kb


def weekly_schedule_group_kb():
    """Create weekly schedule group selection keyboard."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("Group 01", callback_data=CALLBACK_WEEKLY_SCHEDULE_GROUP_01))
    kb.add(types.InlineKeyboardButton("Group 02", callback_data=CALLBACK_WEEKLY_SCHEDULE_GROUP_02))
    kb.add(types.InlineKeyboardButton("Group 03", callback_data=CALLBACK_WEEKLY_SCHEDULE_GROUP_03))
    kb.add(types.InlineKeyboardButton("Group 4", callback_data=CALLBACK_WEEKLY_SCHEDULE_GROUP_04))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_HW_BACK))
    return kb


def weekly_schedule_time_kb(group_number: str):
    """Create weekly schedule time selection keyboard for a specific group."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("توقيت اليوم", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_TODAY}{group_number}"))
    kb.add(types.InlineKeyboardButton("توقيت الغد", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_TOMORROW}{group_number}"))
    kb.add(types.InlineKeyboardButton("التوقيت الأسبوعي كاملا", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_WEEK}{group_number}"))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_WEEKLY_SCHEDULE))
    return kb


def try_get_chat_variants(raw_val, bot_obj):
    """
    Try different chat_id variants: id, -id, -100id
    Returns (info, used_id) or (None, last_exception)
    """
    last_err = None
    try:
        base = int(raw_val)
    except Exception as e:
        return None, e

    variants = [base]
    if base > 0:
        variants.append(-base)
        try:
            variants.append(int(f"-100{base}"))
        except Exception:
            pass
    else:
        s = str(abs(base))
        if not str(base).startswith("-100"):
            try:
                variants.append(int(f"-100{s}"))
            except Exception:
                pass

    for v in variants:
        try:
            info = bot_obj.get_chat(v)
            return info, v
        except Exception as e:
            last_err = e
            continue
    return None, last_err


def notification_settings_kb(homework_enabled: bool, manual_enabled: bool, custom_enabled: bool):
    """Create notification settings keyboard."""
    kb = types.InlineKeyboardMarkup()
    
    # Homework reminders
    if homework_enabled:
        kb.add(types.InlineKeyboardButton("✅ تذكيرات الواجبات (مفعّلة)", callback_data=CALLBACK_NOTIFICATION_DISABLE_HOMEWORK))
    else:
        kb.add(types.InlineKeyboardButton("❌ تذكيرات الواجبات (معطّلة)", callback_data=CALLBACK_NOTIFICATION_ENABLE_HOMEWORK))
    
    # Manual reminders
    if manual_enabled:
        kb.add(types.InlineKeyboardButton("✅ تذكيرات الأدمين (مفعّلة)", callback_data=CALLBACK_NOTIFICATION_DISABLE_MANUAL))
    else:
        kb.add(types.InlineKeyboardButton("❌ تذكيرات الأدمين (معطّلة)", callback_data=CALLBACK_NOTIFICATION_ENABLE_MANUAL))
    
    # Custom reminders
    if custom_enabled:
        kb.add(types.InlineKeyboardButton("✅ تذكيراتي المخصصة (مفعّلة)", callback_data=CALLBACK_NOTIFICATION_DISABLE_CUSTOM))
    else:
        kb.add(types.InlineKeyboardButton("❌ تذكيراتي المخصصة (معطّلة)", callback_data=CALLBACK_NOTIFICATION_ENABLE_CUSTOM))
    
    # Enable/Disable all
    if homework_enabled and manual_enabled and custom_enabled:
        kb.add(types.InlineKeyboardButton("🔕 إيقاف جميع الإشعارات", callback_data=CALLBACK_NOTIFICATION_DISABLE_ALL))
    else:
        kb.add(types.InlineKeyboardButton("🔔 استعادة جميع الإشعارات", callback_data=CALLBACK_NOTIFICATION_ENABLE_ALL))
    
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_HW_BACK))
    return kb
