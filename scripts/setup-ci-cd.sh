#!/bin/bash

# Pathfinder CI/CD Setup Script
# This script helps set up Azure credentials and GitHub secrets for the CI/CD pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SUBSCRIPTION_ID=""
RESOURCE_GROUP_PREFIX="rg-pathfinder"
APP_NAME="pathfinder"
LOCATION="eastus"

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

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        echo "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    print_success "Azure CLI is installed"
    
    # Check if GitHub CLI is installed (optional)
    if command -v gh &> /dev/null; then
        print_success "GitHub CLI is installed"
        GH_CLI_AVAILABLE=true
    else
        print_warning "GitHub CLI is not installed. You'll need to set secrets manually."
        GH_CLI_AVAILABLE=false
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_error "jq is not installed. Please install it first."
        echo "On macOS: brew install jq"
        echo "On Ubuntu: sudo apt-get install jq"
        exit 1
    fi
    print_success "jq is installed"
}

azure_login() {
    print_header "Azure Authentication"
    
    echo "Please log in to Azure..."
    az login
    
    # Get subscription ID if not provided
    if [ -z "$SUBSCRIPTION_ID" ]; then
        echo ""
        echo "Available subscriptions:"
        az account list --output table
        echo ""
        read -p "Enter your Azure Subscription ID: " SUBSCRIPTION_ID
    fi
    
    # Set the subscription
    az account set --subscription "$SUBSCRIPTION_ID"
    print_success "Set active subscription to: $SUBSCRIPTION_ID"
}

