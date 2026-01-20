import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../tests/utils';
import { HomePage } from '../pages/HomePage';
import { useAuth } from '../contexts/AuthContext';

// Mock the useAuth hook
vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => <div {...props}>{children}</div>,
    p: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => <p {...props}>{children}</p>,
    h1: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => <h1 {...props}>{children}</h1>,
  },
  AnimatePresence: ({ children }: React.PropsWithChildren) => children,
}));

const mockUseAuth = vi.mocked(useAuth);

describe('HomePage', () => {
  it('renders the home page with title when authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      getAccessToken: vi.fn(),
      user: {
        id: 'test',
        email: 'test@test.com',
        name: 'Test User',
        givenName: 'Test',
        familyName: 'User',
        permissions: [],
        vedProfile: {
          profileId: 'test',
          subscriptionTier: 'free',
          appsEnrolled: [],
          preferences: {}
        }
      },
      isLoading: false,
      error: null
    });

    render(<HomePage />);

    // Check for main headline text
    expect(screen.getByText(/plan trips that/i)).toBeInTheDocument();
    expect(screen.getByText(/everyone/i)).toBeInTheDocument();
    expect(screen.getByText(/will love/i)).toBeInTheDocument();
  });

  it('displays features section', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      getAccessToken: vi.fn(),
      user: {
        id: 'test',
        email: 'test@test.com',
        name: 'Test User',
        givenName: 'Test',
        familyName: 'User',
        permissions: [],
        vedProfile: {
          profileId: 'test',
          subscriptionTier: 'free',
          appsEnrolled: [],
          preferences: {}
        }
      },
      isLoading: false,
      error: null
    });

    render(<HomePage />);

    // Check for features section header
    expect(screen.getByText(/Everything you need for/i)).toBeInTheDocument();
    expect(screen.getByText(/AI-Powered Planning/i)).toBeInTheDocument();
  });

  it('shows call to action buttons when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      getAccessToken: vi.fn(),
      user: null,
      isLoading: false,
      error: null
    });

    render(<HomePage />);

    // Check for CTA buttons
    expect(screen.getByRole('button', { name: /start planning free/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /watch demo/i })).toBeInTheDocument();
  });

  it('shows dashboard link when authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      getAccessToken: vi.fn(),
      user: {
        id: 'test',
        email: 'test@test.com',
        name: 'Test User',
        givenName: 'Test',
        familyName: 'User',
        permissions: [],
        vedProfile: {
          profileId: 'test',
          subscriptionTier: 'free',
          appsEnrolled: [],
          preferences: {}
        }
      },
      isLoading: false,
      error: null
    });

    render(<HomePage />);

    // Check for Dashboard button in nav
    expect(screen.getByRole('button', { name: /dashboard/i })).toBeInTheDocument();
  });
});
