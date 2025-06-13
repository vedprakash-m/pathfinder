#!/bin/bash
# CI/CD Failure Diagnostic and Fix Script
# Helps identify and resolve common CI/CD pipeline issues

set -e

echo "🔧 Pathfinder CI/CD Failure Diagnostic"
echo "======================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_action() {
    echo -e "${YELLOW}👉 $1${NC}"
}

print_header "Common CI/CD Failure Causes"

echo "Let's identify why your CI/CD pipeline failed:"
echo ""

print_header "1. GitHub Secrets Check"

echo "The most common cause is missing GitHub repository secrets."
echo ""
echo "Required secrets for your CI/CD pipeline:"
echo ""
echo "🔐 Core Infrastructure Secrets:"
echo "   • AZURE_CREDENTIALS - Service principal JSON"
echo "   • SQL_ADMIN_USERNAME - Database admin username"
echo "   • SQL_ADMIN_PASSWORD - Database admin password"
echo ""
echo "🔐 Optional but Recommended:"
echo "   • OPENAI_API_KEY - For AI features"
echo ""

print_action "To check/configure GitHub secrets:"
echo "1. Go to: https://github.com/vedprakash-m/pathfinder/settings/secrets/actions"
echo "2. Verify all required secrets are listed"
echo "3. If missing, follow: docs/GITHUB_SECRETS_SETUP.md"
echo ""

print_header "2. Workflow Trigger Analysis"

# Check what triggered the last workflow
echo "Analyzing what triggered the CI/CD pipeline..."
echo ""

# Check if infrastructure files were changed in last commit
if git diff --name-only HEAD~1 HEAD | grep -q "infrastructure/"; then
    print_info "Infrastructure files were changed - this triggered the infrastructure deployment workflow"
    echo "Files changed:"
    git diff --name-only HEAD~1 HEAD | grep "infrastructure/" | sed 's/^/   • /'
    echo ""
fi

# Check if regular code files were changed
if git diff --name-only HEAD~1 HEAD | grep -E "(backend/|frontend/|\.github/workflows/ci-cd)" > /dev/null; then
    print_info "Application code was changed - this triggered the main CI/CD workflow"
    echo ""
fi

print_header "3. Quick Diagnostic Commands"

echo "Run these commands to diagnose the issue:"
echo ""

echo "🔍 Check GitHub Actions logs:"
echo "   Visit: https://github.com/vedprakash-m/pathfinder/actions"
echo ""

echo "🔍 Test Azure authentication locally:"
echo "   az account show"
echo ""

echo "🔍 Validate Bicep template locally:"
echo "   az deployment group validate \\"
echo "     --resource-group pathfinder-rg \\"
echo "     --template-file infrastructure/bicep/pathfinder-single-rg.bicep \\"
echo "     --parameters appName=pathfinder location=eastus \\"
echo "     sqlAdminLogin=testuser sqlAdminPassword='TestPass123!'"
echo ""

print_header "4. Quick Fixes"

echo "Based on common issues, try these fixes:"
echo ""

print_action "Fix 1: Configure Missing Secrets"
echo "If secrets are missing:"
echo "   • Follow the complete guide: docs/GITHUB_SECRETS_SETUP.md"
echo "   • Or use the helper script: ./scripts/setup-github-secrets-helper.sh"
echo ""

print_action "Fix 2: Skip Infrastructure Deployment Temporarily"
echo "If you just want to test the application CI/CD:"
echo "   • Make a small change to backend or frontend code"
echo "   • Push without changing infrastructure/ files"
echo "   • This will skip infrastructure deployment"
echo ""

print_action "Fix 3: Manual Infrastructure Deployment"
echo "Deploy infrastructure manually first:"
echo "   • Set up secrets following docs/GITHUB_SECRETS_SETUP.md"
echo "   • Run: ./scripts/deploy-single-rg.sh"
echo "   • Then retry CI/CD pipeline"
echo ""

print_action "Fix 4: Emergency Deploy (Skip Tests)"
echo "For urgent deploys, skip quality checks:"
echo "   • Go to: https://github.com/vedprakash-m/pathfinder/actions/workflows/ci-cd-pipeline.yml"
echo "   • Click 'Run workflow'"
echo "   • Check 'Skip quality checks (emergency deploy)'"
echo ""

print_header "5. Step-by-Step Recovery"

echo "Follow these steps to get CI/CD working:"
echo ""
echo "Step 1️⃣  Configure GitHub Secrets"
echo "   → Use guide: docs/GITHUB_SECRETS_SETUP.md"
echo ""
echo "Step 2️⃣  Test Local Deployment"
echo "   → Run: ./scripts/verify-cicd-setup.sh"
echo "   → Run: ./scripts/deploy-single-rg.sh"
echo ""
echo "Step 3️⃣  Test CI/CD Pipeline"
echo "   → Make a small change (e.g., update README.md)"
echo "   → Push to main branch"
echo "   → Monitor: https://github.com/vedprakash-m/pathfinder/actions"
echo ""

print_header "6. Get Help"

echo "If you're still stuck:"
echo ""
echo "📋 Gather this information:"
echo "   • GitHub Actions error logs"
echo "   • Output from: az account show"
echo "   • List of configured GitHub secrets"
echo ""
echo "📞 Resources:"
echo "   • GitHub Actions docs: https://docs.github.com/en/actions"
echo "   • Azure CLI docs: https://docs.microsoft.com/en-us/cli/azure/"
echo "   • Pathfinder setup guide: docs/GITHUB_SECRETS_SETUP.md"
echo ""

print_success "Diagnostic complete!"
echo ""
print_action "Most likely fix: Configure GitHub secrets following docs/GITHUB_SECRETS_SETUP.md"
echo ""
