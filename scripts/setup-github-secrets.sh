#!/bin/bash
# GitHub Secrets Setup Script for Pathfinder CI/CD
# This script helps you configure GitHub repository secrets

set -e

echo "🔐 GitHub Secrets Setup for Pathfinder CI/CD"
echo "============================================="
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI is required but not installed."
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if logged into GitHub
if ! gh auth status &> /dev/null; then
    echo "🔑 Please login to GitHub CLI:"
    gh auth login
fi

echo "✅ GitHub CLI authenticated"
echo ""

# Check if in correct repository
REPO_NAME=$(gh repo view --json name -q .name 2>/dev/null || echo "")
if [ "$REPO_NAME" != "pathfinder" ]; then
    echo "❌ Please run this script from the pathfinder repository root"
    exit 1
fi

echo "📋 Setting up secrets for repository: $(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo ""

# Function to set secret with confirmation
set_secret() {
    local secret_name="$1"
    local description="$2"
    local example="$3"
    
    echo "🔐 Setting up: $secret_name"
    echo "Description: $description"
    if [ ! -z "$example" ]; then
        echo "Example: $example"
    fi
    echo ""
    
    read -sp "Enter value for $secret_name: " secret_value
    echo ""
    
    if [ -z "$secret_value" ]; then
        echo "⚠️  Skipping empty value for $secret_name"
        echo ""
        return
    fi
    
    gh secret set "$secret_name" --body "$secret_value"
    echo "✅ Set $secret_name"
    echo ""
}

echo "🚀 Let's set up your GitHub repository secrets!"
echo ""

# Azure Service Principal
echo "📝 First, create an Azure Service Principal:"
echo "Run this command in Azure CLI:"
echo ""
echo "az ad sp create-for-rbac \\"
echo "  --name 'pathfinder-github-actions' \\"
echo "  --role 'Contributor' \\"
echo "  --scopes '/subscriptions/YOUR_SUBSCRIPTION_ID' \\"
echo "  --sdk-auth"
echo ""
echo "Copy the entire JSON output for the AZURE_CREDENTIALS secret."
echo ""

read -p "Press Enter when you've created the service principal..."

# Set secrets
set_secret "AZURE_CREDENTIALS" "Service principal JSON from Azure CLI" '{"clientId":"...","clientSecret":"...","subscriptionId":"...","tenantId":"..."}'

set_secret "AZURE_SUBSCRIPTION_ID" "Your Azure subscription ID" "12345678-1234-1234-1234-123456789012"

set_secret "AZURE_RG" "Azure resource group name" "pathfinder-rg-prod"

set_secret "SQL_ADMIN_LOGIN" "Database admin username" "pathfinderadmin"

set_secret "SQL_ADMIN_PASSWORD" "Strong database password (12+ chars)" "(hidden)"

set_secret "OPENAI_API_KEY" "OpenAI API key for AI features" "sk-..."

echo "🎯 Optional: Azure Entra ID configuration (skip if not using authentication)"
echo ""

read -p "Do you want to configure Azure Entra ID? (y/N): " configure_azure
if [[ "$configure_azure" =~ ^[Yy]$ ]]; then
    set_secret "AZURE_TENANT_ID" "Azure Tenant ID" "your-tenant-id"
    set_secret "AZURE_CLIENT_ID" "Azure Client ID" "your-client-id"
    set_secret "AZURE_CLIENT_SECRET" "Azure Client Secret" "(hidden)"
fi

echo ""
echo "🎉 GitHub Secrets Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Push to main branch to trigger deployment"
echo "2. Monitor at: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions"
echo "3. Check deployment status in Azure Portal"
echo ""
echo "🚀 Ready for production deployment!" 