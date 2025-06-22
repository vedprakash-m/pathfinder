# Environment Setup for Microsoft Entra External ID

This document describes the environment variables needed to configure Microsoft Entra External ID authentication.

## Required Environment Variables

Create a `.env.local` file in the `frontend/` directory with the following variables:

```bash
# Microsoft Entra External ID Configuration

# Required: Your Entra External ID Tenant ID
VITE_ENTRA_EXTERNAL_TENANT_ID=your-tenant-id-here

# Required: Your Entra External ID Application Client ID
VITE_ENTRA_EXTERNAL_CLIENT_ID=your-client-id-here

# Optional: API URL (defaults to localhost:8000 in development)
VITE_API_URL=http://localhost:8000
```

## How to Get These Values

1. **Azure Portal Setup**:
   - Navigate to [Azure Portal](https://portal.azure.com)
   - Go to **Azure Active Directory** > **App registrations**
   - Select your application or create a new one

2. **Tenant ID**:
   - In your app registration, go to **Overview**
   - Copy the **Directory (tenant) ID**

3. **Client ID**:
   - In your app registration, go to **Overview**
   - Copy the **Application (client) ID**

## Backend Environment Variables

Ensure your backend also has the corresponding variables in `backend/.env`:

```bash
# Microsoft Entra External ID Configuration
ENTRA_EXTERNAL_TENANT_ID=your-tenant-id-here
ENTRA_EXTERNAL_CLIENT_ID=your-client-id-here
ENTRA_EXTERNAL_CLIENT_SECRET=your-client-secret-here
```

## Development vs Production

- **Development**: Uses test values for quick setup
- **Production**: Requires actual Azure Entra External ID values

The application will warn if test values are detected in production.

## Migration Notes

This replaces the previous Auth0 configuration:
- ~~`VITE_AUTH0_DOMAIN`~~ → `VITE_ENTRA_EXTERNAL_TENANT_ID`
- ~~`VITE_AUTH0_CLIENT_ID`~~ → `VITE_ENTRA_EXTERNAL_CLIENT_ID`
- ~~`VITE_AUTH0_AUDIENCE`~~ → Handled automatically by MSAL 