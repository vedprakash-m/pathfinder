/**
 * Unauthorized access page - shown when users don't have required role permissions
 * Part of UX Implementation Plan Phase 1 - Role System Alignment
 */

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldXIcon, HomeIcon, ArrowLeftIcon } from 'lucide-react';
import { useRolePermissions } from '@/components/auth/RoleBasedRoute';
import { UserRole } from '@/types';

export const UnauthorizedPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, hasRole } = useRolePermissions();

  const getRoleDisplayName = (role: UserRole): string => {
    switch (role) {
      case UserRole.SUPER_ADMIN:
        return 'Super Administrator';
      case UserRole.FAMILY_ADMIN:
        return 'Family Administrator';
      case UserRole.TRIP_ORGANIZER:
        return 'Trip Organizer';
      case UserRole.FAMILY_MEMBER:
        return 'Family Member';
      default:
        return 'Unknown Role';
    }
  };

  const getRecommendedActions = () => {
    if (!user) return [];

    const actions = [];

    if (hasRole(UserRole.FAMILY_MEMBER)) {
      actions.push({
        title: 'Contact Your Family Admin',
        description: 'Ask your Family Admin to perform this action or grant additional permissions.',
        icon: '👥'
      });
    }

    if (hasRole(UserRole.FAMILY_ADMIN)) {
      actions.push({
        title: 'Create a Trip',
        description: 'Become a Trip Organizer by creating your own trip.',
        icon: '✈️',
        link: '/trips/new'
      });
    }

    actions.push({
      title: 'Return to Dashboard',
      description: 'Go back to your dashboard to access features available to your role.',
      icon: '🏠',
      link: '/dashboard'
    });

    return actions;
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <ShieldXIcon className="h-16 w-16 text-red-500" />
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Access Denied
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          You don't have permission to access this page
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="space-y-6">
            {/* Current Role Display */}
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {user?.name?.charAt(0) || 'U'}
                    </span>
                  </div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-blue-800">
                    Your current role
                  </p>
                  <p className="text-sm text-blue-600">
                    {user ? getRoleDisplayName(user.role) : 'Not authenticated'}
                  </p>
                </div>
              </div>
            </div>

            {/* Recommended Actions */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900">
                What can you do?
              </h3>
              
              {getRecommendedActions().map((action, index) => (
                <div key={index} className="border border-gray-200 rounded-md p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start space-x-3">
                    <span className="text-2xl">{action.icon}</span>
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-gray-900">
                        {action.title}
                      </h4>
                      <p className="text-sm text-gray-600 mt-1">
                        {action.description}
                      </p>
                      {action.link && (
                        <Link
                          to={action.link}
                          className="inline-flex items-center text-sm text-blue-600 hover:text-blue-500 mt-2"
                        >
                          Go there
                          <ArrowLeftIcon className="ml-1 h-4 w-4 transform rotate-180" />
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Navigation Options */}
            <div className="flex space-x-4">
              <button
                onClick={() => navigate(-1)}
                className="flex-1 flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <ArrowLeftIcon className="h-4 w-4 mr-2" />
                Go Back
              </button>
              <Link
                to="/dashboard"
                className="flex-1 flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <HomeIcon className="h-4 w-4 mr-2" />
                Dashboard
              </Link>
            </div>

            {/* Help Text */}
            <div className="text-center">
              <p className="text-xs text-gray-500">
                If you believe you should have access to this page, please contact your Family Admin or{' '}
                <a href="mailto:support@pathfinder.com" className="text-blue-600 hover:text-blue-500">
                  contact support
                </a>
                .
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
