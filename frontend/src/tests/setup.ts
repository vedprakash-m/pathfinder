import { expect, afterEach, vi, beforeEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';
import '@testing-library/jest-dom/vitest';

// Extend Vitest's expect method with testing-library methods
expect.extend(matchers);

// Clean up after each test case
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

beforeEach(() => {
  // Reset all mocks before each test
  vi.clearAllMocks();
});

// Mock IntersectionObserver for framer-motion
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  root: null,
  rootMargin: '',
  thresholds: [],
  takeRecords: vi.fn(() => []),
})) as any;

// Mock fetch API globally
global.fetch = vi.fn();

// Mock window.matchMedia for responsive components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock API service
vi.mock('@/services/api', () => import('./__mocks__/api'));

// Mock auth hook
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    isLoading: false,
    user: {
      id: 'test-user-id',
      email: 'test@example.com',
      name: 'Test User',
      roles: ['family_admin'],
    },
    login: vi.fn(),
    logout: vi.fn(),
    getAccessToken: vi.fn().mockResolvedValue('mock-token'),
  }),
}));

// Mock router hooks
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom') as any;
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useParams: () => ({}),
    useLocation: () => ({ pathname: '/', search: '', hash: '', state: null }),
  };
});

// Mock MSAL React
vi.mock('@azure/msal-react', async () => {
  const actual = await vi.importActual('@azure/msal-react') as any;
  return {
    ...actual,
    useAccount: vi.fn(() => ({
      homeAccountId: 'test-home-account-id',
      environment: 'test-environment',
      tenantId: 'test-tenant-id',
      username: 'test@example.com',
      localAccountId: 'test-local-account-id',
      name: 'Test User',
    })),
    useMsal: vi.fn(() => ({
      instance: {
        loginRedirect: vi.fn(),
        logout: vi.fn(),
        acquireTokenSilent: vi.fn().mockResolvedValue({
          accessToken: 'mock-access-token',
          account: {
            username: 'test@example.com',
            name: 'Test User',
          },
        }),
      },
      accounts: [{
        homeAccountId: 'test-home-account-id',
        environment: 'test-environment',
        tenantId: 'test-tenant-id',
        username: 'test@example.com',
        localAccountId: 'test-local-account-id',
        name: 'Test User',
      }],
      inProgress: 'none',
    })),
    MsalProvider: ({ children }: { children: React.ReactNode }) => children,
  };
});
