import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, Title3, Body2, Button } from '@fluentui/react-components';

interface DebugInfo {
  token?: string;
  apiUrl?: string;
  status?: number;
  statusText?: string;
  response?: string;
  headers?: Record<string, string>;
  error?: string;
  stack?: string;
}

export const ApiDebug: React.FC = () => {
  const { getAccessToken, isAuthenticated, user } = useAuth();
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [loading, setLoading] = useState(false);

  const testApiCall = async () => {
    setLoading(true);
    try {
      // Get the access token
      const token = await getAccessToken();

      console.log('🔐 Access Token:', token);

      // Test the API call
      const apiUrl = import.meta.env.VITE_API_URL
        ? `${import.meta.env.VITE_API_URL}/api/v1`
        : '/api/v1';

      const response = await fetch(`${apiUrl}/trips/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.text();

      setDebugInfo({
        token: token ? token.substring(0, 50) + '...' : 'No token',
        apiUrl,
        status: response.status,
        statusText: response.statusText,
        response: data,
        headers: Object.fromEntries(response.headers.entries())
      });

    } catch (error: unknown) {
      const err = error as Error;
      console.error('❌ API Test Error:', err);
      setDebugInfo({
        error: err.message || String(error),
        stack: err.stack
      });
    }
    setLoading(false);
  };

  if (!isAuthenticated) {
    return (
      <Card className="p-4 mb-4 bg-yellow-50 border border-yellow-200">
        <Title3 className="mb-2">🔧 API Debug</Title3>
        <Body2>Please login first to test API calls.</Body2>
      </Card>
    );
  }

  return (
    <Card className="p-4 mb-4 bg-blue-50 border border-blue-200">
      <Title3 className="mb-2">🔧 API Debug Info</Title3>

      <div className="space-y-2 mb-4">
        <Body2><strong>User:</strong> {user?.email}</Body2>
        <Body2><strong>Auth Status:</strong> {isAuthenticated ? 'Authenticated' : 'Not Authenticated'}</Body2>
        <Body2><strong>API URL:</strong> {import.meta.env.VITE_API_URL || 'Local (/api/v1)'}</Body2>
      </div>

      <Button
        onClick={testApiCall}
        disabled={loading}
        appearance="primary"
        className="mb-4"
      >
        {loading ? 'Testing...' : 'Test API Call'}
      </Button>

      {debugInfo && (
        <div className="mt-4 p-3 bg-white border rounded text-sm">
          <pre className="whitespace-pre-wrap overflow-auto max-h-96">
            {JSON.stringify(debugInfo, null, 2)}
          </pre>
        </div>
      )}
    </Card>
  );
};
