import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TripCard } from '../../components/trips/TripCard';
import { TestWrapper } from '../utils';

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

const mockTrip = {
  id: '1',
  title: 'Amazing Europe Trip',
  description: 'A wonderful journey through Europe',
  destination: 'Paris, France',
  startDate: '2025-08-15',
  endDate: '2025-08-25',
  status: 'planning' as const,
  budgetTotal: 5000,
  maxParticipants: 10,
  currentParticipants: 3,
  isPublic: false,
  createdBy: 'user1',
  families: [
    { id: 'fam1', name: 'Smith Family' },
    { id: 'fam2', name: 'Johnson Family' },
  ],
};

describe('TripCard', () => {
  it('renders trip information correctly', () => {
    render(
      <TestWrapper>
        <TripCard trip={mockTrip} />
      </TestWrapper>
    );

    expect(screen.getByText('Amazing Europe Trip')).toBeInTheDocument();
    expect(screen.getByText('Paris, France')).toBeInTheDocument();
    expect(screen.getByText(/Aug 15.*Aug 25/)).toBeInTheDocument();
    expect(screen.getByText('$5,000')).toBeInTheDocument();
    expect(screen.getByText('3/10 participants')).toBeInTheDocument();
  });

  it('displays correct status badge', () => {
    render(
      <TestWrapper>
        <TripCard trip={mockTrip} />
      </TestWrapper>
    );

    expect(screen.getByText('Planning')).toBeInTheDocument();
  });

  it('shows family participants', () => {
    render(
      <TestWrapper>
        <TripCard trip={mockTrip} />
      </TestWrapper>
    );

    expect(screen.getByText('Smith Family')).toBeInTheDocument();
    expect(screen.getByText('Johnson Family')).toBeInTheDocument();
  });

  it('handles different trip statuses', () => {
    const activeTrip = { ...mockTrip, status: 'active' as const };
    const { rerender } = render(
      <TestWrapper>
        <TripCard trip={activeTrip} />
      </TestWrapper>
    );

    expect(screen.getByText('Active')).toBeInTheDocument();

    const completedTrip = { ...mockTrip, status: 'completed' as const };
    rerender(
      <TestWrapper>
        <TripCard trip={completedTrip} />
      </TestWrapper>
    );

    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('displays budget information correctly', () => {
    const expensiveTrip = { ...mockTrip, budgetTotal: 15000 };
    render(
      <TestWrapper>
        <TripCard trip={expensiveTrip} />
      </TestWrapper>
    );

    expect(screen.getByText('$15,000')).toBeInTheDocument();
  });

  it('handles trips with no families', () => {
    const tripWithoutFamilies = { ...mockTrip, families: [] };
    render(
      <TestWrapper>
        <TripCard trip={tripWithoutFamilies} />
      </TestWrapper>
    );

    // Should still render without crashing
    expect(screen.getByText('Amazing Europe Trip')).toBeInTheDocument();
  });

  it('links to trip detail page', () => {
    render(
      <TestWrapper>
        <TripCard trip={mockTrip} />
      </TestWrapper>
    );

    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', `/trips/${mockTrip.id}`);
  });

  it('handles click events properly', () => {
    const onCardClick = vi.fn();
    render(
      <TestWrapper>
        <TripCard trip={mockTrip} onClick={onCardClick} />
      </TestWrapper>
    );

    const card = screen.getByRole('article');
    fireEvent.click(card);
    expect(onCardClick).toHaveBeenCalledWith(mockTrip);
  });

  it('displays duration correctly', () => {
    render(
      <TestWrapper>
        <TripCard trip={mockTrip} />
      </TestWrapper>
    );

    // Trip is 10 days long (Aug 15-25)
    expect(screen.getByText(/10 days/i)).toBeInTheDocument();
  });

  it('shows private/public status', () => {
    const publicTrip = { ...mockTrip, isPublic: true };
    render(
      <TestWrapper>
        <TripCard trip={publicTrip} />
      </TestWrapper>
    );

    expect(screen.getByText(/public/i)).toBeInTheDocument();
  });
});
