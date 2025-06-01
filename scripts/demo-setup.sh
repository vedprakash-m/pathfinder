#!/bin/bash
# Quick Demo Setup - Minimal Configuration for Testing
# This script sets up basic environment variables for immediate testing

set -e

echo "🎯 Pathfinder Demo Setup"
echo "========================"
echo ""
echo "This will configure minimal settings for testing the AI functionality."
echo "You'll only need an OpenAI API key to proceed."
echo ""

# Check Azure CLI
command -v az >/dev/null 2>&1 || { 
    echo "❌ Azure CLI is required but not installed."
    exit 1
}

RESOURCE_GROUP="pathfinder-rg-dev"
BACKEND_APP="pathfinder-backend"
FRONTEND_APP="pathfinder-frontend"

# Check login
if ! az account show &>/dev/null; then
    echo "Please log in to Azure:"
    az login
fi

echo "🤖 OpenAI API Configuration"
echo "============================"
echo ""
echo "To test AI itinerary generation, you need an OpenAI API key."
echo "Get one from: https://platform.openai.com/api-keys"
echo ""
echo -n "OpenAI API Key (sk-...): "
read -s OPENAI_API_KEY
echo ""

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OpenAI API key is required for AI functionality"
    exit 1
fi

echo ""
echo "🔑 Generating Security Keys"
echo "=========================="

# Generate secure keys
SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
CSRF_SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

echo "✅ Generated security keys"

echo ""
echo "🔧 Updating Backend Configuration"
echo "================================="

# Minimal backend configuration for AI testing
backend_env_vars=(
    "SECRET_KEY=$SECRET_KEY"
    "CSRF_SECRET_KEY=$CSRF_SECRET_KEY"
    "OPENAI_API_KEY=$OPENAI_API_KEY"
    "ENVIRONMENT=production"
    "DEBUG=false"
    "AI_DAILY_BUDGET_LIMIT=10.0"
    "AI_REQUEST_LIMIT_PER_HOUR=20"
    "CORS_ORIGINS=[\"*\"]"
    "AUTH_DISABLED=true"
    "DEMO_MODE=true"
)

# Update backend
if az containerapp update \
    --name $BACKEND_APP \
    --resource-group $RESOURCE_GROUP \
    --set-env-vars "${backend_env_vars[@]}" \
    --output none; then
    echo "✅ Backend configured for demo mode"
else
    echo "❌ Failed to update backend"
    exit 1
fi

echo ""
echo "🎉 Demo Setup Complete!"
echo "======================="
echo ""
echo "🌐 Application URLs:"
echo "   Frontend:  https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo "   Backend:   https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo "   API Docs:  https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/docs"
echo ""
echo "⏳ Waiting for backend to restart..."

# Wait for backend to be ready
sleep 15
for i in {1..6}; do
    if curl -s "https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/health" >/dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    else
        echo "⏳ Backend starting... (attempt $i/6)"
        sleep 10
    fi
done

echo ""
echo "🧪 Testing AI Functionality"
echo "==========================="

# Test itinerary generation endpoint
echo "Testing AI itinerary generation..."
if curl -s -X POST "https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/api/v1/test/ai" \
    -H "Content-Type: application/json" \
    -d '{"destination":"Paris","duration_days":3}' >/dev/null; then
    echo "✅ AI service is responding!"
else
    echo "⚠️ AI service may need a moment to initialize"
fi

echo ""
echo "🎯 What You Can Test Now:"
echo "========================="
echo "1. Visit the API docs to explore endpoints"
echo "2. Test AI itinerary generation via API"
echo "3. Create trips and test core functionality"
echo ""
echo "🔧 To add full authentication later, run:"
echo "   ./scripts/production-setup.sh"
echo ""
