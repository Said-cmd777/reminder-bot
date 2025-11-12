# init_group3_schedule.py
"""Initialize Group 3 schedule in database."""
from db_utils import db_connection
from db_schedule import (
    insert_schedule_class, insert_schedule_location,
    get_schedule_classes
)

# Courses المشتركة بين جميع المجموعات (من Group 1)
SHARED_COURSES = {
    "saturday": [
        {"time_start": "08:00", "time_end": "09:30", "course": "Analysis1", "location": "Amphi H", "type": "Course"},
        {"time_start": "09:40", "time_end": "11:10", "course": "Algebra1", "location": "Amphi H", "type": "Course"},
        {"time_start": "11:20", "time_end": "12:50", "course": "Statistics1", "location": "Room 395T", "type": "Course"},
    ],
    "sunday": [
        {"time_start": "08:00", "time_end": "09:30", "course": "Algorithm1", "location": "Amphi O", "type": "Course"},
        {"time_start": "14:40", "time_end": "16:10", "course": "Analysis1", "location": "Amphi K", "type": "Course"},
    ],
    "tuesday": [
        {"time_start": "14:40", "time_end": "16:10", "course": "Algebra1", "location": "Amphi M", "type": "Course"},
    ],
}

# Online Courses المشتركة بين جميع المجموعات
SHARED_ONLINE_COURSES = {
    "monday": [
        {"time_start": "11:20", "time_end": "12:50", "course": "ICT", "location": "Online (Google Meet)", "type": "Online Session"},
    ],
    "wednesday": [
        {"time_start": "09:00", "time_end": "10:30", "course": "English1", "location": "Online (Google Meet)", "type": "Online Session"},
    ],
}

# Group 3 specific Tutorial Sessions and Laboratory Sessions
GROUP_3_SPECIFIC = {
    "saturday": [
        {"time_start": "13:00", "time_end": "14:30", "course": "Analysis1", "location": "Room 320D", "type": "Tutorial Session"},
        {"time_start": "14:40", "time_end": "16:10", "course": "Statistics1", "location": "Room 304", "type": "Tutorial Session"},
    ],
    "sunday": [
        {"time_start": "11:20", "time_end": "12:50", "course": "Analysis1", "location": "Room 332D", "type": "Tutorial Session"},
        {"time_start": "13:00", "time_end": "14:30", "course": "Algebra1", "location": "Room R3", "type": "Tutorial Session"},
    ],
    "monday": [
        {"time_start": "09:40", "time_end": "11:10", "course": "Algorithm1", "location": "Lab E2.07", "type": "Laboratory Session", "alternating": True, "alternating_key": "algorithm1"},
    ],
    "tuesday": [
        {"time_start": "11:20", "time_end": "12:50", "course": "Algorithm1", "location": "Room 385", "type": "Tutorial Session"},
    ],
    "thursday": [
        {"time_start": "08:00", "time_end": "11:10", "course": "Statistics1", "location": "Lab E0.05", "type": "Laboratory Session", "alternating": True, "alternating_key": "statistics1"},
    ],
}

# New locations for Group 3
NEW_LOCATIONS = {
    "Room 304": "https://maps.app.goo.gl/WXbgQQ3udPJ6sipX6",
    "Room R3": "https://maps.app.goo.gl/vMWGM19TSYzw2haXA",
    "Lab E2.07": "https://maps.app.goo.gl/dYm1eKeBCH36L2AV8",
    "Room 385": "https://maps.app.goo.gl/Bxh3r4oRg3XKa8eh8",
    # Lab E0.05 is already in database
}

def init_group3_schedule():
    """Initialize Group 3 schedule in database."""
    print("Initializing Group 3 schedule...")
    print("NOTE: Group 3 uses same alternating logic as Group 1 (week 0 = has labs)")
    
    with db_connection() as conn:
        # Insert new locations (only if they have URLs)
        if NEW_LOCATIONS:
            print("\nInserting new locations...")
            for location, maps_url in NEW_LOCATIONS.items():
                if maps_url and maps_url != "TODO: Add Google Maps URL":
                    try:
                        from db_schedule import insert_schedule_location
                        insert_schedule_location(conn, location, maps_url)
                        print(f"  [OK] {location}")
                    except Exception as e:
                        print(f"  [WARNING] {location}: {e}")
                else:
                    print(f"  [SKIP] {location}: No Google Maps URL provided yet")
        
        # Insert shared courses for Group 3
        print("\nInserting shared courses for Group 3...")
        day_order = ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday"]
        
        for day in day_order:
            # Collect all classes for this day (shared courses + online courses + group-specific)
            all_classes = []
            
            # Add shared courses
            if day in SHARED_COURSES:
                all_classes.extend(SHARED_COURSES[day])
            
            # Add shared online courses
            if day in SHARED_ONLINE_COURSES:
                all_classes.extend(SHARED_ONLINE_COURSES[day])
            
            # Add Group 3 specific sessions (Tutorial and Laboratory)
            if day in GROUP_3_SPECIFIC:
                all_classes.extend(GROUP_3_SPECIFIC[day])
            
            # Sort all classes by time_start
            all_classes.sort(key=lambda x: x["time_start"])
            
            # Insert classes in chronological order
            for display_order, cls in enumerate(all_classes):
                try:
                    class_id = insert_schedule_class(
                        conn,
                        group_number="03",
                        day_name=day,
                        time_start=cls["time_start"],
                        time_end=cls["time_end"],
                        course=cls["course"],
                        location=cls["location"],
                        class_type=cls["type"],
                        is_alternating=cls.get("alternating", False),
                        alternating_key=cls.get("alternating_key"),
                        display_order=display_order
                    )
                    alt_info = f" (alternating: {cls.get('alternating_key')})" if cls.get("alternating") else ""
                    print(f"  [OK] {day}: {cls['time_start']}-{cls['time_end']} {cls['course']} ({cls['type']}{alt_info}, ID: {class_id})")
                except Exception as e:
                    print(f"  [ERROR] Error inserting {cls['course']} on {day}: {e}")
    
    print("\n[SUCCESS] Group 3 schedule initialized successfully!")
    print("\n[NOTE] Please provide Google Maps URLs for the following locations:")
    print("  - Room 304")
    print("  - Room R3")
    print("  - Lab E2.07")
    print("  - Room 385")
    print("(You can add them later using the admin location management feature)")

if __name__ == "__main__":
    init_group3_schedule()

