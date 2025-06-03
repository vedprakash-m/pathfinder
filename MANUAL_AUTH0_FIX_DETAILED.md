# 🔧 Manual Auth0 Fix - Step-by-Step Guide

## Situation Summary
- ✅ Auth0 credentials were rotated on May 31, 2025
- ✅ New credentials stored in Azure Key Vault `pathfinder-kv-dev`
- ❌ Frontend still built with placeholder instead of actual Client ID
- 🚨 **Result:** Users cannot login - authentication completely broken

## Manual Fix Process (15-30 minutes)

### Step 1: Retrieve Actual Auth0 Client ID

#### Option A: Azure Portal
1. Go to https://portal.azure.com
2. Navigate to **Key Vaults** → **pathfinder-kv-dev**
3. Click **Secrets** in the left menu
4. Find and click **auth0-client-id**
5. Click on the current version
6. Copy the **Secret Value** (32-character string)

#### Option B: Azure CLI (if available)
```bash
az keyvault secret show \
  --vault-name pathfinder-kv-dev \
  --name auth0-client-id \
  --query 'value' \
  --output tsv
```

### Step 2: Update Frontend Configuration

**File to edit:** `frontend/.env.production`

**Current content:**
```bash
VITE_AUTH0_CLIENT_ID=PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID
```

**Update to:**
```bash
VITE_AUTH0_CLIENT_ID=ACTUAL_32_CHAR_CLIENT_ID_FROM_STEP1
```

**Example:**
```bash
# Replace PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID with the actual value
VITE_AUTH0_CLIENT_ID=AbC123XyZ789... # (actual 32-character Client ID)
```

### Step 3: Update Auth0 Config Fallback (Optional)

**File to edit:** `frontend/src/auth0-config.ts`

**Current line 7:**
```typescript
clientId: import.meta.env.VITE_AUTH0_CLIENT_ID || 'PLACEHOLDER_CLIENT_ID_NEEDS_ROTATION',
```

**Update to:**
```typescript
clientId: import.meta.env.VITE_AUTH0_CLIENT_ID || 'ACTUAL_CLIENT_ID_HERE',
```

### Step 4: Rebuild and Deploy Frontend

#### Option A: Azure Container Registry Build (Recommended)
```bash
# Set environment variables
export VITE_AUTH0_DOMAIN="dev-jwnud3v8ghqnyygr.us.auth0.com"
export VITE_AUTH0_CLIENT_ID="ACTUAL_CLIENT_ID_FROM_STEP1"
export VITE_AUTH0_AUDIENCE="https://pathfinder-api.com"
export VITE_API_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

# Build using Azure Container Registry
az acr build \
  --registry pathfinderdevregistry \
  --image pathfinder-frontend:auth0-fixed \
  --file frontend/Dockerfile \
  --build-arg VITE_AUTH0_DOMAIN="$VITE_AUTH0_DOMAIN" \
  --build-arg VITE_AUTH0_CLIENT_ID="$VITE_AUTH0_CLIENT_ID" \
  --build-arg VITE_AUTH0_AUDIENCE="$VITE_AUTH0_AUDIENCE" \
  --build-arg VITE_API_URL="$VITE_API_URL" \
  frontend/

# Update container app
az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --image pathfinderdevregistry.azurecr.io/pathfinder-frontend:auth0-fixed
```

#### Option B: Container Environment Variables (Alternative)
1. Go to Azure Portal → Container Apps → **pathfinder-frontend**
2. Click **Configuration** → **Environment variables**
3. Find `VITE_AUTH0_CLIENT_ID` and update its value to the actual Client ID
4. Click **Save** and restart the container

### Step 5: Verification Testing

1. **Open the application:**
   https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/

2. **Test login functionality:**
   - Click the "Login" button
   - Should redirect to Auth0 login page (not show errors)
   - Complete login with test credentials
   - Should redirect back to dashboard

3. **Check browser console (F12):**
   - Should NOT see "Unknown host" errors
   - Should NOT see Auth0 client errors
   - Should see successful authentication logs

### Step 6: Verify Fix is Complete

**Expected Results:**
- ✅ Auth0 login page loads without errors
- ✅ Users can complete authentication flow  
- ✅ No "Unknown host" or "Invalid client" errors
- ✅ Authenticated users reach dashboard
- ✅ Browser console shows no Auth0 errors

**If issues persist:**
1. Verify the Client ID was copied correctly (32 characters, no spaces)
2. Check that the Auth0 domain is still `dev-jwnud3v8ghqnyygr.us.auth0.com`
3. Confirm the container was rebuilt with the new credentials
4. Review container logs for any build or runtime errors

## 🚨 Why This Fix is Critical

**Current Impact:**
- 🔴 **Zero users can login** - authentication completely broken
- 🔴 **Phase 1 MVP cannot be demonstrated** - core functionality inaccessible  
- 🔴 **Business operations halted** - no access to trip planning features

**Post-Fix:**
- ✅ **Full authentication functionality restored**
- ✅ **Phase 1 MVP fully operational**
- ✅ **Users can access all protected features**

## Expected Timeline
- **Credential Retrieval:** 5 minutes
- **Configuration Update:** 5 minutes  
- **Container Rebuild:** 10-15 minutes
- **Testing & Verification:** 5 minutes
- **Total:** 25-30 minutes

---

**Priority:** 🔴 CRITICAL - Zero user authentication capability
**Complexity:** Medium (requires Azure access and container rebuild)
**Success Criteria:** Users can successfully login and access dashboard
