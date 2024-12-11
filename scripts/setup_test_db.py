#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def setup_test_database():
    # Load environment variables
    load_dotenv(".env.development")
    
    # Database configuration
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    TEST_DB_NAME = "loadapp_test"
    
    # Create admin connection URL
    ADMIN_DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
    
    try:
        # Create engine for admin operations
        engine = create_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
        
        with engine.connect() as conn:
            # Terminate existing connections
            conn.execute(text(
                f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
                AND pid <> pg_backend_pid()
                """
            ))
            print(f"Terminated existing connections to '{TEST_DB_NAME}'")
            
            # Drop test database if it exists
            conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
            print(f"Dropped existing database '{TEST_DB_NAME}' if it existed")
            
            # Create new test database
            conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
            print(f"Created new database '{TEST_DB_NAME}'")
            
            # Create extensions if needed
            test_db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"
            test_engine = create_engine(test_db_url, isolation_level="AUTOCOMMIT")
            with test_engine.connect() as test_conn:
                # Add any required PostgreSQL extensions here
                test_conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                print("Created required database extensions")
        
        print("\nTest database setup completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\nError setting up test database: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(setup_test_database()) 