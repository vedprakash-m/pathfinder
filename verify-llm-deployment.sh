#!/bin/bash
# LLM Orchestration Service Deployment Verification
# Run this script after deploying the LLM service to verify everything works

set -e

echo "🔍 LLM Orchestration Service - Deployment Verification"
echo "======================================================"

# Get service URL (if deployed with our script, check container IP)
if [ -z "$LLM_SERVICE_URL" ]; then
    echo "📝 Please provide the LLM service URL:"
    echo "   For Azure Container Instance: http://[CONTAINER_IP]:8000"
    echo "   For App Service: https://your-app.azurewebsites.net"
    echo ""
    read -p "🌐 Enter LLM Service URL: " LLM_SERVICE_URL
fi

# Remove trailing slash
LLM_SERVICE_URL=${LLM_SERVICE_URL%/}

echo ""
echo "🧪 Testing LLM Service at: $LLM_SERVICE_URL"
echo ""

# Test 1: Basic connectivity
echo "1️⃣ Testing basic connectivity..."
if curl -s --max-time 10 "$LLM_SERVICE_URL/" | grep -q "LLM Orchestration"; then
    echo "   ✅ Basic connectivity - PASSED"
else
    echo "   ❌ Basic connectivity - FAILED"
    echo "   🔧 Troubleshooting:"
    echo "      - Check if the service is running"
    echo "      - Verify the URL is correct"
    echo "      - Check firewall/network security group settings"
    exit 1
fi

# Test 2: Health check
echo ""
echo "2️⃣ Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s --max-time 10 "$LLM_SERVICE_URL/health" || echo "failed")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "   ✅ Health check - PASSED"
    echo "   📊 Service details:"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo "   ❌ Health check - FAILED"
    echo "   📋 Response: $HEALTH_RESPONSE"
fi

# Test 3: API documentation
echo ""
echo "3️⃣ Testing API documentation..."
if curl -s --max-time 10 "$LLM_SERVICE_URL/docs" | grep -q "FastAPI"; then
    echo "   ✅ API documentation accessible - PASSED"
    echo "   📖 Docs URL: $LLM_SERVICE_URL/docs"
else
    echo "   ⚠️ API documentation may not be accessible"
fi

# Test 4: LLM generation endpoint
echo ""
echo "4️⃣ Testing LLM generation endpoint..."
LLM_RESPONSE=$(curl -s --max-time 30 -X POST "$LLM_SERVICE_URL/v1/generate" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Hello, this is a test", "user_id": "verification_test"}' || echo "failed")

if echo "$LLM_RESPONSE" | grep -q "content"; then
    echo "   ✅ LLM generation - PASSED"
    echo "   📝 Sample response:"
    echo "$LLM_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LLM_RESPONSE"
else
    echo "   ❌ LLM generation - FAILED"
    echo "   📋 Response: $LLM_RESPONSE"
fi

# Test 5: Metrics endpoint
echo ""
echo "5️⃣ Testing metrics endpoint..."
METRICS_RESPONSE=$(curl -s --max-time 10 "$LLM_SERVICE_URL/metrics" || echo "failed")
if echo "$METRICS_RESPONSE" | grep -q "requests"; then
    echo "   ✅ Metrics endpoint - PASSED"
    echo "   📊 Current metrics:"
    echo "$METRICS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$METRICS_RESPONSE"
else
    echo "   ⚠️ Metrics endpoint response: $METRICS_RESPONSE"
fi

# Test 6: CORS headers (important for frontend integration)
echo ""
echo "6️⃣ Testing CORS configuration..."
CORS_RESPONSE=$(curl -s -I --max-time 10 "$LLM_SERVICE_URL/" | grep -i "access-control" || echo "no-cors")
if [ "$CORS_RESPONSE" != "no-cors" ]; then
    echo "   ✅ CORS headers present - PASSED"
    echo "   🔧 CORS headers: $CORS_RESPONSE"
else
    echo "   ⚠️ CORS headers not detected (may be configured for specific origins)"
fi

echo ""
echo "🎯 Integration Testing"
echo "====================="

# Test 7: Auth0 integration (if available)
echo ""
echo "7️⃣ Testing Auth0 integration..."
AUTH_RESPONSE=$(curl -s --max-time 10 "$LLM_SERVICE_URL/v1/auth/status" || echo "failed")
if echo "$AUTH_RESPONSE" | grep -q "auth0"; then
    echo "   ✅ Auth0 integration available - PASSED"
else
    echo "   ℹ️ Auth0 integration endpoint not available (may be protected)"
fi

echo ""
echo "📋 DEPLOYMENT VERIFICATION SUMMARY"
echo "=================================="

# Summary
echo "🌐 Service URL: $LLM_SERVICE_URL"
echo "📖 API Docs: $LLM_SERVICE_URL/docs"
echo "📊 Health Check: $LLM_SERVICE_URL/health"
echo "📈 Metrics: $LLM_SERVICE_URL/metrics"

echo ""
echo "🔗 Integration URLs for Pathfinder:"
echo "Frontend: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo "Backend: https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo "LLM Service: $LLM_SERVICE_URL"

echo ""
echo "🔧 Next Steps:"
echo "1. Update backend environment variables to include LLM_SERVICE_URL"
echo "2. Configure API keys for OpenAI, Gemini, and Anthropic"
echo "3. Test end-to-end integration with frontend"
echo "4. Set up monitoring and alerting"

echo ""
if curl -s --max-time 5 "$LLM_SERVICE_URL/health" | grep -q "healthy"; then
    echo "🎉 LLM Orchestration Service is OPERATIONAL and ready for use!"
else
    echo "⚠️ Service may need additional configuration or troubleshooting"
fi

echo ""
echo "💡 Troubleshooting commands:"
echo "az container logs --name llm-orchestration-service --resource-group llm-orchestration-demo"
echo "curl -v $LLM_SERVICE_URL/health"
echo ""
