#!/bin/bash

# Default values
DATABASE="postgres"
COVERAGE=false
VERBOSE=false
MARKERS=""
PARALLEL=false
PATTERN="tests/"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Help message
show_help() {
    echo "Usage: ./run_tests.sh [options]"
    echo
    echo "Options:"
    echo "  -d, --database <type>    Specify database type (sqlite/postgres) [default: postgres]"
    echo "  -c, --coverage           Generate coverage report"
    echo "  -v, --verbose            Run tests in verbose mode"
    echo "  -m, --markers <markers>  Specify pytest markers (e.g., 'not slow')"
    echo "  -p, --parallel           Run tests in parallel"
    echo "  -f, --filter <pattern>   Filter test files by pattern [default: tests/]"
    echo "  -h, --help              Show this help message"
    echo
    echo "Examples:"
    echo "  ./run_tests.sh                          # Run all tests with PostgreSQL"
    echo "  ./run_tests.sh -d sqlite              # Run all tests with SQLite"
    echo "  ./run_tests.sh -d sqlite -c -v        # Run with SQLite, coverage, and verbose output"
    echo "  ./run_tests.sh -m 'not slow'           # Skip slow tests"
    echo "  ./run_tests.sh -f 'tests/unit/'        # Run only unit tests"
    echo "  ./run_tests.sh -p                      # Run tests in parallel"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--database)
            DATABASE="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -f|--filter)
            PATTERN="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate database type
if [[ "$DATABASE" != "sqlite" && "$DATABASE" != "postgres" ]]; then
    echo -e "${RED}Error: Invalid database type. Use 'sqlite' or 'postgres'${NC}"
    exit 1
fi

# Build pytest command
PYTEST_CMD="pytest $PATTERN"

# Add options based on flags
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=term-missing --cov-report=html"
fi

if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m \"$MARKERS\""
fi

if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

# Setup database-specific configuration
if [ "$DATABASE" = "postgres" ]; then
    echo -e "${YELLOW}Setting up PostgreSQL test database...${NC}"
    
    # Check if PostgreSQL is running
    if ! pg_isready > /dev/null 2>&1; then
        echo -e "${RED}Error: PostgreSQL is not running${NC}"
        echo "Please start PostgreSQL:"
        echo "  macOS:    brew services start postgresql"
        echo "  Linux:    sudo service postgresql start"
        echo "  Windows:  net start postgresql"
        exit 1
    fi
    
    # Setup test database
    if ! python scripts/setup_test_db.py; then
        echo -e "${RED}Error: Failed to setup PostgreSQL test database${NC}"
        exit 1
    fi
    
    # Set environment variables for PostgreSQL
    export TEST_DATABASE="postgres"
    export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/test_db"
    
    # Add PostgreSQL-specific markers
    if [ -n "$MARKERS" ]; then
        MARKERS="$MARKERS and not skip_postgres"
    else
        MARKERS="not skip_postgres"
    fi
    PYTEST_CMD="$PYTEST_CMD -m \"$MARKERS\""
else
    # Set environment variables for SQLite
    export TEST_DATABASE="sqlite"
fi

# Print test configuration
echo -e "${GREEN}Running tests with configuration:${NC}"
echo "Database: $DATABASE"
echo "Coverage: $COVERAGE"
echo "Verbose: $VERBOSE"
echo "Markers: ${MARKERS:-none}"
echo "Parallel: $PARALLEL"
echo "Pattern: $PATTERN"
echo

# Run the tests
echo -e "${GREEN}Running tests...${NC}"
echo "$PYTEST_CMD"
eval "$PYTEST_CMD"

# Check exit status
STATUS=$?

# Display coverage report location if generated
if [ "$COVERAGE" = true ]; then
    echo -e "\n${GREEN}Coverage report generated:${NC}"
    echo "HTML report: ./htmlcov/index.html"
fi

# Exit with pytest status
exit $STATUS 