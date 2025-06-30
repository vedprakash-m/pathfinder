import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { ApiResponse } from '@/types';

// Simple in-memory cache implementation
interface CacheEntry {
  timestamp: number;
  data: any;
  expiresIn: number;
}

class ApiCache {
  private cache: Record<string, CacheEntry> = {};
  
  // Default cache duration in milliseconds (5 minutes)
  private defaultCacheTime = 1000 * 60 * 5;
  
  get(key: string): any | null {
    const entry = this.cache[key];
    if (!entry) return null;
    
    // Check if cache entry has expired
    if (Date.now() - entry.timestamp > entry.expiresIn) {
      delete this.cache[key];
      return null;
    }
    
    return entry.data;
  }
  
  set(key: string, data: any, expiresIn: number = this.defaultCacheTime): void {
    this.cache[key] = {
      timestamp: Date.now(),
      data,
      expiresIn
    };
  }
  
  invalidate(keyPattern: string): void {
    // Invalidate all cache entries matching the pattern
    // Example: invalidate('trips') will clear 'trips', 'trips/1', etc.
    Object.keys(this.cache).forEach(key => {
      if (key.includes(keyPattern)) {
        delete this.cache[key];
      }
    });
  }
  
  clear(): void {
    this.cache = {};
  }
}

const apiCache = new ApiCache();

// Global token getter function - will be set by the Auth provider
let getAccessToken: (() => Promise<string>) | null = null;

// Function to set the token getter (called from Auth provider)
export const setTokenGetter = (tokenGetter: () => Promise<string>) => {
  getAccessToken = tokenGetter;
};

