import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { DashboardPage } from '../../pages/DashboardPage';
import { AllProviders } from '../utils';

// Mock the trip service
vi.mock('../../services/tripService', () => ({
  tripService: {
    getUserTrips: vi.fn(),
  },
}));

// Mock the API service
vi.mock('../../services/api', () => ({
  apiService: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock MSAL for Entra ID authentication
vi.mock('@azure/msal-react', () => ({
  useMsal: () => ({
    instance: {
      getActiveAccount: () => ({
        localAccountId: 'test-user-id',
        username: 'test@vedprakash.net',
        name: 'Test User',
      }),
      acquireTokenSilent: vi.fn(() => Promise.resolve({ accessToken: 'mock-entra-token' })),
    },
    accounts: [{
      localAccountId: 'test-user-id',
      username: 'test@vedprakash.net',
      name: 'Test User',
    }],
  }),
  useAccount: vi.fn(() => ({
    homeAccountId: 'test-user-id',
    environment: 'test-environment',
    tenantId: 'vedid.onmicrosoft.com',
    username: 'test@vedprakash.net',
    localAccountId: 'test-user-id',
    name: 'Test User',
  })),
  useIsAuthenticated: vi.fn(() => true),
  MsalProvider: ({ children }: { children: React.ReactNode }) => children,
}));

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the dashboard with user greeting', async () => {
    // Mock API responses
    const { tripService } = await import('../../services/tripService');
    (tripService.getUserTrips as any).mockResolvedValue({
      data: {
        items: [
          { id: '1', title: 'Trip 1', status: 'planning', start_date: '2025-07-01' },
          { id: '2', title: 'Trip 2', status: 'active', start_date: '2025-08-01' },
        ],
        total: 2,
        page: 1,
        pageSize: 10,
      },
    });

    render(
      <AllProviders>
        <DashboardPage />
      </AllProviders>
    );

    // Wait for loading to finish and content to appear
    await waitFor(() => {
      expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('displays trip statistics when available', async () => {
    const { tripService } = await import('../../services/tripService');
    (tripService.getUserTrips as any).mockResolvedValue({
      data: {
        items: [
          { id: '1', title: 'Trip 1', status: 'planning', start_date: '2025-07-01' },
          { id: '2', title: 'Trip 2', status: 'confirmed', start_date: '2025-08-01' },
        ],
        total: 2,
        page: 1,
        pageSize: 10,
      },
    });

    render(
      <AllProviders>
        <DashboardPage />
      </AllProviders>
    );

    await waitFor(() => {
      // Look for trip counts in the dashboard
      expect(screen.getByText(/2/)).toBeInTheDocument(); // Total trips
    }, { timeout: 3000 });
  });

  it('shows empty state when no trips exist', async () => {
    const { tripService } = await import('../../services/tripService');
    (tripService.getUserTrips as any).mockResolvedValue({
      data: {
        items: [],
        total: 0,
        page: 1,
        pageSize: 10,
      },
    });

    render(
      <AllProviders>
        <DashboardPage />
      </AllProviders>
    );

    await waitFor(() => {
      // Look for empty state or create trip message
      expect(screen.getByText(/create.*trip|no trips|get started/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('displays create trip call-to-action for new users', async () => {
    const { tripService } = await import('../../services/tripService');
    (tripService.getUserTrips as any).mockResolvedValue({
      data: {
        items: [],
        total: 0,
        page: 1,
        pageSize: 10,
      },
    });

    render(
      <AllProviders>
        <DashboardPage />
      </AllProviders>
    );

    await waitFor(() => {
      // Look for any button or link that mentions trip creation
      const createElements = screen.getAllByText(/create|new trip|add trip/i);
      expect(createElements.length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  });

  it('handles API errors gracefully', async () => {
    const { tripService } = await import('../../services/tripService');
    (tripService.getUserTrips as any).mockRejectedValue(new Error('API Error'));

    render(
      <AllProviders>
        <DashboardPage />
      </AllProviders>
    );

    // Should render error state or still show basic page structure
    await waitFor(() => {
      expect(screen.getByText(/error|try again|something went wrong/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
