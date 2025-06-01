#!/bin/sh
# Runtime environment variable replacement script
# This script replaces build-time environment variables with runtime values

echo "🔧 Applying runtime environment variable fixes..."

# Find all JavaScript files in the build directory
find /usr/share/nginx/html -name "*.js" -type f | while read -r file; do
    echo "Processing: $file"
    
    # Replace the incorrect Auth0 domain with the correct one from environment variable
    if [ -n "$VITE_AUTH0_DOMAIN" ]; then
        sed -i "s/dev-pathfinder\.us\.auth0\.com/$VITE_AUTH0_DOMAIN/g" "$file"
        echo "✅ Replaced Auth0 domain in $file"
    fi
    
    # Replace other environment variables if needed
    if [ -n "$VITE_AUTH0_CLIENT_ID" ]; then
        # This is more complex as the client ID might be in multiple places
        echo "ℹ️  Auth0 Client ID available for replacement if needed"
    fi
done

echo "✅ Runtime environment variable replacement completed"

# Start nginx
echo "🚀 Starting nginx..."
exec nginx -g "daemon off;"
