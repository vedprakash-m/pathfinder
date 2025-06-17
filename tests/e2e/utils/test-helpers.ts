import axios from 'axios';
import { MongoClient } from 'mongodb';
import Redis from 'redis';

// Environment configuration
export const E2E_CONFIG = {
  frontend: {
    url: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3001',
  },
  backend: {
    url: process.env.API_BASE_URL || 'http://localhost:8001',
  },
  mongodb: {
    url: process.env.MONGODB_URL || 'mongodb://localhost:27018/pathfinder_e2e',
  },
  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6380',
  },
};

// Test user credentials for E2E tests
export const TEST_USERS = {
  user1: {
    email: 'user1@e2e.test',
    password: 'TestPass123!',
    name: 'Test User One',
    auth0_id: 'auth0|e2e_user_1',
  },
  user2: {
    email: 'user2@e2e.test',
    password: 'TestPass123!',
    name: 'Test User Two',
    auth0_id: 'auth0|e2e_user_2',
  },
  familyAdmin: {
    email: 'admin@family.test',
    password: 'AdminPass123!',
    name: 'Family Admin',
    auth0_id: 'auth0|family_admin',
  },
};

// Test data templates
export const TEST_DATA = {
  family: {
    name: 'E2E Test Family',
    description: 'A test family for E2E testing',
    preferences: {
      activities: ['sightseeing', 'restaurants', 'museums'],
      budget_level: 'medium',
      dietary_restrictions: ['vegetarian'],
      accessibility_needs: [],
      travel_style: 'relaxed',
    },
  },
  trip: {
    title: 'E2E Test Trip',
    description: 'A test trip for E2E validation',
    destination: 'San Francisco, CA',
    budget_total: 3000.0,
    max_participants: 10,
    is_public: false,
  },
};

/**
 * Health check all services
 */
export async function healthCheck() {
  const results = {
    frontend: false,
    backend: false,
    mongodb: false,
    redis: false,
    allHealthy: false,
  };

  try {
    // Frontend health check
    const frontendResponse = await axios.get(E2E_CONFIG.frontend.url, { timeout: 5000 });
    results.frontend = frontendResponse.status === 200;
  } catch (error) {
    console.warn('Frontend health check failed:', error.message);
  }

  try {
    // Backend health check
    const backendResponse = await axios.get(`${E2E_CONFIG.backend.url}/health`, { timeout: 5000 });
    results.backend = backendResponse.status === 200;
  } catch (error) {
    console.warn('Backend health check failed:', error.message);
  }

  try {
    // MongoDB health check
    const mongoClient = new MongoClient(E2E_CONFIG.mongodb.url);
    await mongoClient.connect();
    await mongoClient.db().admin().ping();
    await mongoClient.close();
    results.mongodb = true;
  } catch (error) {
    console.warn('MongoDB health check failed:', error.message);
  }

  try {
    // Redis health check
    const redisClient = Redis.createClient({ url: E2E_CONFIG.redis.url });
    await redisClient.connect();
    await redisClient.ping();
    await redisClient.quit();
    results.redis = true;
  } catch (error) {
    console.warn('Redis health check failed:', error.message);
  }

  results.allHealthy = results.frontend && results.backend && results.mongodb && results.redis;
  return results;
}

/**
 * Setup test database with initial data
 */
export async function setupTestDatabase() {
  const mongoClient = new MongoClient(E2E_CONFIG.mongodb.url);
  
  try {
    await mongoClient.connect();
    const db = mongoClient.db();

    // Clear existing test data
    await db.collection('users').deleteMany({ email: { $regex: '@e2e.test$' } });
    await db.collection('families').deleteMany({ name: /E2E Test/ });
    await db.collection('trips').deleteMany({ title: /E2E Test/ });

    // Create test users
    await db.collection('users').insertMany([
      {
        email: TEST_USERS.user1.email,
        name: TEST_USERS.user1.name,
        auth0_id: TEST_USERS.user1.auth0_id,
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
      },
      {
        email: TEST_USERS.user2.email,
        name: TEST_USERS.user2.name,
        auth0_id: TEST_USERS.user2.auth0_id,
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
      },
      {
        email: TEST_USERS.familyAdmin.email,
        name: TEST_USERS.familyAdmin.name,
        auth0_id: TEST_USERS.familyAdmin.auth0_id,
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
      },
    ]);

    console.log('✅ Test users created');

    // Create test family
    const familyResult = await db.collection('families').insertOne({
      name: TEST_DATA.family.name,
      description: TEST_DATA.family.description,
      preferences: TEST_DATA.family.preferences,
      created_by: TEST_USERS.familyAdmin.auth0_id,
      created_at: new Date(),
      updated_at: new Date(),
    });

    console.log('✅ Test family created:', familyResult.insertedId);

  } finally {
    await mongoClient.close();
  }
}

/**
 * Cleanup test database
 */
export async function cleanupTestDatabase() {
  const mongoClient = new MongoClient(E2E_CONFIG.mongodb.url);
  
  try {
    await mongoClient.connect();
    const db = mongoClient.db();

    // Remove all test data
    await db.collection('users').deleteMany({ email: { $regex: '@e2e.test$' } });
    await db.collection('families').deleteMany({ name: /E2E Test/ });
    await db.collection('trips').deleteMany({ title: /E2E Test/ });
    await db.collection('invitations').deleteMany({ email: { $regex: '@e2e.test$' } });

    console.log('✅ Test data cleaned up');

  } finally {
    await mongoClient.close();
  }
}

/**
 * Wait for element with retry logic
 */
export async function waitForElement(page: any, selector: string, timeout = 10000) {
  return await page.waitForSelector(selector, { timeout });
}

/**
 * Generate test data with faker
 */
export function generateTestData() {
  return {
    email: `test.${Date.now()}@e2e.test`,
    name: `Test User ${Math.random().toString(36).substring(7)}`,
    tripTitle: `Test Trip ${Math.random().toString(36).substring(7)}`,
    familyName: `Test Family ${Math.random().toString(36).substring(7)}`,
  };
}

/**
 * Mock authentication for testing
 */
export async function mockAuth(page: any, user = TEST_USERS.user1) {
  await page.addInitScript((userData) => {
    // Mock localStorage auth data
    window.localStorage.setItem('auth_token', 'mock-jwt-token');
    window.localStorage.setItem('user_data', JSON.stringify(userData));
    
    // Mock Auth0 state
    window.localStorage.setItem('auth0-is-authenticated', 'true');
    window.localStorage.setItem('auth0-user', JSON.stringify({
      sub: userData.auth0_id,
      email: userData.email,
      name: userData.name,
      picture: 'https://example.com/avatar.png',
    }));
  }, user);
}

/**
 * API request helper with authentication
 */
export async function apiRequest(method: string, endpoint: string, data?: any, token?: string) {
  const headers: any = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await axios({
    method,
    url: `${E2E_CONFIG.backend.url}${endpoint}`,
    data,
    headers,
  });

  return response;
}

/**
 * Take screenshot with timestamp
 */
export async function takeScreenshot(page: any, name: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({ 
    path: `test-results/screenshots/${name}-${timestamp}.png`,
    fullPage: true 
  });
}
