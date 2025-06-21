import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { DashboardPage } from '../../pages/DashboardPage';
import { TestWrapper } from '../utils';

// Mock the API service
vi.mock('../../services/api', () => ({
  api: {
    trips: {
      getAll: vi.fn(),
      getStats: vi.fn(),
    },
    families: {
      getAll: vi.fn(),
    },
    notifications: {
      getUnread: vi.fn(),
    },
  },
}));

// Mock Auth0
vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    user: {
      email: 'test@example.com',
      name: 'Test User',
    },
    isAuthenticated: true,
    isLoading: false,
  }),
}));

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the dashboard with user greeting', async () => {
    // Mock API responses
    const { api } = await import('../../services/api');
    (api.trips.getAll as any).mockResolvedValue([]);
    (api.trips.getStats as any).mockResolvedValue({
      totalTrips: 0,
      upcomingTrips: 0,
      activeTrips: 0,
    });
    (api.families.getAll as any).mockResolvedValue([]);
    (api.notifications.getUnread as any).mockResolvedValue([]);

    render(
      <TestWrapper>
        <DashboardPage />
      </TestWrapper>
    );

    // Check for dashboard elements
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
    
    // Wait for async content to load
    await waitFor(() => {
      expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    });
  });

  it('displays trip statistics when available', async () => {
    const { api } = await import('../../services/api');
    (api.trips.getAll as any).mockResolvedValue([
      { id: '1', title: 'Test Trip 1', status: 'planning' },
      { id: '2', title: 'Test Trip 2', status: 'active' },
    ]);
    (api.trips.getStats as any).mockResolvedValue({
      totalTrips: 2,
      upcomingTrips: 1,
      activeTrips: 1,
    });
    (api.families.getAll as any).mockResolvedValue([]);
    (api.notifications.getUnread as any).mockResolvedValue([]);

    render(
      <TestWrapper>
        <DashboardPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // Total trips
      expect(screen.getByText('1')).toBeInTheDocument(); // Active trips
    });
  });

  it('shows empty state when no trips exist', async () => {
    const { api } = await import('../../services/api');
    (api.trips.getAll as any).mockResolvedValue([]);
    (api.trips.getStats as any).mockResolvedValue({
      totalTrips: 0,
      upcomingTrips: 0,
      activeTrips: 0,
    });
    (api.families.getAll as any).mockResolvedValue([]);
    (api.notifications.getUnread as any).mockResolvedValue([]);

    render(
      <TestWrapper>
        <DashboardPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/no trips/i)).toBeInTheDocument();
    });
  });

  it('displays create trip call-to-action for new users', async () => {
    const { api } = await import('../../services/api');
    (api.trips.getAll as any).mockResolvedValue([]);
    (api.trips.getStats as any).mockResolvedValue({
      totalTrips: 0,
      upcomingTrips: 0,
      activeTrips: 0,
    });
    (api.families.getAll as any).mockResolvedValue([]);
    (api.notifications.getUnread as any).mockResolvedValue([]);

    render(
      <TestWrapper>
        <DashboardPage />
      </TestWrapper>
    );

    await waitFor(() => {
      const createButton = screen.getByRole('button', { name: /create.*trip/i });
      expect(createButton).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const { api } = await import('../../services/api');
    (api.trips.getAll as any).mockRejectedValue(new Error('API Error'));
    (api.trips.getStats as any).mockRejectedValue(new Error('API Error'));
    (api.families.getAll as any).mockResolvedValue([]);
    (api.notifications.getUnread as any).mockResolvedValue([]);

    render(
      <TestWrapper>
        <DashboardPage />
      </TestWrapper>
    );

    // Should still render the page without crashing
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
  });
});
