// API client for Pathfinder backend
// Uses Azure Functions backend with MSAL authentication

import { PublicClientApplication } from '@azure/msal-browser';
import { apiRequest } from '../msal-config';

interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// MSAL instance for token acquisition
let msalInstance: PublicClientApplication | null = null;

export function setMsalInstance(instance: PublicClientApplication) {
  msalInstance = instance;
}

class ApiClient {
  private baseURL: string;

  constructor() {
    // Use environment variable or default to local Azure Functions
    this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:7071/api';
  }

  private async getAccessToken(): Promise<string | null> {
    if (!msalInstance) {
      console.warn('MSAL instance not set, trying localStorage fallback');
      return localStorage.getItem('auth_token');
    }

    try {
      const accounts = msalInstance.getAllAccounts();
      if (accounts.length === 0) {
        return null;
      }

      const response = await msalInstance.acquireTokenSilent({
        ...apiRequest,
        account: accounts[0],
      });

      return response.accessToken;
    } catch (error) {
      console.error('Failed to acquire token silently:', error);

      // Try interactive token acquisition as fallback
      try {
        const accounts = msalInstance.getAllAccounts();
        if (accounts.length === 0) {
          return null;
        }

        const response = await msalInstance.acquireTokenPopup({
          ...apiRequest,
          account: accounts[0],
        });

        return response.accessToken;
      } catch (interactiveError) {
        console.error('Failed to acquire token interactively:', interactiveError);
        return null;
      }
    }
  }

  private async getAuthHeaders(): Promise<HeadersInit> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const token = await this.getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    const contentType = response.headers.get('content-type');

    if (!contentType?.includes('application/json')) {
      if (!response.ok) {
        return {
          data: {} as T,
          success: false,
          message: `HTTP ${response.status}: ${response.statusText}`,
        };
      }
      return {
        data: {} as T,
        success: true,
      };
    }

    const json = await response.json();

    if (!response.ok) {
      const error = json as ApiError;
      return {
        data: {} as T,
        success: false,
        message: error.message || `HTTP ${response.status}`,
        error,
      };
    }

    // Handle both wrapped and unwrapped responses
    if ('data' in json && 'success' in json) {
      return json as ApiResponse<T>;
    }

    return {
      data: json as T,
      success: true,
    };
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'GET',
        headers,
      });

      return this.handleResponse<T>(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Network error';
      return {
        data: {} as T,
        success: false,
        message,
      };
    }
  }

  async post<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'POST',
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });

      return this.handleResponse<T>(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Network error';
      return {
        data: {} as T,
        success: false,
        message,
      };
    }
  }

  async put<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'PUT',
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });

      return this.handleResponse<T>(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Network error';
      return {
        data: {} as T,
        success: false,
        message,
      };
    }
  }

  async patch<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'PATCH',
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });

      return this.handleResponse<T>(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Network error';
      return {
        data: {} as T,
        success: false,
        message,
      };
    }
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        method: 'DELETE',
        headers,
      });

      return this.handleResponse<T>(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Network error';
      return {
        data: {} as T,
        success: false,
        message,
      };
    }
  }
}

export const api = new ApiClient();
