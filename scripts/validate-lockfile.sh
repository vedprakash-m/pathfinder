#!/bin/bash

# Frontend Lockfile Validation Script
# Ensures pnpm-lock.yaml is synchronized with package.json
# Used by local validation and CI/CD to prevent lockfile mismatches

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FRONTEND_DIR="frontend"
FIX_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=true
            shift
            ;;
        --frontend-dir)
            FRONTEND_DIR="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--fix] [--frontend-dir <dir>]"
            echo "  --fix: Automatically regenerate lockfile if out of sync"
            echo "  --frontend-dir: Specify frontend directory (default: frontend)"
            exit 1
            ;;
    esac
done

echo "🔒 Frontend Lockfile Validation"
echo "================================"

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Frontend directory '$FRONTEND_DIR' not found${NC}"
    exit 1
fi

# Check if package.json exists
if [ ! -f "$FRONTEND_DIR/package.json" ]; then
    echo -e "${RED}❌ package.json not found in $FRONTEND_DIR${NC}"
    exit 1
fi

# Check if pnpm is available
if ! command -v pnpm &> /dev/null; then
    echo -e "${RED}❌ pnpm is not installed${NC}"
    echo "   💡 Install with: npm install -g pnpm"
    exit 1
fi

cd "$FRONTEND_DIR"

# Check if lockfile exists
if [ ! -f "pnpm-lock.yaml" ]; then
    echo -e "${RED}❌ pnpm-lock.yaml not found${NC}"
    if [ "$FIX_MODE" = true ]; then
        echo "   🔧 Generating lockfile..."
        pnpm install
        echo -e "${GREEN}✅ Lockfile generated${NC}"
    else
        echo "   💡 Generate with: cd $FRONTEND_DIR && pnpm install"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Found pnpm-lock.yaml${NC}"
fi

# Test lockfile synchronization (simulating CI/CD behavior)
echo "   Testing lockfile synchronization..."

# First try offline to catch obvious sync issues
if pnpm install --frozen-lockfile --offline >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Lockfile is synchronized (offline test passed)${NC}"
    exit 0
fi

# If offline fails, try with network (might need to download new deps)
echo "   Offline test failed, trying with network..."
if pnpm install --frozen-lockfile >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Lockfile is synchronized (required dependency download)${NC}"
    exit 0
fi

# Lockfile is out of sync
echo -e "${RED}❌ Lockfile is out of sync with package.json${NC}"
echo "   This will cause CI/CD failure with --frozen-lockfile"

if [ "$FIX_MODE" = true ]; then
    echo "   🔧 Regenerating lockfile..."
    pnpm install
    echo -e "${GREEN}✅ Lockfile regenerated and synchronized${NC}"
else
    echo "   💡 Fix with: cd $FRONTEND_DIR && pnpm install"
    echo "   💡 Or run this script with --fix flag"
    exit 1
fi
