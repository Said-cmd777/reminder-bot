# validators.py
"""Input validation utilities."""

from typing import Optional, Tuple
from constants import MAX_INPUT_LENGTH, MAX_DESCRIPTION_LENGTH
from utils import parse_dt, is_cancel_text


def validate_text_input(text: Optional[str], max_length: int = MAX_INPUT_LENGTH) -> Tuple[bool, Optional[str]]:
    """
    Validate text input.
    
    Returns:
        (is_valid, error_message)
    """
    if not text:
        return False, "النص فارغ"
    
    text = text.strip()
    if len(text) > max_length:
        return False, f"النص طويل جداً (الحد الأقصى: {max_length} حرف)"
    
    return True, None


def validate_datetime(dt_str: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate datetime string.
    
    Returns:
        (is_valid, error_message, parsed_datetime_string)
    """
    if not dt_str:
        return False, "التاريخ فارغ", None
    
    dt_str = dt_str.strip()
    if is_cancel_text(dt_str):
        return False, "تم الإلغاء", None
    
    try:
        dt = parse_dt(dt_str)
        return True, None, dt_str
    except ValueError:
        return False, "صيغة التاريخ غير صحيحة. استخدم: YYYY-MM-DD HH:MM", None


def validate_user_id(user_id_str: Optional[str]) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Validate user ID string.
    
    Returns:
        (is_valid, user_id, error_message)
    """
    if not user_id_str:
        return False, None, "معرف المستخدم فارغ"
    
    user_id_str = user_id_str.strip()
    if user_id_str.lower() in ("all", "none"):
        return True, None, None  # None means "all users"
    
    try:
        uid = int(user_id_str)
        if uid <= 0:
            return False, None, "معرف المستخدم يجب أن يكون رقماً موجباً"
        return True, uid, None
    except ValueError:
        return False, None, "معرف المستخدم غير صحيح. يجب أن يكون رقماً"


def validate_reminders(reminders_str: Optional[str]) -> Tuple[bool, str, Optional[str]]:
    """
    Validate reminders string.
    
    Returns:
        (is_valid, reminders_string, error_message)
    """
    if not reminders_str:
        return True, "3,2,1", None  # Default
    
    reminders_str = reminders_str.strip()
    if reminders_str.lower() == "default":
        return True, "3,2,1", None
    
    parts = [p.strip() for p in reminders_str.split(",") if p.strip()]
    valid_parts = []
    
    for part in parts:
        try:
            v = int(part)
            if 0 <= v < 10000:
                valid_parts.append(str(v))
        except ValueError:
            continue
    
    if not valid_parts:
        return True, "3,2,1", None  # Default if invalid
    
    return True, ",".join(valid_parts), None


def validate_url(url_str: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Basic URL validation.
    
    Returns:
        (is_valid, url, error_message)
    """
    if not url_str:
        return True, None, None  # None is allowed
    
    url_str = url_str.strip()
    if url_str.lower() == "none":
        return True, None, None
    
    # Basic URL check
    if url_str.startswith(("http://", "https://")):
        if len(url_str) > 500:
            return False, None, "الرابط طويل جداً"
        return True, url_str, None
    
    return False, None, "الرابط يجب أن يبدأ بـ http:// أو https://"