create_service_principal() {
    print_header "Creating Service Principal"
    
    SP_NAME="pathfinder-github-actions"
    
    print_info "Creating service principal: $SP_NAME"
    
    # Create service principal with Contributor role
    SP_OUTPUT=$(az ad sp create-for-rbac \
        --name "$SP_NAME" \
        --role "Contributor" \
        --scopes "/subscriptions/$SUBSCRIPTION_ID" \
        --sdk-auth 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        print_success "Service principal created successfully"
        echo ""
        print_info "AZURE_CREDENTIALS secret value:"
        echo "Copy this JSON and add it as a GitHub secret named AZURE_CREDENTIALS:"
        echo ""
        echo "$SP_OUTPUT" | jq .
        echo ""
        
        # Save to file for reference
        echo "$SP_OUTPUT" > azure-credentials.json
        print_info "Also saved to azure-credentials.json (delete this file after setting up secrets)"
        echo ""
    else
        print_error "Failed to create service principal"
        exit 1
    fi
}

generate_secrets_template() {
    print_header "Generating GitHub Secrets Template"
    
    cat > github-secrets-template.md << EOF
# GitHub Secrets Configuration for Pathfinder CI/CD

Add these secrets to your GitHub repository:
**Settings > Secrets and variables > Actions > New repository secret**

## Required Secrets

### Azure Authentication
\`\`\`
AZURE_CREDENTIALS
Value: (Use the JSON output from the service principal creation above)

AZURE_SUBSCRIPTION_ID
Value: $SUBSCRIPTION_ID
\`\`\`

### Database Configuration
\`\`\`
SQL_ADMIN_LOGIN
Value: pathfinderadmin
(or your preferred SQL admin username)

SQL_ADMIN_PASSWORD
Value: (Generate a strong password with uppercase, lowercase, numbers, and symbols)
Example: P@thf1nd3r2024!Secure
\`\`\`

### External APIs
\`\`\`
OPENAI_API_KEY
Value: sk-your-openai-api-key-here
(Get from: https://platform.openai.com/api-keys)
\`\`\`

### Auth0 Configuration
\`\`\`
AUTH0_DOMAIN
Value: your-auth0-domain.auth0.com
(e.g., dev-jwnud3v8ghqnyygr.us.auth0.com)

AUTH0_AUDIENCE
Value: your-api-audience-identifier
(e.g., https://pathfinder-api)

AUTH0_CLIENT_ID
Value: your-auth0-client-id
(from Auth0 Application settings)
\`\`\`

### Azure Resource Connection Strings (Will be auto-generated after first deployment)
\`\`\`
AZURE_COSMOS_ENDPOINT
Value: (Will be available after infrastructure deployment)

AZURE_COSMOS_KEY
Value: (Will be available after infrastructure deployment)

SQL_CONNECTION_STRING
Value: (Will be auto-generated from SQL_ADMIN_LOGIN and SQL_ADMIN_PASSWORD)
\`\`\`

## Manual Secret Setup Steps

1. Go to your GitHub repository
2. Click Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each secret with the exact name and value shown above
5. Click "Add secret"
6. Repeat for all required secrets

## Using GitHub CLI (if available)

If you have GitHub CLI installed and authenticated:

\`\`\`bash
# Set the basic secrets (you'll need to provide the actual values)
gh secret set AZURE_CREDENTIALS < azure-credentials.json
gh secret set AZURE_SUBSCRIPTION_ID --body "$SUBSCRIPTION_ID"
gh secret set SQL_ADMIN_LOGIN --body "pathfinderadmin"
gh secret set SQL_ADMIN_PASSWORD --body "YourSecurePassword123!"
gh secret set OPENAI_API_KEY --body "sk-your-openai-key"
gh secret set AUTH0_DOMAIN --body "your-domain.auth0.com"
gh secret set AUTH0_AUDIENCE --body "https://pathfinder-api"
gh secret set AUTH0_CLIENT_ID --body "your-client-id"
\`\`\`

## Security Best Practices

- Use strong, unique passwords for SQL_ADMIN_PASSWORD
- Rotate API keys regularly (especially OPENAI_API_KEY)
- Limit Auth0 application permissions to minimum required
- Monitor Azure spending and set up billing alerts
- Review service principal permissions periodically

## Testing the Pipeline

After setting up all secrets:

1. Push to develop branch to test quality checks
2. Create a pull request to test PR validation
3. Push to main branch to trigger full deployment
4. Use workflow_dispatch to manually deploy to specific environments

## Troubleshooting

- **Authentication failures**: Verify AZURE_CREDENTIALS JSON format
- **Permission errors**: Check service principal has Contributor role
- **Build failures**: Verify all secrets are set correctly
- **Deployment failures**: Check Azure resource naming conflicts

EOF

    print_success "GitHub secrets template created: github-secrets-template.md"
}

setup_github_secrets() {
    if [ "$GH_CLI_AVAILABLE" = true ]; then
        print_header "GitHub CLI Secret Setup"
        
        echo "Would you like to set up GitHub secrets using GitHub CLI? (y/n)"
        read -p "> " setup_with_cli
        
        if [ "$setup_with_cli" = "y" ] || [ "$setup_with_cli" = "Y" ]; then
            print_info "Setting up Azure credentials..."
            gh secret set AZURE_CREDENTIALS < azure-credentials.json
            gh secret set AZURE_SUBSCRIPTION_ID --body "$SUBSCRIPTION_ID"
            
            print_info "Please provide the following values:"
            
            read -p "SQL Admin Login (default: pathfinderadmin): " sql_login
            sql_login=${sql_login:-pathfinderadmin}
            gh secret set SQL_ADMIN_LOGIN --body "$sql_login"
            
            read -s -p "SQL Admin Password: " sql_password
            echo ""
            gh secret set SQL_ADMIN_PASSWORD --body "$sql_password"
            
            read -p "OpenAI API Key: " openai_key
            gh secret set OPENAI_API_KEY --body "$openai_key"
            
            read -p "Auth0 Domain: " auth0_domain
            gh secret set AUTH0_DOMAIN --body "$auth0_domain"
            
            read -p "Auth0 Audience: " auth0_audience
            gh secret set AUTH0_AUDIENCE --body "$auth0_audience"
            
            read -p "Auth0 Client ID: " auth0_client_id
            gh secret set AUTH0_CLIENT_ID --body "$auth0_client_id"
            
            print_success "GitHub secrets set up successfully!"
        fi
    fi
}

cleanup() {
    print_header "Cleanup"
    
    if [ -f "azure-credentials.json" ]; then
        echo "Would you like to delete the azure-credentials.json file? (recommended for security) (y/n)"
        read -p "> " delete_file
        
        if [ "$delete_file" = "y" ] || [ "$delete_file" = "Y" ]; then
            rm azure-credentials.json
            print_success "Deleted azure-credentials.json"
        else
            print_warning "azure-credentials.json kept. Please delete it manually after setting up secrets."
        fi
    fi
}

main() {
    echo ""
    print_header "Pathfinder CI/CD Setup Script"
    echo "This script will help you set up Azure credentials and GitHub secrets for the CI/CD pipeline."
    echo ""
    
    check_prerequisites
    azure_login
    create_service_principal
    generate_secrets_template
    setup_github_secrets
    cleanup
    
    echo ""
    print_success "Setup completed!"
    echo ""
    print_info "Next steps:"
    echo "1. Review github-secrets-template.md for all required secrets"
    echo "2. Set up any remaining secrets in GitHub"
    echo "3. Test the pipeline by pushing to the develop branch"
    echo "4. Check the pipeline documentation in docs/CI_CD_PIPELINE.md"
    echo ""
}

# Run main function
main "$@" 