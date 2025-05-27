import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '../tests/utils';
import { TripDetailPage } from '../pages/TripDetailPage';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

// Mock the React Router hook
vi.mock('react-router-dom', () => ({
  useParams: vi.fn(),
  Link: ({ to, children, ...rest }: any) => (
    <a href={to} {...rest}>{children}</a>
  ),
  Navigate: ({ to }: any) => <div data-testid="mock-navigate" data-to={to} />
}));

// Mock the React Query hook
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn()
}));

describe('TripDetailPage', () => {
  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    
    // Default mocks
    (useParams as any).mockReturnValue({ tripId: '123' });
    (useQuery as any).mockReturnValue({
      data: {
        id: '123',
        name: 'Paris Adventure',
        description: 'A wonderful trip to Paris',
        destination: 'Paris, France',
        start_date: '2025-06-01',
        end_date: '2025-06-08',
        status: 'planning',
        budget_total: 5000,
        creator_id: 'user123',
        created_at: '2025-05-25T12:00:00Z',
        updated_at: '2025-05-25T12:00:00Z',
        is_public: false,
        participations: [
          {
            id: 'p1',
            family_id: 'f1',
            family_name: 'Smith Family',
            status: 'confirmed',
            members: 4
          }
        ]
      },
      isLoading: false,
      isError: false,
      error: null
    });
  });
  
  it('renders the trip details when data is loaded', async () => {
    // Arrange
    render(<TripDetailPage />);
    
    // Assert
    await waitFor(() => {
      expect(screen.getByText('Paris Adventure')).toBeInTheDocument();
      expect(screen.getByText('Paris, France', { exact: false })).toBeInTheDocument();
      expect(screen.getByText('Jun 1, 2025', { exact: false })).toBeInTheDocument();
    });
  });
  
  it('displays loading state while fetching data', async () => {
    // Arrange
    (useQuery as any).mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
      error: null
    });
    
    // Act
    render(<TripDetailPage />);
    
    // Assert
    expect(screen.queryByText('Paris Adventure')).not.toBeInTheDocument();
    expect(screen.getByText(/loading/i) || screen.getByRole('progressbar')).toBeInTheDocument();
  });
  
  it('shows error state when trip fetch fails', async () => {
    // Arrange
    (useQuery as any).mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: new Error('Failed to load trip')
    });
    
    // Act
    render(<TripDetailPage />);
    
    // Assert
    await waitFor(() => {
      expect(screen.getByText(/unable to load trip/i, { exact: false })).toBeInTheDocument();
    });
  });
  
  it('redirects to not found page when trip id is invalid', async () => {
    // Arrange
    (useParams as any).mockReturnValue({ tripId: undefined });
    
    // Act
    render(<TripDetailPage />);
    
    // Assert
    expect(screen.getByTestId('mock-navigate')).toHaveAttribute('data-to', '/not-found');
  });
});
