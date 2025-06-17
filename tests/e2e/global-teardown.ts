import { FullConfig } from '@playwright/test';
import { cleanupTestDatabase } from './utils/test-helpers';

/**
 * Global teardown that runs once after all tests
 * Cleans up test data and resources
 */
async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting E2E test environment cleanup...');

  // Cleanup test database
  console.log('🗑️ Cleaning up test database...');
  await cleanupTestDatabase();
  console.log('✅ Test database cleaned');

  console.log('✅ E2E environment cleanup complete');
}

export default globalTeardown;
