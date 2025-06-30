import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useOnboarding } from '../hooks/useOnboarding';
import { Card, Button } from '@fluentui/react-components';
import { Link } from 'react-router-dom';

export const DebugPage: React.FC = () => {
  const { 
    isAuthenticated, 
    isLoading: authLoading, 
    user, 
    error: authError,
    getAccessToken 
  } = useAuth();
  
  const { 
    onboardingStatus, 
    isLoading: onboardingLoading, 
    error: onboardingError, 
    needsOnboarding,
    checkOnboardingStatus 
  } = useOnboarding();

  const testAPICall = async () => {
    try {
      const token = await getAccessToken();
      console.log('Token:', token ? token.substring(0, 20) + '...' : 'No token');
      
      const response = await fetch('https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/api/v1/auth/user/onboarding-status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.text();
      console.log('API Response:', response.status, data);
    } catch (error) {
      console.error('API Test Error:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">Authentication Debug</h1>
        
        {/* Authentication Status */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Authentication Status</h2>
          <div className="space-y-2">
            <p><strong>Loading:</strong> {authLoading ? 'Yes' : 'No'}</p>
            <p><strong>Authenticated:</strong> {isAuthenticated ? 'Yes' : 'No'}</p>
            <p><strong>User Email:</strong> {user?.email || 'Not available'}</p>
            <p><strong>User ID:</strong> {user?.id || 'Not available'}</p>
            <p><strong>Error:</strong> {authError || 'None'}</p>
          </div>
        </Card>

        {/* Onboarding Status */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Onboarding Status</h2>
          <div className="space-y-2">
            <p><strong>Loading:</strong> {onboardingLoading ? 'Yes' : 'No'}</p>
            <p><strong>Needs Onboarding:</strong> {needsOnboarding ? 'Yes' : 'No'}</p>
            <p><strong>Completed:</strong> {onboardingStatus?.completed ? 'Yes' : 'No'}</p>
            <p><strong>Completed At:</strong> {onboardingStatus?.completed_at || 'Not completed'}</p>
            <p><strong>Trip Type:</strong> {onboardingStatus?.trip_type || 'Not set'}</p>
            <p><strong>Error:</strong> {onboardingError || 'None'}</p>
          </div>
          <div className="mt-4 space-x-2">
            <Button onClick={() => checkOnboardingStatus()}>Retry Check</Button>
            <Button onClick={testAPICall}>Test API Call</Button>
          </div>
        </Card>

        {/* Navigation */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Navigation</h2>
          <div className="space-x-2">
            <Link to="/login"><Button>Login</Button></Link>
            <Link to="/dashboard"><Button>Dashboard</Button></Link>
            <Link to="/onboarding"><Button>Onboarding</Button></Link>
            <Link to="/"><Button>Home</Button></Link>
          </div>
        </Card>

        {/* Current URL */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Current State</h2>
          <div className="space-y-2">
            <p><strong>Current URL:</strong> {window.location.href}</p>
            <p><strong>Pathname:</strong> {window.location.pathname}</p>
            <p><strong>Search:</strong> {window.location.search}</p>
            <p><strong>Hash:</strong> {window.location.hash}</p>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default DebugPage;
