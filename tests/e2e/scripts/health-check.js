#!/usr/bin/env node

const axios = require('axios');

const E2E_CONFIG = {
  frontend: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3001',
  backend: process.env.API_BASE_URL || 'http://localhost:8001',
  mongodb: process.env.MONGODB_URL || 'mongodb://localhost:27018/pathfinder_e2e',
  redis: process.env.REDIS_URL || 'redis://localhost:6380',
};

// Add timeout and retry configuration
const HEALTH_CHECK_CONFIG = {
  timeout: 10000,
  retries: 3,
  retryDelay: 2000,
};

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function checkWithRetry(checkFn, name, retries = HEALTH_CHECK_CONFIG.retries) {
  for (let i = 0; i <= retries; i++) {
    try {
      await checkFn();
      return true;
    } catch (error) {
      if (i === retries) {
        console.log(`❌ ${name}: ${error.message}`);
        return false;
      }
      console.log(`⏳ ${name}: Attempt ${i + 1}/${retries + 1} failed, retrying...`);
      await delay(HEALTH_CHECK_CONFIG.retryDelay);
    }
  }
}

async function healthCheck() {
  console.log('🏥 Performing health checks...');
  
  const results = {
    frontend: false,
    backend: false,
    mongodb: false,
    redis: false,
  };

  // Frontend health check with retry
  results.frontend = await checkWithRetry(async () => {
    const response = await axios.get(E2E_CONFIG.frontend, { 
      timeout: HEALTH_CHECK_CONFIG.timeout 
    });
    if (response.status !== 200) {
      throw new Error(`Status: ${response.status}`);
    }
  }, 'Frontend');

  if (results.frontend) {
    console.log(`✅ Frontend: ${E2E_CONFIG.frontend}`);
  }

  // Backend health check with retry
  results.backend = await checkWithRetry(async () => {
    const response = await axios.get(`${E2E_CONFIG.backend}/health`, { 
      timeout: HEALTH_CHECK_CONFIG.timeout 
    });
    if (response.status !== 200) {
      throw new Error(`Status: ${response.status}`);
    }
  }, 'Backend');

  if (results.backend) {
    console.log(`✅ Backend: ${E2E_CONFIG.backend}/health`);
  }

  // MongoDB health check with retry
  results.mongodb = await checkWithRetry(async () => {
    const { MongoClient } = require('mongodb');
    const client = new MongoClient(E2E_CONFIG.mongodb);
    await client.connect();
    await client.db().admin().ping();
    await client.close();
  }, 'MongoDB');

  if (results.mongodb) {
    console.log(`✅ MongoDB: ${E2E_CONFIG.mongodb}`);
  }

  // Redis health check with retry
  results.redis = await checkWithRetry(async () => {
    const redis = require('redis');
    const client = redis.createClient({ url: E2E_CONFIG.redis });
    await client.connect();
    await client.ping();
    await client.quit();
  }, 'Redis');

  if (results.redis) {
    console.log(`✅ Redis: ${E2E_CONFIG.redis}`);
  }

  const allHealthy = Object.values(results).every(Boolean);
  
  console.log('\n📊 Health Check Summary:');
  console.log(`Frontend: ${results.frontend ? '✅' : '❌'}`);
  console.log(`Backend: ${results.backend ? '✅' : '❌'}`);
  console.log(`MongoDB: ${results.mongodb ? '✅' : '❌'}`);
  console.log(`Redis: ${results.redis ? '✅' : '❌'}`);
  console.log(`Overall: ${allHealthy ? '✅ HEALTHY' : '❌ UNHEALTHY'}`);

  process.exit(allHealthy ? 0 : 1);
}

if (require.main === module) {
  healthCheck().catch(console.error);
}

module.exports = { healthCheck };
