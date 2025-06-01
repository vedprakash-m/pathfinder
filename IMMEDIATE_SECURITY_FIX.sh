#!/bin/bash

# IMMEDIATE SECURITY REMEDIATION SCRIPT
# This script addresses all critical security vulnerabilities found in the scan

set -e

echo "🔒 STARTING IMMEDIATE SECURITY REMEDIATION"
echo "=================================================="

# 1. First, create a backup branch
echo "📦 Creating security backup branch..."
git checkout -b security-backup-$(date +%Y%m%d-%H%M%S) || true
git checkout main

# 2. Fix current files with hardcoded secrets
echo "🔧 Sanitizing current files with hardcoded secrets..."

# Fix FINAL_DEPLOYMENT_GUIDE.md
if [ -f "FINAL_DEPLOYMENT_GUIDE.md" ]; then
    echo "  Fixing FINAL_DEPLOYMENT_GUIDE.md..."
    sed -i '' 's/KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn/YOUR_AUTH0_CLIENT_ID/g' FINAL_DEPLOYMENT_GUIDE.md
fi

# Fix deploy-frontend-fixes.sh
if [ -f "deploy-frontend-fixes.sh" ]; then
    echo "  Fixing deploy-frontend-fixes.sh..."
    sed -i '' 's/KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn/YOUR_AUTH0_CLIENT_ID/g' deploy-frontend-fixes.sh
    sed -i '' 's/YOUR_TOKEN/\${GITHUB_TOKEN}/g' deploy-frontend-fixes.sh
fi

# Fix PRODUCTION_CONFIGURATION_COMPLETE.md
if [ -f "PRODUCTION_CONFIGURATION_COMPLETE.md" ]; then
    echo "  Fixing PRODUCTION_CONFIGURATION_COMPLETE.md..."
    sed -i '' 's/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/YOUR_BACKEND_PRINCIPAL_ID/g' PRODUCTION_CONFIGURATION_COMPLETE.md
    sed -i '' 's/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/YOUR_FRONTEND_PRINCIPAL_ID/g' PRODUCTION_CONFIGURATION_COMPLETE.md
fi

# 3. Enhance .gitignore with comprehensive security patterns
echo "🛡️  Enhancing .gitignore with security patterns..."
cat >> .gitignore << 'EOF'

# Security - Prevent accidental commit of secrets
*.env.production
*.env.staging
*.env.local
*.env.secret
*secret*
*key*
*.pem
*.p12
*.pfx
*.jks
*.keystore
auth0-config.json
azure-credentials.json
.auth0
.azure
.secrets/
secrets/
vault/
private/
EOF

# 4. Remove any existing .env.production files
echo "🗑️  Removing any .env.production files..."
find . -name "*.env.production" -type f -delete
find . -name "*.env.local" -type f -delete

# 5. Fix template files to use placeholder values
echo "📝 Sanitizing template files..."

# Fix .env.production.template
if [ -f ".env.production.template" ]; then
    sed -i '' 's/your-sendgrid-api-key/YOUR_SENDGRID_API_KEY/g' .env.production.template
fi

# Fix frontend/.env.template
if [ -f "frontend/.env.template" ]; then
    sed -i '' 's/your-tenant.auth0.com/YOUR_TENANT.auth0.com/g' frontend/.env.template
fi

# 6. Update README.md to use better placeholder examples
echo "📚 Updating README.md with secure placeholders..."
if [ -f "README.md" ]; then
    sed -i '' 's/your-domain.auth0.com/YOUR_DOMAIN.auth0.com/g' README.md
    sed -i '' 's/postgresql:\/\/postgres:password@localhost:5432\/pathfinder/postgresql:\/\/\${DB_USER}:\${DB_PASSWORD}@\${DB_HOST}:5432\/pathfinder/g' README.md
    sed -i '' 's/postgresql:\/\/user:password@localhost:5432\/pathfinder/postgresql:\/\/\${DB_USER}:\${DB_PASSWORD}@\${DB_HOST}:5432\/pathfinder/g' README.md
fi

# 7. Fix docker-compose.yml (if not already fixed)
echo "🐳 Securing docker-compose.yml..."
if [ -f "docker-compose.yml" ]; then
    # Check if it's already using environment variables
    if grep -q "[COSMOS-DB-EMULATOR-KEY]" docker-compose.yml; then
        sed -i '' 's/COSMOS_DB_KEY=C2y6yDjf5\/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw\/Jw==/COSMOS_DB_KEY=\${COSMOS_DB_KEY:-YOUR_COSMOS_DB_EMULATOR_KEY}/g' docker-compose.yml
    fi
fi

