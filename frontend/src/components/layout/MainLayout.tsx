import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { motion } from 'framer-motion';
import {
  Button,
  Avatar,
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  Badge,
} from '@fluentui/react-components';
import {
  HomeIcon,
  MapIcon,
  UsersIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
  ShieldCheckIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';
import { RoleGuard, useRolePermissions, UserRole } from '@/components/auth/RoleBasedRoute';
import { useAuthStore } from '@/store';

interface MainLayoutProps {
  children: React.ReactNode;
}

interface NavItem {
  name: string;
  path: string;
  icon: React.ComponentType<any>;
  allowedRoles?: UserRole[];
  badge?: string;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const location = useLocation();
  const { logout } = useAuth0();
  const { user } = useAuthStore();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const { 
    canManageTrips, 
    canManageFamilies, 
    isSuperAdmin,
    getUserRoleDisplayName 
  } = useRolePermissions();

  const navigationItems: NavItem[] = [
    {
      name: 'Dashboard',
      path: '/dashboard',
      icon: HomeIcon,
    },
    {
      name: 'Trips',
      path: '/trips',
      icon: MapIcon,
    },
    {
      name: 'Families',
      path: '/families',
      icon: UsersIcon,
      allowedRoles: [UserRole.FAMILY_ADMIN, UserRole.SUPER_ADMIN],
    },
    {
      name: 'Admin',
      path: '/admin/dashboard',
      icon: ShieldCheckIcon,
      allowedRoles: [UserRole.SUPER_ADMIN],
      badge: 'Admin',
    },
  ];

  const isActiveRoute = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const handleLogout = () => {
    logout({ logoutParams: { returnTo: window.location.origin } });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo and Main Navigation */}
            <div className="flex items-center">
              <Link to="/dashboard" className="flex items-center">
                <h1 className="text-xl font-bold text-primary-600 mr-8">Pathfinder</h1>
              </Link>
              
              {/* Desktop Navigation */}
              <div className="hidden md:flex space-x-1">
                {navigationItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = isActiveRoute(item.path);
                  
                  // Check if user has permission for this nav item
                  if (item.allowedRoles && !item.allowedRoles.some(role => {
                    switch (role) {
                      case UserRole.FAMILY_ADMIN:
                        return canManageFamilies();
                      case UserRole.SUPER_ADMIN:
                        return isSuperAdmin();
                      default:
                        return true;
                    }
                  })) {
                    return null;
                  }
                  
                  return (
                    <Link
                      key={item.name}
                      to={item.path}
                      className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-primary-50 text-primary-700 border border-primary-200'
                          : 'text-gray-600 hover:text-primary-600 hover:bg-gray-50'
                      }`}
                      aria-label={`Navigate to ${item.name}`}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <Icon className="w-4 h-4 mr-2" />
                      {item.name}
                      {item.badge && (
                        <Badge size="small" color="important" className="ml-2">
                          {item.badge}
                        </Badge>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Right side - Quick Actions & User Menu */}
            <div className="flex items-center space-x-3">
              {/* Quick Create Trip Button - Role-based */}
              {canManageTrips() && (
                <RoleGuard allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}>
                  <Link to="/trips/new">
                    <Button
                      appearance="primary"
                      size="small"
                      icon={<PlusIcon className="w-4 h-4" />}
                      className="hidden sm:flex"
                    >
                      Create Trip
                    </Button>
                  </Link>
                </RoleGuard>
              )}

              {/* User Menu */}
              <Menu>
                <MenuTrigger disableButtonEnhancement>
                  <Button
                    appearance="subtle"
                    className="flex items-center space-x-2 p-2"
                  >
                    <Avatar
                      name={user?.name || 'User'}
                      size={32}
                      className="w-8 h-8"
                    />
                    <div className="hidden sm:block text-left">
                      <div className="text-sm font-medium text-gray-900">
                        {user?.name || 'User'}
                      </div>
                      <div className="text-xs text-gray-500">
                        {getUserRoleDisplayName()}
                      </div>
                    </div>
                  </Button>
                </MenuTrigger>
                
                <MenuPopover>
                  <MenuList>
                    <MenuItem icon={<UserCircleIcon className="w-4 h-4" />}>
                      <Link to="/profile" className="block w-full">
                        Profile Settings
                      </Link>
                    </MenuItem>
                    
                    {canManageFamilies() && (
                      <MenuItem icon={<UsersIcon className="w-4 h-4" />}>
                        <Link to="/families" className="block w-full">
                          Manage Families
                        </Link>
                      </MenuItem>
                    )}
                    
                    {isSuperAdmin() && (
                      <MenuItem icon={<ShieldCheckIcon className="w-4 h-4" />}>
                        <Link to="/admin/dashboard" className="block w-full">
                          Admin Dashboard
                        </Link>
                      </MenuItem>
                    )}
                    
                    <MenuItem
                      icon={<ArrowRightOnRectangleIcon className="w-4 h-4" />}
                      onClick={handleLogout}
                    >
                      Sign Out
                    </MenuItem>
                  </MenuList>
                </MenuPopover>
              </Menu>

              {/* Mobile Menu Button */}
              <Button
                appearance="subtle"
                className="md:hidden"
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                aria-label={isMobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
                aria-expanded={isMobileMenuOpen}
                aria-controls="mobile-navigation"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d={isMobileMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"}
                  />
                </svg>
              </Button>
            </div>
          </div>

          {/* Mobile Navigation */}
          {isMobileMenuOpen && (
            <motion.div
              id="mobile-navigation"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-t border-gray-200 py-2"
              role="navigation"
              aria-label="Mobile navigation menu"
            >
              <div className="px-2 pb-3 space-y-1">
                {navigationItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = isActiveRoute(item.path);
                  
                  // Check permissions for mobile nav
                  if (item.allowedRoles && !item.allowedRoles.some(role => {
                    switch (role) {
                      case UserRole.FAMILY_ADMIN:
                        return canManageFamilies();
                      case UserRole.SUPER_ADMIN:
                        return isSuperAdmin();
                      default:
                        return true;
                    }
                  })) {
                    return null;
                  }
                  
                  return (
                    <Link
                      key={item.name}
                      to={item.path}
                      className={`flex items-center px-3 py-2 rounded-md text-base font-medium ${
                        isActive
                          ? 'bg-primary-50 text-primary-700'
                          : 'text-gray-600 hover:text-primary-600 hover:bg-gray-50'
                      }`}
                      onClick={() => setIsMobileMenuOpen(false)}
                      aria-label={`Navigate to ${item.name}`}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <Icon className="w-5 h-5 mr-3" />
                      {item.name}
                      {item.badge && (
                        <Badge size="small" color="important" className="ml-2">
                          {item.badge}
                        </Badge>
                      )}
                    </Link>
                  );
                })}
                
                {/* Mobile Quick Actions */}
                {canManageTrips() && (
                  <Link
                    to="/trips/new"
                    className="flex items-center px-3 py-2 rounded-md text-base font-medium text-primary-600 hover:bg-primary-50"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <PlusIcon className="w-5 h-5 mr-3" />
                    Create Trip
                  </Link>
                )}
              </div>
            </motion.div>
          )}
        </div>
      </nav>
      
      {/* Main content */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </div>
      </main>
    </div>
  );
};
