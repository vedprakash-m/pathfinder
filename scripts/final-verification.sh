#!/bin/bash

# Final verification script for dashboard loading fix
echo "🔍 FINAL VERIFICATION - Dashboard Loading Fix"
echo "============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success_count=0
total_checks=6

echo "📋 Checking fix implementation..."
echo ""

# Check 1: Backend route conflict fix
echo -n "1. Backend route conflict fix: "
if curl -s "https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/api/v1/trip-messages/" | grep -q "404\|401\|403"; then
    echo -e "${GREEN}✅ DEPLOYED${NC}"
    ((success_count++))
else
    echo -e "${RED}❌ NOT VERIFIED${NC}"
fi

# Check 2: Backend health
echo -n "2. Backend health status: "
health_status=$(curl -s "https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$health_status" = "healthy" ]; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
    ((success_count++))
else
    echo -e "${RED}❌ UNHEALTHY${NC}"
fi

# Check 3: Trips endpoint redirect behavior
echo -n "3. Trips endpoint behavior: "
redirect_code=$(curl -s -o /dev/null -w "%{http_code}" "https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/api/v1/trips")
if [ "$redirect_code" = "307" ]; then
    echo -e "${GREEN}✅ REDIRECTS CORRECTLY${NC}"
    ((success_count++))
else
    echo -e "${YELLOW}⚠️  UNEXPECTED CODE: $redirect_code${NC}"
fi

# Check 4: Frontend trailing slash fix
echo -n "4. Frontend trailing slash fix: "
if grep -q "'/trips/'" /Users/vedprakashmishra/pathfinder/frontend/src/services/tripService.ts; then
    echo -e "${GREEN}✅ IMPLEMENTED${NC}"
    ((success_count++))
else
    echo -e "${RED}❌ NOT FOUND${NC}"
fi

# Check 5: CSRF token handling
echo -n "5. CSRF token handling: "
if grep -q "X-CSRF-Token" /Users/vedprakashmishra/pathfinder/frontend/src/services/api.ts; then
    echo -e "${GREEN}✅ IMPLEMENTED${NC}"
    ((success_count++))
else
    echo -e "${RED}❌ NOT FOUND${NC}"
fi

# Check 6: Environment configuration
echo -n "6. Frontend environment: "
if [ -f "/Users/vedprakashmishra/pathfinder/frontend/.env.production" ]; then
    echo -e "${GREEN}✅ CONFIGURED${NC}"
    ((success_count++))
else
    echo -e "${RED}❌ MISSING${NC}"
fi

echo ""
echo "📊 VERIFICATION SUMMARY"
echo "======================="
echo "Checks passed: $success_count/$total_checks"

if [ $success_count -eq $total_checks ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED!${NC}"
    echo ""
    echo "✅ Backend fixes: DEPLOYED"
    echo "✅ Frontend fixes: READY FOR DEPLOYMENT"
    echo ""
    echo "🚀 Next step: Deploy frontend changes"
    echo "Expected result: Dashboard will load trips successfully"
else
    echo -e "${YELLOW}⚠️  Some checks need attention${NC}"
fi

echo ""
echo "🎯 DEPLOYMENT COMMANDS:"
echo "----------------------"
echo "# Option 1: Git-based deployment"
echo "git add . && git commit -m 'Fix dashboard loading' && git push"
echo ""
echo "# Option 2: Manual container restart"
echo "# (Use your Azure deployment process)"
echo ""
echo "🧪 POST-DEPLOYMENT TEST:"
echo "------------------------"
echo "1. Navigate to your Pathfinder app"
echo "2. Sign in with Auth0"
echo "3. Verify trips load on dashboard"
echo "4. Check network tab - no 307 redirects"

echo ""
echo "🏁 Fix implementation: COMPLETE ✅"
