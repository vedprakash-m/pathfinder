import React, { useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { setTokenGetter } from '@/services/api';

interface Auth0ApiProviderProps {
  children: React.ReactNode;
}

export const Auth0ApiProvider: React.FC<Auth0ApiProviderProps> = ({ children }) => {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  useEffect(() => {
    if (isAuthenticated) {
      // Set up the token getter for the API service
      setTokenGetter(async () => {
        try {
          const token = await getAccessTokenSilently({
            authorizationParams: {
              audience: 'https://pathfinder-api.com',
              scope: 'openid profile email'
            }
          });
          return token;
        } catch (error) {
          console.error('Failed to get access token:', error);
          throw error;
        }
      });
    }
  }, [isAuthenticated, getAccessTokenSilently]);

  return <>{children}</>;
}; 