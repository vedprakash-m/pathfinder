import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useOnboarding } from '../../hooks/useOnboarding';
import { LoadingSpinner } from '../ui/LoadingSpinner';

interface OnboardingGateProps {
  children: React.ReactNode;
}

const OnboardingGate: React.FC<OnboardingGateProps> = ({ children }) => {
  const { isLoading, needsOnboarding } = useOnboarding();
  const location = useLocation();

  // Don't redirect if already on onboarding page
  const isOnOnboardingPage = location.pathname === '/onboarding';

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600">Checking your profile...</p>
        </div>
      </div>
    );
  }

  // If user needs onboarding and not on onboarding page, redirect
  if (needsOnboarding && !isOnOnboardingPage) {
    return <Navigate to="/onboarding" replace />;
  }

  // If user has completed onboarding and is on onboarding page, redirect to dashboard
  if (!needsOnboarding && isOnOnboardingPage) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export default OnboardingGate;
