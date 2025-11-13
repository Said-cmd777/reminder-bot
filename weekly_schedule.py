# weekly_schedule.py
"""Weekly schedule data and utilities for groups."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# Group 1 Schedule
GROUP_1_SCHEDULE = {
    "saturday": [
        {"time": "08:00-09:30", "course": "Analysis1", "location": "Amphi H", "type": "Course"},
        {"time": "09:40-11:10", "course": "Algebra1", "location": "Amphi H", "type": "Course"},
        {"time": "11:20-12:50", "course": "Statistics1", "location": "Room 395T", "type": "Course"},
        {"time": "13:00-14:30", "course": "Algorithm1", "location": "Room C206", "type": "Tutorial Session"},
        {"time": "14:40-16:10", "course": "Analysis1", "location": "Room C206", "type": "Tutorial Session"},
    ],
    "sunday": [
        {"time": "08:00-09:30", "course": "Algorithm1", "location": "Amphi O", "type": "Course"},
        {"time": "09:40-11:10", "course": "Analysis1", "location": "Room 301D", "type": "Tutorial Session"},
        {"time": "14:40-16:10", "course": "Analysis1", "location": "Amphi K", "type": "Course"},
    ],
    "monday": [
        {"time": "08:00-09:30", "course": "Algorithm1", "location": "LabE2.01", "type": "Laboratory Session", "alternating": True, "alternating_key": "algorithm1"},
        {"time": "11:20-12:50", "course": "ICT", "location": "Online (Google Meet)", "type": "Online Session"},
    ],
    "tuesday": [
        {"time": "11:20-12:50", "course": "Statistics1", "location": "Room C5", "type": "Tutorial Session"},
        {"time": "13:00-14:30", "course": "Algebra1", "location": "Room 320D", "type": "Tutorial Session"},
        {"time": "14:40-16:10", "course": "Algebra1", "location": "Amphi M", "type": "Course"},
    ],
    "wednesday": [
        {"time": "09:00-10:30", "course": "English1", "location": "Online (Google Meet)", "type": "Online Session"},
    ],
    "thursday": [
        {"time": "08:00-11:10", "course": "Statistics1", "location": "LabE2.01", "type": "Laboratory Session", "alternating": True, "alternating_key": "statistics1"},
    ],
    "friday": [],  # No classes on Friday
}

# Map English day names to Arabic
DAY_NAMES_AR = {
    "saturday": "السبت",
    "sunday": "الأحد",
    "monday": "الاثنين",
    "tuesday": "الثلاثاء",
    "wednesday": "الأربعاء",
    "thursday": "الخميس",
    "friday": "الجمعة",
}

# Map locations to Google Maps URLs
LOCATION_MAPS = {
    "Amphi H": "https://maps.app.goo.gl/dVN1fct8vKn7qtCK9",
    "Room 395T": "https://maps.app.goo.gl/48W4CSMDsJ7BWZJT7",
    "Room C206": "https://maps.app.goo.gl/oFPEBQLKUoJHUmQU6",
    "Amphi O": "https://maps.app.goo.gl/hdGS4iixtNLS5yQP7",
    "Room 301D": "https://maps.app.goo.gl/ZJtAzqzirGNPiDK77",
    "Amphi K": "https://maps.app.goo.gl/Y47Xunf9egcdazMm7",
    "LabE2.01": "https://maps.app.goo.gl/dYm1eKeBCH36L2AV8",
    "Room C5": "https://maps.app.goo.gl/vDKgWcQ5sDbnorXz9",
    "Room 320D": "https://maps.app.goo.gl/Bxh3r4oRg3XKa8eh8",
    "Amphi M": "https://maps.app.goo.gl/jgWiMD8QwpaFVxrBA",
}

# Map weekday numbers to day names (0=Monday, 6=Sunday in Python, but we use Saturday=0)
WEEKDAY_TO_DAY = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}

# Reverse mapping for our schedule (Saturday=0)
SCHEDULE_DAY_TO_WEEKDAY = {
    "saturday": 5,
    "sunday": 6,
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
}


def get_current_week_number() -> int:
    """
    Get current week number since a reference date.
    Returns 0 for weeks with Algorithm1 lab AND Statistics lab, 1 for weeks without.
    Reference: User said:
    - They studied Algorithm1 lab this week (week 0)
    - They will study Statistics lab this week (week 0)
    So both labs are in week 0, neither in week 1
    """
    # Reference date: November 11, 2024 (Monday) - assuming this is week 0
    # This week (week 0): has Algorithm1 lab AND Statistics lab
    # Next week (week 1): no Algorithm1 lab, no Statistics lab
    reference_date = datetime(2024, 11, 11)  # Monday
    today = datetime.now()
    days_diff = (today - reference_date).days
    week_number = days_diff // 7
    return week_number % 2  # 0 = has both labs, 1 = no labs


def is_algorithm1_lab_week() -> bool:
    """
    Check if this week has Algorithm1 Laboratory Session.
    User said: they studied it this week, so this week = 0 (has lab)
    """
    return get_current_week_number() == 0


def is_statistics_lab_week() -> bool:
    """
    Check if this week has Statistics Laboratory Session.
    User said: they will study it this week, so this week = 0 (has lab)
    Next week = 1 (no lab)
    """
    return get_current_week_number() == 0


def get_today_schedule_day() -> str:
    """Get today's day name in schedule format (saturday, sunday, etc.)."""
    today = datetime.now()
    weekday = today.weekday()  # 0=Monday, 6=Sunday
    return WEEKDAY_TO_DAY[weekday]


