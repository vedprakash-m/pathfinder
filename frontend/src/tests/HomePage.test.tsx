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

const mockUseAuth = vi.mocked(useAuth);

describe('HomePage', () => {
  it('renders the home page with title and call to action when authenticated', () => {
    // Mock authenticated state
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

    // Arrange
    render(<HomePage />);
    
    // Act - None, just render
    
    // Assert
    expect(screen.getByText(/plan perfect trips with/i)).toBeInTheDocument();
    expect(screen.getByText(/ai intelligence/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /go to dashboard/i })).toBeInTheDocument();
  });
  
  it('displays features section', () => {
    // Mock authenticated state
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

    // Arrange
    render(<HomePage />);
    
    // Assert
    const featuresSection = screen.getByText(/why choose pathfinder/i);
    expect(featuresSection).toBeInTheDocument();
  });
  
  it('shows call to action buttons when not authenticated', () => {
    // Mock unauthenticated state
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      getAccessToken: vi.fn(),
      user: null,
      isLoading: false,
      error: null
    });

    // Arrange
    render(<HomePage />);
    
    // Assert
    const getStartedButton = screen.getByRole('button', { name: /get started free/i });
    expect(getStartedButton).toBeInTheDocument();
    
    const signInButton = screen.getByRole('button', { name: /sign in/i });
    expect(signInButton).toBeInTheDocument();
  });
});
