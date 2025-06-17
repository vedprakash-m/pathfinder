import { test as setup, expect } from '@playwright/test';
import { setupTestDatabase, healthCheck } from '../utils/test-helpers';

const authFile = 'playwright/.auth/user.json';

/**
 * Global setup for all E2E tests
 * This runs once before all test files
 */
setup('authenticate users and setup data', async ({ page }) => {
  console.log('🔧 Setting up E2E test environment...');

  // Verify all services are healthy
  const health = await healthCheck();
  expect(health.allHealthy, 'All services should be healthy').toBe(true);

  // Setup test database
  await setupTestDatabase();

  // Authenticate test user and save state
  await page.goto('/');
  
  // Mock authentication since we're using mock auth service
  await page.addInitScript(() => {
    // Mock successful authentication
    window.localStorage.setItem('auth_token', 'mock-e2e-token');
    window.localStorage.setItem('auth0-is-authenticated', 'true');
    window.localStorage.setItem('auth0-user', JSON.stringify({
      sub: 'auth0|e2e_user_1',
      email: 'user1@e2e.test',
      name: 'Test User One',
      picture: 'https://example.com/avatar.png'
    }));
  });

  // Navigate to ensure auth state is applied
  await page.goto('/dashboard');
  
  // Wait for authentication to be processed
  await expect(page.getByText(/dashboard|welcome/i)).toBeVisible({ timeout: 10000 });

  // Save auth state
  await page.context().storageState({ path: authFile });
  
  console.log('✅ E2E setup complete');
});
