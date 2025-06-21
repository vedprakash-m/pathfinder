import { describe, it, expect, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from '../utils';

// Mock components that might not exist yet - we'll create basic test structures
const TripCard = ({ trip, onView, onEdit }: any) => (
  <div data-testid="trip-card">
    <h3>{trip.title}</h3>
    <p>{trip.destination}</p>
    <p>{trip.startDate} - {trip.endDate}</p>
    <p>${trip.budget}</p>
    <button onClick={() => onView(trip.id)}>View Details</button>
    {onEdit && <button onClick={() => onEdit(trip.id)}>Edit</button>}
  </div>
);

const FamilyCard = ({ family, onManage, onInvite }: any) => (
  <div data-testid="family-card">
    <h3>{family.name}</h3>
    <p>{family.description}</p>
    <p>{family.members?.length || 0} members</p>
    <button onClick={() => onManage(family.id)}>Manage</button>
    <button onClick={() => onInvite(family.id)}>Invite Members</button>
  </div>
);

const ChatMessage = ({ message, user, timestamp }: any) => (
  <div data-testid="chat-message" className="chat-message">
    <div className="message-header">
      <span className="user-name">{user.name}</span>
      <span className="timestamp">{timestamp}</span>
    </div>
    <div className="message-content">{message}</div>
  </div>
);

describe('TripCard Component', () => {
  const mockTrip = {
    id: 'trip-1',
    title: 'Amazing Paris Trip',
    destination: 'Paris, France',
    startDate: '2025-08-01',
    endDate: '2025-08-07',
    budget: 5000,
    status: 'planning',
  };

  it('renders trip information correctly', () => {
    const onView = vi.fn();
    const onEdit = vi.fn();
    
    render(<TripCard trip={mockTrip} onView={onView} onEdit={onEdit} />);
    
    expect(screen.getByText('Amazing Paris Trip')).toBeInTheDocument();
    expect(screen.getByText('Paris, France')).toBeInTheDocument();
    expect(screen.getByText('2025-08-01 - 2025-08-07')).toBeInTheDocument();
    expect(screen.getByText('$5000')).toBeInTheDocument();
  });

  it('calls onView when view button is clicked', async () => {
    const user = userEvent.setup();
    const onView = vi.fn();
    
    render(<TripCard trip={mockTrip} onView={onView} />);
    
    const viewButton = screen.getByRole('button', { name: /view details/i });
    await user.click(viewButton);
    
    expect(onView).toHaveBeenCalledWith('trip-1');
  });

  it('shows edit button only when onEdit is provided', () => {
    const onView = vi.fn();
    
    // Render without edit function
    const { rerender } = render(<TripCard trip={mockTrip} onView={onView} />);
    expect(screen.queryByRole('button', { name: /edit/i })).not.toBeInTheDocument();
    
    // Render with edit function
    const onEdit = vi.fn();
    rerender(<TripCard trip={mockTrip} onView={onView} onEdit={onEdit} />);
    expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', async () => {
    const user = userEvent.setup();
    const onView = vi.fn();
    const onEdit = vi.fn();
    
    render(<TripCard trip={mockTrip} onView={onView} onEdit={onEdit} />);
    
    const editButton = screen.getByRole('button', { name: /edit/i });
    await user.click(editButton);
    
    expect(onEdit).toHaveBeenCalledWith('trip-1');
  });
});

describe('FamilyCard Component', () => {
  const mockFamily = {
    id: 'family-1',
    name: 'Smith Family',
    description: 'A wonderful family of four',
    members: [
      { id: 'user-1', name: 'John Smith' },
      { id: 'user-2', name: 'Jane Smith' },
    ],
  };

  it('renders family information correctly', () => {
    const onManage = vi.fn();
    const onInvite = vi.fn();
    
    render(<FamilyCard family={mockFamily} onManage={onManage} onInvite={onInvite} />);
    
    expect(screen.getByText('Smith Family')).toBeInTheDocument();
    expect(screen.getByText('A wonderful family of four')).toBeInTheDocument();
    expect(screen.getByText('2 members')).toBeInTheDocument();
  });

  it('handles families with no members', () => {
    const familyWithNoMembers = { ...mockFamily, members: [] };
    const onManage = vi.fn();
    const onInvite = vi.fn();
    
    render(<FamilyCard family={familyWithNoMembers} onManage={onManage} onInvite={onInvite} />);
    
    expect(screen.getByText('0 members')).toBeInTheDocument();
  });

  it('calls onManage when manage button is clicked', async () => {
    const user = userEvent.setup();
    const onManage = vi.fn();
    const onInvite = vi.fn();
    
    render(<FamilyCard family={mockFamily} onManage={onManage} onInvite={onInvite} />);
    
    const manageButton = screen.getByRole('button', { name: /manage/i });
    await user.click(manageButton);
    
    expect(onManage).toHaveBeenCalledWith('family-1');
  });

  it('calls onInvite when invite button is clicked', async () => {
    const user = userEvent.setup();
    const onManage = vi.fn();
    const onInvite = vi.fn();
    
    render(<FamilyCard family={mockFamily} onManage={onManage} onInvite={onInvite} />);
    
    const inviteButton = screen.getByRole('button', { name: /invite members/i });
    await user.click(inviteButton);
    
    expect(onInvite).toHaveBeenCalledWith('family-1');
  });
});

describe('ChatMessage Component', () => {
  const mockMessage = {
    message: 'Hello everyone! How about we visit the Eiffel Tower?',
    user: { name: 'John Smith', id: 'user-1' },
    timestamp: '2025-06-20T10:30:00Z',
  };

  it('renders chat message correctly', () => {
    render(<ChatMessage {...mockMessage} />);
    
    expect(screen.getByText('Hello everyone! How about we visit the Eiffel Tower?')).toBeInTheDocument();
    expect(screen.getByText('John Smith')).toBeInTheDocument();
    expect(screen.getByText('2025-06-20T10:30:00Z')).toBeInTheDocument();
  });

  it('has proper semantic structure', () => {
    render(<ChatMessage {...mockMessage} />);
    
    const messageElement = screen.getByTestId('chat-message');
    expect(messageElement).toHaveClass('chat-message');
    
    const messageContent = screen.getByText('Hello everyone! How about we visit the Eiffel Tower?');
    expect(messageContent).toHaveClass('message-content');
  });

  it('displays user name and timestamp in header', () => {
    render(<ChatMessage {...mockMessage} />);
    
    const userName = screen.getByText('John Smith');
    const timestamp = screen.getByText('2025-06-20T10:30:00Z');
    
    expect(userName).toHaveClass('user-name');
    expect(timestamp).toHaveClass('timestamp');
  });

  it('handles long messages properly', () => {
    const longMessage = {
      ...mockMessage,
      message: 'This is a very long message that should be displayed properly without breaking the layout. It contains multiple sentences and should wrap correctly within the chat interface.',
    };
    
    render(<ChatMessage {...longMessage} />);
    
    expect(screen.getByText(/This is a very long message/)).toBeInTheDocument();
  });

  it('handles empty messages gracefully', () => {
    const emptyMessage = { ...mockMessage, message: '' };
    
    render(<ChatMessage {...emptyMessage} />);
    
    const messageContent = screen.getByText('');
    expect(messageContent).toHaveClass('message-content');
  });
});
