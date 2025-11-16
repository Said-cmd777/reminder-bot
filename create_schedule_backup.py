#!/usr/bin/env python3
"""
Create a minimal reminders.db database using only JSON as backup.
This avoids sqlite3 issues on Replit.
"""
import json
import os

def create_json_backup():
    """Create JSON backup of schedule data."""
    schedule_data = {
        "version": "1.0",
        "date": "2025-11-16",
        "classes": [
            # Group 01
            {"group": "01", "day": "saturday", "time_start": "08:00", "time_end": "09:30", "course": "Analysis1", "location": "Amphi H", "type": "Course", "alternating": False},
            {"group": "01", "day": "saturday", "time_start": "09:40", "time_end": "11:10", "course": "Algebra1", "location": "Amphi H", "type": "Course", "alternating": False},
            {"group": "01", "day": "monday", "time_start": "08:00", "time_end": "09:30", "course": "Algorithm1", "location": "LabE2.01", "type": "Laboratory Session", "alternating": True, "alt_key": "algorithm1"},
            {"group": "01", "day": "thursday", "time_start": "08:00", "time_end": "11:10", "course": "Statistics1", "location": "LabE2.01", "type": "Laboratory Session", "alternating": True, "alt_key": "statistics1"},
            
            # Group 02
            {"group": "02", "day": "saturday", "time_start": "08:00", "time_end": "09:30", "course": "Analysis1", "location": "Amphi H", "type": "Course", "alternating": False},
            {"group": "02", "day": "monday", "time_start": "09:40", "time_end": "11:10", "course": "Algorithm1", "location": "Lab E0.05", "type": "Laboratory Session", "alternating": True, "alt_key": "algorithm1"},
            
            # Group 03
            {"group": "03", "day": "saturday", "time_start": "08:00", "time_end": "09:30", "course": "Analysis1", "location": "Amphi H", "type": "Course", "alternating": False},
            {"group": "03", "day": "monday", "time_start": "08:00", "time_end": "09:30", "course": "Algorithm1", "location": "LabE2.01", "type": "Laboratory Session", "alternating": True, "alt_key": "algorithm1"},
            
            # Group 04
            {"group": "04", "day": "saturday", "time_start": "08:00", "time_end": "09:30", "course": "Analysis1", "location": "Amphi H", "type": "Course", "alternating": False},
            {"group": "04", "day": "saturday", "time_start": "09:40", "time_end": "11:10", "course": "Algebra1", "location": "Amphi H", "type": "Course", "alternating": False},
            {"group": "04", "day": "saturday", "time_start": "11:20", "time_end": "12:50", "course": "Statistics1", "location": "Room 395T", "type": "Course", "alternating": False},
            {"group": "04", "day": "saturday", "time_start": "13:00", "time_end": "14:30", "course": "Statistics1", "location": "Room 300", "type": "Tutorial Session", "alternating": False},
            {"group": "04", "day": "saturday", "time_start": "14:40", "time_end": "16:10", "course": "Analysis1", "location": "Room C206", "type": "Tutorial Session", "alternating": False},
            
            {"group": "04", "day": "sunday", "time_start": "08:00", "time_end": "09:30", "course": "Algorithm1", "location": "Amphi O", "type": "Course", "alternating": False},
            {"group": "04", "day": "sunday", "time_start": "09:40", "time_end": "11:10", "course": "Analysis1", "location": "Room 301D", "type": "Tutorial Session", "alternating": False},
            {"group": "04", "day": "sunday", "time_start": "11:20", "time_end": "12:50", "course": "Algebra1", "location": "Room R3", "type": "Tutorial Session", "alternating": False},
            {"group": "04", "day": "sunday", "time_start": "14:40", "time_end": "16:10", "course": "Analysis1", "location": "Amphi K", "type": "Course", "alternating": False},
            
            {"group": "04", "day": "monday", "time_start": "09:40", "time_end": "11:10", "course": "Algorithm1", "location": "Lab E0.05", "type": "Laboratory Session", "alternating": True, "alt_key": "algorithm1"},
            {"group": "04", "day": "monday", "time_start": "11:20", "time_end": "12:50", "course": "ICT", "location": "Online (Google Meet)", "type": "Online Session", "alternating": False},
            
            {"group": "04", "day": "tuesday", "time_start": "13:00", "time_end": "14:30", "course": "Algorithm1", "location": "Room R6", "type": "Tutorial Session", "alternating": False},
            {"group": "04", "day": "tuesday", "time_start": "14:40", "time_end": "16:10", "course": "Algebra1", "location": "Amphi M", "type": "Course", "alternating": False},
            
            {"group": "04", "day": "wednesday", "time_start": "09:00", "time_end": "10:30", "course": "English1", "location": "Online (Google Meet)", "type": "Online Session", "alternating": False},
            
            {"group": "04", "day": "thursday", "time_start": "08:00", "time_end": "11:10", "course": "Statistics1", "location": "Lab E0.05", "type": "Laboratory Session", "alternating": True, "alt_key": "statistics1"},
        ],
        "alternating_config": [
            {"key": "algorithm1", "reference_date": "2025-11-15", "description": "Laboratory Session Algorithm1 (Monday)"},
            {"key": "statistics1", "reference_date": "2025-11-15", "description": "Laboratory Session Statistics1 (Thursday)"}
        ]
    }
    
    # Save as JSON
    with open("schedule_backup.json", "w", encoding="utf-8") as f:
        json.dump(schedule_data, f, ensure_ascii=False, indent=2)
    
    print("✅ Created schedule_backup.json")
    print(f"   Classes: {len(schedule_data['classes'])}")
    print(f"   Config: {len(schedule_data['alternating_config'])}")

if __name__ == "__main__":
    create_json_backup()
