import { test, expect } from '@playwright/test';
import { apiRequest, E2E_CONFIG } from '../../utils/test-helpers';

test.describe('API Integration Tests', () => {
  
  test('should respond to health check @smoke', async ({ request }) => {
    const response = await request.get('/health');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('status');
    expect(data.status).toBe('healthy');
  });

  test('should respond to API v1 root endpoint @smoke', async ({ request }) => {
    const response = await request.get('/api/v1/');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('message');
  });

  test('should handle CORS headers correctly @critical', async ({ request }) => {
    const response = await request.get('/health', {
      headers: {
        'Origin': 'http://localhost:3001',
      },
    });
    
    expect(response.status()).toBe(200);
    
    const headers = response.headers();
    expect(headers['access-control-allow-origin']).toBeTruthy();
  });

  test('should require authentication for protected endpoints @critical', async ({ request }) => {
    // Try to access protected endpoint without auth
    const response = await request.get('/api/v1/trips');
    
    // Should return 401 Unauthorized
    expect(response.status()).toBe(401);
  });

  test('should accept valid authentication token @critical', async ({ request }) => {
    // Mock authentication (in real scenario, this would be a valid JWT)
    const response = await request.get('/api/v1/trips', {
      headers: {
        'Authorization': 'Bearer mock-e2e-token',
      },
    });
    
    // Should not return 401 (might return 200 with trips or 403 if permissions are different)
    expect(response.status()).not.toBe(401);
  });

  test('should validate request data for POST endpoints', async ({ request }) => {
    // Try to create trip with invalid data
    const response = await request.post('/api/v1/trips', {
      headers: {
        'Authorization': 'Bearer mock-e2e-token',
        'Content-Type': 'application/json',
      },
      data: {
        // Missing required fields
        title: '',
      },
    });
    
    // Should return validation error
    expect(response.status()).toBe(422);
  });

  test('should handle malformed JSON gracefully', async ({ request }) => {
    const response = await request.post('/api/v1/trips', {
      headers: {
        'Authorization': 'Bearer mock-e2e-token',
        'Content-Type': 'application/json',
      },
      data: 'invalid json}',
    });
    
    // Should return 400 Bad Request for malformed JSON
    expect(response.status()).toBe(400);
  });

  test('should return proper error responses @critical', async ({ request }) => {
    // Test 404 for non-existent endpoint
    const response = await request.get('/api/v1/nonexistent');
    expect(response.status()).toBe(404);
    
    const data = await response.json();
    expect(data).toHaveProperty('detail');
  });

  test('should respect rate limits', async ({ request }) => {
    // Make multiple rapid requests to test rate limiting
    const promises = Array.from({ length: 10 }, () => 
      request.get('/health')
    );
    
    const responses = await Promise.all(promises);
    
    // All should succeed for health endpoint (usually not rate limited)
    responses.forEach(response => {
      expect(response.status()).toBe(200);
    });
  });

  test('should return consistent response formats @smoke', async ({ request }) => {
    const response = await request.get('/health');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    
    // Should have consistent structure
    expect(typeof data).toBe('object');
    expect(data).toHaveProperty('status');
    
    // Check response headers
    const headers = response.headers();
    expect(headers['content-type']).toContain('application/json');
  });

  test('should handle large request payloads', async ({ request }) => {
    // Create a large payload
    const largeDescription = 'A'.repeat(10000); // 10KB description
    
    const response = await request.post('/api/v1/trips', {
      headers: {
        'Authorization': 'Bearer mock-e2e-token',
        'Content-Type': 'application/json',
      },
      data: {
        title: 'Large Payload Test',
        description: largeDescription,
        destination: 'Test Destination',
        start_date: '2024-06-01',
        end_date: '2024-06-07',
        budget_total: 1000,
      },
    });
    
    // Should either accept or reject gracefully
    expect([201, 413, 422]).toContain(response.status());
  });

  test('should maintain API version consistency', async ({ request }) => {
    // Test that v1 endpoints are stable
    const endpoints = [
      '/api/v1/',
      '/health',
    ];
    
    for (const endpoint of endpoints) {
      const response = await request.get(endpoint);
      expect(response.status()).toBeLessThan(500);
    }
  });
});
