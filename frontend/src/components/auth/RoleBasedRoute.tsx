/**
 * Role-based routing component for UX Implementation Plan Phase 2
 * Enforces role-based access control with backend integration
 */

import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole, UserProfile } from '@/types';
import { useAuthStore } from '@/store';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { authService } from '@/services/auth';

// Re-export UserRole for convenience
export { UserRole } from '@/types';

interface RoleBasedRouteProps {
  children: React.ReactNode;
  allowedRoles: UserRole[];
  fallbackPath?: string;
}

/**
 * Role-based route wrapper that checks user roles with backend verification
 * Part of UX Implementation Plan Phase 2 - Backend Integration
 */
export const RoleBasedRoute: React.FC<RoleBasedRouteProps> = ({
  children,
  allowedRoles,
  fallbackPath = '/unauthorized'
}) => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const authStore = useAuthStore();
  const [backendUser, setBackendUser] = useState<UserProfile | null>(null);
  const [backendLoading, setBackendLoading] = useState(true);

  // Sync user data with backend when Auth0 is authenticated
  useEffect(() => {
    const syncUserWithBackend = async () => {
      if (!isAuthenticated || authLoading) {
        setBackendLoading(false);
        return;
      }

      try {
        setBackendLoading(true);

        // Use the Auth Integration Service to sync with backend
        const response = await authService.getCurrentUser();
        if (response && response.data) {
          setBackendUser(response.data);
          console.log('✅ Backend sync successful:', response.data.email, 'Role:', response.data.role);
        } else {
          console.warn('⚠️ Backend sync returned null');
        }
      } catch (error) {
        console.error('❌ Failed to sync user with backend:', error);
        authStore.logout();
      } finally {
        setBackendLoading(false);
      }
    };

    syncUserWithBackend();
  }, [isAuthenticated, authLoading, authStore]);

  // Show loading spinner while checking authentication and syncing with backend
  if (authLoading || backendLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
        <p className="ml-4 text-gray-600">Verifying permissions...</p>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Use backend user data if available, otherwise fall back to auth store
  const user = backendUser || authStore.user;

  // Check if user has required role
  if (!user || !allowedRoles.includes(user.role)) {
    console.warn(`Access denied: User role ${user?.role} not in allowed roles: ${allowedRoles.join(', ')}`);
    return <Navigate to={fallbackPath} replace />;
  }

  // User has proper role, render the protected content
  return <>{children}</>;
};

/**
 * Higher-order component for role-based route protection
 * Usage: export default withRoleProtection(MyComponent, [UserRole.FAMILY_ADMIN]);
 */
export const withRoleProtection = <P extends Record<string, unknown>>(
  WrappedComponent: React.ComponentType<P>,
  allowedRoles: UserRole[],
  fallbackPath?: string
) => {
  return (props: P) => (
    <RoleBasedRoute allowedRoles={allowedRoles} fallbackPath={fallbackPath}>
      <WrappedComponent {...props} />
    </RoleBasedRoute>
  );
};

/**
 * Hook for checking user permissions in components with backend integration
 * Returns helper functions for role-based UI rendering
 */
export const useRolePermissions = () => {
  const { isAuthenticated } = useAuth();
  const authStore = useAuthStore();
  const [backendUser, setBackendUser] = useState<UserProfile | null>(null);

  // Sync with backend user data
  useEffect(() => {
    const syncUser = async () => {
      if (!isAuthenticated) return;

      try {
        const response = await authService.getCurrentUser();
        if (response.data) {
          setBackendUser(response.data);
          // Keep auth store in sync
          authStore.setUser(response.data);
        }
      } catch (error) {
        console.error('Failed to get user data in useRolePermissions:', error);
      }
    };

    syncUser();
  }, [isAuthenticated, authStore]);

  // Use backend user data if available, otherwise fall back to auth store
  const user = backendUser || authStore.user;

  const hasRole = (role: UserRole): boolean => {
    return user?.role === role;
  };

  const hasAnyRole = (roles: UserRole[]): boolean => {
    return user ? roles.includes(user.role) : false;
  };

  const isFamilyAdmin = (): boolean => {
    return hasRole(UserRole.FAMILY_ADMIN);
  };

  const isTripOrganizer = (): boolean => {
    return hasRole(UserRole.TRIP_ORGANIZER);
  };

  const isSuperAdmin = (): boolean => {
    return hasRole(UserRole.SUPER_ADMIN);
  };

  const isFamilyMember = (): boolean => {
    return hasRole(UserRole.FAMILY_MEMBER);
  };

  // Check for combined roles (Family Admin + Trip Organizer)
  const canManageTrips = (): boolean => {
    return hasAnyRole([UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]);
  };

  const canManageFamilies = (): boolean => {
    return hasAnyRole([UserRole.FAMILY_ADMIN, UserRole.SUPER_ADMIN]);
  };

  const canAccessAdminFeatures = (): boolean => {
    return hasRole(UserRole.SUPER_ADMIN);
  };

  const getUserRoleDisplayName = (): string => {
    if (!user?.role) return 'Guest';

    switch (user.role) {
      case UserRole.SUPER_ADMIN:
        return 'Super Admin';
      case UserRole.FAMILY_ADMIN:
        return 'Family Admin';
      case UserRole.TRIP_ORGANIZER:
        return 'Trip Organizer';
      case UserRole.FAMILY_MEMBER:
        return 'Family Member';
      default:
        return 'User';
    }
  };

  return {
    user,
    hasRole,
    hasAnyRole,
    isFamilyAdmin,
    isTripOrganizer,
    isSuperAdmin,
    isFamilyMember,
    canManageTrips,
    canManageFamilies,
    canAccessAdminFeatures,
    getUserRoleDisplayName
  };
};

/**
 * Component for conditional rendering based on user roles
 * Usage: <RoleGuard allowedRoles={[UserRole.FAMILY_ADMIN]}>Content for family admins</RoleGuard>
 */
export const RoleGuard: React.FC<{
  children: React.ReactNode;
  allowedRoles: UserRole[];
  fallback?: React.ReactNode;
}> = ({ children, allowedRoles, fallback = null }) => {
  const { hasAnyRole } = useRolePermissions();

  if (!hasAnyRole(allowedRoles)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
