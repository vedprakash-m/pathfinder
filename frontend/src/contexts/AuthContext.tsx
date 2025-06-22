// AuthContext with Microsoft Entra External ID (MSAL) authentication
// Replaces Auth0 with Microsoft's identity platform

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useMsal, useAccount, useIsAuthenticated } from '@azure/msal-react';
import { loginRequest } from '../msal-config';
import { AccountInfo } from '@azure/msal-browser';

interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { instance, accounts } = useMsal();
  const account = useAccount(accounts[0] || {});
  const isAuthenticated = useIsAuthenticated();
  
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setIsLoading(true);
        
        if (isAuthenticated && account) {
          // Transform MSAL account to our User interface
          setUser({
            id: account.localAccountId || account.homeAccountId || '',
            email: account.username || '',
            name: account.name || account.username || '',
            picture: undefined, // Can be fetched from Graph API if needed
          });
          setError(null);
        } else {
          setUser(null);
        }
      } catch (err) {
        console.error('Auth initialization error:', err);
        setError(err instanceof Error ? err.message : 'Authentication error');
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [isAuthenticated, account]);

  const login = async () => {
    try {
      setError(null);
      setIsLoading(true);
      
      const loginResponse = await instance.loginPopup(loginRequest);
      console.log('Login successful:', loginResponse);
      
      // User state will be updated via the useEffect above
    } catch (err) {
      console.error('Login error:', err);
      setError(err instanceof Error ? err.message : 'Login failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setError(null);
      setIsLoading(true);
      
      await instance.logoutPopup({
        postLogoutRedirectUri: window.location.origin,
        mainWindowRedirectUri: window.location.origin,
      });
      
      setUser(null);
    } catch (err) {
      console.error('Logout error:', err);
      setError(err instanceof Error ? err.message : 'Logout failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const getAccessToken = async (): Promise<string | null> => {
    if (!account) {
      return null;
    }

    try {
      const response = await instance.acquireTokenSilent({
        ...loginRequest,
        account: account,
      });
      
      return response.accessToken;
    } catch (err) {
      console.error('Token acquisition error:', err);
      
      // If silent token acquisition fails, try interactive
      try {
        const response = await instance.acquireTokenPopup({
          ...loginRequest,
          account: account,
        });
        return response.accessToken;
      } catch (interactiveErr) {
        console.error('Interactive token acquisition error:', interactiveErr);
        return null;
      }
    }
  };

  const contextValue: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    getAccessToken,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
