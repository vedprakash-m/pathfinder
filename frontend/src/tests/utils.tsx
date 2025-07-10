import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import { vi } from 'vitest';
import { AuthProvider } from '../contexts/AuthContext';
import { VedUser } from '../types/auth';

// Set up proper mocks for modules before using them
vi.mock('@azure/msal-react', () => ({
  useMsal: () => ({
    instance: {
      getActiveAccount: () => null,
      acquireTokenSilent: vi.fn(() => Promise.resolve({ accessToken: 'mock-token' })),
      loginPopup: vi.fn(() => Promise.resolve({ account: mockAccount })),
      logoutPopup: vi.fn(() => Promise.resolve()),
    },
    accounts: [mockAccount],
  }),
  useAccount: () => mockAccount,
  useIsAuthenticated: () => true,
  MsalProvider: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual('@tanstack/react-query') as any;
  return {
    ...actual,
    useQuery: vi.fn(() => ({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: vi.fn()
    })),
    useMutation: vi.fn(() => ({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
      isError: false,
      error: null,
      data: null,
      reset: vi.fn()
    })),
    useQueryClient: vi.fn(() => ({
      invalidateQueries: vi.fn(),
      setQueryData: vi.fn(),
      getQueryData: vi.fn()
    }))
  };
});

// Mock account data for tests
const mockAccount = {
  localAccountId: 'test-user-id',
  username: 'test@vedprakash.net',
  name: 'Test User',
  given_name: 'Test',
  family_name: 'User',
  idTokenClaims: {
    oid: 'test-user-id',
    preferred_username: 'test@vedprakash.net',
    name: 'Test User'
  }
};

// Create a custom render function that includes providers
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 0,
    },
  },
});

interface CustomRenderOptions extends Omit<RenderOptions, 'queries'> {
  route?: string;
}

// Set up providers for testing - use only our mocked providers
const AllProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <FluentProvider theme={webLightTheme}>
        <MemoryRouter>
          <AuthProvider>
            {children}
          </AuthProvider>
        </MemoryRouter>
      </FluentProvider>
    </QueryClientProvider>
  );
};

// Custom render with all providers
const customRender = (
  ui: ReactElement,
  options?: CustomRenderOptions
) => {
  // Set URL if provided
  if (options?.route) {
    window.history.pushState({}, 'Test page', options.route);
  }
  
  return render(ui, { wrapper: AllProviders, ...options });
};

// Mock for MSAL Entra ID authentication (already mocked above with @azure/msal-react)
const mockMsal = {
  instance: {
    getActiveAccount: () => mockAccount,
    acquireTokenSilent: vi.fn(() => Promise.resolve({ accessToken: 'mock-entra-token' })),
  },
  accounts: [mockAccount],
  inProgress: 'none'
};

// Mock for React Query hooks
const createMockQueryResult = (data: any) => ({
  data,
  isLoading: false,
  isError: false,
  error: null,
  refetch: vi.fn(),
  isFetching: false
});

// Mock VedUser for tests
const mockVedUser: VedUser = {
  id: 'test-user-id',
  email: 'test@vedprakash.net',
  name: 'Test User',
  givenName: 'Test',
  familyName: 'User',
  permissions: ['read:trips', 'write:trips', 'manage:family'],
  vedProfile: {
    profileId: 'test-user-id',
    subscriptionTier: 'free',
    appsEnrolled: ['pathfinder'],
    preferences: {}
  }
};

// Export the custom render as the default render
export { customRender as render };
export { AllProviders };
export { mockMsal };
export { mockVedUser };
export { createMockQueryResult };

// Re-export testing utilities
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
