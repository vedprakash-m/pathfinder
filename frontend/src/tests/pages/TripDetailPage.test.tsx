import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TripDetailPage } from '../../pages/TripDetailPage';
import { TestWrapper } from '../utils';

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  useParams: () => ({ id: 'test-trip-1' }),
  useNavigate: () => vi.fn(),
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

// Mock the API services
vi.mock('../../services/tripService', () => ({
  tripService: {
    getTrip: vi.fn(),
    updateTrip: vi.fn(),
    deleteTrip: vi.fn(),
  },
}));

vi.mock('../../services/familyService', () => ({
  familyService: {
    getFamilies: vi.fn(),
  },
}));

// Mock Auth0
vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    user: {
      email: 'test@example.com',
      name: 'Test User',
      sub: 'auth0|test123',
    },
    isAuthenticated: true,
    isLoading: false,
  }),
}));

const mockTrip = {
  id: 'test-trip-1',
  title: 'Amazing Europe Adventure',
  description: 'A comprehensive journey through Europe',
  destination: 'Paris, Rome, Barcelona',
  startDate: '2025-08-15',
  endDate: '2025-08-30',
  status: 'planning' as const,
  budgetTotal: 12000,
  maxParticipants: 15,
  currentParticipants: 8,
  isPublic: false,
  createdBy: 'auth0|test123',
  families: [
    { id: 'fam1', name: 'Smith Family' },
    { id: 'fam2', name: 'Johnson Family' },
    { id: 'fam3', name: 'Williams Family' },
  ],
  itinerary: [
    {
      day: 1,
      date: '2025-08-15',
      location: 'Paris',
      activities: [
        { time: '09:00', activity: 'Eiffel Tower Visit', duration: 3 },
        { time: '14:00', activity: 'Louvre Museum', duration: 4 },
      ],
    },
    {
      day: 2,
      date: '2025-08-16',
      location: 'Paris',
      activities: [
        { time: '10:00', activity: 'Notre Dame Cathedral', duration: 2 },
        { time: '15:00', activity: 'Seine River Cruise', duration: 2 },
      ],
    },
  ],
  budget: {
    accommodation: 4000,
    transportation: 3000,
    food: 3000,
    activities: 2000,
  },
  participants: [
    { familyId: 'fam1', confirmed: true, joinedAt: '2025-06-01' },
    { familyId: 'fam2', confirmed: true, joinedAt: '2025-06-02' },
    { familyId: 'fam3', confirmed: false, joinedAt: '2025-06-05' },
  ],
};

describe('TripDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders trip details correctly', async () => {
    const { tripService } = await import('../../services/tripService');
    (tripService.getTrip as any).mockResolvedValue({ data: mockTrip });

    render(
      <TestWrapper>
        <TripDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Amazing Europe Adventure')).toBeInTheDocument();
      expect(screen.getByText('Paris, Rome, Barcelona')).toBeInTheDocument();
      expect(screen.getByText('$12,000')).toBeInTheDocument();
    });
  });

  it('displays trip itinerary', async () => {
    const { tripService } = await import('../../services/tripService');
    (tripService.getTrip as any).mockResolvedValue({ data: mockTrip });

    render(
      <TestWrapper>
        <TripDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Eiffel Tower Visit')).toBeInTheDocument();
      expect(screen.getByText('Louvre Museum')).toBeInTheDocument();
      expect(screen.getByText('Seine River Cruise')).toBeInTheDocument();
    });
  });

  it('shows participating families', async () => {
    const { tripService } = await import('../../services/tripService');
    (tripService.getTrip as any).mockResolvedValue({ data: mockTrip });

    render(
      <TestWrapper>
        <TripDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Smith Family')).toBeInTheDocument();
      expect(screen.getByText('Johnson Family')).toBeInTheDocument();
      expect(screen.getByText('Williams Family')).toBeInTheDocument();
    });
  });

  it('displays budget breakdown', async () => {
    const { tripService } = await import('../../services/tripService');
    (tripService.getTrip as any).mockResolvedValue({ data: mockTrip });

    render(
      <TestWrapper>
        <TripDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/accommodation.*4,000/i)).toBeInTheDocument();
      expect(screen.getByText(/transportation.*3,000/i)).toBeInTheDocument();
      expect(screen.getByText(/food.*3,000/i)).toBeInTheDocument();
      expect(screen.getByText(/activities.*2,000/i)).toBeInTheDocument();
    });
  });

  it('allows trip owner to edit trip', async () => {
    const user = userEvent.setup();
    const { tripService } = await import('../../services/tripService');
    (tripService.getTrip as any).mockResolvedValue({ data: mockTrip });

    render(
      <TestWrapper>
        <TripDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      const editButton = screen.getByRole('button', { name: /edit trip/i });
      expect(editButton).toBeInTheDocument();
    });
  });

  it('shows trip status correctly', async () => {
    const { tripService } = await import('../../services/tripService');
    (tripService.getTrip as any).mockResolvedValue({ data: mockTrip });

    render(
      <TestWrapper>
        <TripDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Planning')).toBeInTheDocument();
    });
  });

  it('displays participant count and capacity', async () => {
    const { tripService } = await import('../../services/tripService');
    (tripService.getTrip as any).mockResolvedValue({ data: mockTrip });

    render(
      <TestWrapper>
        <TripDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('8/15 participants')).toBeInTheDocument();
    });
  });

  it('handles trip not found error', async () => {
    const { tripService } = await import('../../services/tripService');
    (tripService.getTrip as any).mockRejectedValue({
      response: { status: 404 },
      message: 'Trip not found',
    });

    render(
      <TestWrapper>
        <TripDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/trip not found/i)).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    const { tripService } = await import('../../services/tripService');
    // Don't resolve the promise to test loading state
    (tripService.getTrip as any).mockImplementation(() => new Promise(() => {}));

    render(
      <TestWrapper>
        <TripDetailPage />
      </TestWrapper>
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('allows updating trip when user is owner', async () => {
    const user = userEvent.setup();
    const { tripService } = await import('../../services/tripService');
    (tripService.getTrip as any).mockResolvedValue({ data: mockTrip });
    (tripService.updateTrip as any).mockResolvedValue({ data: { ...mockTrip, title: 'Updated Trip' } });

    render(
      <TestWrapper>
        <TripDetailPage />
      </TestWrapper>
    );

    await waitFor(() => {
      const editButton = screen.getByRole('button', { name: /edit trip/i });
      expect(editButton).toBeInTheDocument();
    });

    const editButton = screen.getByRole('button', { name: /edit trip/i });
    await user.click(editButton);

    // Fill edit form
    const titleInput = screen.getByDisplayValue('Amazing Europe Adventure');
    await user.clear(titleInput);
    await user.type(titleInput, 'Updated Trip');

    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(tripService.updateTrip).toHaveBeenCalledWith('test-trip-1', {
        title: 'Updated Trip',
      });
    });
  });
});
