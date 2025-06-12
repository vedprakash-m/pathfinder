import React, { useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { setTokenGetter } from '@/services/api';

interface Auth0ApiProviderProps {
  children: React.ReactNode;
}

export const Auth0ApiProvider: React.FC<Auth0ApiProviderProps> = ({ children }) => {
  const { getAccessTokenSilently, isAuthenticated, isLoading } = useAuth0();

  useEffect(() => {
    // Always set up the token getter, but handle different states
    setTokenGetter(async () => {
      // If not authenticated, throw an error
      if (!isAuthenticated) {
        throw new Error('User not authenticated');
      }

      try {
        const token = await getAccessTokenSilently({
          authorizationParams: {
            audience: 'https://pathfinder-api.com',
            scope: 'openid profile email'
          }
        });
        console.log('🎫 Got Auth0 token:', token.substring(0, 20) + '...');
        return token;
      } catch (error) {
        console.error('❌ Failed to get Auth0 access token:', error);
        throw error;
      }
    });
  }, [isAuthenticated, isLoading, getAccessTokenSilently]);

  return <>{children}</>;
}; 