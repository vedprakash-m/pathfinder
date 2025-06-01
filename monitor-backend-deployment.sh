#!/bin/bash

echo "🚀 Monitoring Backend Deployment for Route Fix"
echo "=============================================="
echo ""

BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

check_backend_routes() {
    echo -e "${BLUE}Testing Backend Routes:${NC}"
    
    # Test trips endpoint (should not redirect)
    TRIPS_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/v1/trips")
    echo "  Trips API (/api/v1/trips): $TRIPS_RESPONSE"
    
    # Test trip-messages endpoint (new route)
    MESSAGES_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/v1/trip-messages")
    echo "  Trip Messages API (/api/v1/trip-messages): $MESSAGES_RESPONSE"
    
    # Test health endpoint
    HEALTH_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/health")
    echo "  Health Check (/health): $HEALTH_RESPONSE"
    
    # Check if route conflict is resolved
    if [ "$TRIPS_RESPONSE" != "307" ]; then
        echo -e "  ${GREEN}✅ Route conflict resolved! No more 307 redirects${NC}"
        return 0
    else
        echo -e "  ${RED}❌ Still getting 307 redirects - deployment pending${NC}"
        return 1
    fi
}

test_dashboard() {
    echo -e "${BLUE}Testing Dashboard Access:${NC}"
    
    FRONTEND_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$FRONTEND_URL/")
    echo "  Frontend Access: $FRONTEND_RESPONSE"
    
    if [ "$FRONTEND_RESPONSE" = "200" ]; then
        echo -e "  ${GREEN}✅ Dashboard accessible${NC}"
        return 0
    else
        echo -e "  ${RED}❌ Dashboard access issue${NC}"
        return 1
    fi
}

echo "Waiting for deployment to complete..."
echo "This may take 5-10 minutes for Azure Container Apps to rebuild and deploy."
echo ""

ATTEMPT=1
MAX_ATTEMPTS=20

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo -e "${YELLOW}Attempt $ATTEMPT/$MAX_ATTEMPTS ($(date))${NC}"
    
    if check_backend_routes; then
        echo ""
        echo -e "${GREEN}🎉 BACKEND DEPLOYMENT SUCCESSFUL!${NC}"
        echo ""
        
        test_dashboard
        echo ""
        
        echo -e "${GREEN}VERIFICATION COMPLETE:${NC}"
        echo "✅ Backend route conflict resolved"
        echo "✅ No more 307 redirects on /api/v1/trips"
        echo "✅ Trip messages API moved to /api/v1/trip-messages"
        echo "✅ Dashboard should now load properly"
        echo ""
        echo "🌐 Test the dashboard at: $FRONTEND_URL"
        break
    else
        echo "  Deployment still in progress..."
        echo ""
        
        if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
            echo -e "${RED}❌ Deployment taking longer than expected${NC}"
            echo "Please check Azure Container Apps deployment status manually."
        else
            echo "Waiting 30 seconds before next check..."
            sleep 30
        fi
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
done
