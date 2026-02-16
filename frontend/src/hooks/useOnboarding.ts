import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import apiService from '../services/api';
import { AxiosError } from 'axios';

// Type guard for axios error responses
interface ErrorResponse {
  detail?: string;
}

function isAxiosError(error: unknown): error is AxiosError<ErrorResponse> {
  return (
    typeof error === 'object' &&
    error !== null &&
    'isAxiosError' in error &&
    (error as AxiosError).isAxiosError === true
  );
}

function getErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    return error.response?.data?.detail || error.message || 'An error occurred';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An error occurred';
}

function getErrorStatus(error: unknown): number | undefined {
  if (isAxiosError(error)) {
    return error.response?.status;
  }
  return undefined;
}

function getErrorCode(error: unknown): string | undefined {
  if (isAxiosError(error)) {
    return error.code;
  }
  return undefined;
}

interface OnboardingStatus {
  completed: boolean;
  completed_at?: string | null;
  trip_type?: string | null;
}

export const useOnboarding = () => {
  const [onboardingStatus, setOnboardingStatus] = useState<OnboardingStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const { isAuthenticated } = useAuth();
  const isMountedRef = useRef(true);
  const retryTimeoutRef = useRef<NodeJS.Timeout>();

  const checkOnboardingStatus = useCallback(async (retry: boolean = false) => {
    if (!isAuthenticated || !isMountedRef.current) {
      setIsLoading(false);
      setOnboardingStatus({ completed: true }); // Default to completed if not authenticated
      return;
    }

    // Prevent infinite loops - don't retry if we've already failed 3 times
    if (retry && retryCount >= 3) {
      setIsLoading(false);
      // For authentication failures after retries, assume onboarding is completed to prevent redirect loops
      setOnboardingStatus({ completed: true });
      return;
    }

    try {
      setIsLoading(true);
      if (!retry) setError(null);

      const response = await apiService.get('/auth/user/onboarding-status');

      if (isMountedRef.current) {
        setOnboardingStatus(response.data as OnboardingStatus);
        setRetryCount(0); // Reset retry count on success
      }
    } catch (err: unknown) {
      console.error('Failed to check onboarding status:', err);

      if (!isMountedRef.current) return;

      const errorMessage = getErrorMessage(err);
      const errorStatus = getErrorStatus(err);
      const errorCode = getErrorCode(err);
      setError(errorMessage);

      // Check for authentication failures (401, 403) or credential validation errors
      const isAuthError = errorStatus === 401 ||
                         errorStatus === 403 ||
                         errorMessage.includes('Could not validate credentials') ||
                         errorMessage.includes('Not authenticated');

      // For auth errors, assume onboarding is completed to prevent redirect loops
      if (isAuthError) {
        console.warn('Authentication error detected, assuming onboarding completed to prevent redirect loop');
        setOnboardingStatus({ completed: true });
        setIsLoading(false);
        return;
      }

      // Set default values if API fails after all retries
      if (retryCount >= 3) {
        setOnboardingStatus({ completed: true }); // Changed to true to prevent redirect loops
        setIsLoading(false);
        return;
      }

      // Auto-retry up to 3 times with exponential backoff, but only for network errors
      const isNetworkError = errorCode === 'ERR_NETWORK' || errorMessage.includes('Network Error');
      const isServerError = errorStatus !== undefined && errorStatus >= 500;

      if (retryCount < 3 && isMountedRef.current && (isNetworkError || isServerError)) {
        const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
        retryTimeoutRef.current = setTimeout(() => {
          if (isMountedRef.current) {
            setRetryCount(prev => prev + 1);
            checkOnboardingStatus(true);
          }
        }, delay);
      } else {
        // Final fallback - assume onboarding completed for client errors to prevent redirect loops
        setOnboardingStatus({ completed: true });
      }
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [isAuthenticated, retryCount]);

  const retryCheckStatus = useCallback(() => {
    setRetryCount(0);
    setError(null);
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }
    checkOnboardingStatus();
  }, [checkOnboardingStatus]);

  const completeOnboarding = async (data: {
    trip_type?: string;
    completion_time?: number;
    sample_trip_id?: string;
  }) => {
    try {
      setError(null);
      await apiService.post('/auth/user/complete-onboarding', data);

      // Update local state
      if (isMountedRef.current) {
        setOnboardingStatus({
          completed: true,
          completed_at: new Date().toISOString(),
          trip_type: data.trip_type
        });
      }

      return true;
    } catch (err: unknown) {
      console.error('Failed to complete onboarding:', err);
      const errorMessage = getErrorMessage(err);
      if (isMountedRef.current) {
        setError(errorMessage);
      }
      throw new Error(errorMessage);
    }
  };

  useEffect(() => {
    isMountedRef.current = true;

    if (isAuthenticated) {
      checkOnboardingStatus();
    } else {
      setIsLoading(false);
      setOnboardingStatus(null);
    }

    return () => {
      isMountedRef.current = false;
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [isAuthenticated, checkOnboardingStatus]);

  return {
    onboardingStatus,
    isLoading,
    error,
    checkOnboardingStatus,
    completeOnboarding,
    retryCheckStatus,
    needsOnboarding: onboardingStatus && !onboardingStatus.completed
  };
};
