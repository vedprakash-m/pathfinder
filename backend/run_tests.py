#!/usr/bin/env python3
"""
pytest runner script that sets up the test environment properly.
"""
import os
import sys
from pathlib import Path

# Get the backend directory
backend_dir = Path(__file__).parent
root_dir = backend_dir.parent

# Set environment variables before any imports
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["DISABLE_TELEMETRY"] = "true"

# Load additional test environment variables
env_test_file = backend_dir / ".env.test"
if env_test_file.exists():
    with open(env_test_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

# Add the backend directory to the Python path
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main(sys.argv[1:]))
