// Simple AuthContext for the onboarding system
// This provides compatibility with the existing Auth0 setup

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

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
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user: auth0User, isAuthenticated, isLoading: auth0Loading } = useAuth0();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated && auth0User) {
      // Transform Auth0 user to our User interface
      setUser({
        id: auth0User.sub || '',
        email: auth0User.email || '',
        name: auth0User.name || '',
        picture: auth0User.picture,
      });
    } else {
      setUser(null);
    }
  }, [isAuthenticated, auth0User]);

  const contextValue: AuthContextType = {
    user,
    isAuthenticated,
    isLoading: auth0Loading,
    error,
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
