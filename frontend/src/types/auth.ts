/**
 * Vedprakash Domain Standard User Object
 * Implements the exact interface specified in Apps_Auth_Requirement.md
 */

export interface VedUser {
  id: string;           // Entra ID subject claim (primary user identifier)
  email: string;        // User's email address
  name: string;         // Full display name
  givenName: string;    // First name
  familyName: string;   // Last name
  permissions: string[]; // App-specific permissions from JWT claims
  vedProfile: {
    profileId: string;                           // Vedprakash domain profile ID
    subscriptionTier: 'free' | 'premium' | 'enterprise';
    appsEnrolled: string[];                      // List of enrolled apps
    preferences: Record<string, any>;            // User preferences
  };
}

export interface AuthContextType {
  user: VedUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
}

export interface AuthError {
  code: 'AUTH_TOKEN_MISSING' | 'AUTH_TOKEN_INVALID' | 'AUTH_PERMISSION_DENIED';
  message: string;
}
