# Deploying Fixed Frontend to Azure

This document outlines the steps to deploy the fixed frontend with the correct Auth0 domain.

## Prerequisites
- A machine with Docker installed
- Azure CLI installed and configured
- Access to the Azure subscription containing Pathfinder resources
- Access to the Azure Container Registry

## Deployment Steps

### Option 1: Using the Deployment Script

1. Copy the built frontend code to a machine with Docker and Azure access
2. Run the provided deployment script:
   ```bash
   ./deploy-fixed-frontend.sh
   ```

### Option 2: Manual Deployment

1. **Build the Docker image**
   ```bash
   cd /path/to/pathfinder/frontend
   docker build -t pathfinder-frontend:fixed .
   ```

2. **Tag and push to Azure Container Registry**
   ```bash
   ACR_NAME="pathfinderacr"
   az acr login --name $ACR_NAME
   docker tag pathfinder-frontend:fixed $ACR_NAME.azurecr.io/pathfinder-frontend:latest
   docker push $ACR_NAME.azurecr.io/pathfinder-frontend:latest
   ```

3. **Update the Container App**
   ```bash
   az containerapp update \
     --name pathfinder-frontend \
     --resource-group pathfinder-rg \
     --image $ACR_NAME.azurecr.io/pathfinder-frontend:latest
   ```

## Verification

After deployment, verify that:

1. The application loads correctly
2. Users can sign up and log in without the "Unknown host" error
3. Authentication flows work end-to-end

## Rollback Procedure

If issues occur with the new deployment:

1. **Revert to previous image**
   ```bash
   az containerapp revision list --name pathfinder-frontend --resource-group pathfinder-rg
   
   # Find the previous working revision and activate it
   az containerapp revision activate \
     --name pathfinder-frontend \
     --resource-group pathfinder-rg \
     --revision [previous-revision-name]
   ```

## Troubleshooting

If authentication issues persist:
1. Verify Key Vault has the correct Auth0 domain: `dev-jwnud3v8ghqnyygr.us.auth0.com`
2. Confirm Container App environment variables are correctly using Key Vault references
3. Check the application logs for any errors related to Auth0 configuration
