#!/bin/bash
# CI/CD Security Enhancement Setup Script
# This script helps implement the security recommendations from the CI/CD review

set -e

echo "🔐 Pathfinder CI/CD Security Enhancement Setup"
echo "=============================================="
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

# Check prerequisites
print_header "Checking Prerequisites"

if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI is required but not installed."
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    print_error "Not logged into GitHub CLI. Please run 'gh auth login' first."
    exit 1
fi

print_success "Prerequisites check passed"

# Check current secrets
print_header "Current GitHub Secrets Status"

REQUIRED_SECRETS=(
    "AZURE_CREDENTIALS"
    "SQL_ADMIN_USERNAME" 
    "SQL_ADMIN_PASSWORD"
    "OPENAI_API_KEY"
    "AUTH0_DOMAIN"
    "AUTH0_CLIENT_ID"
    "AUTH0_AUDIENCE"
)

OPTIONAL_SECRETS=(
    "SNYK_TOKEN"
    "SLACK_WEBHOOK_URL"
    "EMAIL_USERNAME"
    "EMAIL_PASSWORD"
)

echo "Required secrets:"
for secret in "${REQUIRED_SECRETS[@]}"; do
    if gh secret list | grep -q "$secret"; then
        print_success "$secret (configured)"
    else
        print_error "$secret (missing)"
    fi
done

echo ""
echo "Optional security secrets:"
for secret in "${OPTIONAL_SECRETS[@]}"; do
    if gh secret list | grep -q "$secret"; then
        print_success "$secret (configured)"
    else
        print_warning "$secret (not configured)"
    fi
done

# Setup missing secrets
print_header "Setting Up Missing Security Secrets"

if ! gh secret list | grep -q "SNYK_TOKEN"; then
    print_info "SNYK_TOKEN is required for dependency vulnerability scanning"
    echo "1. Go to https://snyk.io and create a free account"
    echo "2. Go to Account Settings > API Token"
    echo "3. Copy your token"
    echo ""
    read -p "Enter your Snyk token (or press Enter to skip): " snyk_token
    if [ ! -z "$snyk_token" ]; then
        gh secret set SNYK_TOKEN --body "$snyk_token"
        print_success "SNYK_TOKEN configured"
    else
        print_warning "SNYK_TOKEN skipped (security scanning will be disabled)"
    fi
fi

# Test workflows
print_header "Testing Workflows"

echo "Available workflows to test:"
echo "1. Security Scanning (requires SNYK_TOKEN)"
echo "2. Cost Monitoring" 
echo "3. Performance Monitoring"
echo "4. Main CI/CD Pipeline"
echo ""

read -p "Would you like to test the workflows? (y/N): " test_workflows

if [[ "$test_workflows" =~ ^[Yy]$ ]]; then
    print_info "Creating a test branch for workflow validation..."
    
    # Create test branch
    BRANCH_NAME="security-enhancements-test-$(date +%s)"
    git checkout -b "$BRANCH_NAME"
    
    # Commit our changes
    git add .
    git commit -m "feat: add security enhancements and monitoring workflows

- Add security scanning workflow with Snyk, Trivy, GitLeaks, and CodeQL
- Add cost monitoring with budget alerts
- Add performance monitoring with k6 and Lighthouse
- Fix hardcoded secrets in Bicep templates
- Add rollback mechanism to CI/CD pipeline
- Create security policy documentation
- Update resume script with Auth0 parameters

Security improvements:
- Remove hardcoded Auth0 credentials from infrastructure
- Add comprehensive security scanning
- Implement proper secret management
- Add automated cost monitoring"
    
    git push origin "$BRANCH_NAME"
    
    print_success "Test branch created: $BRANCH_NAME"
    print_info "Monitor the workflow execution at: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions"
    
    echo ""
    echo "After testing, you can:"
    echo "1. Create a PR to merge changes to main"
    echo "2. Or merge directly: git checkout main && git merge $BRANCH_NAME"
else
    print_info "Workflow testing skipped"
fi

# Summary
print_header "Setup Summary"

echo "✅ Security enhancements implemented:"
echo "   • Security scanning workflow created"
echo "   • Hardcoded secrets removed from Bicep templates"
echo "   • Security policy documentation added"
echo "   • Cost monitoring workflow added"
echo "   • Performance monitoring workflow added"
echo ""

echo "📋 Next steps:"
echo "1. Configure missing secrets (especially SNYK_TOKEN)"
echo "2. Test workflows in a feature branch"
echo "3. Monitor security scan results"
echo "4. Set up cost alerts and notifications"
echo "5. Review and tune performance thresholds"
echo ""

echo "📊 Expected improvements:"
echo "   • Zero critical vulnerabilities in production"
echo "   • Automated cost monitoring and alerts"
echo "   • Improved deployment reliability (>95% success rate)"
echo "   • Faster incident response with proper notifications"
echo ""

print_success "Security enhancement setup complete!"
echo ""
print_info "For questions or issues, refer to the security policy: SECURITY.md"
