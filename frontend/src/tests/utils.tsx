import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import { vi } from 'vitest';

// Create a custom render function that includes providers
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

interface CustomRenderOptions extends Omit<RenderOptions, 'queries'> {
  route?: string;
}

// Set up providers for testing
const AllProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <FluentProvider theme={webLightTheme}>
        <BrowserRouter>
          {children}
        </BrowserRouter>
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

// Mock for Auth0
const mockAuth0 = {
  isAuthenticated: true,
  user: {
    name: 'Test User',
    email: 'test@example.com',
    sub: 'auth0|12345',
    picture: 'https://example.com/avatar.png'
  },
  isLoading: false,
  loginWithRedirect: vi.fn(),
  logout: vi.fn(),
  getAccessTokenSilently: vi.fn()
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

export * from '@testing-library/react';
export { customRender as render, mockAuth0, createMockQueryResult };
export { AllProviders as TestWrapper };
