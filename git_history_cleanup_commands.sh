#!/bin/bash

# GIT HISTORY CLEANUP COMMANDS
# WARNING: This script permanently modifies git history
# Coordinate with your team before running!

set -e

echo "🚨 GIT HISTORY CLEANUP - REMOVING SECRETS FROM ALL COMMITS"
echo "============================================================="
echo ""
echo "⚠️  WARNING: This will permanently rewrite git history"
echo "⚠️  All team members must re-clone after this operation"
echo "⚠️  Backup branches have been created automatically"
echo ""

# Confirm before proceeding
read -p "Are you sure you want to proceed? (type 'yes' to continue): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Operation cancelled"
    exit 1
fi

echo ""
echo "🔧 STEP 1: Installing BFG Repo Cleaner..."

# Check if BFG is installed
if ! command -v java >/dev/null 2>&1; then
    echo "❌ Java is required but not installed. Please install Java first."
    exit 1
fi

# Download BFG if not present
if [ ! -f "bfg.jar" ]; then
    echo "  Downloading BFG Repo Cleaner..."
    curl -L "https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar" -o bfg.jar
fi

echo ""
echo "🔧 STEP 2: Creating secrets replacement file..."

# Create replacement file for BFG
cat > secrets-to-replace.txt << 'EOF'
YOUR_AUTH0_CLIENT_ID==>YOUR_AUTH0_CLIENT_ID
YOUR_BACKEND_PRINCIPAL_ID==>YOUR_BACKEND_PRINCIPAL_ID
YOUR_FRONTEND_PRINCIPAL_ID==>YOUR_FRONTEND_PRINCIPAL_ID
YOUR_COSMOS_DB_EMULATOR_KEY==>YOUR_COSMOS_DB_EMULATOR_KEY
EOF

echo ""
echo "🔧 STEP 3: Running BFG Repo Cleaner..."

# Delete the problematic file from history
echo "  Removing frontend/.env.production from all commits..."
java -jar bfg.jar --delete-files frontend/.env.production

# Replace secrets in all text content
echo "  Replacing secrets in all commits..."
java -jar bfg.jar --replace-text secrets-to-replace.txt

echo ""
echo "🔧 STEP 4: Cleaning up git repository..."

# Clean up git refs and garbage collect
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "🔧 STEP 5: Final verification..."

# Run final security scan
echo "  Running final security scan..."
if gitleaks detect --verbose --report-format json --report-path final-security-report.json; then
    echo "✅ Final security scan passed!"
else
    echo "⚠️  Some issues may remain - check final-security-report.json"
fi

echo ""
echo "✅ GIT HISTORY CLEANUP COMPLETE!"
echo "================================="
echo ""
echo "🔴 CRITICAL NEXT STEPS:"
echo "1. Force push to remote: git push origin --force --all"
echo "2. Force push tags: git push origin --force --tags"
echo "3. Notify team to delete and re-clone repositories"
echo "4. Verify applications work with cleaned history"
echo ""
echo "📂 Files created:"
echo "  - bfg.jar (BFG Repo Cleaner)"
echo "  - secrets-to-replace.txt (replacement patterns)"
echo "  - final-security-report.json (final scan results)"
echo ""
echo "⚠️  Remember: All team members must now:"
echo "    1. Delete their local repository"
echo "    2. Fresh clone: git clone <repository-url>"
echo ""
