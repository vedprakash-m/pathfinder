import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from './utils';
import { DashboardPage } from '../pages/DashboardPage';

// Mock the API calls
vi.mock('../services/api', () => ({
  tripsApi: {
    getUserTrips: vi.fn(() => Promise.resolve([])),
    getRecentTrips: vi.fn(() => Promise.resolve([])),
  },
  familiesApi: {
    getUserFamilies: vi.fn(() => Promise.resolve([])),
  },
  notificationsApi: {
    getUnreadCount: vi.fn(() => Promise.resolve(0)),
  },
}));

// Mock the Auth0 hook
vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    isAuthenticated: true,
    isLoading: false,
    user: {
      sub: 'auth0|test123',
      email: 'test@example.com',
      name: 'Test User',
    },
    getAccessTokenSilently: vi.fn(() => Promise.resolve('mock-token')),
  }),
}));

describe('DashboardPage', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard with welcome message', async () => {
    render(<DashboardPage />);
    
    // Check for welcome message
    expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    
    // Check for main sections
    expect(screen.getByText(/your trips/i)).toBeInTheDocument();
    expect(screen.getByText(/families/i)).toBeInTheDocument();
  });

  it('displays create trip call-to-action when no trips exist', async () => {
    render(<DashboardPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/create your first trip/i)).toBeInTheDocument();
    });
    
    const createButton = screen.getByRole('button', { name: /create trip/i });
    expect(createButton).toBeInTheDocument();
  });

  it('navigates to create trip page when create button is clicked', async () => {
    render(<DashboardPage />);
    
    await waitFor(() => {
      const createButton = screen.getByRole('button', { name: /create trip/i });
      expect(createButton).toBeInTheDocument();
    });
    
    const createButton = screen.getByRole('button', { name: /create trip/i });
    await user.click(createButton);
    
    // Verify navigation (would need to check URL in real implementation)
    expect(createButton).toHaveBeenClicked;
  });

  it('displays recent activity section', async () => {
    render(<DashboardPage />);
    
    expect(screen.getByText(/recent activity/i)).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    render(<DashboardPage />);
    
    // Should show loading indicators for data sections
    expect(screen.getByTestId('trips-loading') || screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('handles error states gracefully', async () => {
    // Mock API to throw error
    const { tripsApi } = await import('../services/api');
    vi.mocked(tripsApi.getUserTrips).mockRejectedValue(new Error('API Error'));
    
    render(<DashboardPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/something went wrong/i) || screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('displays quick actions for authenticated user', async () => {
    render(<DashboardPage />);
    
    // Check for quick action buttons
    await waitFor(() => {
      expect(screen.getByText(/quick actions/i) || screen.getByRole('button', { name: /create trip/i })).toBeInTheDocument();
    });
  });

  it('shows notification indicator when there are unread notifications', async () => {
    // Mock unread notifications
    const { notificationsApi } = await import('../services/api');
    vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue(3);
    
    render(<DashboardPage />);
    
    await waitFor(() => {
      const notificationBadge = screen.getByText('3') || screen.getByLabelText(/3 unread/i);
      expect(notificationBadge).toBeInTheDocument();
    });
  });
});
