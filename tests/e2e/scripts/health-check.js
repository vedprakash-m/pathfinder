#!/usr/bin/env node

const axios = require('axios');

const E2E_CONFIG = {
  frontend: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3001',
  backend: process.env.API_BASE_URL || 'http://localhost:8001',
  mongodb: process.env.MONGODB_URL || 'mongodb://localhost:27018/pathfinder_e2e',
  redis: process.env.REDIS_URL || 'redis://localhost:6380',
};

async function healthCheck() {
  console.log('🏥 Performing health checks...');
  
  const results = {
    frontend: false,
    backend: false,
    mongodb: false,
    redis: false,
  };

  // Frontend health check
  try {
    const response = await axios.get(E2E_CONFIG.frontend, { timeout: 5000 });
    results.frontend = response.status === 200;
    console.log(`✅ Frontend: ${E2E_CONFIG.frontend}`);
  } catch (error) {
    console.log(`❌ Frontend: ${E2E_CONFIG.frontend} - ${error.message}`);
  }

  // Backend health check
  try {
    const response = await axios.get(`${E2E_CONFIG.backend}/health`, { timeout: 5000 });
    results.backend = response.status === 200;
    console.log(`✅ Backend: ${E2E_CONFIG.backend}/health`);
  } catch (error) {
    console.log(`❌ Backend: ${E2E_CONFIG.backend}/health - ${error.message}`);
  }

  // MongoDB health check
  try {
    const { MongoClient } = require('mongodb');
    const client = new MongoClient(E2E_CONFIG.mongodb);
    await client.connect();
    await client.db().admin().ping();
    await client.close();
    results.mongodb = true;
    console.log(`✅ MongoDB: ${E2E_CONFIG.mongodb}`);
  } catch (error) {
    console.log(`❌ MongoDB: ${E2E_CONFIG.mongodb} - ${error.message}`);
  }

  // Redis health check
  try {
    const redis = require('redis');
    const client = redis.createClient({ url: E2E_CONFIG.redis });
    await client.connect();
    await client.ping();
    await client.quit();
    results.redis = true;
    console.log(`✅ Redis: ${E2E_CONFIG.redis}`);
  } catch (error) {
    console.log(`❌ Redis: ${E2E_CONFIG.redis} - ${error.message}`);
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