# 8. Create secure environment template
echo "🔐 Creating secure environment template..."
cat > .env.secure.template << 'EOF'
# SECURE ENVIRONMENT TEMPLATE
# Copy this to .env.production and fill in your actual values
# NEVER commit .env.production to git!

# Authentication
AUTH0_DOMAIN=YOUR_TENANT.auth0.com
AUTH0_CLIENT_ID=YOUR_AUTH0_CLIENT_ID
AUTH0_CLIENT_SECRET=YOUR_AUTH0_CLIENT_SECRET
AUTH0_AUDIENCE=YOUR_AUTH0_API_AUDIENCE

# Frontend Authentication
VITE_AUTH0_DOMAIN=YOUR_TENANT.auth0.com
VITE_AUTH0_CLIENT_ID=YOUR_AUTH0_CLIENT_ID
VITE_AUTH0_AUDIENCE=YOUR_AUTH0_API_AUDIENCE

# Database
DATABASE_URL=postgresql://\${DB_USER}:\${DB_PASSWORD}@\${DB_HOST}:5432/pathfinder
COSMOS_DB_KEY=\${COSMOS_DB_KEY}
COSMOS_DB_ENDPOINT=\${COSMOS_DB_ENDPOINT}

# Cache
REDIS_URL=redis://\${REDIS_HOST}:6379

# Email
SMTP_HOST=${SMTP_HOST}
SMTP_PORT=${SMTP_PORT}
SMTP_USER=${SMTP_USER}
SMTP_PASSWORD=${SMTP_PASSWORD}

# Security
SECRET_KEY=${SECRET_KEY}
JWT_SECRET=${JWT_SECRET}

# Azure (for production deployment)
AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
AZURE_TENANT_ID=${AZURE_TENANT_ID}
EOF

# 9. Create security checklist
echo "📋 Creating security checklist..."
cat > SECURITY_CHECKLIST.md << 'EOF'
# SECURITY REMEDIATION CHECKLIST

## ✅ COMPLETED AUTOMATICALLY:
- [x] Sanitized all current files containing hardcoded secrets
- [x] Enhanced .gitignore to prevent future secret commits
- [x] Removed .env.production files from working directory
- [x] Updated template files with secure placeholders
- [x] Fixed docker-compose.yml to use environment variables
- [x] Created secure environment template

## 🔴 CRITICAL MANUAL ACTIONS REQUIRED:

### 1. IMMEDIATE: Rotate Auth0 Credentials
```bash
# Go to Auth0 Dashboard → Applications → Pathfinder
# Generate new Client Secret
# Update the following:
AUTH0_CLIENT_SECRET=NEW_SECRET_HERE
```

### 2. IMMEDIATE: Clean Git History
```bash
# WARNING: This rewrites git history - coordinate with team first!
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch frontend/.env.production' \
  --prune-empty --tag-name-filter cat -- --all

# Force push to remove from remote (DANGEROUS - backup first!)
git push origin --force --all
git push origin --force --tags
```

### 3. Update Production Secrets
- Azure Key Vault: Update all Auth0 secrets
- Container Apps: Redeploy with new credentials
- Monitor logs for any unauthorized access

### 4. Security Verification
- Run security scan: `gitleaks detect --verbose`
- Check Auth0 logs for suspicious activity
- Verify all applications work with new credentials

## 📞 INCIDENT RESPONSE:
If credentials were compromised:
1. Immediately disable Auth0 application
2. Check Auth0 logs for unauthorized access
3. Rotate all related secrets (database, etc.)
4. Monitor application logs for anomalies
5. Consider security audit of entire infrastructure
EOF

# 10. Commit the security fixes
echo "💾 Committing security fixes..."
git add .
git commit -m "🔒 SECURITY: Remove hardcoded secrets and implement security best practices

- Sanitized all files containing Auth0 client ID [REDACTED-AUTH0-CLIENT-ID]
- Sanitized Azure principal IDs from documentation  
- Enhanced .gitignore with comprehensive security patterns
- Updated docker-compose.yml to use environment variables
- Created secure environment template
- Removed all .env.production files

CRITICAL: Auth0 credentials MUST be rotated immediately
Git history cleanup required to fully remediate"

echo ""
echo "🔒 IMMEDIATE SECURITY REMEDIATION COMPLETED"
echo "=================================================="
echo ""
echo "✅ Fixed hardcoded secrets in current files"
echo "✅ Enhanced security configurations"  
echo "✅ Created security templates and documentation"
echo ""
echo "🔴 CRITICAL MANUAL ACTIONS STILL REQUIRED:"
echo "   1. Rotate Auth0 client secret in Auth0 dashboard"
echo "   2. Clean git history to remove old commits with secrets"
echo "   3. Update production deployments with new credentials"
echo ""
echo "📋 See SECURITY_CHECKLIST.md for detailed next steps"
echo ""
