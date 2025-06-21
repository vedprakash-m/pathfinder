import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FamilyManagement } from '../../components/families/FamilyManagement';
import { TestWrapper } from '../utils';

// Mock the API service
vi.mock('../../services/api', () => ({
  api: {
    families: {
      getAll: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      inviteMember: vi.fn(),
      removeMember: vi.fn(),
    },
  },
}));

const mockFamilies = [
  {
    id: 'fam1',
    name: 'Smith Family',
    description: 'The Smith family loves adventure',
    members: [
      { id: 'user1', name: 'John Smith', email: 'john@smith.com', role: 'admin' },
      { id: 'user2', name: 'Jane Smith', email: 'jane@smith.com', role: 'member' },
    ],
    preferences: {
      activities: ['hiking', 'museums'],
      budgetLevel: 'medium',
      dietaryRestrictions: ['vegetarian'],
    },
  },
  {
    id: 'fam2',
    name: 'Johnson Family',
    description: 'The Johnson family enjoys relaxation',
    members: [
      { id: 'user3', name: 'Bob Johnson', email: 'bob@johnson.com', role: 'admin' },
    ],
    preferences: {
      activities: ['beaches', 'restaurants'],
      budgetLevel: 'high',
      dietaryRestrictions: [],
    },
  },
];

describe('FamilyManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders family list correctly', async () => {
    const { api } = await import('../../services/api');
    (api.families.getAll as any).mockResolvedValue(mockFamilies);

    render(
      <TestWrapper>
        <FamilyManagement />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Smith Family')).toBeInTheDocument();
      expect(screen.getByText('Johnson Family')).toBeInTheDocument();
    });
  });

  it('displays family member counts', async () => {
    const { api } = await import('../../services/api');
    (api.families.getAll as any).mockResolvedValue(mockFamilies);

    render(
      <TestWrapper>
        <FamilyManagement />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('2 members')).toBeInTheDocument();
      expect(screen.getByText('1 member')).toBeInTheDocument();
    });
  });

  it('shows create family button', async () => {
    const { api } = await import('../../services/api');
    (api.families.getAll as any).mockResolvedValue([]);

    render(
      <TestWrapper>
        <FamilyManagement />
      </TestWrapper>
    );

    expect(screen.getByRole('button', { name: /create family/i })).toBeInTheDocument();
  });

  it('opens create family modal when button is clicked', async () => {
    const user = userEvent.setup();
    const { api } = await import('../../services/api');
    (api.families.getAll as any).mockResolvedValue([]);

    render(
      <TestWrapper>
        <FamilyManagement />
      </TestWrapper>
    );

    const createButton = screen.getByRole('button', { name: /create family/i });
    await user.click(createButton);

    expect(screen.getByText(/create new family/i)).toBeInTheDocument();
  });

  it('creates a new family successfully', async () => {
    const user = userEvent.setup();
    const { api } = await import('../../services/api');
    (api.families.getAll as any).mockResolvedValue([]);
    (api.families.create as any).mockResolvedValue({
      id: 'new-fam',
      name: 'New Family',
      description: 'A new family',
      members: [],
    });

    render(
      <TestWrapper>
        <FamilyManagement />
      </TestWrapper>
    );

    // Open create modal
    const createButton = screen.getByRole('button', { name: /create family/i });
    await user.click(createButton);

    // Fill form
    const nameInput = screen.getByLabelText(/family name/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    await user.type(nameInput, 'New Family');
    await user.type(descriptionInput, 'A new family');

    // Submit
    const submitButton = screen.getByRole('button', { name: /create/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(api.families.create).toHaveBeenCalledWith({
        name: 'New Family',
        description: 'A new family',
      });
    });
  });

  it('displays family preferences', async () => {
    const { api } = await import('../../services/api');
    (api.families.getAll as any).mockResolvedValue(mockFamilies);

    render(
      <TestWrapper>
        <FamilyManagement />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('hiking')).toBeInTheDocument();
      expect(screen.getByText('museums')).toBeInTheDocument();
      expect(screen.getByText('vegetarian')).toBeInTheDocument();
    });
  });

  it('allows inviting new family members', async () => {
    const user = userEvent.setup();
    const { api } = await import('../../services/api');
    (api.families.getAll as any).mockResolvedValue(mockFamilies);
    (api.families.inviteMember as any).mockResolvedValue({ success: true });

    render(
      <TestWrapper>
        <FamilyManagement />
      </TestWrapper>
    );

    await waitFor(() => {
      const inviteButton = screen.getByRole('button', { name: /invite member/i });
      expect(inviteButton).toBeInTheDocument();
    });

    // Click invite button for Smith Family
    const inviteButtons = screen.getAllByRole('button', { name: /invite member/i });
    await user.click(inviteButtons[0]);

    // Fill invitation form
    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 'newmember@smith.com');

    const sendButton = screen.getByRole('button', { name: /send invitation/i });
    await user.click(sendButton);

    await waitFor(() => {
      expect(api.families.inviteMember).toHaveBeenCalledWith('fam1', {
        email: 'newmember@smith.com',
      });
    });
  });

  it('handles empty family list', async () => {
    const { api } = await import('../../services/api');
    (api.families.getAll as any).mockResolvedValue([]);

    render(
      <TestWrapper>
        <FamilyManagement />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/no families/i)).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const { api } = await import('../../services/api');
    (api.families.getAll as any).mockRejectedValue(new Error('API Error'));

    render(
      <TestWrapper>
        <FamilyManagement />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/error loading families/i)).toBeInTheDocument();
    });
  });

  it('shows family admin privileges', async () => {
    const { api } = await import('../../services/api');
    (api.families.getAll as any).mockResolvedValue(mockFamilies);

    render(
      <TestWrapper>
        <FamilyManagement />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('John Smith')).toBeInTheDocument();
      expect(screen.getByText('admin')).toBeInTheDocument();
    });
  });
});
