import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from './utils';
import { CreateTripPage } from '../pages/CreateTripPage';

// Mock the API calls
vi.mock('../services/api', () => ({
  tripsApi: {
    createTrip: vi.fn(() => Promise.resolve({ id: 'trip-123', title: 'Test Trip' })),
  },
  familiesApi: {
    getUserFamilies: vi.fn(() => Promise.resolve([
      { id: 'family-1', name: 'Test Family', members: [] }
    ])),
  },
}));

// Mock React Router
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

// Mock Auth0
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

describe('CreateTripPage', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders create trip form with all required fields', async () => {
    render(<CreateTripPage />);
    
    // Check for form title
    expect(screen.getByText(/create new trip/i)).toBeInTheDocument();
    
    // Check for required form fields
    expect(screen.getByLabelText(/trip title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/destination/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/end date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/budget/i)).toBeInTheDocument();
    
    // Check for submit button
    expect(screen.getByRole('button', { name: /create trip/i })).toBeInTheDocument();
  });

  it('validates required fields before submission', async () => {
    render(<CreateTripPage />);
    
    const submitButton = screen.getByRole('button', { name: /create trip/i });
    await user.click(submitButton);
    
    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/title is required/i) || screen.getByText(/required/i)).toBeInTheDocument();
    });
  });

  it('validates date range (end date after start date)', async () => {
    render(<CreateTripPage />);
    
    const startDateInput = screen.getByLabelText(/start date/i);
    const endDateInput = screen.getByLabelText(/end date/i);
    
    // Set end date before start date
    await user.type(startDateInput, '2025-12-31');
    await user.type(endDateInput, '2025-12-01');
    
    const submitButton = screen.getByRole('button', { name: /create trip/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/end date must be after start date/i) || screen.getByText(/invalid date range/i)).toBeInTheDocument();
    });
  });

  it('validates budget input (positive number)', async () => {
    render(<CreateTripPage />);
    
    const budgetInput = screen.getByLabelText(/budget/i);
    await user.type(budgetInput, '-100');
    
    const submitButton = screen.getByRole('button', { name: /create trip/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/budget must be positive/i) || screen.getByText(/invalid budget/i)).toBeInTheDocument();
    });
  });

  it('successfully creates trip with valid data', async () => {
    const { tripsApi } = await import('../services/api');
    const mockNavigate = vi.fn();
    
    render(<CreateTripPage />);
    
    // Fill out the form
    await user.type(screen.getByLabelText(/trip title/i), 'Amazing Family Vacation');
    await user.type(screen.getByLabelText(/destination/i), 'Paris, France');
    await user.type(screen.getByLabelText(/start date/i), '2025-08-01');
    await user.type(screen.getByLabelText(/end date/i), '2025-08-07');
    await user.type(screen.getByLabelText(/budget/i), '5000');
    
    // Submit the form
    const submitButton = screen.getByRole('button', { name: /create trip/i });
    await user.click(submitButton);
    
    // Verify API was called
    await waitFor(() => {
      expect(tripsApi.createTrip).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Amazing Family Vacation',
          destination: 'Paris, France',
          budget_total: 5000,
        })
      );
    });
  });

  it('shows loading state during trip creation', async () => {
    render(<CreateTripPage />);
    
    // Fill out and submit form
    await user.type(screen.getByLabelText(/trip title/i), 'Test Trip');
    await user.type(screen.getByLabelText(/destination/i), 'Test Destination');
    await user.type(screen.getByLabelText(/start date/i), '2025-08-01');
    await user.type(screen.getByLabelText(/end date/i), '2025-08-07');
    await user.type(screen.getByLabelText(/budget/i), '1000');
    
    const submitButton = screen.getByRole('button', { name: /create trip/i });
    await user.click(submitButton);
    
    // Check for loading state
    expect(screen.getByText(/creating/i) || screen.getByRole('button', { name: /creating/i })).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    const { tripsApi } = await import('../services/api');
    vi.mocked(tripsApi.createTrip).mockRejectedValue(new Error('Server Error'));
    
    render(<CreateTripPage />);
    
    // Fill out and submit form
    await user.type(screen.getByLabelText(/trip title/i), 'Test Trip');
    await user.type(screen.getByLabelText(/destination/i), 'Test Destination');
    await user.type(screen.getByLabelText(/start date/i), '2025-08-01');
    await user.type(screen.getByLabelText(/end date/i), '2025-08-07');
    await user.type(screen.getByLabelText(/budget/i), '1000');
    
    const submitButton = screen.getByRole('button', { name: /create trip/i });
    await user.click(submitButton);
    
    // Check for error message
    await waitFor(() => {
      expect(screen.getByText(/error creating trip/i) || screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });
  });

  it('displays family selection when user has multiple families', async () => {
    const { familiesApi } = await import('../services/api');
    vi.mocked(familiesApi.getUserFamilies).mockResolvedValue([
      { id: 'family-1', name: 'Family One', members: [] },
      { id: 'family-2', name: 'Family Two', members: [] },
    ]);
    
    render(<CreateTripPage />);
    
    await waitFor(() => {
      expect(screen.getByLabelText(/select family/i) || screen.getByText(/family/i)).toBeInTheDocument();
    });
  });

  it('shows trip privacy options', async () => {
    render(<CreateTripPage />);
    
    // Look for privacy/visibility options
    expect(
      screen.getByLabelText(/private/i) || 
      screen.getByLabelText(/public/i) || 
      screen.getByText(/visibility/i)
    ).toBeInTheDocument();
  });

  it('provides helpful field descriptions and examples', async () => {
    render(<CreateTripPage />);
    
    // Check for helpful text/placeholders
    expect(screen.getByPlaceholderText(/paris, tokyo/i) || screen.getByText(/example/i)).toBeInTheDocument();
  });
});
