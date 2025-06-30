import { vi } from 'vitest';

// Mock users for consistent test data
const mockUsers = [
  {
    id: 'test-user-id',
    email: 'test@example.com',
    name: 'Test User',
    role: 'family_admin',
    familyId: 'test-family-id'
  }
];

// Mock trips for consistent test data
const mockTrips = [
  {
    id: 'trip-1',
    name: 'Summer Vacation',
    destination: 'Orlando, FL',
    startDate: '2024-07-15',
    endDate: '2024-07-22',
    status: 'planning',
    creatorId: 'test-user-id'
  },
  {
    id: 'trip-2', 
    name: 'Winter Getaway',
    destination: 'Aspen, CO',
    startDate: '2024-12-20',
    endDate: '2024-12-27',
    status: 'confirmed',
    creatorId: 'test-user-id'
  }
];

// Enhanced mock implementation with realistic responses
export const apiService = {
  get: vi.fn().mockImplementation((url: string) => {
    // Return appropriate mock data based on URL
    if (url.includes('/auth/me')) {
      return Promise.resolve({ 
        data: mockUsers[0], 
        status: 'success' 
      });
    }
    if (url.includes('/trips')) {
      return Promise.resolve({ 
        data: mockTrips, 
        status: 'success' 
      });
    }
    if (url.includes('/families')) {
      return Promise.resolve({ 
        data: [{ 
          id: 'test-family-id', 
          name: 'Test Family',
          adminId: 'test-user-id'
        }], 
        status: 'success' 
      });
    }
    // Default response
    return Promise.resolve({ data: [], status: 'success' });
  }),
  post: vi.fn().mockResolvedValue({ data: {}, status: 'success' }),
  put: vi.fn().mockResolvedValue({ data: {}, status: 'success' }),
  patch: vi.fn().mockResolvedValue({ data: {}, status: 'success' }),
  delete: vi.fn().mockResolvedValue({ data: {}, status: 'success' }),
  clearCache: vi.fn(),
  invalidateCache: vi.fn(),
};

export const uploadFile = vi.fn().mockResolvedValue({ data: {}, status: 'success' });

// Token setter for auth integration
export const setTokenGetter = vi.fn();

export default apiService;
