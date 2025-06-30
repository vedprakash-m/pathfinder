import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CreateTripPage } from '../pages/CreateTripPage';

// Mock the trip service
vi.mock('../services/tripService', () => ({
  tripService: {
    createTrip: vi.fn()
  }
}));

// Mock React Router
vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn(() => vi.fn())
}));

describe('CreateTripPage', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    });
    vi.clearAllMocks();
  });

  const renderWithProvider = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  it('renders the create trip form', () => {
    renderWithProvider(<CreateTripPage />);
    
    expect(screen.getByText(/create trip/i)).toBeInTheDocument();
  });

  it('handles form submission', async () => {
    const { tripService } = await import('../services/tripService');
    (tripService.createTrip as any).mockResolvedValue({ id: 1, name: 'Test Trip' });

    renderWithProvider(<CreateTripPage />);
    
    // This is a basic test - adjust based on actual form fields
    const submitButton = screen.getByRole('button', { name: /create/i });
    if (submitButton) {
      fireEvent.click(submitButton);
    }
  });
});
