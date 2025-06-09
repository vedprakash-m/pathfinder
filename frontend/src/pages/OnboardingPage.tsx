import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import OnboardingFlow, { TripType } from '../components/onboarding/OnboardingFlow';
import { useOnboarding } from '../hooks/useOnboarding';

const OnboardingPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth0();
  const { completeOnboarding, onboardingStatus, isLoading, error, retryCheckStatus } = useOnboarding();
  const [isCompleting, setIsCompleting] = useState(false);
  const [completionError, setCompletionError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    if (onboardingStatus?.completed) {
      navigate('/dashboard');
      return;
    }
  }, [isAuthenticated, onboardingStatus, navigate]);

  const handleOnboardingComplete = async (data: { tripType: TripType; completionTime: number }) => {
    try {
      setIsCompleting(true);
      setCompletionError(null);
      
      await completeOnboarding({
        trip_type: data.tripType,
        completion_time: data.completionTime
      });
      
      // Redirect to dashboard after a short delay
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
    } catch (error: any) {
      console.error('Failed to complete onboarding:', error);
      setCompletionError(error.message || 'Failed to complete onboarding. Please try again.');
    } finally {
      setIsCompleting(false);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Setting up your experience...</p>
        </div>
      </div>
    );
  }

  // Error state with retry option
  if (error && !onboardingStatus) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center p-6 bg-white rounded-lg shadow-lg">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={retryCheckStatus}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Completion error state
  if (completionError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center p-6 bg-white rounded-lg shadow-lg">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Oops! Something went wrong</h2>
          <p className="text-gray-600 mb-4">{completionError}</p>
          <div className="space-y-2">
            <button
              onClick={() => setCompletionError(null)}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Skip for Now
            </button>
          </div>
        </div>
      </div>
    );
  }
  // Main onboarding flow
  return (
    <div className="relative">
      {isCompleting && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg text-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-700">Completing your setup...</p>
          </div>
        </div>
      )}
      <OnboardingFlow onComplete={handleOnboardingComplete} />
    </div>
  );
};

export default OnboardingPage;
