#!/bin/bash

# Exit on error
set -e

echo "Pathfinder Test Runner"
echo "======================"

# Determine the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Set default values
COVERAGE=1
VERBOSE=0
BACKEND_ONLY=0
FRONTEND_ONLY=0
COMPONENTS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --no-coverage)
      COVERAGE=0
      shift
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    --backend)
      BACKEND_ONLY=1
      shift
      ;;
    --frontend)
      FRONTEND_ONLY=1
      shift
      ;;
    --component)
      COMPONENTS="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option: $key"
      exit 1
      ;;
  esac
done

# Function to run backend tests
run_backend_tests() {
  echo ""
  echo "Running Backend Tests"
  echo "--------------------"
  cd "$PROJECT_ROOT/backend"
  
  # Check if python environment is activated
  if [ -z "$VIRTUAL_ENV" ]; then
    echo "Creating virtual environment for testing..."
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
  fi
  
  # Run linting
  echo "Running linters..."
  black --check .
  flake8 .
  
  # Run tests
  if [ $COVERAGE -eq 1 ]; then
    if [ -n "$COMPONENTS" ]; then
      echo "Running tests with coverage for components: $COMPONENTS"
      python -m pytest tests/test_$COMPONENTS.py -v --cov=app --cov-report=term --cov-report=xml
    else
      echo "Running all tests with coverage..."
      python -m pytest -v --cov=app --cov-report=term --cov-report=xml
    fi
  else
    if [ -n "$COMPONENTS" ]; then
      echo "Running tests for components: $COMPONENTS"
      python -m pytest tests/test_$COMPONENTS.py -v
    else
      echo "Running all tests..."
      python -m pytest -v
    fi
  fi
}

# Function to run frontend tests
run_frontend_tests() {
  echo ""
  echo "Running Frontend Tests"
  echo "--------------------"
  cd "$PROJECT_ROOT/frontend"
  
  # Install dependencies if needed
  if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
  fi
  
  # Run linting
  echo "Running linters..."
  npm run lint
  npm run type-check
  
  # Run tests
  if [ $COVERAGE -eq 1 ]; then
    echo "Running tests with coverage..."
    npm run test:coverage
  else
    echo "Running tests..."
    npm test
  fi
}

# Main execution
if [ $FRONTEND_ONLY -eq 1 ]; then
  run_frontend_tests
elif [ $BACKEND_ONLY -eq 1 ]; then
  run_backend_tests
else
  run_backend_tests
  run_frontend_tests
fi

echo ""
echo "Tests completed successfully!"