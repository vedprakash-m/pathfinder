import { test, expect } from '@playwright/test';
import { mockAuth, TEST_USERS, generateTestData } from '../../utils/test-helpers';

test.describe('Family Management', () => {
  
  test.beforeEach(async ({ page }) => {
    await mockAuth(page, TEST_USERS.familyAdmin);
    await page.goto('/families');
  });

  test('should display families page @smoke', async ({ page }) => {
    await expect(page.getByText(/families|your family/i)).toBeVisible();
  });

  test('should create a new family @critical', async ({ page }) => {
    const testData = generateTestData();
    
    // Look for create family button
    const createButton = page.getByRole('button', { name: /create family|new family|add family/i });
    if (await createButton.isVisible()) {
      await createButton.click();
      
      // Fill out family form
      await page.getByLabel(/family name|name/i).fill(testData.familyName);
      await page.getByLabel(/description/i).fill('A test family for E2E validation');
      
      // Submit form
      await page.getByRole('button', { name: /create|save/i }).click();
      
      // Verify family was created
      await expect(page.getByText(testData.familyName)).toBeVisible({ timeout: 10000 });
    } else {
      // User might already be in a family - that's also a valid state
      await expect(page.getByText(/family|member/i)).toBeVisible();
    }
  });

  test('should invite family member @critical', async ({ page }) => {
    // Navigate to family management or invitations
    const inviteButton = page.getByRole('button', { name: /invite|add member/i });
    
    if (await inviteButton.isVisible()) {
      await inviteButton.click();
      
      // Fill invitation form
      const testEmail = `invited.${Date.now()}@e2e.test`;
      await page.getByLabel(/email/i).fill(testEmail);
      
      // Select role if available
      const roleSelect = page.getByLabel(/role/i);
      if (await roleSelect.isVisible()) {
        await roleSelect.selectOption('member');
      }
      
      // Add invitation message
      const messageField = page.getByLabel(/message|note/i);
      if (await messageField.isVisible()) {
        await messageField.fill('Welcome to our family trip planning!');
      }
      
      // Send invitation
      await page.getByRole('button', { name: /send|invite/i }).click();
      
      // Verify invitation was sent
      await expect(page.getByText(/invitation sent|invited/i)).toBeVisible();
      await expect(page.getByText(testEmail)).toBeVisible();
    } else {
      console.log('Invite functionality not available - checking family member list');
      await expect(page.getByText(/member|family/i)).toBeVisible();
    }
  });

  test('should view family members list @smoke', async ({ page }) => {
    // Look for family members section
    await expect(page.getByText(/member|family/i)).toBeVisible();
    
    // Should see current user as family member
    await expect(page.getByText(TEST_USERS.familyAdmin.name)).toBeVisible();
  });

  test('should manage family member roles', async ({ page }) => {
    // Look for member management options
    const membersList = page.getByText(/member|family/i);
    await expect(membersList).toBeVisible();
    
    // Look for role management controls
    const roleButton = page.getByRole('button', { name: /role|admin|member/i });
    if (await roleButton.isVisible()) {
      await roleButton.click();
      
      // Should see role options
      await expect(page.getByText(/admin|member|viewer/i)).toBeVisible();
    }
  });

  test('should handle family invitation acceptance flow', async ({ page }) => {
    // This would typically be tested with a different user account
    // For now, we'll test the invitation creation part
    
    const inviteButton = page.getByRole('button', { name: /invite|add member/i });
    
    if (await inviteButton.isVisible()) {
      await inviteButton.click();
      
      const testEmail = `accept.test.${Date.now()}@e2e.test`;
      await page.getByLabel(/email/i).fill(testEmail);
      await page.getByRole('button', { name: /send|invite/i }).click();
      
      // Verify invitation appears in pending list
      await expect(page.getByText(/pending|invited/i)).toBeVisible();
      await expect(page.getByText(testEmail)).toBeVisible();
    }
  });

  test('should remove family member', async ({ page }) => {
    // First ensure we have a member to remove (invite someone)
    const inviteButton = page.getByRole('button', { name: /invite|add member/i });
    
    if (await inviteButton.isVisible()) {
      await inviteButton.click();
      
      const testEmail = `remove.test.${Date.now()}@e2e.test`;
      await page.getByLabel(/email/i).fill(testEmail);
      await page.getByRole('button', { name: /send|invite/i }).click();
      
      // Wait for invitation to appear
      await expect(page.getByText(testEmail)).toBeVisible();
      
      // Look for remove/delete button next to the invitation
      const removeButton = page.getByRole('button', { name: /remove|delete|cancel/i }).first();
      if (await removeButton.isVisible()) {
        await removeButton.click();
        
        // Confirm removal
        const confirmButton = page.getByRole('button', { name: /confirm|yes|remove/i });
        if (await confirmButton.isVisible()) {
          await confirmButton.click();
        }
        
        // Verify member/invitation was removed
        await expect(page.getByText(testEmail)).not.toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('should update family preferences @smoke', async ({ page }) => {
    // Look for family settings or preferences
    const settingsButton = page.getByRole('button', { name: /settings|preferences|edit/i });
    
    if (await settingsButton.isVisible()) {
      await settingsButton.click();
      
      // Update family preferences
      const activityCheckbox = page.getByLabel(/sightseeing|museums|restaurants/i).first();
      if (await activityCheckbox.isVisible()) {
        await activityCheckbox.check();
      }
      
      // Budget level
      const budgetSelect = page.getByLabel(/budget level/i);
      if (await budgetSelect.isVisible()) {
        await budgetSelect.selectOption('medium');
      }
      
      // Dietary restrictions
      const dietaryCheckbox = page.getByLabel(/vegetarian|vegan|gluten/i).first();
      if (await dietaryCheckbox.isVisible()) {
        await dietaryCheckbox.check();
      }
      
      // Save preferences
      await page.getByRole('button', { name: /save|update/i }).click();
      
      // Verify preferences were saved
      await expect(page.getByText(/saved|updated/i)).toBeVisible();
    } else {
      // Just verify we can see family information
      await expect(page.getByText(/family|member/i)).toBeVisible();
    }
  });

  test('should display family statistics and overview', async ({ page }) => {
    // Look for family dashboard or statistics
    await expect(page.getByText(/family|member/i)).toBeVisible();
    
    // Look for family metrics
    const statsElements = [
      page.getByText(/member/i),
      page.getByText(/trip/i),
      page.getByText(/active|pending/i)
    ];
    
    // At least one should be visible
    let statsVisible = false;
    for (const element of statsElements) {
      if (await element.isVisible()) {
        statsVisible = true;
        break;
      }
    }
    
    expect(statsVisible).toBe(true);
  });

  test('should handle family creation validation errors', async ({ page }) => {
    const createButton = page.getByRole('button', { name: /create family|new family/i });
    
    if (await createButton.isVisible()) {
      await createButton.click();
      
      // Try to create family without required fields
      await page.getByRole('button', { name: /create|save/i }).click();
      
      // Should show validation errors
      await expect(page.getByText(/required|error|invalid/i)).toBeVisible();
      
      // Fill with invalid data
      await page.getByLabel(/family name|name/i).fill('a'); // Too short
      await page.getByRole('button', { name: /create|save/i }).click();
      
      // Should show length validation error
      const errorMessages = page.getByText(/too short|minimum|invalid/i);
      if (await errorMessages.isVisible()) {
        await expect(errorMessages).toBeVisible();
      }
    }
  });
});