def get_tomorrow_schedule_day() -> str:
    """Get tomorrow's day name in schedule format."""
    tomorrow = datetime.now() + timedelta(days=1)
    weekday = tomorrow.weekday()
    return WEEKDAY_TO_DAY[weekday]


def format_class_entry(entry: Dict) -> str:
    """Format a single class entry for display."""
    time_str = entry["time"]
    course = entry["course"]
    location = entry["location"]
    class_type = entry.get("type", "Class")
    
    # Format based on type
    if class_type == "Online Session":
        return f"🖥️ {time_str} - {course} ({location})"
    elif class_type == "Laboratory Session":
        return f"🔬 {time_str} - {class_type} {course} ({location})"
    elif class_type == "Tutorial Session":
        return f"📝 {time_str} - {class_type} {course} ({location})"
    else:  # Course
        return f"📚 {time_str} - {course} ({location})"


def get_group_schedule(group_number: str, day: str) -> List[Dict]:
    """
    Get schedule for a specific group and day.
    Handles alternating weeks for laboratory sessions.
    Reads from database if available, falls back to hardcoded data.
    """
    try:
        # Try to read from database first
        from db_schedule import get_schedule_classes, get_alternating_week_config
        from db_utils import db_connection
        from datetime import datetime, timedelta
        
        with db_connection() as conn:
            db_classes = get_schedule_classes(conn, group_number, day.lower())
            
            if db_classes:
                # Process database classes
                filtered_schedule = []
                for cls in db_classes:
                    try:
                        cls_dict = dict(cls)
                        
                        # Check if alternating
                        if cls_dict.get('is_alternating', 0):
                            alternating_key = cls_dict.get('alternating_key')
                            if alternating_key:
                                try:
                                    # Get alternating week config
                                    config = get_alternating_week_config(conn, alternating_key)
                                    if config:
                                        ref_date = datetime.strptime(config['reference_date'], "%Y-%m-%d")
                                        today = datetime.now()
                                        days_diff = (today - ref_date).days
                                        week_number = (days_diff // 7) % 2
                                        
                                        # Group 1: Week 0 = has lab, Week 1 = no lab (normal logic)
                                        # Group 2: Week 0 = no lab, Week 1 = has lab (reversed logic)
                                        # Group 3: Week 0 = has lab, Week 1 = no lab (same as Group 1 - normal logic)
                                        # Group 4: Week 0 = no lab, Week 1 = has lab (same as Group 2 - reversed logic)
                                        if group_number in ["02", "04"]:
                                            # Group 2 & 4: reversed logic (week 0 = no lab, week 1 = has lab)
                                            if week_number != 1:
                                                continue  # Skip this class (only show in week 1)
                                        else:
                                            # Group 1, 3, and others: normal logic (week 0 = has lab, week 1 = no lab)
                                            if week_number != 0:
                                                continue  # Skip this class (only show in week 0)
                                except Exception as alt_error:
                                    # إذا فشل التحقق من الحصة الدورية، نتخطاها
                                    import logging
                                    logging.warning(f"Failed to check alternating for class: {alt_error}")
                                    continue
                        
                        # Convert to format expected by rest of code
                        entry = {
                            "time": f"{cls_dict['time_start']}-{cls_dict['time_end']}",
                            "course": cls_dict['course'],
                            "location": cls_dict['location'],
                            "type": cls_dict['class_type'],
                            "alternating": bool(cls_dict.get('is_alternating', 0)),
                            "alternating_key": cls_dict.get('alternating_key')
                        }
                        filtered_schedule.append(entry)
                    except Exception as cls_error:
                        # إذا فشل معالجة حصة واحدة، نتخطاها ونكمل
                        import logging
                        logging.warning(f"Failed to process class entry: {cls_error}")
                        continue
                
                return filtered_schedule
    except Exception as db_error:
        # Fallback to hardcoded data
        import logging
        logging.warning(f"Failed to read from database, falling back to hardcoded data: {db_error}")
        pass
    
    # Fallback to hardcoded Group 1 schedule (only if database is empty)
    try:
        if group_number == "01":
            schedule = GROUP_1_SCHEDULE.get(day.lower(), [])
            
            # Filter alternating classes based on current week
            # Group 1: Week 0 = has lab, Week 1 = no lab
            filtered_schedule = []
            for entry in schedule:
                try:
                    if entry.get("alternating", False):
                        alternating_key = entry.get("alternating_key", "")
                        if alternating_key == "algorithm1":
                            if is_algorithm1_lab_week():  # Week 0
                                filtered_schedule.append(entry)
                        elif alternating_key == "statistics1":
                            if is_statistics_lab_week():  # Week 0
                                filtered_schedule.append(entry)
                        else:
                            # Fallback for other alternating classes
                            filtered_schedule.append(entry)
                    else:
                        filtered_schedule.append(entry)
                except Exception as entry_error:
                    # إذا فشل معالجة حصة واحدة، نتخطاها
                    import logging
                    logging.warning(f"Failed to process hardcoded entry: {entry_error}")
                    # لا نستخدم continue هنا لأننا في حلقة for
                    pass
            
            return filtered_schedule
        else:
            # Other groups are read from database (should have been initialized)
            # If database is empty, return empty list
            # Note: Group 2 uses reversed logic (Week 0 = no lab, Week 1 = has lab)
            return []
    except Exception as fallback_error:
        import logging
        logging.exception(f"Failed to get fallback schedule: {fallback_error}")
        return []


def get_day_schedule_entries(group_number: str, day: str) -> List[Dict]:
    """Get list of schedule entries for a specific day."""
    day_ar = DAY_NAMES_AR.get(day.lower(), day.capitalize())
    schedule = get_group_schedule(group_number, day)
    
    entries = []
    for entry in schedule:
        entry_with_day = entry.copy()
        entry_with_day["day_ar"] = day_ar
        entries.append(entry_with_day)
    
    return entries


def get_today_schedule_entries(group_number: str) -> List[Dict]:
    """Get list of today's schedule entries."""
    today_day = get_today_schedule_day()
    return get_day_schedule_entries(group_number, today_day)


def get_tomorrow_schedule_entries(group_number: str) -> List[Dict]:
    """Get list of tomorrow's schedule entries."""
    tomorrow_day = get_tomorrow_schedule_day()
    return get_day_schedule_entries(group_number, tomorrow_day)


def has_location_map(location: str) -> bool:
    """Check if location has a Google Maps URL (not online)."""
    # Online sessions don't have physical locations
    if "Online" in location or "Google Meet" in location:
        return False
    
    # Try database first
    try:
        from db_schedule import get_schedule_location
        from db_utils import db_connection
        with db_connection() as conn:
            url = get_schedule_location(conn, location)
            if url:
                return True
    except Exception:
        pass
    
    # Fallback to hardcoded maps
    return location in LOCATION_MAPS


def get_location_map_url(location: str) -> Optional[str]:
    """Get Google Maps URL for a location."""
    # Try database first
    try:
        from db_schedule import get_schedule_location
        from db_utils import db_connection
        with db_connection() as conn:
            url = get_schedule_location(conn, location)
            if url:
                return url
    except Exception:
        pass
    
    # Fallback to hardcoded maps
    return LOCATION_MAPS.get(location, None)


def format_single_class_message(entry: Dict, day_ar: str = None) -> str:
    """Format a single class as a message."""
    time_str = entry["time"]
    course = entry["course"]
    location = entry["location"]
    class_type = entry.get("type", "Class")
    day_ar = day_ar or entry.get("day_ar", "")
    
    # Build message
    if day_ar:
        text = f"📅 {day_ar}\n\n"
    else:
        text = ""
    
    # Format based on type
    if class_type == "Online Session":
        text += f"🖥️ {time_str}\n{course}\n{location}"
    elif class_type == "Laboratory Session":
        text += f"🔬 {time_str}\n{class_type} {course}\n{location}"
    elif class_type == "Tutorial Session":
        text += f"📝 {time_str}\n{class_type} {course}\n{location}"
    else:  # Course
        text += f"📚 {time_str}\n{course}\n{location}"
    
    return text


def format_weekly_schedule(group_number: str) -> str:
    """Format full weekly schedule."""
    try:
        text = f"📅 الجدول الأسبوعي الكامل - Group {group_number}\n\n"
        
        days_order = ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday"]
        
        has_any_schedule = False
        for day in days_order:
            try:
                day_ar = DAY_NAMES_AR.get(day, day.capitalize())
                schedule = get_group_schedule(group_number, day)
                
                if schedule:
                    has_any_schedule = True
                    text += f"📅 {day_ar}:\n"
                    for entry in schedule:
                        try:
                            formatted_entry = format_class_entry(entry)
                            text += formatted_entry + "\n"
                        except Exception as entry_error:
                            # إذا فشل تنسيق حصة واحدة، نتخطاها ونكمل
                            import logging
                            logging.warning(f"Failed to format entry for {day}: {entry_error}")
                            continue
                    text += "\n"
            except Exception as day_error:
                # إذا فشل جلب جدول يوم معين، نتخطاه ونكمل
                import logging
                logging.warning(f"Failed to get schedule for {day}: {day_error}")
                continue
        
        # إذا لم توجد أي حصص، نضيف رسالة توضيحية
        if not has_any_schedule:
            text += "لا توجد حصص مسجلة لهذه المجموعة.\n\n"
            text += "يرجى إضافة الحصص من قائمة الإدارة (Admin)."
        else:
            # Add note about alternating weeks (only if there are alternating classes)
            has_alternating = False
            try:
                for day in days_order:
                    try:
                        schedule = get_group_schedule(group_number, day)
                        for entry in schedule:
                            if entry.get("alternating", False):
                                has_alternating = True
                                break
                        if has_alternating:
                            break
                    except Exception:
                        continue
                
                if has_alternating:
                    text += "\n📌 ملاحظة:\n"
                    # Check if this group has alternating labs this week
                    if group_number in ["02", "04"]:
                        # Group 2 & 4: reversed logic (Week 0 = no lab, Week 1 = has lab)
                        algorithm1_has_lab = not is_algorithm1_lab_week()  # Reversed
                        statistics1_has_lab = not is_statistics_lab_week()  # Reversed
                    else:
                        # Group 1, 3, and others: normal logic (Week 0 = has lab, Week 1 = no lab)
                        algorithm1_has_lab = is_algorithm1_lab_week()
                        statistics1_has_lab = is_statistics_lab_week()
                    
                    text += "• Laboratory Session Algorithm1 (الاثنين) دورية - هذا الأسبوع: "
                    text += "✅ موجودة" if algorithm1_has_lab else "❌ غير موجودة"
                    text += "\n"
                    text += "• Laboratory Session Statistics1 (الخميس) دورية - هذا الأسبوع: "
                    text += "✅ موجودة" if statistics1_has_lab else "❌ غير موجودة"
            except Exception as alt_error:
                # إذا فشل التحقق من الحصص الدورية، نتخطاه
                import logging
                logging.warning(f"Failed to check alternating classes: {alt_error}")
        
        return text
    except Exception as e:
        # في حالة فشل كامل، نرجع رسالة خطأ واضحة
        import logging
        logging.exception(f"Failed to format weekly schedule for group {group_number}: {e}")
        return f"📅 الجدول الأسبوعي الكامل - Group {group_number}\n\n❌ حدث خطأ في جلب الجدول.\n\nالخطأ: {str(e)}\n\nيرجى المحاولة مرة أخرى أو الاتصال بالأدمين."

