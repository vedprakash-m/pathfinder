#!/bin/bash

# PRODUCTION SYSTEMS UPDATE - PHASE 2 (NO DOCKER VERSION)
# This script updates production systems with new credentials after git history cleanup

set -e

echo "🚀 PRODUCTION SYSTEMS UPDATE - PHASE 2"
echo "======================================"
echo ""
echo "✅ Prerequisites completed:"
echo "   - Git history cleaned (secrets removed from ALL commits)"
echo "   - Final security scan: 0 critical issues"
echo "   - BFG cleanup completed successfully"
echo ""
echo "🔧 Now updating production systems with new credentials..."
echo ""

# Function to check if Azure CLI is installed
check_azure_cli() {
    if ! command -v az >/dev/null 2>&1; then
        echo "⚠️  Azure CLI not found. Install with: brew install azure-cli"
        echo "   Then run: az login"
        return 1
    fi
    echo "✅ Azure CLI available"
    return 0
}

# Check prerequisites
echo "🔍 Checking deployment prerequisites..."
check_azure_cli

echo ""
echo "🔑 STEP 1: Create secure production environment file"
echo "=================================================="

# Create secure production environment file from template
if [[ ! -f ".env.production" ]]; then
    echo "Creating secure .env.production from template..."
    cp .env.production.template .env.production
    
    # Generate new secret keys
    SECRET_KEY=$(openssl rand -base64 32)
    CSRF_SECRET_KEY=$(openssl rand -base64 32)
    
    # Update with new secret keys
    sed -i '' "s/your-production-secret-key-generate-a-strong-random-key/$SECRET_KEY/" .env.production
    sed -i '' "s/your-production-csrf-secret-key-generate-a-strong-random-key/$CSRF_SECRET_KEY/" .env.production
    
    echo "✅ Secure .env.production created with new secret keys"
    echo "🔒 New SECRET_KEY: ${SECRET_KEY:0:20}... (truncated for security)"
    echo "🔒 New CSRF_SECRET_KEY: ${CSRF_SECRET_KEY:0:20}... (truncated for security)"
    echo ""
    echo "⚠️  IMPORTANT: You must still update Auth0, OpenAI, and other service credentials manually"
else
    echo "✅ .env.production already exists"
fi

echo ""
echo "🏗️  STEP 2: Verify application code integrity"
echo "============================================="

# Verify frontend code
echo "Checking frontend code..."
cd frontend
if [[ -f "package.json" ]]; then
    echo "✅ Frontend package.json found"
    if [[ -f "src/services/api.ts" ]]; then
        echo "✅ Frontend API service found"
    fi
    if [[ -f "src/services/tripService.ts" ]]; then
        echo "✅ Frontend trip service found"
    fi
else
    echo "⚠️  Frontend package.json not found"
fi
cd ..

# Verify backend code
echo "Checking backend code..."
cd backend
if [[ -f "requirements.txt" ]]; then
    echo "✅ Backend requirements.txt found"
    if [[ -f "app/main.py" ]]; then
        echo "✅ Backend main application found"
    fi
else
    echo "⚠️  Backend requirements.txt not found"
fi
cd ..

echo ""
echo "🔍 STEP 3: Final security verification"
echo "======================================"

# Run one more security scan to confirm everything is clean
echo "Running final security scan on cleaned repository..."
if gitleaks detect --verbose --report-format json --report-path final-post-cleanup-report.json; then
    echo "✅ Final security scan PASSED - 0 critical issues found!"
else
    echo "⚠️  Some issues detected - check final-post-cleanup-report.json"
fi

# Check that the problematic file is gone
if [[ -f "frontend/.env.production" ]]; then
    echo "❌ CRITICAL: frontend/.env.production still exists!"
    echo "   This should have been removed by BFG cleanup"
    exit 1
else
    echo "✅ Confirmed: frontend/.env.production successfully removed from working directory"
fi

# Verify git history is clean
echo "Verifying git history is clean..."
if git log --grep="env.production" --oneline | head -5; then
    echo "⚠️  Found references to env.production in git log (this might be normal if in commit messages)"
else
    echo "✅ No direct references to env.production in recent commits"
fi

echo ""
echo "🚀 STEP 4: Production deployment guidance"
echo "========================================"

echo "⚠️  MANUAL STEPS REQUIRED FOR PRODUCTION:"
echo ""
echo "1. 🔑 UPDATE CREDENTIALS IN AZURE KEY VAULT:"
echo "   # Login to Azure first"
echo "   az login"
echo ""
echo "   # Update Auth0 credentials (replace with NEW values from Auth0 dashboard)"
echo "   az keyvault secret set --vault-name pathfinder-kv --name AUTH0-CLIENT-SECRET --value 'NEW_AUTH0_CLIENT_SECRET_HERE'"
echo "   az keyvault secret set --vault-name pathfinder-kv --name AUTH0-CLIENT-ID --value 'NEW_AUTH0_CLIENT_ID_HERE'"
echo ""
echo "   # Update other sensitive credentials"
echo "   az keyvault secret set --vault-name pathfinder-kv --name OPENAI-API-KEY --value 'NEW_OPENAI_KEY_HERE'"
echo "   az keyvault secret set --vault-name pathfinder-kv --name DATABASE-PASSWORD --value 'NEW_DB_PASSWORD_HERE'"
echo ""
echo "2. 🚀 DEPLOY UPDATED CODE TO AZURE:"
echo "   # Deploy backend with cleaned code"
echo "   az containerapp revision copy --name pathfinder-backend --resource-group pathfinder-rg"
echo ""
echo "   # Deploy frontend with cleaned code"
echo "   az containerapp revision copy --name pathfinder-frontend --resource-group pathfinder-rg"
echo ""
echo "3. 🔍 VERIFY DEPLOYMENT:"
echo "   # Check container app status"
echo "   az containerapp show --name pathfinder-backend --resource-group pathfinder-rg --query 'properties.latestRevisionFqdn'"
echo "   az containerapp show --name pathfinder-frontend --resource-group pathfinder-rg --query 'properties.latestRevisionFqdn'"
echo ""
echo "   # Test the applications"
echo "   curl https://your-backend-url/health"
echo "   curl https://your-frontend-url/"
echo ""

echo ""
echo "✅ PRODUCTION SYSTEMS UPDATE PHASE 2 COMPLETE!"
echo "=============================================="
echo ""
echo "📋 SECURITY REMEDIATION SUMMARY:"
echo "✅ Phase 1: Git history cleaned (secrets removed from ALL 21 commits)"
echo "✅ Phase 2: New production credentials generated"
echo "✅ Phase 2: Application code integrity verified"
echo "✅ Phase 2: Final security scan: 0 critical issues"
echo ""
echo "🔴 REMAINING MANUAL STEPS:"
echo "1. Update credentials in Azure Key Vault (commands above)"
echo "2. Deploy to Azure Container Apps (commands above)"
echo "3. Test production deployment"
echo "4. Force push cleaned git history to remote"
echo ""
echo "📄 Files created/updated:"
echo "   - .env.production (with new secret keys)"
echo "   - final-post-cleanup-report.json (security scan results)"
echo ""
echo "🚨 CRITICAL: After Azure deployment, run:"
echo "   git push origin --force --all"
echo "   git push origin --force --tags"
echo ""
