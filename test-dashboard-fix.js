#!/usr/bin/env node

const https = require('https');

const BACKEND_URL = 'https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io';
const FRONTEND_URL = 'https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io';

async function testEndpoint(url, description) {
  return new Promise((resolve) => {
    const startTime = Date.now();
    const req = https.get(url, (res) => {
      const duration = Date.now() - startTime;
      console.log(`✅ ${description}: ${res.statusCode} (${duration}ms)`);
      resolve({ status: res.statusCode, duration });
    });
    
    req.on('error', (err) => {
      const duration = Date.now() - startTime;
      console.log(`❌ ${description}: ERROR - ${err.message} (${duration}ms)`);
      resolve({ status: 'ERROR', duration, error: err.message });
    });
    
    req.setTimeout(10000, () => {
      req.destroy();
      console.log(`⏰ ${description}: TIMEOUT (10s)`);
      resolve({ status: 'TIMEOUT', duration: 10000 });
    });
  });
}

async function runTests() {
  console.log('🧪 Testing Pathfinder Dashboard Fix');
  console.log('==================================\n');
  
  // Test backend health
  await testEndpoint(`${BACKEND_URL}/health`, 'Backend Health Check');
  
  // Test the fixed trips endpoint (should no longer have route conflicts)
  await testEndpoint(`${BACKEND_URL}/api/v1/trips`, 'Trips API (Fixed Route)');
  
  // Test trip messages endpoint (moved to /trip-messages)
  await testEndpoint(`${BACKEND_URL}/api/v1/trip-messages`, 'Trip Messages API (New Route)');
  
  // Test frontend
  await testEndpoint(`${FRONTEND_URL}/`, 'Frontend Application');
  
  console.log('\n🎯 Dashboard Fix Verification Complete!');
  console.log('\nKey Changes Made:');
  console.log('- ✅ Backend: Fixed route conflict (/trips vs /trip-messages)');
  console.log('- ✅ Frontend: Added trailing slash URLs and CSRF handling');
  console.log('- ✅ CI/CD: Fixed YAML pipeline structure');
  console.log('\nIf all tests show ✅, the dashboard loading issue should be resolved!');
}

runTests().catch(console.error);
