"""
This file has been deprecated. All database configuration has been moved to db_setup.py
for better organization and to avoid circular imports.
"""

# This is a placeholder to prevent imports from breaking
# All code should be updated to import from db_setup.py instead
from .db_setup import Base, engine, SessionLocal, get_db
