import { useState, useEffect, useCallback, useContext, createContext, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '@/services/auth';
import { User, UserProfile, RegisterData } from '@/types';

// Type guard for error objects with message property
function isErrorWithMessage(error: unknown): error is { message: string } {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as { message: unknown }).message === 'string'
  );
}

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  register: (userData: RegisterData) => Promise<boolean>;
  updateProfile: (userData: Partial<User>) => Promise<boolean>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const checkAuthStatus = useCallback(async () => {
    try {
      setIsLoading(true);

      if (!authService.isAuthenticated()) {
        setUser(null);
        return;
      }

      const isTokenValid = await authService.validateToken();
      if (!isTokenValid) {
        // Token invalid, clear storage and redirect to login
        localStorage.removeItem('auth_token');
        setUser(null);
        return;
      }

      // Get user profile
      const response = await authService.getCurrentUser();
      setUser(response.data);
    } catch (error) {
      console.error('Auth status check error:', error);
      localStorage.removeItem('auth_token');
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await authService.login({ email, password });
      // Transform User to UserProfile by adding missing fields
      const userProfile: UserProfile = {
        ...response.data.user,
        families: [],
        trips_count: 0
      };
      setUser(userProfile);

      return true;
    } catch (error: unknown) {
      setError(isErrorWithMessage(error) ? error.message : 'Login failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      await authService.logout();
      setUser(null);
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterData): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      await authService.register(userData);
      return true;
    } catch (error: unknown) {
      setError(isErrorWithMessage(error) ? error.message : 'Registration failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const updateProfile = async (userData: Partial<User>): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await authService.updateProfile(userData);
      setUser(prev => prev ? { ...prev, ...response.data } : null);

      return true;
    } catch (error: unknown) {
      setError(isErrorWithMessage(error) ? error.message : 'Profile update failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        register,
        updateProfile,
        error
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default useAuth;