// Create axios instance with default config
const createApiClient = (baseURL: string = (import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api/v1` : 'http://localhost:8000/api/v1')): AxiosInstance => {
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor to add auth token and CSRF token
  client.interceptors.request.use(
    async (config) => {
      // Try to get token from auth provider first, then fallback to localStorage
      try {
        if (getAccessToken) {
          const token = await getAccessToken();
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
            console.log('🔐 Using auth token for API request:', config.url);
          }
        } else {
          // Fallback to localStorage for development
          const token = localStorage.getItem('auth_token');
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
            console.log('🔐 Using localStorage token for API request:', config.url);
          } else {
            console.warn('⚠️ No token available for API request:', config.url);
          }
        }
      } catch (error) {
        console.warn('⚠️ Failed to get access token for API request:', config.url, error);
        // Continue without token - let the backend handle the 401
      }
      
      // Add CSRF token from cookie if available
      const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf='))
        ?.split('=')[1];
      
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken;
      }
      
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Request timing data
  const timings = new Map<string, number>();

  // Request interceptor to track start time
  client.interceptors.request.use(
    (config) => {
      // Start timing this request
      const requestId = Math.random().toString(36).substring(2, 9);
      timings.set(requestId, performance.now());
      
      // Store the request ID on the config object
      config.headers.set('X-Request-Id', requestId);
      
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor for error handling and performance tracking
  client.interceptors.response.use(
    (response) => {
      // Track API performance if we have the request ID
      const requestId = response.config.headers?.['X-Request-Id'] as string;
      if (requestId && timings.has(requestId)) {
        const startTime = timings.get(requestId)!;
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        // Import dynamically to avoid circular dependencies
        import('@/utils/performanceMonitoring').then(({ trackApiCall }) => {
          // Extract endpoint path for tracking
          const url = new URL(response.config.url || '', window.location.origin);
          trackApiCall(url.pathname, duration);
        }).catch(err => console.error('Failed to track API performance', err));
        
        // Clean up timing data
        timings.delete(requestId);
      }
      
      return response;
    },
    (error) => {
      // Track API performance for errors too
      const requestId = error.config?.headers?.['X-Request-Id'] as string;
      if (requestId && timings.has(requestId)) {
        const startTime = timings.get(requestId)!;
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        import('@/utils/performanceMonitoring').then(({ trackApiCall }) => {
          // Mark failed requests
          const url = new URL(error.config?.url || '', window.location.origin);
          trackApiCall(`${url.pathname} (failed)`, duration);
        }).catch(err => console.error('Failed to track API error performance', err));
        
        // Clean up timing data
        timings.delete(requestId);
      }

      // Handle authentication errors per Vedprakash Domain standards
      if (error.response?.status === 401) {
        const errorData = error.response.data;
        const errorCode = errorData?.code;
        
        switch (errorCode) {
          case 'AUTH_TOKEN_MISSING':
            console.error('❌ Authentication token missing');
            // Could trigger login redirect here
            break;
          case 'AUTH_TOKEN_INVALID':
            console.error('❌ Authentication token invalid or expired');
            // Could trigger token refresh here
            break;
          default:
            console.error('❌ Authentication failed:', errorData?.error || error.message);
        }
        
        // Legacy fallback for existing behavior
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      } else if (error.response?.status === 403) {
        const errorData = error.response.data;
        if (errorData?.code === 'AUTH_PERMISSION_DENIED') {
          console.error('❌ Insufficient permissions:', errorData?.error);
        }
      } else if (error.response?.status === 503) {
        const errorData = error.response.data;
        if (errorData?.code === 'AUTH_SERVICE_UNAVAILABLE') {
          console.error('❌ Authentication service temporarily unavailable');
        }
      }
      
      // Transform error to consistent format
      const apiError = {
        message: error.response?.data?.message || error.message || 'An error occurred',
        code: error.response?.data?.code || error.code,
        details: error.response?.data?.details || {},
      };
      
      return Promise.reject(apiError);
    }
  );

  return client;
};

export const apiClient = createApiClient();

// Generic API methods with caching
export const apiService = {
  get: async <T>(url: string, config?: AxiosRequestConfig & { bypassCache?: boolean, cacheTime?: number }): Promise<ApiResponse<T>> => {
    const shouldUseCache = !(config?.bypassCache);
    
    if (shouldUseCache) {
      // Try to get from cache first
      const cacheKey = `GET:${url}`;
      const cachedData = apiCache.get(cacheKey);
      if (cachedData) {
        return cachedData;
      }
    }
    
    // If not in cache or cache bypassed, fetch from API
    const response = await apiClient.get(url, config);
    
    // Store in cache if caching is enabled
    if (shouldUseCache) {
      apiCache.set(`GET:${url}`, response.data, config?.cacheTime);
    }
    
    return response.data;
  },

  post: async <T>(url: string, data?: any, config?: AxiosRequestConfig & { invalidateUrlPatterns?: string[] }): Promise<ApiResponse<T>> => {
    const response = await apiClient.post(url, data, config);
    
    // Invalidate related cache entries when mutating data
    if (config?.invalidateUrlPatterns) {
      config.invalidateUrlPatterns.forEach(pattern => {
        apiCache.invalidate(pattern);
      });
    }
    
    return response.data;
  },

  put: async <T>(url: string, data?: any, config?: AxiosRequestConfig & { invalidateUrlPatterns?: string[] }): Promise<ApiResponse<T>> => {
    const response = await apiClient.put(url, data, config);
    
    // Invalidate related cache entries when mutating data
    if (config?.invalidateUrlPatterns) {
      config.invalidateUrlPatterns.forEach(pattern => {
        apiCache.invalidate(pattern);
      });
    }
    
    return response.data;
  },

  patch: async <T>(url: string, data?: any, config?: AxiosRequestConfig & { invalidateUrlPatterns?: string[] }): Promise<ApiResponse<T>> => {
    const response = await apiClient.patch(url, data, config);
    
    // Invalidate related cache entries when mutating data
    if (config?.invalidateUrlPatterns) {
      config.invalidateUrlPatterns.forEach(pattern => {
        apiCache.invalidate(pattern);
      });
    }
    
    return response.data;
  },

  delete: async <T>(url: string, config?: AxiosRequestConfig & { invalidateUrlPatterns?: string[] }): Promise<ApiResponse<T>> => {
    const response = await apiClient.delete(url, config);
    
    // Invalidate related cache entries when mutating data
    if (config?.invalidateUrlPatterns) {
      config.invalidateUrlPatterns.forEach(pattern => {
        apiCache.invalidate(pattern);
      });
    }
    
    return response.data;
  },
  
  // Method to manually clear cache
  clearCache: () => {
    apiCache.clear();
  },
  
  // Method to invalidate specific cache entries
  invalidateCache: (pattern: string) => {
    apiCache.invalidate(pattern);
  },

  // Onboarding-specific methods
  onboarding: {
    // Create sample trip for onboarding
    createSampleTrip: async (template: 'weekend_getaway' | 'family_vacation' | 'adventure_trip') => {
      return apiService.post<any>(`/api/trips/sample?template=${template}`);
    },

    // Track onboarding analytics
    trackAnalytics: async (data: {
      sessionId: string;
      userId?: string;
      step: string;
      timestamp: number;
      metadata?: any;
    }) => {
      return apiService.post<any>('/api/analytics/onboarding', data);
    },

    // Track onboarding completion
    trackCompletion: async (data: {
      sessionId: string;
      userId?: string;
      completionTime: number;
      tripType: string;
      totalDuration: number;
    }) => {
      return apiService.post<any>('/api/analytics/onboarding/complete', data);
    },

    // Track onboarding drop-off
    trackDropOff: async (data: {
      sessionId: string;
      userId?: string;
      dropOffStep: string;
      timestamp: number;
      reason?: string;
    }) => {
      return apiService.post<any>('/api/analytics/onboarding/drop-off', data);
    }
  }
};

// Upload files
export const uploadFile = async (file: File, endpoint: string): Promise<ApiResponse<any>> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post(endpoint, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export default apiService;