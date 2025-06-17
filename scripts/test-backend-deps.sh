#!/bin/bash

# Quick Backend Dependencies Test
# This script tests if backend dependencies can be installed successfully

echo "🔍 Testing Backend Dependencies Installation..."

# Check Python version
echo "Python version: $(python3 --version)"

# Test pip install with newer dependency-injector version
echo ""
echo "🧪 Testing dependency installation with newer dependency-injector..."

# Create a temporary requirements file with updated dependency-injector
cp backend/requirements.txt backend/requirements.txt.backup
sed 's/dependency-injector==4.41.0/dependency-injector==4.42.0/' backend/requirements.txt > backend/requirements-test.txt

# Test installation (dry run)
echo "Testing with dependency-injector 4.42.0..."
if python3 -m pip install --dry-run -r backend/requirements-test.txt >/dev/null 2>&1; then
    echo "✅ Dependencies appear installable with newer version"
    echo "   Updating requirements.txt to use dependency-injector 4.42.0"
    cp backend/requirements-test.txt backend/requirements.txt
else
    echo "❌ Dependencies still have issues with newer version"
    echo "   Keeping original requirements.txt"
fi

# Cleanup
rm -f backend/requirements-test.txt

echo ""
echo "🔧 Recommendation: Use Python 3.11 in CI/CD to avoid compilation issues"
echo "   (Already configured in .github/workflows/ci-cd-pipeline.yml)"
