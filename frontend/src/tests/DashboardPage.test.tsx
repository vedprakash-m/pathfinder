import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from './utils';
import { DashboardPage } from '../pages/DashboardPage';

// Mock the tripService
vi.mock('../services/tripService', () => ({
  tripService: {
    getUserTrips: vi.fn(() => Promise.resolve({ data: { items: [] } })),
  },
}));

describe('DashboardPage', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard with welcome message', async () => {
    render(<DashboardPage />);
    
    await waitFor(() => {
      // Check for welcome message
      expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
    });
  });

  it('displays empty state when no trips exist', async () => {
    render(<DashboardPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/no family trips yet/i)).toBeInTheDocument();
    });
  });

  it('shows action buttons section', async () => {
    render(<DashboardPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/view all trips/i)).toBeInTheDocument();
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });
  });

  it('shows welcome message and user info', () => {
    render(<DashboardPage />);
    
    // Should show welcome message and basic user info
    expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
    expect(screen.getByText(/family member/i)).toBeInTheDocument();
  });
});
