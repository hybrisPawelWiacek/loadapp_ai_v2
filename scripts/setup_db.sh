#!/bin/bash

set -e  # Exit on any error

# Default values
DB_USER=${DB_USER:-pawelwiacek}
DB_NAME=${DB_NAME:-loadapp}
DB_TEST_NAME=${DB_TEST_NAME:-loadapp_test}
PSQL="/opt/homebrew/opt/libpq/bin/psql"

# Function to terminate existing connections
terminate_connections() {
    local db_name=$1
    echo "Terminating existing connections to $db_name..."
    $PSQL -U $DB_USER postgres -c "
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '$db_name'
        AND pid <> pg_backend_pid();"
}

# Function to create database with UUID extension
create_database() {
    local db_name=$1
    echo "Creating database: $db_name"
    
    # Terminate existing connections
    terminate_connections "$db_name"
    
    # Drop and recreate database
    $PSQL -U $DB_USER postgres -c "DROP DATABASE IF EXISTS $db_name;"
    $PSQL -U $DB_USER postgres -c "CREATE DATABASE $db_name;"
    $PSQL -U $DB_USER $db_name -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
    echo "Database $db_name created successfully with UUID support"
}

echo "Setting up databases..."

# Create main database
create_database $DB_NAME

# Create test database
create_database $DB_TEST_NAME

echo "Running migrations..."
cd backend || exit 1

# Check if alembic is available
if ! command -v alembic &> /dev/null; then
    echo "Error: alembic is not installed. Please install it with: pip install alembic"
    exit 1
fi

# Run migrations
alembic upgrade head

echo "Database setup completed successfully!"
