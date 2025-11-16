"""
Update alternating week reference date for all groups.
This script updates the reference_date for algorithm1 and statistics1 alternating configs.

Updated logic (as of Nov 14, 2025):
- Groups 2 & 4: Week 0 = has lab (this week, starts Saturday Nov 15, 2025)
- Groups 1 & 3: Week 1 = has lab (next week, starts Saturday Nov 22, 2025)

Reference date should be set to Saturday, November 15, 2025 (Week 0 for Groups 2 & 4).
"""

from db_utils import db_connection, safe_get
from db_schedule import set_alternating_week_config, get_alternating_week_config

def update_alternating_reference_date():
    """Update reference date for alternating week configs."""
    print("=" * 60)
    print("Updating Alternating Week Reference Date")
    print("=" * 60)
    
    # New reference date: Saturday, November 15, 2025 (Week 0 for Groups 2 & 4)
    new_reference_date = "2025-11-15"
    
    with db_connection() as conn:
        # Update algorithm1 config
        print(f"\nUpdating algorithm1 reference_date to {new_reference_date}...")
        existing_config = get_alternating_week_config(conn, "algorithm1")
        if existing_config:
            old_date = safe_get(existing_config, 'reference_date', 'N/A')
            print(f"  Old reference_date: {old_date}")
        
        set_alternating_week_config(
            conn, 
            "algorithm1", 
            new_reference_date, 
            "Laboratory Session Algorithm1 (Monday)"
        )
        print(f"  ✅ Updated algorithm1 reference_date to {new_reference_date}")
        
        # Update statistics1 config
        print(f"\nUpdating statistics1 reference_date to {new_reference_date}...")
        existing_config = get_alternating_week_config(conn, "statistics1")
        if existing_config:
            old_date = safe_get(existing_config, 'reference_date', 'N/A')
            print(f"  Old reference_date: {old_date}")
        
        set_alternating_week_config(
            conn, 
            "statistics1", 
            new_reference_date, 
            "Laboratory Session Statistics1 (Thursday)"
        )
        print(f"  ✅ Updated statistics1 reference_date to {new_reference_date}")
        
        # Verify updates
        print("\n" + "=" * 60)
        print("Verification:")
        print("=" * 60)
        algo_config = get_alternating_week_config(conn, "algorithm1")
        stats_config = get_alternating_week_config(conn, "statistics1")
        
        if algo_config:
            print(f"algorithm1: reference_date = {safe_get(algo_config, 'reference_date', 'N/A')}")
        if stats_config:
            print(f"statistics1: reference_date = {safe_get(stats_config, 'reference_date', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("✅ Reference dates updated successfully!")
        print("=" * 60)
        print("\nUpdated logic:")
        print("  - Groups 2 & 4: Week 0 = has lab (this week, starts Nov 15, 2025)")
        print("  - Groups 1 & 3: Week 1 = has lab (next week, starts Nov 22, 2025)")
        print("=" * 60)

if __name__ == "__main__":
    update_alternating_reference_date()

