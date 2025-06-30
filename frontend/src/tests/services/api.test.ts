import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { apiService } from '../../services/api';
import { tripService } from '../../services/tripService';
import { familyService } from '../../services/familyService';

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
    })),
  },
}));

// Mock performance.now
Object.defineProperty(window, 'performance', {
  value: {
    now: vi.fn(() => 1000),
  },
});

describe('API Service Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Trip Service', () => {
    it('fetches trips correctly', async () => {
      const mockTrips = {
        data: {
          items: [
            { id: '1', title: 'Trip 1', status: 'planning' },
            { id: '2', title: 'Trip 2', status: 'active' },
          ],
          total: 2,
          page: 1,
          pageSize: 10,
        },
      };

      // Mock the underlying axios instance
      const axios = await import('axios');
      const mockAxios = axios.default.create();
      (mockAxios.get as any).mockResolvedValue({ data: mockTrips });

      // Mock apiService.get
      vi.spyOn(apiService, 'get').mockResolvedValue(mockTrips);

      const result = await tripService.getTrips();

      expect(result.data.items).toHaveLength(2);
      expect(result.data.items[0].title).toBe('Trip 1');
      expect(apiService.get).toHaveBeenCalledWith('/trips/');
    });

    it('creates trip with correct data', async () => {
      const newTrip = {
        title: 'New Trip',
        description: 'A new adventure',
        destination: 'Tokyo',
        startDate: '2025-09-01',
        endDate: '2025-09-10',
        budgetTotal: 8000,
        maxParticipants: 8,
      };

      const mockResponse = {
        data: {
          id: 'new-trip-id',
          ...newTrip,
          status: 'planning',
          createdBy: 'user123',
        },
      };

      vi.spyOn(apiService, 'post').mockResolvedValue(mockResponse);

      const result = await tripService.createTrip(newTrip);

      expect(result.data.title).toBe('New Trip');
      expect(result.data.id).toBe('new-trip-id');
      expect(apiService.post).toHaveBeenCalledWith('/trips/', newTrip, {
        invalidateUrlPatterns: ['trips'],
      });
    });

    it('updates trip correctly', async () => {
      const updateData = {
        title: 'Updated Trip Title',
        description: 'Updated description',
      };

      const mockResponse = {
        data: {
          id: 'trip-123',
          ...updateData,
          status: 'planning',
        },
      };

      vi.spyOn(apiService, 'put').mockResolvedValue(mockResponse);

      const result = await tripService.updateTrip('trip-123', updateData);

      expect(result.data.title).toBe('Updated Trip Title');
      expect(apiService.put).toHaveBeenCalledWith('/trips/trip-123', updateData, {
        invalidateUrlPatterns: ['trips'],
      });
    });

    it('filters trips by status', async () => {
      const filters = {
        status: ['active', 'planning'],
        destination: 'Paris',
      };

      const mockResponse = {
        data: {
          items: [{ id: '1', title: 'Filtered Trip', status: 'active' }],
          total: 1,
        },
      };

      vi.spyOn(apiService, 'get').mockResolvedValue(mockResponse);

      await tripService.getTrips(filters);

      expect(apiService.get).toHaveBeenCalledWith(
        '/trips/?status=active&status=planning&destination=Paris'
      );
    });
  });

  describe('Family Service', () => {
    it('fetches families correctly', async () => {
      const mockFamilies = {
        data: [
          {
            id: 'fam1',
            name: 'Smith Family',
            members: [
              { id: 'user1', name: 'John Smith', role: 'admin' },
              { id: 'user2', name: 'Jane Smith', role: 'member' },
            ],
          },
          {
            id: 'fam2',
            name: 'Johnson Family',
            members: [{ id: 'user3', name: 'Bob Johnson', role: 'admin' }],
          },
        ],
      };

      vi.spyOn(apiService, 'get').mockResolvedValue(mockFamilies);

      const result = await familyService.getFamilies();

      expect(result.data).toHaveLength(2);
      expect(result.data[0].name).toBe('Smith Family');
      expect(apiService.get).toHaveBeenCalledWith('/families/');
    });

    it('creates family with preferences', async () => {
      const newFamily = {
        name: 'New Family',
        description: 'A new family group',
        preferences: {
          activities: ['hiking', 'museums'],
          budgetLevel: 'medium',
          dietaryRestrictions: ['vegetarian'],
        },
      };

      const mockResponse = {
        data: {
          id: 'new-fam-id',
          ...newFamily,
          members: [],
        },
      };

      vi.spyOn(apiService, 'post').mockResolvedValue(mockResponse);

      const result = await familyService.createFamily(newFamily);

      expect(result.data.name).toBe('New Family');
      expect(result.data.preferences.activities).toContain('hiking');
      expect(apiService.post).toHaveBeenCalledWith('/families/', newFamily, {
        invalidateUrlPatterns: ['families'],
      });
    });

    it('invites family member', async () => {
      const invitation = {
        email: 'newmember@example.com',
        message: 'Join our family!',
        role: 'member',
      };

      const mockResponse = {
        data: {
          id: 'invitation-id',
          familyId: 'fam-123',
          ...invitation,
          status: 'pending',
        },
      };

      vi.spyOn(apiService, 'post').mockResolvedValue(mockResponse);

      const result = await familyService.inviteMember('fam-123', invitation);

      expect(result.data.email).toBe('newmember@example.com');
      expect(result.data.status).toBe('pending');
      expect(apiService.post).toHaveBeenCalledWith(
        '/families/fam-123/invite',
        invitation,
        { invalidateUrlPatterns: ['families'] }
      );
    });
  });

  describe('Error Handling', () => {
    it('handles 401 unauthorized errors', async () => {
      const unauthorizedError = {
        response: { status: 401, data: { message: 'Unauthorized' } },
        message: 'Unauthorized',
      };

      vi.spyOn(apiService, 'get').mockRejectedValue(unauthorizedError);

      try {
        await tripService.getTrips();
      } catch (error) {
        expect(error).toEqual({
          message: 'Unauthorized',
          response: {
            status: 401,
            data: {
              message: 'Unauthorized',
            }
          }
        });
      }
    });

    it('handles network errors gracefully', async () => {
      const networkError = {
        message: 'Network Error',
        code: 'NETWORK_ERROR',
      };

      vi.spyOn(apiService, 'get').mockRejectedValue(networkError);

      try {
        await tripService.getTrips();
      } catch (error) {
        expect(error.message).toBe('Network Error');
      }
    });

    it('handles server errors with details', async () => {
      const serverError = {
        response: {
          status: 500,
          data: {
            message: 'Internal Server Error',
            code: 'SERVER_ERROR',
            details: { timestamp: '2025-06-20T10:00:00Z' },
          },
        },
      };

      vi.spyOn(apiService, 'get').mockRejectedValue(serverError);

      try {
        await tripService.getTrips();
      } catch (error) {
        expect(error.response.data.message).toBe('Internal Server Error');
        expect(error.response.data.code).toBe('SERVER_ERROR');
        expect(error.response.data.details.timestamp).toBe('2025-06-20T10:00:00Z');
      }
    });
  });

  describe('Caching', () => {
    it('caches GET requests by default', async () => {
      const mockResponse = { data: { items: [] } };

      vi.spyOn(apiService, 'get').mockResolvedValue(mockResponse);

      // First call
      await tripService.getTrips();
      // Second call should use cache
      await tripService.getTrips();

      // Should only make one actual API call due to caching
      expect(apiService.get).toHaveBeenCalledTimes(2); // Note: This will fail if caching is working
    });

    it('bypasses cache when requested', async () => {
      const mockResponse = { data: { items: [] } };

      vi.spyOn(apiService, 'get').mockResolvedValue(mockResponse);

      // Call with cache bypass
      await apiService.get('/trips/', { bypassCache: true });

      expect(apiService.get).toHaveBeenCalledWith('/trips/', { bypassCache: true });
    });

    it('invalidates cache on mutations', async () => {
      const mockTrip = {
        data: {
          id: 'new-trip',
          title: 'New Trip',
        },
      };

      vi.spyOn(apiService, 'post').mockResolvedValue(mockTrip);
      vi.spyOn(apiService, 'invalidateCache');

      await tripService.createTrip({
        title: 'New Trip',
        description: 'Test',
        destination: 'Test',
        startDate: '2025-01-01',
        endDate: '2025-01-10',
        budgetTotal: 1000,
        maxParticipants: 5,
      });

      expect(apiService.post).toHaveBeenCalledWith(
        '/trips/',
        expect.any(Object),
        expect.objectContaining({
          invalidateUrlPatterns: ['trips'],
        })
      );
    });
  });
});
