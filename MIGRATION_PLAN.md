# Microsoft Entra External ID Migration Plan
**Project**: Pathfinder Authentication Rip & Replace  
**Timeline**: 5-7 days  
**Strategy**: Complete replacement of Auth0 with Microsoft Entra External ID  

## 🎯 Migration Objectives

- ✅ **Eliminate Auth0 complexity** and test failures
- ✅ **Reduce authentication configuration** from 6 to 3 environment variables
- ✅ **Improve local validation** consistency with CI/CD
- ✅ **Achieve cost savings** (first 50K MAU free vs $23/month Auth0)
- ✅ **Unify Microsoft ecosystem** with existing Azure infrastructure

## 📋 Pre-Migration Checklist

### Azure Prerequisites
- [ ] **Azure Subscription** with contributor access
- [ ] **Entra External ID license** (included in Azure subscription)
- [ ] **Application registration** permissions in Azure AD
- [ ] **Custom domain** (optional) for branding

### Current State Analysis
- ✅ **Auth0 Integration Points Identified**:
  - Frontend: React components, Auth0Provider, token management
  - Backend: JWT validation, user sync, role mapping
  - Testing: Mock authentication, E2E flows
  - CI/CD: Environment variable configuration

## 🚀 Phase 1: Entra External ID Setup (Day 1)

### Step 1.1: Create External ID Tenant
```bash
# Via Azure CLI
az extension add --name authenticationmethod-policy
az ad signed-in-user show
az account set --subscription "your-subscription-id"

# Create External ID tenant
az rest --method POST \
  --url "https://graph.microsoft.com/beta/directory/administrativeUnits" \
  --body '{
    "displayName": "Pathfinder Customers",
    "description": "External ID tenant for Pathfinder customer authentication"
  }'
```

### Step 1.2: Configure Application Registration
- **Application Name**: `Pathfinder Customer App`
- **Application Type**: `Single Page Application (SPA)`
- **Redirect URIs**: 
  - `http://localhost:3000` (development)
  - `https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io` (production)
- **Logout URLs**: Same as redirect URIs
- **Scopes**: `openid`, `profile`, `email`, `offline_access`

### Step 1.3: Enable User Flows
- **Sign-up and Sign-in Flow**: Combined flow with email verification
- **Profile Editing Flow**: Allow users to update profile information  
- **Password Reset Flow**: Self-service password reset
- **Social Providers**: Google, GitHub (replace Auth0's social providers)

## 🔧 Phase 2: Backend Migration (Day 2-3)

### Step 2.1: Update Configuration
Replace Auth0 configuration in `backend/app/core/config.py` with Entra External ID settings.

### Step 2.2: Create New Auth Service
Create `backend/app/services/entra_auth_service.py` to replace Auth0 integration.

### Step 2.3: Update Security Module
Modify `backend/app/core/security.py` to use Entra External ID token validation.

## 🎨 Phase 3: Frontend Migration (Day 3-4)

### Step 3.1: Replace Dependencies
```bash
# Remove Auth0 packages
npm uninstall @auth0/auth0-react @auth0/auth0-spa-js

# Add Microsoft Authentication Library (MSAL)
npm install @azure/msal-browser @azure/msal-react
```

### Step 3.2: Replace Configuration
Replace `frontend/src/auth0-config.ts` with `frontend/src/entra-config.ts`.

### Step 3.3: Update Components
- Replace `Auth0Provider` with `MsalProvider`
- Update authentication hooks and services
- Modify login/logout flows

## 🧪 Phase 4: Testing Migration (Day 4-5)

### Step 4.1: Update Test Mocks
Replace Auth0 test mocks with Entra External ID equivalents.

### Step 4.2: Update E2E Tests
Modify authentication helpers and test flows.

### Step 4.3: Validate Test Coverage
Ensure all authentication tests pass with new provider.

## 🚀 Phase 5: Deployment (Day 5-6)

### Step 5.1: Environment Variables
Update all environment configurations for Entra External ID.

### Step 5.2: CI/CD Pipeline
Modify GitHub Actions workflows for new authentication provider.

### Step 5.3: Infrastructure Updates
Update Bicep templates with Entra External ID configuration.

## 📋 Phase 6: Testing & Validation (Day 6-7)

### Step 6.1: Local Testing Checklist
- [ ] **User Registration**: New user can sign up with email
- [ ] **User Login**: Existing user can sign in  
- [ ] **Social Login**: Google/GitHub authentication works
- [ ] **Token Validation**: Backend validates Entra tokens correctly
- [ ] **User Profile**: Profile data syncs correctly
- [ ] **Role Assignment**: Family Admin role assigned automatically
- [ ] **Family Creation**: Auto-family creation works
- [ ] **Logout**: Clean logout and token cleanup

### Step 6.2: E2E Testing
```bash
# Run comprehensive E2E tests
npm run test:e2e

# Validate authentication flows
npm run test:e2e -- --grep "authentication"

# Test family management with new auth
npm run test:e2e -- --grep "family"
```

### Step 6.3: Performance Testing
- [ ] **Token Acquisition Speed**: < 200ms for silent token refresh
- [ ] **Login Flow Speed**: < 2 seconds for complete login
- [ ] **API Response Times**: No degradation vs Auth0
- [ ] **Memory Usage**: No memory leaks in token management

## 🔄 Rollback Plan (Emergency Only)

### If Migration Fails:
1. **Revert environment variables** to Auth0 configuration
2. **Restore Auth0 dependencies** in package.json
3. **Revert code changes** using git
4. **Redeploy previous working version**

### Rollback Commands:
```bash
# Quick rollback to Auth0
git checkout HEAD~1 -- frontend/src/auth0-config.ts
git checkout HEAD~1 -- backend/app/core/config.py
git checkout HEAD~1 -- backend/app/services/auth_service.py
npm install @auth0/auth0-react @auth0/auth0-spa-js
npm uninstall @azure/msal-browser @azure/msal-react
```

## ✅ Success Criteria

### Functional Requirements
- [ ] Authentication flows work correctly
- [ ] Role-based access control functions
- [ ] Family management integration works
- [ ] Social login providers function

### Technical Requirements  
- [ ] Test pass rate ≥95% (improvement from 73.5%)
- [ ] Local validation matches CI/CD
- [ ] No performance degradation
- [ ] Proper security validation

### Cost Benefits
- [ ] Elimination of Auth0 subscription ($23/month minimum)
- [ ] First 50,000 MAU free with Entra External ID
- [ ] Reduced operational complexity

### Operational Requirements
- [ ] Deployment: Successful deployment to production
- [ ] Monitoring: Proper logging and error tracking
- [ ] Documentation: Updated documentation and runbooks
- [ ] Support: Team trained on Entra External ID administration

## 📞 Support & Resources

### Microsoft Resources
- **Entra External ID Documentation**: https://docs.microsoft.com/en-us/azure/active-directory-b2c/
- **MSAL.js Documentation**: https://docs.microsoft.com/en-us/azure/active-directory/develop/msal-overview
- **Microsoft Graph API**: https://docs.microsoft.com/en-us/graph/

### Internal Resources  
- **Azure Subscription Owner**: [Contact Details]
- **DevOps Lead**: [Contact Details]
- **Security Team**: [Contact Details]

---

**Migration Lead**: [Your Name]  
**Estimated Completion**: Day 7  
**Last Updated**: [Current Date] 

**Estimated Timeline**: 5-7 days  
**Risk Level**: Medium (well-defined migration path)  
**Impact**: High (resolves authentication pain points and reduces costs) 