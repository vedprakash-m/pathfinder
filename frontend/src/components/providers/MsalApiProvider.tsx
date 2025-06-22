import React, { useEffect } from 'react';
import { setTokenGetter } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

interface MsalApiProviderProps {
  children: React.ReactNode;
}

export const MsalApiProvider: React.FC<MsalApiProviderProps> = ({ children }) => {
  const { getAccessToken, isAuthenticated } = useAuth();

  useEffect(() => {
    // Set up the token getter for API calls
    setTokenGetter(async () => {
      // If not authenticated, throw an error
      if (!isAuthenticated) {
        throw new Error('User not authenticated');
      }

      try {
        const token = await getAccessToken();
        if (!token) {
          throw new Error('Failed to acquire access token');
        }
        
        console.log('🎫 Got MSAL token:', token.substring(0, 20) + '...');
        return token;
      } catch (error) {
        console.error('❌ Failed to get MSAL access token:', error);
        throw error;
      }
    });
  }, [isAuthenticated, getAccessToken]);

  return <>{children}</>;
}; 