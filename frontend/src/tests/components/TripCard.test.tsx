import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TripCard } from '../../components/trips/TripCard';
import { AllProviders } from '../utils';
import type { Trip } from '../../types';

const mockTrip: Trip = {
  id: '1',
  title: 'Test Trip',
  name: 'Test Trip',
  description: 'A test trip description',
  destination: 'Test Destination',
  start_date: '2024-06-01',
  end_date: '2024-06-07',
  status: 'planning',
  family_id: 'family-1',
  family_count: 1,
  confirmed_families: 0,
  created_by: 'user-1',
  participants: [],
  reservations: [],
  created_at: '2024-05-01T10:00:00Z',
  updated_at: '2024-05-01T10:00:00Z'
};

describe('TripCard', () => {
  it('renders trip information correctly', () => {
    render(
      <AllProviders>
        <TripCard trip={mockTrip} />
      </AllProviders>
    );

    expect(screen.getByText('Test Trip')).toBeInTheDocument();
    expect(screen.getByText('A test trip description')).toBeInTheDocument();
    expect(screen.getByText('Test Destination')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /view details/i })).toBeInTheDocument();
  });

  it('shows join button when onJoin is provided and status is planning', () => {
    const mockOnJoin = vi.fn();
    
    render(
      <AllProviders>
        <TripCard trip={mockTrip} onJoin={mockOnJoin} />
      </AllProviders>
    );

    const joinButton = screen.getByRole('button', { name: /join trip/i });
    expect(joinButton).toBeInTheDocument();
    
    fireEvent.click(joinButton);
    expect(mockOnJoin).toHaveBeenCalledWith(mockTrip.id);
  });

  it('does not show join button when status is not planning', () => {
    const mockOnJoin = vi.fn();
    const completedTrip = { ...mockTrip, status: 'completed' as const };
    
    render(
      <AllProviders>
        <TripCard trip={completedTrip} onJoin={mockOnJoin} />
      </AllProviders>
    );

    expect(screen.queryByRole('button', { name: /join trip/i })).not.toBeInTheDocument();
  });

  it('shows leave button when onLeave is provided', () => {
    const mockOnLeave = vi.fn();
    
    render(
      <AllProviders>
        <TripCard trip={mockTrip} onLeave={mockOnLeave} />
      </AllProviders>
    );

    const leaveButton = screen.getByRole('button', { name: /leave/i });
    expect(leaveButton).toBeInTheDocument();
    
    fireEvent.click(leaveButton);
    expect(mockOnLeave).toHaveBeenCalledWith(mockTrip.id);
  });

  it('displays trip status badge', () => {
    render(
      <AllProviders>
        <TripCard trip={mockTrip} />
      </AllProviders>
    );

    expect(screen.getByText('planning')).toBeInTheDocument();
  });
});
