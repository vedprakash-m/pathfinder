import { apiService } from './api';
import { User, AuthCredentials, RegisterData, ApiResponse, UserProfile, LoginResponse } from '@/types';

// Auth0 configuration - now sourced from Azure Key Vault via environment variables
const auth0Config = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN!,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID!,
  audience: import.meta.env.VITE_AUTH0_AUDIENCE!,
  redirectUri: `${window.location.origin}/callback`,
};

export const authService = {
  // Login with email and password (development only)
  login: async (credentials: AuthCredentials): Promise<ApiResponse<LoginResponse>> => {
    const response = await apiService.post<LoginResponse>('/auth/login', credentials);
    if (response.data?.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    return response;
  },
  
  // Register a new user
  register: async (userData: RegisterData): Promise<ApiResponse<User>> => {
    return apiService.post<User>('/auth/register', userData);
  },
  
  // Logout the current user
  logout: async (): Promise<void> => {
    try {
      await apiService.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('auth_token');
      sessionStorage.clear();
    }
  },
  
  // Get current user profile
  getCurrentUser: async (): Promise<ApiResponse<UserProfile>> => {
    return apiService.get<UserProfile>('/auth/me');
  },
  
  // Update current user profile
  updateProfile: async (userData: Partial<User>): Promise<ApiResponse<User>> => {
    return apiService.put<User>('/auth/me', userData);
  },
  
  // Validate the current token
  validateToken: async (): Promise<boolean> => {
    try {
      const response = await apiService.get<{ valid: boolean }>('/auth/validate');
      return response.data?.valid === true;
    } catch (error) {
      return false;
    }
  },
  
  // Check if the user is currently authenticated
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('auth_token');
  },
  
  // Auth0 integration
  getAuth0LoginUrl: (): string => {
    const params = {
      client_id: auth0Config.clientId,
      response_type: 'code',
      redirect_uri: auth0Config.redirectUri,
      audience: auth0Config.audience,
      scope: 'openid profile email',
    };
    
    return `https://${auth0Config.domain}/authorize?${new URLSearchParams(params).toString()}`;
  },
  
  // Handle Auth0 callback
  handleAuth0Callback: async (code: string): Promise<ApiResponse<LoginResponse>> => {
    return apiService.post<LoginResponse>('/auth/callback', { code });
  },
  
  // Refresh the authentication token
  refreshToken: async (): Promise<ApiResponse<{ access_token: string }>> => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    const response = await apiService.post<{ access_token: string }>('/auth/refresh-token', {
      refresh_token: refreshToken,
    });
    
    if (response.data?.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    
    return response;
  },
  
  // Associate a social account with existing user
  linkSocialAccount: async (provider: string, accessToken: string): Promise<ApiResponse<User>> => {
    return apiService.post<User>('/auth/link-account', { provider, access_token: accessToken });
  },
  
  // Delete current user account
  deleteAccount: async (): Promise<ApiResponse<void>> => {
    return apiService.delete<void>('/auth/me');
  },
  
  // Request password reset
  requestPasswordReset: async (email: string): Promise<ApiResponse<{ message: string }>> => {
    return apiService.post<{ message: string }>('/auth/password-reset', { email });
  },
  
  // Reset password with token
  resetPassword: async (token: string, newPassword: string): Promise<ApiResponse<{ message: string }>> => {
    return apiService.post<{ message: string }>('/auth/reset-password', { 
      token,
      new_password: newPassword 
    });
  },
};

export default authService;