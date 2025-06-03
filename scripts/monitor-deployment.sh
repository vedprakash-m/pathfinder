#!/bin/bash

# Monitor Frontend Deployment Status
echo "🔍 Monitoring Frontend Deployment Status"
echo "========================================"
echo ""

echo "⏱️  Starting deployment monitor..."
echo "Expected: Frontend should update with new last-modified timestamp"
echo "Current time: $(date)"
echo ""

# Store current timestamp
current_etag=""
iteration=0

while [ $iteration -lt 30 ]; do
    echo "📡 Check #$((iteration+1)) - $(date +%H:%M:%S)"
    
    # Get current frontend info
    frontend_info=$(curl -sI "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/" | grep -E "(last-modified|etag)")
    new_etag=$(echo "$frontend_info" | grep etag | cut -d'"' -f2)
    last_modified=$(echo "$frontend_info" | grep last-modified | cut -d' ' -f2-)
    
    echo "   ETag: $new_etag"
    echo "   Last Modified: $last_modified"
    
    # Check if it changed
    if [[ -n "$current_etag" && "$new_etag" != "$current_etag" ]]; then
        echo ""
        echo "🎉 DEPLOYMENT DETECTED!"
        echo "   New ETag: $new_etag"
        echo "   Deployment Time: $last_modified"
        echo ""
        echo "✅ Frontend has been updated! You can now test the dashboard."
        break
    fi
    
    if [[ -z "$current_etag" ]]; then
        current_etag="$new_etag"
        echo "   Initial ETag captured: $current_etag"
    fi
    
    echo ""
    
    iteration=$((iteration+1))
    
    if [ $iteration -lt 30 ]; then
        sleep 60  # Wait 1 minute between checks
    fi
done

if [ $iteration -eq 30 ]; then
    echo "⏰ Timeout reached. Deployment may take longer than expected."
    echo "You can manually check: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
fi

echo ""
echo "🧪 Next Steps:"
echo "1. Open the Pathfinder app: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo "2. Sign in with Auth0"
echo "3. Check if the dashboard loads trips without errors"
echo "4. Verify no 307 redirects in browser network tab"
