# Secure Key Rotation - File Method
# 1. Create a temporary file with your rotated keys
# 2. Run the update script
# 3. File is automatically deleted

# Step 1: First rotate your keys:
# - Auth0: Dashboard → Applications → Pathfinder Frontend → Settings → Rotate Secret  
# - Google Maps: Google Cloud Console → APIs & Services → Credentials → Regenerate Key

# Step 2: Create temporary file (this file will be deleted automatically)
cat > /tmp/rotated-keys.txt << 'EOF'
AUTH0_CLIENT_SECRET=your-new-rotated-secret-here
GOOGLE_MAPS_API_KEY=your-new-regenerated-key-here
EOF

# Step 3: Run the secure update script
# The script will read from the file and delete it immediately
./scripts/file-key-update.sh

# File is automatically deleted after use for security
