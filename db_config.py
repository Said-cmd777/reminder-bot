"""
Database configuration - detects and configures database backend (SQLite or PostgreSQL).
"""

import os
import logging
from typing import Literal

logger = logging.getLogger(__name__)

# Database types
DatabaseType = Literal["sqlite", "postgresql"]

# Detect database type based on DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

def get_database_type() -> DatabaseType:
    """
    Determine which database to use based on environment variables.
    
    Returns:
        "postgresql" if DATABASE_URL is set, otherwise "sqlite"
    """
    if DATABASE_URL:
        logger.info("✅ DATABASE_URL detected - using PostgreSQL")
        return "postgresql"
    else:
        logger.info("✅ DATABASE_URL not set - using SQLite")
        return "sqlite"

# Set the database type globally
DB_TYPE: DatabaseType = get_database_type()

def get_connection_info():
    """
    Get connection information based on database type.
    
    Returns:
        dict: Connection information for the selected database
    """
    if DB_TYPE == "postgresql":
        return {
            "type": "postgresql",
            "url": DATABASE_URL
        }
    else:
        from config import DB_PATH
        return {
            "type": "sqlite",
            "path": DB_PATH
        }
