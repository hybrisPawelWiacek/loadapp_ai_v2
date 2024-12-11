#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
from typing import Optional
import psycopg
from psycopg.rows import dict_row
import getpass

# Default configuration
DEFAULT_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': getpass.getuser(),
    'password': '',
    'database': 'loadapp_test'
}

def run_command(command: str) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, and stderr."""
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def check_postgres_running() -> bool:
    """Check if PostgreSQL server is running."""
    if sys.platform == 'darwin':  # macOS
        cmd = "pg_isready"
    elif sys.platform == 'linux':
        cmd = "pg_isready"
    else:  # Windows
        cmd = "pg_isready.exe"
    
    exit_code, _, _ = run_command(cmd)
    return exit_code == 0

def get_connection(database: Optional[str] = None) -> psycopg.Connection:
    """Create a database connection using psycopg3."""
    conn_params = {
        'host': DEFAULT_CONFIG['host'],
        'port': DEFAULT_CONFIG['port'],
        'user': DEFAULT_CONFIG['user']
    }
    
    # Only add password if it's not empty
    if DEFAULT_CONFIG['password']:
        conn_params['password'] = DEFAULT_CONFIG['password']
    
    # Add database if specified, otherwise use postgres
    if database:
        conn_params['dbname'] = database
    else:
        conn_params['dbname'] = 'postgres'
    
    # Create connection string
    conninfo = " ".join(f"{key}={value}" for key, value in conn_params.items())
    
    # Create connection with improved defaults
    return psycopg.connect(
        conninfo,
        autocommit=True,
        row_factory=dict_row
    )

def create_test_database():
    """Create the test database if it doesn't exist."""
    try:
        # Connect to PostgreSQL server
        conn = get_connection(database=None)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DEFAULT_CONFIG['database'],)
        )
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database {DEFAULT_CONFIG['database']}...")
            cursor.execute(f"CREATE DATABASE {DEFAULT_CONFIG['database']}")
            print("Database created successfully!")
        else:
            print(f"Database {DEFAULT_CONFIG['database']} already exists.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

def setup_test_user():
    """Create test user with appropriate permissions."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create test user if doesn't exist
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = 'test_user'"
        )
        exists = cursor.fetchone()
        
        if not exists:
            print("Creating test user...")
            cursor.execute(
                "CREATE USER test_user WITH PASSWORD 'test_password'"
            )
            print("Test user created successfully!")
        
        # Grant privileges
        cursor.execute(
            f"GRANT ALL PRIVILEGES ON DATABASE {DEFAULT_CONFIG['database']} TO test_user"
        )
        print("Privileges granted to test user.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error setting up test user: {e}")
        sys.exit(1)

def reset_test_database():
    """Reset the test database to a clean state."""
    try:
        conn = get_connection(DEFAULT_CONFIG['database'])
        cursor = conn.cursor()
        
        # Drop all tables
        cursor.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        print("All tables dropped successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error resetting database: {e}")
        sys.exit(1)

def setup_extensions():
    """Set up required PostgreSQL extensions."""
    try:
        conn = get_connection(DEFAULT_CONFIG['database'])
        cursor = conn.cursor()
        
        # Check available extensions
        cursor.execute("SELECT extname FROM pg_available_extensions")
        available_extensions = {row['extname'] for row in cursor.fetchall()}
        
        # Add required extensions if available
        desired_extensions = [
            'uuid-ossp',  # For UUID generation
            'pg_trgm',    # For text search
            'btree_gin'   # For GIN indexes
        ]
        
        for ext in desired_extensions:
            if ext in available_extensions:
                print(f"Creating extension {ext}...")
                cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {ext}")
            else:
                print(f"Warning: Extension {ext} is not available")
        
        print("Extensions setup completed!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error setting up extensions: {e}")
        # Don't exit on extension errors, just warn
        print("Continuing without all extensions...")

def main():
    parser = argparse.ArgumentParser(description='Set up PostgreSQL test database')
    parser.add_argument('--reset', action='store_true', help='Reset the test database')
    parser.add_argument('--config', type=str, help='Path to config file')
    args = parser.parse_args()
    
    # Check if PostgreSQL is running
    if not check_postgres_running():
        print("Error: PostgreSQL is not running!")
        sys.exit(1)
    
    if args.reset:
        response = input("Are you sure you want to reset the test database? This will delete all data. (y/N) ")
        if response.lower() == 'y':
            reset_test_database()
    
    # Set up database
    create_test_database()
    setup_test_user()
    setup_extensions()
    
    print("\nTest database setup completed successfully!")
    print(f"\nConnection URL: postgresql://{DEFAULT_CONFIG['user']}:{DEFAULT_CONFIG['password']}@{DEFAULT_CONFIG['host']}:{DEFAULT_CONFIG['port']}/{DEFAULT_CONFIG['database']}")

if __name__ == '__main__':
    main() 