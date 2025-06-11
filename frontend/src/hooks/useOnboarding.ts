import { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import apiService from '../services/api';

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
  const { isAuthenticated } = useAuth0();

  const checkOnboardingStatus = async (retry: boolean = false) => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      if (!retry) setError(null);
      
      const response = await apiService.get('/auth/user/onboarding-status');
      
      setOnboardingStatus(response.data as OnboardingStatus);
      setRetryCount(0); // Reset retry count on success
    } catch (err: any) {
      console.error('Failed to check onboarding status:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to check onboarding status';
      setError(errorMessage);
      
      // Set default values if API fails
      setOnboardingStatus({ completed: false });
      
      // Auto-retry up to 3 times with exponential backoff
      if (retryCount < 3) {
        const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          checkOnboardingStatus(true);
        }, delay);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const retryCheckStatus = () => {
    setRetryCount(0);
    checkOnboardingStatus();
  };

  const completeOnboarding = async (data: {
    trip_type?: string;
    completion_time?: number;
    sample_trip_id?: string;
  }) => {
    try {
      setError(null);
      await apiService.post('/auth/user/complete-onboarding', data);
      
      // Update local state
      setOnboardingStatus({
        completed: true,
        completed_at: new Date().toISOString(),
        trip_type: data.trip_type
      });
      
      return true;
    } catch (err: any) {
      console.error('Failed to complete onboarding:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to complete onboarding';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      checkOnboardingStatus();
    }
  }, [isAuthenticated]);

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
