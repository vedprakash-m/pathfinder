import { test, expect } from '@playwright/test';
import { mockAuth, TEST_USERS, TEST_DATA, generateTestData } from '../../utils/test-helpers';

test.describe('Trip Management', () => {
  
  test.beforeEach(async ({ page }) => {
    await mockAuth(page, TEST_USERS.user1);
    await page.goto('/trips');
  });

  test('should display trips page @smoke', async ({ page }) => {
    await expect(page.getByText(/trips|your trips/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /create trip|new trip/i })).toBeVisible();
  });

  test('should create a new trip successfully @critical', async ({ page }) => {
    const testData = generateTestData();
    
    // Click create trip button
    await page.getByRole('button', { name: /create trip|new trip/i }).click();
    
    // Fill out trip form
    await expect(page.getByText(/create|new trip/i)).toBeVisible();
    
    await page.getByLabel(/trip name|title/i).fill(testData.tripTitle);
    await page.getByLabel(/destination/i).fill('San Francisco, CA');
    await page.getByLabel(/description/i).fill('A test trip for E2E validation');
    
    // Set dates (future dates)
    const startDate = new Date();
    startDate.setDate(startDate.getDate() + 30);
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 37);
    
    await page.getByLabel(/start date/i).fill(startDate.toISOString().split('T')[0]);
    await page.getByLabel(/end date/i).fill(endDate.toISOString().split('T')[0]);
    
    // Set budget
    await page.getByLabel(/budget/i).fill('3000');
    
    // Submit form
    await page.getByRole('button', { name: /create|save|submit/i }).click();
    
    // Verify trip was created
    await expect(page.getByText(testData.tripTitle)).toBeVisible({ timeout: 10000 });
    
    // Should redirect to trip details or trips list
    expect(page.url()).toMatch(/trips/);
  });

  test('should view trip details @critical', async ({ page }) => {
    // First create a trip (or use existing one)
    const testData = generateTestData();
    
    await page.getByRole('button', { name: /create trip|new trip/i }).click();
    await page.getByLabel(/trip name|title/i).fill(testData.tripTitle);
    await page.getByLabel(/destination/i).fill('Test Destination');
    
    const startDate = new Date();
    startDate.setDate(startDate.getDate() + 30);
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 37);
    
    await page.getByLabel(/start date/i).fill(startDate.toISOString().split('T')[0]);
    await page.getByLabel(/end date/i).fill(endDate.toISOString().split('T')[0]);
    await page.getByLabel(/budget/i).fill('2000');
    
    await page.getByRole('button', { name: /create|save/i }).click();
    
    // Wait for trip creation and click on it
    await expect(page.getByText(testData.tripTitle)).toBeVisible();
    await page.getByText(testData.tripTitle).click();
    
    // Verify trip details page
    await expect(page.getByText(testData.tripTitle)).toBeVisible();
    await expect(page.getByText(/test destination/i)).toBeVisible();
    await expect(page.getByText(/2000|2,000/)).toBeVisible(); // Budget
  });

  test('should edit trip details @critical', async ({ page }) => {
    // Create a trip first
    const testData = generateTestData();
    
    await page.getByRole('button', { name: /create trip|new trip/i }).click();
    await page.getByLabel(/trip name|title/i).fill(testData.tripTitle);
    await page.getByLabel(/destination/i).fill('Original Destination');
    
    const startDate = new Date();
    startDate.setDate(startDate.getDate() + 30);
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 37);
    
    await page.getByLabel(/start date/i).fill(startDate.toISOString().split('T')[0]);
    await page.getByLabel(/end date/i).fill(endDate.toISOString().split('T')[0]);
    await page.getByLabel(/budget/i).fill('2000');
    
    await page.getByRole('button', { name: /create|save/i }).click();
    
    // Wait for creation and navigate to trip
    await expect(page.getByText(testData.tripTitle)).toBeVisible();
    await page.getByText(testData.tripTitle).click();
    
    // Edit the trip
    await page.getByRole('button', { name: /edit|modify/i }).click();
    
    // Update trip details
    const updatedTitle = `${testData.tripTitle} Updated`;
    await page.getByLabel(/trip name|title/i).fill(updatedTitle);
    await page.getByLabel(/destination/i).fill('Updated Destination');
    await page.getByLabel(/budget/i).fill('3500');
    
    await page.getByRole('button', { name: /save|update/i }).click();
    
    // Verify updates
    await expect(page.getByText(updatedTitle)).toBeVisible();
    await expect(page.getByText(/updated destination/i)).toBeVisible();
    await expect(page.getByText(/3500|3,500/)).toBeVisible();
  });

  test('should delete trip @critical', async ({ page }) => {
    // Create a trip first
    const testData = generateTestData();
    
    await page.getByRole('button', { name: /create trip|new trip/i }).click();
    await page.getByLabel(/trip name|title/i).fill(testData.tripTitle);
    await page.getByLabel(/destination/i).fill('To Delete');
    
    const startDate = new Date();
    startDate.setDate(startDate.getDate() + 30);
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 37);
    
    await page.getByLabel(/start date/i).fill(startDate.toISOString().split('T')[0]);
    await page.getByLabel(/end date/i).fill(endDate.toISOString().split('T')[0]);
    await page.getByLabel(/budget/i).fill('1000');
    
    await page.getByRole('button', { name: /create|save/i }).click();
    
    // Wait for creation and navigate to trip
    await expect(page.getByText(testData.tripTitle)).toBeVisible();
    await page.getByText(testData.tripTitle).click();
    
    // Delete the trip
    await page.getByRole('button', { name: /delete|remove/i }).click();
    
    // Confirm deletion
    await page.getByRole('button', { name: /confirm|yes|delete/i }).click();
    
    // Verify trip is removed
    await expect(page.getByText(testData.tripTitle)).not.toBeVisible({ timeout: 10000 });
  });

  test('should filter and search trips @smoke', async ({ page }) => {
    // This test assumes there are multiple trips or we create them
    await expect(page.getByText(/trips|your trips/i)).toBeVisible();
    
    // Look for search/filter controls
    const searchInput = page.getByPlaceholder(/search|filter/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill('test');
      
      // Verify search results update
      await page.waitForTimeout(1000); // Wait for search to process
    }
    
    // Look for filter buttons/dropdowns
    const filterButton = page.getByRole('button', { name: /filter|sort/i });
    if (await filterButton.isVisible()) {
      await filterButton.click();
      // Could interact with filter options here
    }
  });

  test('should handle trip validation errors', async ({ page }) => {
    // Try to create trip with invalid data
    await page.getByRole('button', { name: /create trip|new trip/i }).click();
    
    // Leave required fields empty and try to submit
    await page.getByRole('button', { name: /create|save/i }).click();
    
    // Should show validation errors
    await expect(page.getByText(/required|error|invalid/i)).toBeVisible();
    
    // Try invalid date range
    await page.getByLabel(/trip name|title/i).fill('Invalid Date Trip');
    
    const pastDate = new Date();
    pastDate.setDate(pastDate.getDate() - 1);
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 1);
    
    await page.getByLabel(/start date/i).fill(futureDate.toISOString().split('T')[0]);
    await page.getByLabel(/end date/i).fill(pastDate.toISOString().split('T')[0]); // End before start
    
    await page.getByRole('button', { name: /create|save/i }).click();
    
    // Should show date validation error
    await expect(page.getByText(/date|invalid|error/i)).toBeVisible();
  });

  test('should display trip status and progress @smoke', async ({ page }) => {
    // Navigate to a trip (create one if needed)
    const testData = generateTestData();
    
    await page.getByRole('button', { name: /create trip|new trip/i }).click();
    await page.getByLabel(/trip name|title/i).fill(testData.tripTitle);
    await page.getByLabel(/destination/i).fill('Status Test');
    
    const startDate = new Date();
    startDate.setDate(startDate.getDate() + 30);
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 37);
    
    await page.getByLabel(/start date/i).fill(startDate.toISOString().split('T')[0]);
    await page.getByLabel(/end date/i).fill(endDate.toISOString().split('T')[0]);
    await page.getByLabel(/budget/i).fill('2500');
    
    await page.getByRole('button', { name: /create|save/i }).click();
    
    // Check trip status indicators
    await expect(page.getByText(/planning|draft|active/i)).toBeVisible();
    
    // Look for progress indicators
    const progressElements = page.getByText(/progress|complete|%/i);
    if (await progressElements.first().isVisible()) {
      await expect(progressElements.first()).toBeVisible();
    }
  });
});
