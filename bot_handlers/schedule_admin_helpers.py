# bot_handlers/schedule_admin_helpers.py
"""Helper functions for schedule admin management."""
from telebot import types
from constants import (
    CALLBACK_WEEKLY_SCHEDULE_ADMIN, CALLBACK_WEEKLY_SCHEDULE_ADMIN_GROUP,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN_DAY, CALLBACK_WEEKLY_SCHEDULE_ADMIN_VIEW,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN_ADD, CALLBACK_WEEKLY_SCHEDULE_ADMIN_EDIT,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN_DELETE, CALLBACK_WEEKLY_SCHEDULE_ADMIN_CONFIRM_DELETE,
    CALLBACK_WEEKLY_SCHEDULE_ADMIN_LOCATIONS, CALLBACK_WEEKLY_SCHEDULE_ADMIN_ALTERNATING,
    CALLBACK_SCHEDULE_EDIT_TIME_START, CALLBACK_SCHEDULE_EDIT_TIME_END,
    CALLBACK_SCHEDULE_EDIT_COURSE, CALLBACK_SCHEDULE_EDIT_LOCATION,
    CALLBACK_SCHEDULE_EDIT_TYPE, CALLBACK_SCHEDULE_EDIT_ALTERNATING,
    CALLBACK_ALTERNATING_LIST, CALLBACK_ALTERNATING_EDIT, CALLBACK_ALTERNATING_EDIT_DATE, CALLBACK_ALTERNATING_ADD,
    CALLBACK_HW_BACK, CALLBACK_HW_CANCEL
)

# Day names in Arabic
DAY_NAMES_AR = {
    "saturday": "السبت",
    "sunday": "الأحد",
    "monday": "الاثنين",
    "tuesday": "الثلاثاء",
    "wednesday": "الأربعاء",
    "thursday": "الخميس",
    "friday": "الجمعة",
}

DAY_ORDER = ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday"]


