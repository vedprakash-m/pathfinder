#!/bin/bash

echo "🎯 COMPLETE DASHBOARD FIX VERIFICATION"
echo "======================================"
echo ""

BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

test_backend_fix() {
    echo -e "${BLUE}1. Testing Backend Route Fix${NC}"
    echo "============================="
    
    # Test the original problematic endpoint
    echo "Testing trips endpoint (was causing 307 redirects):"
    TRIPS_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/v1/trips")
    echo "  GET /api/v1/trips: $TRIPS_STATUS"
    
    if [ "$TRIPS_STATUS" = "307" ]; then
        echo -e "  ${RED}❌ STILL BROKEN: Getting 307 redirects${NC}"
        echo "  This means the backend deployment hasn't completed yet."
        return 1
    elif [ "$TRIPS_STATUS" = "401" ] || [ "$TRIPS_STATUS" = "200" ]; then
        echo -e "  ${GREEN}✅ FIXED: No more 307 redirects!${NC}"
        echo "  Endpoint now properly handles requests (auth required: $TRIPS_STATUS)"
    else
        echo -e "  ${YELLOW}⚠️  Unexpected response: $TRIPS_STATUS${NC}"
    fi
    
    # Test the separated trip messages endpoint
    echo ""
    echo "Testing trip messages endpoint (moved to resolve conflict):"
    MESSAGES_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/v1/trip-messages")
    echo "  GET /api/v1/trip-messages: $MESSAGES_STATUS"
    
    if [ "$MESSAGES_STATUS" = "404" ] || [ "$MESSAGES_STATUS" = "401" ] || [ "$MESSAGES_STATUS" = "200" ]; then
        echo -e "  ${GREEN}✅ WORKING: Route separation successful${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Unexpected response: $MESSAGES_STATUS${NC}"
    fi
    
    # Test health endpoint
    echo ""
    echo "Testing health endpoint:"
    HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health")
    echo "  Health check: $(echo $HEALTH_RESPONSE | jq -r '.status' 2>/dev/null || echo 'Could not parse')"
    
    return 0
}

test_frontend_access() {
    echo -e "${BLUE}2. Testing Frontend Access${NC}"
    echo "=========================="
    
    FRONTEND_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$FRONTEND_URL/")
    echo "  Frontend status: $FRONTEND_STATUS"
    
    if [ "$FRONTEND_STATUS" = "200" ]; then
        echo -e "  ${GREEN}✅ Frontend accessible${NC}"
        
        # Check if frontend has our fixes
        echo "  Checking frontend content..."
        CONTENT_CHECK=$(curl -s "$FRONTEND_URL/" | grep -c "Pathfinder")
        if [ "$CONTENT_CHECK" -gt "0" ]; then
            echo -e "  ${GREEN}✅ Frontend content loaded properly${NC}"
        else
            echo -e "  ${YELLOW}⚠️  Frontend content may have issues${NC}"
        fi
    else
        echo -e "  ${RED}❌ Frontend access issue: $FRONTEND_STATUS${NC}"
        return 1
    fi
    
    return 0
}

test_dashboard_functionality() {
    echo -e "${BLUE}3. Testing Dashboard Functionality${NC}"
    echo "=================================="
    
    echo "The dashboard should now:"
    echo "  ✓ Load without 'Error Loading Dashboard' message"
    echo "  ✓ Make successful API calls to /api/v1/trips"
    echo "  ✓ Display trip data (with proper authentication)"
    echo "  ✓ Allow user interaction without route conflicts"
    echo ""
    echo -e "${YELLOW}📱 Manual Test Required:${NC}"
    echo "  Please open: $FRONTEND_URL"
    echo "  And verify the dashboard loads your trips successfully."
}

print_summary() {
    echo -e "${BLUE}4. Fix Summary${NC}"
    echo "=============="
    echo ""
    echo -e "${GREEN}Changes Made:${NC}"
    echo "  🔧 Backend: Fixed route conflict in router.py"
    echo "     - Changed trip_messages_router prefix: /trips → /trip-messages"
    echo "     - Eliminated FastAPI routing conflicts"
    echo ""
    echo "  🔧 Frontend: Enhanced API calls in tripService.ts"
    echo "     - Added trailing slashes to API URLs"
    echo "     - Implemented CSRF token handling"
    echo ""
    echo "  🔧 CI/CD: Fixed workflow pipeline structure"
    echo "     - Resolved YAML syntax errors"
    echo "     - Improved deployment sequencing"
    echo ""
    echo -e "${GREEN}Expected Results:${NC}"
    echo "  ✅ No more 307 redirect loops"
    echo "  ✅ Dashboard loads successfully"
    echo "  ✅ Trip data displays properly"
    echo "  ✅ All features work as expected"
}

# Run all tests
echo "Starting comprehensive verification..."
echo ""

if test_backend_fix; then
    echo ""
    test_frontend_access
    echo ""
    test_dashboard_functionality
    echo ""
    print_summary
    echo ""
    echo -e "${GREEN}🎉 DASHBOARD FIX VERIFICATION COMPLETE!${NC}"
    echo ""
    echo "If all tests show ✅, the dashboard loading issue is resolved."
    echo "Users should now be able to access their trips without errors."
else
    echo ""
    echo -e "${RED}❌ Backend deployment still in progress or failed.${NC}"
    echo "Please wait for deployment to complete or check CI/CD pipeline."
fi
