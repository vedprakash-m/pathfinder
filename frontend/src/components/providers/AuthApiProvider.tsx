import React, { useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { setTokenGetter } from '@/services/api';

interface AuthApiProviderProps {
  children: React.ReactNode;
}

export const AuthApiProvider: React.FC<AuthApiProviderProps> = ({ children }) => {
  const { getAccessToken, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    // Always set up the token getter, but handle different states
    setTokenGetter(async () => {
      // If not authenticated, throw an error
      if (!isAuthenticated) {
        throw new Error('User not authenticated');
      }

      try {
        const token = await getAccessToken();
        console.log('🎫 Got access token:', token ? token.substring(0, 20) + '...' : 'No token');
        if (!token) {
          throw new Error('No access token available');
        }
        return token;
      } catch (error) {
        console.error('❌ Failed to get access token:', error);
        throw error;
      }
    });
  }, [isAuthenticated, isLoading, getAccessToken]);

  return <>{children}</>;
}; 