def schedule_admin_groups_kb(groups: list) -> types.InlineKeyboardMarkup:
    """Create keyboard for selecting a group to manage."""
    kb = types.InlineKeyboardMarkup()
    for group in sorted(groups):
        kb.add(types.InlineKeyboardButton(f"Group {group}", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_GROUP}{group}"))
    kb.add(types.InlineKeyboardButton("➕ إضافة مجموعة جديدة", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_GROUP}new"))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_HW_BACK))
    return kb


def schedule_admin_days_kb(group_number: str) -> types.InlineKeyboardMarkup:
    """Create keyboard for selecting a day to manage."""
    kb = types.InlineKeyboardMarkup()
    for day in DAY_ORDER:
        day_ar = DAY_NAMES_AR[day]
        kb.add(types.InlineKeyboardButton(day_ar, callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_DAY}{group_number}:{day}"))
    kb.add(types.InlineKeyboardButton("📋 عرض الجدول الكامل", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_VIEW}{group_number}"))
    kb.add(types.InlineKeyboardButton("📍 إدارة المواقع", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN_LOCATIONS))
    kb.add(types.InlineKeyboardButton("🔄 إدارة الحصص الدورية", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN_ALTERNATING))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN))
    return kb


def schedule_admin_day_menu_kb(group_number: str, day: str) -> types.InlineKeyboardMarkup:
    """Create keyboard for managing a specific day."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📋 عرض حصص اليوم", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_VIEW}{group_number}:{day}"))
    kb.add(types.InlineKeyboardButton("➕ إضافة حصة", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_ADD}{group_number}:{day}"))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_GROUP}{group_number}"))
    return kb


def schedule_admin_classes_list_kb(group_number: str, day: str, classes: list) -> types.InlineKeyboardMarkup:
    """Create keyboard listing classes for a day."""
    kb = types.InlineKeyboardMarkup()
    for cls in classes:
        class_id = cls['id']
        time_str = f"{cls['time_start']}-{cls['time_end']}"
        course = cls['course']
        btn_text = f"{time_str} - {course}"
        kb.add(types.InlineKeyboardButton(btn_text, callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_EDIT}{class_id}"))
    kb.add(types.InlineKeyboardButton("➕ إضافة حصة", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_ADD}{group_number}:{day}"))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_DAY}{group_number}:{day}"))
    return kb


def schedule_admin_class_actions_kb(class_id: int, group_number: str, day: str) -> types.InlineKeyboardMarkup:
    """Create keyboard for class actions (edit fields/delete)."""
    kb = types.InlineKeyboardMarkup()
    # Edit field buttons
    kb.add(types.InlineKeyboardButton("⏰ تعديل وقت البداية", callback_data=f"{CALLBACK_SCHEDULE_EDIT_TIME_START}{class_id}"))
    kb.add(types.InlineKeyboardButton("⏰ تعديل وقت الانتهاء", callback_data=f"{CALLBACK_SCHEDULE_EDIT_TIME_END}{class_id}"))
    kb.add(types.InlineKeyboardButton("📚 تعديل المادة", callback_data=f"{CALLBACK_SCHEDULE_EDIT_COURSE}{class_id}"))
    kb.add(types.InlineKeyboardButton("📍 تعديل المكان", callback_data=f"{CALLBACK_SCHEDULE_EDIT_LOCATION}{class_id}"))
    kb.add(types.InlineKeyboardButton("🏷️ تعديل النوع", callback_data=f"{CALLBACK_SCHEDULE_EDIT_TYPE}{class_id}"))
    kb.add(types.InlineKeyboardButton("🔄 تعديل الحالة الدورية", callback_data=f"{CALLBACK_SCHEDULE_EDIT_ALTERNATING}{class_id}"))
    kb.add(types.InlineKeyboardButton("🗑️ حذف", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_DELETE}{class_id}"))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_VIEW}{group_number}:{day}"))
    return kb


def format_class_for_display(cls: dict) -> str:
    """Format a class for display."""
    time_str = f"{cls['time_start']}-{cls['time_end']}"
    course = cls['course']
    location = cls['location']
    class_type = cls['class_type']
    
    text = f"🆔 ID: {cls['id']}\n"
    text += f"⏰ الوقت: {time_str}\n"
    text += f"📚 المادة: {course}\n"
    text += f"📍 المكان: {location}\n"
    text += f"🏷️ النوع: {class_type}\n"
    
    if cls.get('is_alternating', 0):
        text += f"🔄 دورية: نعم ({cls.get('alternating_key', 'N/A')})\n"
    
    return text


def schedule_admin_edit_class_menu_kb(class_id: int, group_number: str, day: str) -> types.InlineKeyboardMarkup:
    """Create keyboard for editing class fields."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⏰ تعديل وقت البداية", callback_data=f"{CALLBACK_SCHEDULE_EDIT_TIME_START}{class_id}"))
    kb.add(types.InlineKeyboardButton("⏰ تعديل وقت الانتهاء", callback_data=f"{CALLBACK_SCHEDULE_EDIT_TIME_END}{class_id}"))
    kb.add(types.InlineKeyboardButton("📚 تعديل المادة", callback_data=f"{CALLBACK_SCHEDULE_EDIT_COURSE}{class_id}"))
    kb.add(types.InlineKeyboardButton("📍 تعديل المكان", callback_data=f"{CALLBACK_SCHEDULE_EDIT_LOCATION}{class_id}"))
    kb.add(types.InlineKeyboardButton("🏷️ تعديل النوع", callback_data=f"{CALLBACK_SCHEDULE_EDIT_TYPE}{class_id}"))
    kb.add(types.InlineKeyboardButton("🔄 تعديل الحالة الدورية", callback_data=f"{CALLBACK_SCHEDULE_EDIT_ALTERNATING}{class_id}"))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=f"{CALLBACK_WEEKLY_SCHEDULE_ADMIN_EDIT}{class_id}"))
    return kb


def format_alternating_config_for_display(config: dict) -> str:
    """Format alternating week configuration for display."""
    text = f"🔄 مفتاح الحصة الدورية: {config.get('alternating_key', 'N/A')}\n"
    text += f"📅 تاريخ المرجع: {config.get('reference_date', 'N/A')}\n"
    if config.get('description'):
        text += f"📝 الوصف: {config.get('description')}\n"
    return text


def alternating_configs_list_kb(configs: list) -> types.InlineKeyboardMarkup:
    """Create keyboard listing alternating week configurations."""
    kb = types.InlineKeyboardMarkup()
    for config in configs:
        key = config.get('alternating_key', 'N/A')
        kb.add(types.InlineKeyboardButton(f"🔄 {key}", callback_data=f"{CALLBACK_ALTERNATING_EDIT}{key}"))
    kb.add(types.InlineKeyboardButton("➕ إضافة إعداد جديد", callback_data=CALLBACK_ALTERNATING_ADD))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_WEEKLY_SCHEDULE_ADMIN))
    return kb


def alternating_config_actions_kb(alternating_key: str) -> types.InlineKeyboardMarkup:
    """Create keyboard for alternating config actions."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📅 تعديل تاريخ المرجع", callback_data=f"{CALLBACK_ALTERNATING_EDIT_DATE}{alternating_key}"))
    kb.add(types.InlineKeyboardButton("↩️ رجوع", callback_data=CALLBACK_ALTERNATING_LIST))
    return kb

