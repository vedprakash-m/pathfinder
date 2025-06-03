#!/bin/bash

# filepath: /Users/vedprakashmishra/pathfinder/llm_orchestration/start_service.sh

set -e

echo "Starting LLM Orchestration Service..."

# Check if Python 3.11+ is available
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.11 or higher is required. Found: $python_version"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs
mkdir -p data

# Start Redis if not running (for local development)
if ! pgrep -f redis-server > /dev/null; then
    echo "Starting Redis server..."
    if command -v redis-server &> /dev/null; then
        redis-server --daemonize yes --port 6379
        sleep 2
    else
        echo "Warning: Redis not found. Please start Redis manually or use Docker."
    fi
fi

# Run database migrations (if needed)
# python3 migrate.py

# Start the service
echo "Starting LLM Orchestration service on port 8000..."
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload --log-level info

echo "Service started successfully!"
echo "Health check: http://localhost:8000/api/v1/health"
echo "API docs: http://localhost:8000/docs"
