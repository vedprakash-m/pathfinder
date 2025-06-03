# 🔧 Manual Auth0 Fix Completion Guide

## Current Status
- ✅ Auth0 credentials were rotated on May 31, 2025 at 23:09-23:10 UTC
- ✅ Azure Key Vault contains the new rotated credentials
- ❌ Frontend `.env.production` still contains placeholder `PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID`
- ✅ Application is accessible at https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/

## Problem
The frontend container was built with the placeholder value instead of the actual rotated Auth0 Client ID from Azure Key Vault. The terminal Azure CLI commands are not working properly in the current environment.

## Manual Solution Approach

### Option 1: Azure Portal Manual Fix
1. **Access Azure Key Vault via Portal:**
   - Go to https://portal.azure.com
   - Navigate to `pathfinder-kv-dev` Key Vault
   - Find secret `auth0-client-id` and copy the actual value

2. **Update Frontend Environment:**
   - Replace `PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID` in `frontend/.env.production`
   - Use the actual Client ID from Key Vault

3. **Rebuild and Deploy:**
   - Trigger a rebuild of the frontend container with correct credentials

### Option 2: Container Environment Variable Fix
1. **Update Container App Environment Variables:**
   - In Azure Portal, go to Container Apps
   - Find `pathfinder-frontend` container app
   - Update environment variable `VITE_AUTH0_CLIENT_ID` to use the Key Vault reference

### Current Auth0 Configuration
- **Domain:** `dev-jwnud3v8ghqnyygr.us.auth0.com` ✅ Correct
- **Client ID:** `PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID` ❌ Needs actual value
- **Audience:** `https://pathfinder-api.com` ✅ Correct

## Expected Auth0 Client ID Format
The rotated Auth0 Client ID should be a 32-character alphanumeric string (different from the old exposed one: `KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn`).

## Next Steps
1. Access Azure Portal to get the actual Auth0 Client ID
2. Update the frontend configuration
3. Rebuild and deploy the frontend
4. Test authentication functionality

## Verification
Once fixed, users should be able to:
- ✅ Click "Login" without "Unknown host" errors
- ✅ Complete Auth0 authentication flow
- ✅ Access protected routes after login

---
**Status:** Ready for manual completion via Azure Portal
**Priority:** High - Authentication is currently broken for users
