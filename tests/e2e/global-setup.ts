import { FullConfig } from '@playwright/test';
import { setupTestDatabase, healthCheck } from './utils/test-helpers';

/**
 * Global setup that runs once before all tests
 * Sets up test data, verifies services are healthy
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E test environment setup...');

  // Health check all services
  console.log('⚡ Performing health checks...');
  const healthResults = await healthCheck();
  
  if (!healthResults.allHealthy) {
    console.error('❌ Some services are not healthy:', healthResults);
    throw new Error('Services not ready for testing');
  }
  
  console.log('✅ All services healthy');

  // Setup test database with initial data
  console.log('🗄️ Setting up test database...');
  await setupTestDatabase();
  console.log('✅ Test database initialized');

  console.log('🎯 E2E environment ready for testing!');
}

export default globalSetup;
