import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserProfile, ApiError } from '@/types';

export interface AuthState {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: ApiError | null;
  
  // Actions
  setUser: (user: UserProfile) => void;
  updateProfile: (profile: Partial<UserProfile>) => void;
  setToken: (token: string) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: ApiError | null) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setUser: (user: UserProfile) => {
        set({ 
          user, 
          isAuthenticated: true,
          error: null 
        });
      },

      updateProfile: (profile: Partial<UserProfile>) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...profile } : null
        }));
      },

      setToken: (token: string) => {
        set({ token });
        localStorage.setItem('auth_token', token);
      },

      logout: () => {
        set({ 
          user: null, 
          token: null, 
          isAuthenticated: false,
          error: null 
        });
        localStorage.removeItem('auth_token');
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      setError: (error: ApiError | null) => {
        set({ error });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'pathfinder-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);