/**
 * Auth Integration Service for Phase 2 - Backend Integration & Auto-Family Creation
 * Handles the integration between Auth0 frontend authentication and backend user management
 */

import { useAuth0 } from '@auth0/auth0-react';
import { authService } from './auth';
import { UserRole, UserProfile, UserCreate } from '@/types';
import { useAuthStore } from '@/store';

export interface Auth0UserInfo {
  sub: string;
  name?: string;
  email: string;
  picture?: string;
  phone_number?: string;
  email_verified?: boolean;
  family_name?: string;
  given_name?: string;
}

export class AuthIntegrationService {
  /**
   * Process Auth0 login and sync with backend
   * This handles the auto-family creation workflow for new users
   */
  static async processAuth0Login(auth0User: Auth0UserInfo): Promise<UserProfile | null> {
    try {
      console.log('🔄 Processing Auth0 login for:', auth0User.email);

      // First, try to get existing user from backend
      const currentUserResponse = await authService.getCurrentUser();
      
      if (currentUserResponse.data) {
        console.log('✅ Existing user found in backend:', currentUserResponse.data.email);
        return currentUserResponse.data;
      }

      // User doesn't exist in backend, create new user with auto-family creation
      console.log('🆕 Creating new user in backend with auto-family creation...');
      
      const newUserData: UserCreate = {
        email: auth0User.email,
        name: auth0User.name || `${auth0User.given_name || ''} ${auth0User.family_name || ''}`.trim() || auth0User.email.split('@')[0],
        auth0_id: auth0User.sub,
        picture: auth0User.picture,
        phone: auth0User.phone_number,
        // Additional fields that might be in UserCreate
        preferences: {},
      };

      // Register user - this triggers auto-family creation in backend
      const registerResponse = await authService.register(newUserData as any);
      
      if (!registerResponse.data) {
        throw new Error('Failed to register user in backend');
      }

      console.log('✅ User registered with auto-family creation:', registerResponse.data.email);

      // Now get the full user profile with family information
      const userProfileResponse = await authService.getCurrentUser();
      
      if (userProfileResponse.data) {
        console.log('✅ User profile retrieved with family data');
        return userProfileResponse.data;
      }

      throw new Error('Failed to retrieve user profile after registration');

    } catch (error) {
      console.error('❌ Auth0 login processing failed:', error);
      throw error;
    }
  }

  /**
   * Verify user role and permissions with backend
   */
  static async verifyUserRole(): Promise<UserRole | null> {
    try {
      const response = await authService.getCurrentUser();
      return response.data?.role || null;
    } catch (error) {
      console.error('Failed to verify user role:', error);
      return null;
    }
  }

  /**
   * Handle Auth0 callback and complete user setup
   */
  static async handleAuth0Callback(code: string): Promise<UserProfile | null> {
    try {
      // Exchange Auth0 code for backend token and user data
      const callbackResponse = await authService.handleAuth0Callback(code);
      
      if (!callbackResponse.data) {
        throw new Error('Auth0 callback failed');
      }

      // Convert User to UserProfile by adding missing fields
      const user = callbackResponse.data.user;
      const userProfile: UserProfile = {
        ...user,
        families: [],
        trips_count: 0
      };
      
      console.log('✅ Auth0 callback processed, user:', userProfile.email);
      
      return userProfile;
    } catch (error) {
      console.error('❌ Auth0 callback handling failed:', error);
      throw error;
    }
  }

  /**
   * Test auto-family creation workflow
   */
  static async testAutoFamilyCreation(): Promise<boolean> {
    try {
      console.log('🧪 Testing auto-family creation workflow...');
      
      // Get current user
      const userResponse = await authService.getCurrentUser();
      if (!userResponse.data) {
        console.log('❌ No authenticated user found');
        return false;
      }

      const user = userResponse.data;
      console.log('✅ Current user:', user.email, 'Role:', user.role);
      
      // Check if user has Family Admin role (default for new users)
      if (user.role !== UserRole.FAMILY_ADMIN) {
        console.log('⚠️ User role is not FAMILY_ADMIN:', user.role);
        return false;
      }

      // Check if user has families (auto-created family)
      if (!user.families || user.families.length === 0) {
        console.log('❌ No families found for user - auto-family creation may have failed');
        return false;
      }

      console.log('✅ User has', user.families.length, 'family(ies):');
      user.families.forEach(family => {
        console.log(`  - ${family.name} (Role: ${family.role})`);
      });

      return true;
    } catch (error) {
      console.error('❌ Auto-family creation test failed:', error);
      return false;
    }
  }
}

/**
 * React hook for Auth0 backend integration
 */
/**
 * React hook for Auth0 backend integration
 */
export const useAuth0BackendIntegration = () => {
  const { user: auth0User, isAuthenticated } = useAuth0();
  const authStore = useAuthStore();

  const syncWithBackend = async (): Promise<UserProfile | null> => {
    if (!isAuthenticated || !auth0User) {
      return null;
    }

    try {
      // Convert Auth0 user to our Auth0UserInfo interface
      const auth0UserInfo: Auth0UserInfo = {
        sub: auth0User.sub || '',
        name: auth0User.name,
        email: auth0User.email || '',
        picture: auth0User.picture,
        phone_number: auth0User.phone_number,
        email_verified: auth0User.email_verified,
        family_name: auth0User.family_name,
        given_name: auth0User.given_name,
      };

      const userProfile = await AuthIntegrationService.processAuth0Login(auth0UserInfo);
      
      if (userProfile) {
        authStore.setUser(userProfile);
      }
      
      return userProfile;
    } catch (error) {
      console.error('Backend sync failed:', error);
      authStore.setError({ message: 'Failed to sync with backend' });
      return null;
    }
  };

  const testAutoFamilyCreation = () => {
    return AuthIntegrationService.testAutoFamilyCreation();
  };

  return {
    syncWithBackend,
    testAutoFamilyCreation,
    isAuthenticated,
    auth0User,
  };
};

export default AuthIntegrationService;
