#!/bin/bash
# Pathfinder Production Setup Script
# This script automates the configuration of production environment variables

set -e  # Exit on any error

echo "🚀 Pathfinder Production Setup"
echo "==============================="
echo ""
echo "This script will configure your production environment variables."
echo "Make sure you have the following ready:"
echo "- Auth0 application credentials"
echo "- OpenAI API key"
echo "- Google Maps API key"
echo "- SendGrid API key (optional)"
echo ""

# Check if required tools are installed
command -v az >/dev/null 2>&1 || { 
    echo "❌ Azure CLI is required but not installed."
    echo "Please install it from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Set Azure variables
RESOURCE_GROUP="pathfinder-rg-dev"
BACKEND_APP="pathfinder-backend"
FRONTEND_APP="pathfinder-frontend"

echo "🔐 Azure Login Check"
if ! az account show &>/dev/null; then
    echo "Please log in to Azure:"
    az login
fi

echo "✅ Logged in to Azure"
echo ""

# Check if resource group exists
if ! az group show --name $RESOURCE_GROUP &>/dev/null; then
    echo "❌ Resource group '$RESOURCE_GROUP' not found."
    echo "Please make sure the infrastructure is deployed first."
    exit 1
fi

echo "✅ Resource group found: $RESOURCE_GROUP"
echo ""

# Function to read password securely
read_secret() {
    local prompt="$1"
    local var_name="$2"
    
    echo -n "$prompt: "
    read -s value
    echo ""
    
    if [ -z "$value" ]; then
        echo "❌ $var_name cannot be empty"
        return 1
    fi
    
    eval "$var_name='$value'"
    return 0
}

# Function to read normal input
read_input() {
    local prompt="$1"
    local var_name="$2"
    local example="$3"
    
    echo -n "$prompt"
    if [ ! -z "$example" ]; then
        echo -n " (e.g., $example)"
    fi
    echo -n ": "
    read value
    
    if [ -z "$value" ]; then
        echo "❌ $var_name cannot be empty"
        return 1
    fi
    
    eval "$var_name='$value'"
    return 0
}

echo "📝 Configuration Input"
echo "======================"

# Auth0 Configuration
echo ""
echo "🔐 Auth0 Configuration"
echo "----------------------"
read_input "Auth0 Domain" AUTH0_DOMAIN "your-tenant.auth0.com"
read_input "Auth0 Client ID" AUTH0_CLIENT_ID
read_secret "Auth0 Client Secret" AUTH0_CLIENT_SECRET

# OpenAI Configuration
echo ""
echo "🤖 OpenAI Configuration"
echo "-----------------------"
read_secret "OpenAI API Key" OPENAI_API_KEY

# Google Maps Configuration
echo ""
echo "🗺️ Google Maps Configuration"
echo "----------------------------"
read_secret "Google Maps API Key" GOOGLE_MAPS_API_KEY

# SendGrid Configuration (optional)
echo ""
echo "📧 Email Configuration (Optional)"
echo "--------------------------------"
read -p "Do you want to configure SendGrid for email notifications? (y/n): " configure_email

if [[ $configure_email == "y" || $configure_email == "Y" ]]; then
    read_secret "SendGrid API Key" SENDGRID_API_KEY
    read_input "From Email Address" FROM_EMAIL "noreply@yourdomain.com"
else
    SENDGRID_API_KEY=""
    FROM_EMAIL="noreply@pathfinder.com"
fi

# Generate secure secret keys
echo ""
echo "🔑 Generating Security Keys"
echo "============================"

# Generate a secure secret key
SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
echo "✅ Generated SECRET_KEY"

# Generate CSRF secret key
CSRF_SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
echo "✅ Generated CSRF_SECRET_KEY"

echo ""
echo "🔧 Updating Container Apps Configuration"
echo "========================================"

echo "📱 Updating backend configuration..."

# Build backend environment variables array
backend_env_vars=(
    "SECRET_KEY=$SECRET_KEY"
    "CSRF_SECRET_KEY=$CSRF_SECRET_KEY"
    "AUTH0_DOMAIN=$AUTH0_DOMAIN"
    "AUTH0_CLIENT_ID=$AUTH0_CLIENT_ID"
    "AUTH0_CLIENT_SECRET=$AUTH0_CLIENT_SECRET"
    "AUTH0_AUDIENCE=https://pathfinder-api.com"
    "AUTH0_ISSUER=https://$AUTH0_DOMAIN/"
    "OPENAI_API_KEY=$OPENAI_API_KEY"
    "GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY"
    "ENVIRONMENT=production"
    "DEBUG=false"
    "AI_DAILY_BUDGET_LIMIT=50.0"
    "AI_REQUEST_LIMIT_PER_HOUR=100"
    "CORS_ORIGINS=[\"https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io\"]"
    "ALLOWED_HOSTS=[\"pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io\"]"
)

# Add email configuration if provided
if [ ! -z "$SENDGRID_API_KEY" ]; then
    backend_env_vars+=("SENDGRID_API_KEY=$SENDGRID_API_KEY")
    backend_env_vars+=("FROM_EMAIL=$FROM_EMAIL")
    backend_env_vars+=("FROM_NAME=Pathfinder")
fi

# Update backend container app
if az containerapp update \
    --name $BACKEND_APP \
    --resource-group $RESOURCE_GROUP \
    --set-env-vars "${backend_env_vars[@]}" \
    --output none; then
    echo "✅ Backend configuration updated successfully"
else
    echo "❌ Failed to update backend configuration"
    exit 1
fi

echo "🌐 Updating frontend configuration..."

# Build frontend environment variables array
frontend_env_vars=(
    "VITE_AUTH0_DOMAIN=$AUTH0_DOMAIN"
    "VITE_AUTH0_CLIENT_ID=$AUTH0_CLIENT_ID"
    "VITE_AUTH0_AUDIENCE=https://pathfinder-api.com"
    "VITE_API_BASE_URL=https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
    "VITE_GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY"
    "VITE_ENVIRONMENT=production"
)

# Update frontend container app
if az containerapp update \
    --name $FRONTEND_APP \
    --resource-group $RESOURCE_GROUP \
    --set-env-vars "${frontend_env_vars[@]}" \
    --output none; then
    echo "✅ Frontend configuration updated successfully"
else
    echo "❌ Failed to update frontend configuration"
    exit 1
fi

echo ""
echo "🎉 Production Setup Complete!"
echo "============================="
echo ""
echo "🌐 Application URLs:"
echo "   Frontend:  https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo "   Backend:   https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo "   API Docs:  https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/docs"
echo ""
echo "⏳ Container apps are restarting with new configuration..."
echo "   This may take 2-3 minutes to complete."
echo ""
echo "📋 Next Steps:"
echo "   1. Wait for containers to restart (check Azure Portal)"
echo "   2. Test authentication workflow"
echo "   3. Create a test family and trip"
echo "   4. Verify AI itinerary generation"
echo "   5. Test end-to-end user journey"
echo ""
echo "🔍 To check status:"
echo "   az containerapp show --name $BACKEND_APP --resource-group $RESOURCE_GROUP --query 'properties.latestRevisionName'"
echo "   az containerapp show --name $FRONTEND_APP --resource-group $RESOURCE_GROUP --query 'properties.latestRevisionName'"
echo ""
echo "🔧 To view logs:"
echo "   az containerapp logs show --name $BACKEND_APP --resource-group $RESOURCE_GROUP --follow"
echo ""

# Test if the backend is responding
echo "🧪 Testing backend health..."
sleep 10  # Give it a moment to start

for i in {1..12}; do  # Try for 2 minutes
    if curl -s "https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/health" >/dev/null 2>&1; then
        echo "✅ Backend is responding!"
        break
    else
        echo "⏳ Waiting for backend to start... (attempt $i/12)"
        sleep 10
    fi
done

echo ""
echo "🎯 Configuration Summary:"
echo "   ✅ Auth0: Configured"
echo "   ✅ OpenAI: Configured"
echo "   ✅ Google Maps: Configured"
if [ ! -z "$SENDGRID_API_KEY" ]; then
    echo "   ✅ SendGrid: Configured"
else
    echo "   ⚠️ SendGrid: Not configured (optional)"
fi
echo "   ✅ Security: Keys generated"
echo "   ✅ CORS: Production URLs set"
echo ""
echo "🚀 Your Pathfinder application is now ready for production use!"
