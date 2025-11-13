
"""Initialize Group 2 schedule in database."""
from db_utils import db_connection
from db_schedule import (
    insert_schedule_class, insert_schedule_location,
    get_schedule_classes
)


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


SHARED_ONLINE_COURSES = {
    "monday": [
        {"time_start": "11:20", "time_end": "12:50", "course": "ICT", "location": "Online (Google Meet)", "type": "Online Session"},
    ],
    "wednesday": [
        {"time_start": "09:00", "time_end": "10:30", "course": "English1", "location": "Online (Google Meet)", "type": "Online Session"},
    ],
}


GROUP_2_SPECIFIC = {
    "saturday": [
        {"time_start": "13:00", "time_end": "14:30", "course": "Analysis1", "location": "Room 320D", "type": "Tutorial Session"},
        {"time_start": "14:40", "time_end": "16:10", "course": "Algorithm1", "location": "Room 336D", "type": "Tutorial Session"},
    ],
    "sunday": [
        {"time_start": "11:20", "time_end": "12:50", "course": "Analysis1", "location": "Room 332D", "type": "Tutorial Session"},
    ],
    "monday": [
        {"time_start": "08:00", "time_end": "09:30", "course": "Algorithm1", "location": "Lab E0.05", "type": "Laboratory Session", "alternating": True, "alternating_key": "algorithm1"},
    ],
    "tuesday": [
        {"time_start": "11:20", "time_end": "12:50", "course": "Algorithm1", "location": "Room C6", "type": "Tutorial Session"},
        {"time_start": "13:00", "time_end": "14:30", "course": "Statistics1", "location": "Room 362", "type": "Tutorial Session"},
    ],
    "thursday": [
        {"time_start": "08:00", "time_end": "11:10", "course": "Statistics1", "location": "Lab E2.01", "type": "Laboratory Session", "alternating": True, "alternating_key": "statistics1"},
    ],
}


NEW_LOCATIONS = {
    "Room 336D": "https://maps.app.goo.gl/WXbgQQ3udPJ6sipX6",
    "Room 332D": "https://maps.app.goo.gl/WXbgQQ3udPJ6sipX6",
    "Lab E0.05": "https://maps.app.goo.gl/dYm1eKeBCH36L2AV8",
    "Room C6": "https://maps.app.goo.gl/vDKgWcQ5sDbnorXz9",
    "Room 362": "https://maps.app.goo.gl/WXbgQQ3udPJ6sipX6",
}

def init_group2_schedule():
    """Initialize Group 2 schedule in database."""
    print("Initializing Group 2 schedule...")
    
    with db_connection() as conn:
        
        print("\nInserting new locations...")
        for location, maps_url in NEW_LOCATIONS.items():
            try:
                from db_schedule import insert_schedule_location
                insert_schedule_location(conn, location, maps_url)
                print(f"  [OK] {location}")
            except Exception as e:
                print(f"  [WARNING] {location}: {e}")
        
        
        print("\nInserting shared courses for Group 2...")
        day_order = ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday"]
        
        for day in day_order:
            
            all_classes = []
            
            
            if day in SHARED_COURSES:
                all_classes.extend(SHARED_COURSES[day])
            
            
            if day in SHARED_ONLINE_COURSES:
                all_classes.extend(SHARED_ONLINE_COURSES[day])
            
            
            if day in GROUP_2_SPECIFIC:
                all_classes.extend(GROUP_2_SPECIFIC[day])
            
            
            all_classes.sort(key=lambda x: x["time_start"])
            
            
            for display_order, cls in enumerate(all_classes):
                try:
                    class_id = insert_schedule_class(
                        conn,
                        group_number="02",
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
    
    print("\n[SUCCESS] Group 2 schedule initialized successfully!")

if __name__ == "__main__":
    init_group2_schedule()

