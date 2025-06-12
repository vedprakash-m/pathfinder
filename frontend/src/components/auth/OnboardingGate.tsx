import React, { useRef, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useOnboarding } from '../../hooks/useOnboarding';
import { LoadingSpinner } from '../ui/LoadingSpinner';

interface OnboardingGateProps {
  children: React.ReactNode;
}

const OnboardingGate: React.FC<OnboardingGateProps> = ({ children }) => {
  const { isLoading, needsOnboarding, error } = useOnboarding();
  const location = useLocation();
  const redirectCountRef = useRef(0);
  const lastPathRef = useRef(location.pathname);

  // Don't redirect if already on onboarding page
  const isOnOnboardingPage = location.pathname === '/onboarding';

  // Circuit breaker - prevent infinite redirects
  useEffect(() => {
    if (lastPathRef.current !== location.pathname) {
      redirectCountRef.current = 0; // Reset counter on navigation
    }
    lastPathRef.current = location.pathname;
  }, [location.pathname]);

  // If there are errors with onboarding status check, allow access to prevent redirect loops
  if (error && redirectCountRef.current > 2) {
    console.warn('OnboardingGate: Too many redirects detected, allowing access to prevent loop');
    return <>{children}</>;
  }

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
    redirectCountRef.current += 1;
    if (redirectCountRef.current > 3) {
      console.warn('OnboardingGate: Redirect loop detected, allowing access');
      return <>{children}</>;
    }
    return <Navigate to="/onboarding" replace />;
  }

  // If user has completed onboarding and is on onboarding page, redirect to dashboard
  if (!needsOnboarding && isOnOnboardingPage) {
    redirectCountRef.current += 1;
    if (redirectCountRef.current > 3) {
      console.warn('OnboardingGate: Redirect loop detected, staying on current page');
      return <>{children}</>;
    }
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export default OnboardingGate;
