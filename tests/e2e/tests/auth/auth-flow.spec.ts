import { test, expect } from '@playwright/test';
import { mockAuth, TEST_USERS } from '../../utils/test-helpers';

test.describe('Authentication Flow', () => {
  
  test.beforeEach(async ({ page }) => {
    // Start with clean state
    await page.goto('/');
  });

  test('should display login page for unauthenticated users @smoke', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Should redirect to login or show login prompt
    await expect(page.getByText(/sign in|login|get started/i)).toBeVisible();
    await expect(page.url()).toMatch(/login|auth|signin/);
  });

  test('should navigate to dashboard after successful authentication @critical', async ({ page }) => {
    // Mock successful authentication
    await mockAuth(page, TEST_USERS.user1);
    
    await page.goto('/');
    
    // Click login/get started button
    const loginButton = page.getByRole('button', { name: /get started|sign in|login/i });
    if (await loginButton.isVisible()) {
      await loginButton.click();
    }
    
    // Should navigate to dashboard or show authenticated content
    await expect(page.getByText(/dashboard|welcome/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(TEST_USERS.user1.name)).toBeVisible();
  });

  test('should handle logout correctly @critical', async ({ page }) => {
    // Start authenticated
    await mockAuth(page, TEST_USERS.user1);
    await page.goto('/dashboard');
    
    // Find and click logout
    const userMenu = page.getByRole('button', { name: new RegExp(TEST_USERS.user1.name, 'i') });
    if (await userMenu.isVisible()) {
      await userMenu.click();
      await page.getByRole('button', { name: /logout|sign out/i }).click();
    } else {
      // Look for direct logout button
      await page.getByRole('button', { name: /logout|sign out/i }).click();
    }
    
    // Should redirect to homepage or login
    await expect(page.getByText(/sign in|login|get started/i)).toBeVisible();
  });

  test('should display user profile information @smoke', async ({ page }) => {
    await mockAuth(page, TEST_USERS.user1);
    await page.goto('/dashboard');
    
    // Verify user profile is displayed
    await expect(page.getByText(TEST_USERS.user1.name)).toBeVisible();
    await expect(page.getByText(TEST_USERS.user1.email)).toBeVisible();
  });

  test('should handle authentication errors gracefully', async ({ page }) => {
    // Mock failed authentication
    await page.addInitScript(() => {
      window.localStorage.setItem('auth0-is-authenticated', 'false');
      window.localStorage.removeItem('auth_token');
    });
    
    await page.goto('/dashboard');
    
    // Should handle error gracefully
    await expect(page.getByText(/error|sign in|login/i)).toBeVisible();
  });

  test('should maintain authentication state across navigation @critical', async ({ page }) => {
    await mockAuth(page, TEST_USERS.user1);
    await page.goto('/dashboard');
    
    // Navigate to different pages
    const pages = ['/trips', '/families', '/dashboard'];
    
    for (const path of pages) {
      await page.goto(path);
      await expect(page.getByText(TEST_USERS.user1.name)).toBeVisible();
    }
  });

  test('should redirect to intended page after authentication', async ({ page }) => {
    // Try to access protected page while unauthenticated
    await page.goto('/trips/new');
    
    // Should redirect to login
    await expect(page.getByText(/sign in|login/i)).toBeVisible();
    
    // Mock authentication
    await mockAuth(page, TEST_USERS.user1);
    await page.reload();
    
    // Should redirect back to intended page
    await expect(page.url()).toContain('/trips');
  });
});
