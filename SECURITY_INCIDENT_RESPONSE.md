# Security Incident Response - API Key Exposure

**Date:** May 31, 2025  
**Incident:** API keys exposed in chat conversation  
**Severity:** Medium (keys were used for development/testing)  
**Status:** Response in progress

## 🚨 Immediate Actions Required

### 1. **Rotate All Exposed Keys** (URGENT)

**Auth0 Credentials:**
- [ ] Go to Auth0 Dashboard → Applications → Pathfinder Frontend
- [ ] Click "Rotate Secret" to generate new Client Secret
- [ ] Copy new Client Secret for Key Vault update

**Google Maps API:**
- [ ] Go to Google Cloud Console → APIs & Services → Credentials  
- [ ] Find the exposed API key → Click "Regenerate Key"
- [ ] Copy new API key for Key Vault update

### 2. **Update Key Vault** (After rotation)

```bash
# Update Auth0 Client Secret
az keyvault secret set \
  --vault-name pathfinder-kv-dev \
  --name auth0-client-secret \
  --value "NEW_ROTATED_SECRET"

# Update Google Maps API Key  
az keyvault secret set \
  --vault-name pathfinder-kv-dev \
  --name google-maps-api-key \
  --value "NEW_REGENERATED_KEY"

# Restart containers to pick up new keys
az containerapp revision restart \
  --name pathfinder-backend \
  --resource-group pathfinder-rg-dev \
  --revision $(az containerapp revision list --name pathfinder-backend --resource-group pathfinder-rg-dev --query "[0].name" --output tsv)

az containerapp revision restart \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --revision $(az containerapp revision list --name pathfinder-frontend --resource-group pathfinder-rg-dev --query "[0].name" --output tsv)
```

### 3. **Security Monitoring**

**Auth0 Monitoring:**
- [ ] Check Auth0 logs for any unauthorized access attempts
- [ ] Review recent login attempts and API calls
- [ ] Monitor for unusual authentication patterns

**Google Maps Monitoring:**  
- [ ] Check Google Cloud Console → APIs & Services → Quotas
- [ ] Review recent API usage for anomalies
- [ ] Set up billing alerts if not already configured

### 4. **Preventive Measures**

**For Future Development:**
- ✅ Use placeholder values in documentation
- ✅ Never share actual API keys in chat/email
- ✅ Use environment variables and Key Vault references
- ✅ Implement API key rotation schedules
- ✅ Set up monitoring and alerting for API usage

**Key Vault Security:**
- ✅ RBAC permissions properly configured
- ✅ Access logging enabled
- ✅ Regular access reviews scheduled

## 📋 Post-Incident Checklist

After rotating keys:
- [ ] Verify application functionality with new keys
- [ ] Test Auth0 login flow
- [ ] Test Google Maps integration
- [ ] Update any documentation with placeholder values
- [ ] Schedule regular key rotation (quarterly)

## 🎯 Lessons Learned

1. **Never share production API keys in any medium**
2. **Use placeholder/dummy values in examples** 
3. **Implement automated key rotation where possible**
4. **Regular security reviews of exposed credentials**

---

**Next Review Date:** August 31, 2025  
**Responsible:** Development Team  
**Status:** In Progress → Complete after key rotation
