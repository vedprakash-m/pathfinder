import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, Title3, Body2 } from '@fluentui/react-components';

export const AuthDebug: React.FC = () => {
  const { isLoading, isAuthenticated, error, user } = useAuth();

  return (
    <Card className="p-4 mb-4 bg-neutral-50">
      <Title3 className="mb-2">🔧 Auth Debug Info</Title3>
      
      <div className="space-y-2">
        <Body2>
          <strong>Loading:</strong> {isLoading ? 'Yes' : 'No'}
        </Body2>
        
        <Body2>
          <strong>Authenticated:</strong> {isAuthenticated ? 'Yes' : 'No'}
        </Body2>
        
        <Body2>
          <strong>Tenant ID:</strong> {import.meta.env.VITE_AZURE_TENANT_ID || 'vedprakash.onmicrosoft.com'}
        </Body2>
        
        <Body2>
          <strong>Client ID:</strong> {(import.meta.env.VITE_AZURE_CLIENT_ID || 'your-client-id').substring(0, 8)}...
        </Body2>
        
        <Body2>
          <strong>Redirect URI:</strong> {window.location.origin}
        </Body2>
        
        <Body2>
          <strong>Current URL:</strong> {window.location.href}
        </Body2>
        
        {error && (
          <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded">
            <Body2 className="text-red-700">
              <strong>Error:</strong> {error}
            </Body2>
          </div>
        )}
        
        {user && (
          <div className="mt-2 p-2 bg-green-100 border border-green-300 rounded">
            <Body2 className="text-green-700">
              <strong>User:</strong> {user.email || user.name || 'Unknown'}
            </Body2>
          </div>
        )}
      </div>
    </Card>
  );
}; 