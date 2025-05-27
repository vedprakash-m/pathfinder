import { test, expect } from '@playwright/test';

// Basic home page test
test('homepage has title and links', async ({ page }) => {
  await page.goto('/');
  
  // Check title
  await expect(page).toHaveTitle(/Pathfinder/i);
  
  // Check for main heading
  const heading = page.getByRole('heading', { level: 1 });
  await expect(heading).toContainText(/Pathfinder/i);
  
  // Check for Get Started link
  const getStartedLink = page.getByRole('link', { name: /get started/i });
  await expect(getStartedLink).toBeVisible();
  
  // Ensure the link goes to login page
  await expect(getStartedLink).toHaveAttribute('href', '/login');
});

// Authentication flow test
test('login form works correctly', async ({ page }) => {
  await page.goto('/login');
  
  // Verify login form elements
  await expect(page.getByText(/sign in/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /login/i })).toBeVisible();
  
  // Note: Can't fully test Auth0 login since it's external
  // This would be a point where we'd mock the Auth0 service
});

// Navigation flow test (requires authentication mock)
test('authenticated user can navigate through app', async ({ page }) => {
  // Mock authentication
  await page.addInitScript(() => {
    window.localStorage.setItem('auth0-is-authenticated', 'true');
    window.localStorage.setItem('auth0-user', JSON.stringify({
      name: 'Test User',
      email: 'test@example.com',
      sub: 'auth0|test123',
      picture: 'https://example.com/avatar.png'
    }));
  });
  
  // Go to dashboard (which requires auth)
  await page.goto('/dashboard');
  
  // Check dashboard elements
  await expect(page.getByText(/dashboard/i)).toBeVisible();
  
  // Navigate to trips page
  await page.getByRole('link', { name: /trips/i }).click();
  await expect(page.url()).toContain('/trips');
  
  // Check trips page elements
  await expect(page.getByText(/your trips/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /create trip/i })).toBeVisible();
});

// Create trip flow test (requires authentication mock)
test('user can start trip creation process', async ({ page }) => {
  // Mock authentication
  await page.addInitScript(() => {
    window.localStorage.setItem('auth0-is-authenticated', 'true');
    window.localStorage.setItem('auth0-user', JSON.stringify({
      name: 'Test User',
      email: 'test@example.com',
      sub: 'auth0|test123'
    }));
  });
  
  // Go to trips page
  await page.goto('/trips');
  
  // Click on create trip button
  await page.getByRole('button', { name: /create trip/i }).click();
  await expect(page.url()).toContain('/trips/new');
  
  // Check create trip form elements
  await expect(page.getByText(/create new trip/i)).toBeVisible();
  await expect(page.getByLabel(/trip name/i)).toBeVisible();
  await expect(page.getByLabel(/destination/i)).toBeVisible();
  
  // Fill out the form
  await page.getByLabel(/trip name/i).fill('Paris Adventure');
  await page.getByLabel(/destination/i).fill('Paris, France');
  
  // Note: In a real test, we would complete the form submission
  // and verify the new trip appears in the trips list
});
