/**
 * Auth Integration Service - Microsoft Entra ID Integration
 * Handles the integration between Entra ID authentication and backend user management
 * Aligned with Vedprakash Domain Authentication Standards
 */

import { UserCreate, UserRole, UserProfile } from '@/types';
import { apiService } from './api';

export interface UserInfo {
  id: string;
  name?: string;
  email: string;
  picture?: string;
  phone_number?: string;
  email_verified?: boolean;
  familyName?: string;
  givenName?: string;
  // Entra ID specific fields
  entra_id?: string;
  preferred_username?: string;
}

export class AuthIntegrationService {
  /**
   * Process user login and sync with backend
   * This handles the auto-family creation workflow for new users
   */
  static async processUserLogin(user: UserInfo): Promise<UserProfile | null> {
    try {
      console.log('🔄 Processing Entra ID user login for:', user.email);

      // First, try to get existing user from backend
      try {
        const currentUserResponse = await apiService.get<UserProfile>('/auth/me');
        if (currentUserResponse.data) {
          console.log('✅ Existing user found in backend:', currentUserResponse.data.email);
          return currentUserResponse.data;
        }
      } catch (error) {
        console.log('🔄 User not found in backend, proceeding with registration...');
      }

      // User doesn't exist in backend, create new user with auto-family creation
      console.log('🆕 Creating new user in backend with auto-family creation...');

      const newUserData: UserCreate = {
        email: user.email,
        name: user.name || `${user.givenName || ''} ${user.familyName || ''}`.trim() || user.email.split('@')[0],
        entra_id: user.entra_id || user.id,
        picture: user.picture,
        phone: user.phone_number,
        preferences: {},
      };

      // Register user - this triggers auto-family creation in backend
      const registerResponse = await apiService.post<UserProfile>('/auth/register', newUserData);

      if (!registerResponse.data) {
        throw new Error('Failed to register user in backend');
      }

      console.log('✅ User registered with auto-family creation:', registerResponse.data.email);

      // Now get the full user profile with family information
      const userProfileResponse = await apiService.get<UserProfile>('/auth/me');

      if (userProfileResponse.data) {
        console.log('✅ User profile retrieved with family data');
        return userProfileResponse.data;
      }

      throw new Error('Failed to retrieve user profile after registration');

    } catch (error) {
      console.error('❌ Entra ID login processing failed:', error);
      return null;
    }
  }

  /**
   * Verify user role and permissions with backend
   */
  static async verifyUserRole(): Promise<UserRole | null> {
    try {
      const response = await apiService.get<UserProfile>('/auth/me');
      return response.data?.role || null;
    } catch (error) {
      console.error('Failed to verify user role:', error);
      return null;
    }
  }

  /**
   * Test auto-family creation workflow
   */
  static async testAutoFamilyCreation(): Promise<boolean> {
    try {
      console.log('🧪 Testing auto-family creation workflow...');

      // Get current user
      const userResponse = await apiService.get<UserProfile>('/auth/me');
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
      user.families.forEach((family: { name: string; role: string }) => {
        console.log(`  - ${family.name} (Role: ${family.role})`);
      });

      return true;
    } catch (error) {
      console.error('❌ Auto-family creation test failed:', error);
      return false;
    }
  }

  /**
   * Handle user logout and cleanup
   */
  static async handleLogout(): Promise<void> {
    try {
      console.log('🔄 Processing user logout...');
      await apiService.post<void>('/auth/logout', {});
      console.log('✅ User logout processed successfully');
    } catch (error) {
      console.error('❌ Logout processing failed:', error);
      throw error;
    }
  }
}

export default AuthIntegrationService;
