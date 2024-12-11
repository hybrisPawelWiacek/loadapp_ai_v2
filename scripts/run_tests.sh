#!/bin/bash

# Default values
VERBOSE=""
PARALLEL=""
TEST_PATH="tests/"
COVERAGE=""
MARKERS=""

# Parse command line arguments
while getopts "vpf:m:c" opt; do
  case $opt in
    v)
      VERBOSE="-v"
      ;;
    p)
      PARALLEL="-n auto"
      ;;
    f)
      TEST_PATH="$OPTARG"
      ;;
    m)
      MARKERS="-m $OPTARG"
      ;;
    c)
      COVERAGE="--cov=backend --cov=frontend --cov-report=html:reports/coverage"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Ensure virtual environment is active and dependencies are installed
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    else
        echo "Creating virtual environment..."
        python -m venv venv
        source venv/bin/activate
    fi
fi

# Install or upgrade dependencies
echo "Installing/upgrading dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup test environment
echo "Setting up test environment..."
python scripts/setup_test_db.py
if [ $? -ne 0 ]; then
    echo "Failed to setup test database!"
    exit 1
fi

# Run the tests
echo "Running tests..."
PYTHONPATH=. pytest $VERBOSE $PARALLEL $TEST_PATH $MARKERS $COVERAGE \
    --tb=short \
    --strict-markers \
    --color=yes \
    -p no:warnings

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "All tests passed!"
    exit 0
else
    echo "Some tests failed!"
    exit 1
fi 