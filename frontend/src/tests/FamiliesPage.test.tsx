import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from './utils';
import { FamiliesPage } from '../pages/FamiliesPage';

// Mock the API calls
vi.mock('../services/api', () => ({
  familiesApi: {
    getUserFamilies: vi.fn(() => Promise.resolve([
      {
        id: 'family-1',
        name: 'Smith Family',
        description: 'A loving family of four',
        members: [
          { id: 'user-1', name: 'John Smith', email: 'john@example.com', role: 'admin' },
          { id: 'user-2', name: 'Jane Smith', email: 'jane@example.com', role: 'member' },
        ],
        created_at: '2025-01-01T00:00:00Z',
      }
    ])),
    createFamily: vi.fn(() => Promise.resolve({ id: 'family-2', name: 'New Family' })),
    inviteMember: vi.fn(() => Promise.resolve({ success: true })),
    updateFamily: vi.fn(() => Promise.resolve({ success: true })),
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

describe('FamiliesPage', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders families page with family list', async () => {
    render(<FamiliesPage />);
    
    // Check for page title
    expect(screen.getByText(/families/i)).toBeInTheDocument();
    
    // Wait for family data to load
    await waitFor(() => {
      expect(screen.getByText(/smith family/i)).toBeInTheDocument();
    });
    
    // Check for family details
    expect(screen.getByText(/a loving family of four/i)).toBeInTheDocument();
  });

  it('displays create family button for family admins', async () => {
    render(<FamiliesPage />);
    
    expect(screen.getByRole('button', { name: /create family/i }) || 
           screen.getByRole('button', { name: /new family/i })).toBeInTheDocument();
  });

  it('shows family member list with roles', async () => {
    render(<FamiliesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/john smith/i)).toBeInTheDocument();
      expect(screen.getByText(/jane smith/i)).toBeInTheDocument();
    });
    
    // Check for role indicators
    expect(screen.getByText(/admin/i) || screen.getByText(/member/i)).toBeInTheDocument();
  });

  it('allows inviting new family members', async () => {
    render(<FamiliesPage />);
    
    await waitFor(() => {
      const inviteButton = screen.getByRole('button', { name: /invite member/i }) ||
                          screen.getByRole('button', { name: /invite/i });
      expect(inviteButton).toBeInTheDocument();
    });
    
    const inviteButton = screen.getByRole('button', { name: /invite/i });
    await user.click(inviteButton);
    
    // Should open invite dialog/form
    await waitFor(() => {
      expect(screen.getByLabelText(/email/i) || screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
    });
  });

  it('validates email format in invite form', async () => {
    render(<FamiliesPage />);
    
    // Open invite form
    await waitFor(() => {
      const inviteButton = screen.getByRole('button', { name: /invite/i });
      user.click(inviteButton);
    });
    
    await waitFor(() => {
      const emailInput = screen.getByLabelText(/email/i) || screen.getByPlaceholderText(/email/i);
      expect(emailInput).toBeInTheDocument();
    });
    
    const emailInput = screen.getByLabelText(/email/i) || screen.getByPlaceholderText(/email/i);
    await user.type(emailInput, 'invalid-email');
    
    const sendButton = screen.getByRole('button', { name: /send/i }) || 
                      screen.getByRole('button', { name: /invite/i });
    await user.click(sendButton);
    
    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/valid email/i) || screen.getByText(/invalid email/i)).toBeInTheDocument();
    });
  });

  it('successfully sends family invitation', async () => {
    const { familiesApi } = await import('../services/api');
    
    render(<FamiliesPage />);
    
    // Open invite form and fill valid email
    await waitFor(() => {
      const inviteButton = screen.getByRole('button', { name: /invite/i });
      user.click(inviteButton);
    });
    
    await waitFor(() => {
      const emailInput = screen.getByLabelText(/email/i) || screen.getByPlaceholderText(/email/i);
      user.type(emailInput, 'newmember@example.com');
    });
    
    const sendButton = screen.getByRole('button', { name: /send/i }) || 
                      screen.getByRole('button', { name: /invite/i });
    await user.click(sendButton);
    
    // Verify API call
    await waitFor(() => {
      expect(familiesApi.inviteMember).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          email: 'newmember@example.com'
        })
      );
    });
  });

  it('displays family preferences and settings', async () => {
    render(<FamiliesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/preferences/i) || 
             screen.getByText(/settings/i) ||
             screen.getByRole('button', { name: /settings/i })).toBeInTheDocument();
    });
  });

  it('allows editing family information for admins', async () => {
    render(<FamiliesPage />);
    
    await waitFor(() => {
      const editButton = screen.getByRole('button', { name: /edit/i }) ||
                        screen.getByLabelText(/edit family/i);
      expect(editButton).toBeInTheDocument();
    });
    
    const editButton = screen.getByRole('button', { name: /edit/i });
    await user.click(editButton);
    
    // Should open edit form
    await waitFor(() => {
      expect(screen.getByDisplayValue(/smith family/i) || 
             screen.getByLabelText(/family name/i)).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching families', () => {
    render(<FamiliesPage />);
    
    // Should show loading indicator
    expect(screen.getByText(/loading/i) || 
           screen.getByTestId('families-loading') ||
           screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles empty family list gracefully', async () => {
    const { familiesApi } = await import('../services/api');
    vi.mocked(familiesApi.getUserFamilies).mockResolvedValue([]);
    
    render(<FamiliesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/no families/i) || 
             screen.getByText(/create your first family/i)).toBeInTheDocument();
    });
  });

  it('displays family statistics and member count', async () => {
    render(<FamiliesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/2 members/i) || 
             screen.getByText(/members: 2/i)).toBeInTheDocument();
    });
  });

  it('shows recent family activity', async () => {
    render(<FamiliesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/recent activity/i) || 
             screen.getByText(/activity/i)).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const { familiesApi } = await import('../services/api');
    vi.mocked(familiesApi.getUserFamilies).mockRejectedValue(new Error('API Error'));
    
    render(<FamiliesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading families/i) || 
             screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });
  });
});
