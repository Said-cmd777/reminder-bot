# init_schedule_db.py
"""Initialize schedule database with existing Group 1 data."""
from db_utils import db_connection
from db_schedule import (
    insert_schedule_class, insert_schedule_location,
    set_alternating_week_config
)
from weekly_schedule import GROUP_1_SCHEDULE, LOCATION_MAPS
from datetime import datetime

def init_schedule_database():
    """Initialize schedule database with Group 1 data."""
    print("Initializing schedule database...")
    
    with db_connection() as conn:
        # Insert locations
        print("Inserting locations...")
        for location, maps_url in LOCATION_MAPS.items():
            insert_schedule_location(conn, location, maps_url)
            print(f"  - {location}")
        
        # Insert Group 1 schedule
        print("\nInserting Group 1 schedule...")
        day_order = ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday"]
        
        for day in day_order:
            classes = GROUP_1_SCHEDULE.get(day, [])
            for idx, cls in enumerate(classes):
                time_parts = cls["time"].split("-")
                time_start = time_parts[0].strip()
                time_end = time_parts[1].strip() if len(time_parts) > 1 else ""
                
                is_alternating = cls.get("alternating", False)
                alternating_key = cls.get("alternating_key")
                
                class_id = insert_schedule_class(
                    conn,
                    group_number="01",
                    day_name=day,
                    time_start=time_start,
                    time_end=time_end,
                    course=cls["course"],
                    location=cls["location"],
                    class_type=cls["type"],
                    is_alternating=is_alternating,
                    alternating_key=alternating_key,
                    display_order=idx
                )
                print(f"  - {day}: {time_start}-{time_end} {cls['course']} (ID: {class_id})")
        
        # Set alternating week configurations
        print("\nSetting alternating week configurations...")
        # Reference date: November 11, 2024 (Monday) - week 0
        reference_date = "2024-11-11"
        set_alternating_week_config(conn, "algorithm1", reference_date, "Laboratory Session Algorithm1 (Monday)")
        set_alternating_week_config(conn, "statistics1", reference_date, "Laboratory Session Statistics1 (Thursday)")
        print("  - algorithm1: reference_date =", reference_date)
        print("  - statistics1: reference_date =", reference_date)
    
    print("\nSchedule database initialized successfully!")

if __name__ == "__main__":
    init_schedule_database()

