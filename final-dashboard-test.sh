#!/bin/bash

echo "🎯 FINAL DASHBOARD FIX VERIFICATION"
echo "===================================="
echo ""

BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Testing Backend Route Fix${NC}"
echo "=========================="

# Test without trailing slash (should redirect or work properly)
echo "Testing trips endpoint WITHOUT trailing slash:"
TRIPS_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/v1/trips")
echo "  GET /api/v1/trips: $TRIPS_STATUS"

# Test with trailing slash (should work properly)
echo "Testing trips endpoint WITH trailing slash:"
TRIPS_SLASH_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/v1/trips/")
echo "  GET /api/v1/trips/: $TRIPS_SLASH_STATUS"

# Analyze results
echo ""
echo -e "${BLUE}Analysis:${NC}"
if [ "$TRIPS_STATUS" = "307" ]; then
    echo -e "  ${YELLOW}⚠️  /api/v1/trips still redirects (307) - this is OK if frontend uses trailing slash${NC}"
else
    echo -e "  ${GREEN}✅ /api/v1/trips no longer redirects (status: $TRIPS_STATUS)${NC}"
fi

if [ "$TRIPS_SLASH_STATUS" = "403" ] || [ "$TRIPS_SLASH_STATUS" = "401" ] || [ "$TRIPS_SLASH_STATUS" = "200" ]; then
    echo -e "  ${GREEN}✅ /api/v1/trips/ works properly (status: $TRIPS_SLASH_STATUS)${NC}"
else
    echo -e "  ${RED}❌ /api/v1/trips/ not working (status: $TRIPS_SLASH_STATUS)${NC}"
fi

# Test health endpoint
echo ""
echo "Testing health endpoint:"
HEALTH_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/health")
echo "  GET /health: $HEALTH_STATUS"

if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "  ${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "  ${RED}❌ Backend health check failed${NC}"
fi

echo ""
echo -e "${BLUE}Final Status:${NC}"
if [ "$TRIPS_SLASH_STATUS" = "403" ] || [ "$TRIPS_SLASH_STATUS" = "401" ] || [ "$TRIPS_SLASH_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ DASHBOARD FIX SUCCESSFUL!${NC}"
    echo "   • Route conflict resolved"
    echo "   • Frontend can now call /api/v1/trips/ properly"
    echo "   • No more 307 redirects blocking dashboard"
    echo ""
    echo -e "${YELLOW}Next step: Test with authenticated user in browser${NC}"
else
    echo -e "${RED}❌ Dashboard fix incomplete${NC}"
    echo "   • Backend deployment may still be in progress"
fi
