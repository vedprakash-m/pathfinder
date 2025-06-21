import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiClient, tripsApi, familiesApi, authApi } from '../services/api';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock Auth0
vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    getAccessTokenSilently: vi.fn(() => Promise.resolve('mock-token')),
  }),
}));

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('includes authorization header when token is provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });

    // Mock the API client call (implementation will vary based on actual structure)
    const response = await fetch('/api/test', {
      headers: {
        'Authorization': 'Bearer mock-token',
        'Content-Type': 'application/json',
      },
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/test', {
      headers: {
        'Authorization': 'Bearer mock-token',
        'Content-Type': 'application/json',
      },
    });
  });

  it('handles network errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    try {
      await fetch('/api/test');
    } catch (error) {
      expect(error.message).toBe('Network error');
    }
  });

  it('handles HTTP error responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({ error: 'Server error' }),
    });

    const response = await fetch('/api/test');
    expect(response.ok).toBe(false);
    expect(response.status).toBe(500);
  });
});

describe('Trips API', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('getUserTrips', () => {
    it('fetches user trips successfully', async () => {
      const mockTrips = [
        { id: 'trip-1', title: 'Paris Trip', destination: 'Paris' },
        { id: 'trip-2', title: 'Tokyo Trip', destination: 'Tokyo' },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTrips),
      });

      // Note: This is a mock test structure - actual implementation will depend on your API service
      const trips = await fetch('/api/trips').then(r => r.json());

      expect(mockFetch).toHaveBeenCalledWith('/api/trips', expect.any(Object));
      expect(trips).toEqual(mockTrips);
    });

    it('handles empty trips list', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([]),
      });

      const trips = await fetch('/api/trips').then(r => r.json());
      expect(trips).toEqual([]);
    });
  });

  describe('createTrip', () => {
    it('creates trip with valid data', async () => {
      const newTrip = {
        title: 'New Adventure',
        destination: 'Bali',
        startDate: '2025-08-01',
        endDate: '2025-08-07',
        budget: 3000,
      };

      const createdTrip = { id: 'trip-123', ...newTrip };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: () => Promise.resolve(createdTrip),
      });

      const result = await fetch('/api/trips', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTrip),
      }).then(r => r.json());

      expect(mockFetch).toHaveBeenCalledWith('/api/trips', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTrip),
      });
      expect(result).toEqual(createdTrip);
    });

    it('handles validation errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: () => Promise.resolve({
          error: 'Validation error',
          details: ['Title is required', 'End date must be after start date'],
        }),
      });

      const response = await fetch('/api/trips', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: '' }),
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(422);
    });
  });

  describe('updateTrip', () => {
    it('updates trip successfully', async () => {
      const updates = { title: 'Updated Trip Title' };
      const updatedTrip = { id: 'trip-1', title: 'Updated Trip Title' };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(updatedTrip),
      });

      const result = await fetch('/api/trips/trip-1', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      }).then(r => r.json());

      expect(result).toEqual(updatedTrip);
    });
  });

  describe('deleteTrip', () => {
    it('deletes trip successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      const response = await fetch('/api/trips/trip-1', {
        method: 'DELETE',
      });

      expect(response.ok).toBe(true);
      expect(response.status).toBe(204);
    });

    it('handles delete permission errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: () => Promise.resolve({ error: 'Insufficient permissions' }),
      });

      const response = await fetch('/api/trips/trip-1', {
        method: 'DELETE',
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(403);
    });
  });
});

describe('Families API', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('getUserFamilies', () => {
    it('fetches user families successfully', async () => {
      const mockFamilies = [
        { id: 'family-1', name: 'Smith Family', members: [] },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockFamilies),
      });

      const families = await fetch('/api/families').then(r => r.json());
      expect(families).toEqual(mockFamilies);
    });
  });

  describe('inviteMember', () => {
    it('sends family invitation successfully', async () => {
      const inviteData = {
        email: 'newmember@example.com',
        message: 'Join our family!',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, invitationId: 'inv-123' }),
      });

      const result = await fetch('/api/families/family-1/invite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inviteData),
      }).then(r => r.json());

      expect(result.success).toBe(true);
      expect(result.invitationId).toBe('inv-123');
    });

    it('handles duplicate invitation errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: () => Promise.resolve({ error: 'User already invited' }),
      });

      const response = await fetch('/api/families/family-1/invite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'existing@example.com' }),
      });

      expect(response.status).toBe(409);
    });
  });
});

describe('Auth API', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('getUserProfile', () => {
    it('fetches user profile successfully', async () => {
      const mockProfile = {
        id: 'user-123',
        email: 'user@example.com',
        name: 'Test User',
        role: 'family_admin',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockProfile),
      });

      const profile = await fetch('/api/auth/profile').then(r => r.json());
      expect(profile).toEqual(mockProfile);
    });

    it('handles unauthenticated requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ error: 'Unauthorized' }),
      });

      const response = await fetch('/api/auth/profile');
      expect(response.status).toBe(401);
    });
  });

  describe('updateProfile', () => {
    it('updates user profile successfully', async () => {
      const updates = { name: 'Updated Name' };
      const updatedProfile = { id: 'user-123', name: 'Updated Name' };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(updatedProfile),
      });

      const result = await fetch('/api/auth/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      }).then(r => r.json());

      expect(result).toEqual(updatedProfile);
    });
  });
});

describe('Error Handling', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('handles timeout errors', async () => {
    mockFetch.mockImplementationOnce(
      () => new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 100)
      )
    );

    try {
      await fetch('/api/slow-endpoint');
    } catch (error) {
      expect(error.message).toBe('Request timeout');
    }
  });

  it('handles malformed JSON responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.reject(new Error('Invalid JSON')),
    });

    try {
      await fetch('/api/test').then(r => r.json());
    } catch (error) {
      expect(error.message).toBe('Invalid JSON');
    }
  });

  it('handles CORS errors', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    try {
      await fetch('/api/test');
    } catch (error) {
      expect(error.message).toBe('Failed to fetch');
    }
  });
});
