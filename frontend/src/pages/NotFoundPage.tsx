import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Button,
  Title1,
  Title2,
  Body1,
  Body2,
} from '@fluentui/react-components';
import {
  HomeIcon,
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

export const NotFoundPage: React.FC = () => {
  const location = useLocation();

  const suggestions = [
    { path: '/dashboard', label: 'Dashboard', icon: HomeIcon },
    { path: '/trips', label: 'Your Trips', icon: MagnifyingGlassIcon },
    { path: '/families', label: 'Family Groups', icon: MagnifyingGlassIcon },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-2xl mx-auto"
      >
        {/* Error Icon */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="w-32 h-32 bg-gradient-to-r from-primary-600 to-secondary-600 rounded-full mx-auto mb-8 flex items-center justify-center"
        >
          <ExclamationTriangleIcon className="w-16 h-16 text-white" />
        </motion.div>

        {/* Error Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-8"
        >
          <Title1 className="text-6xl font-bold text-neutral-900 mb-4">404</Title1>
          <Title2 className="text-neutral-900 mb-4">Page Not Found</Title2>
          <Body1 className="text-neutral-600 mb-2">
            The page you're looking for doesn't exist or has been moved.
          </Body1>
          {location.pathname && (
            <Body2 className="text-neutral-500 font-mono bg-neutral-100 px-3 py-1 rounded inline-block">
              {location.pathname}
            </Body2>
          )}
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="space-y-6"
        >
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/dashboard">
              <Button
                appearance="primary"
                size="large"
                icon={<HomeIcon className="w-5 h-5" />}
              >
                Go to Dashboard
              </Button>
            </Link>
            <Button
              appearance="outline"
              size="large"
              onClick={() => window.history.back()}
            >
              Go Back
            </Button>
          </div>

          {/* Suggestions */}
          <div className="bg-white rounded-lg p-6 shadow-lg">
            <Title2 className="text-neutral-900 mb-4">Try these instead:</Title2>
            <div className="grid sm:grid-cols-3 gap-4">
              {suggestions.map((suggestion, index) => {
                const Icon = suggestion.icon;
                return (
                  <motion.div
                    key={suggestion.path}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.4 + index * 0.1 }}
                  >
                    <Link
                      to={suggestion.path}
                      className="flex flex-col items-center p-4 rounded-lg border-2 border-transparent hover:border-primary-100 transition-colors group"
                    >
                      <div className="w-12 h-12 bg-primary-50 rounded-full flex items-center justify-center mb-3 group-hover:bg-primary-100 transition-colors">
                        <Icon className="w-6 h-6 text-primary-600" />
                      </div>
                      <Body1 className="font-medium text-neutral-900 group-hover:text-primary-600 transition-colors">
                        {suggestion.label}
                      </Body1>
                    </Link>
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* Help Section */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="bg-neutral-50 rounded-lg p-6"
          >
            <Body1 className="text-neutral-700 mb-3">
              Still can't find what you're looking for?
            </Body1>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link to="/help">
                <Button appearance="outline">
                  Visit Help Center
                </Button>
              </Link>
              <Button appearance="subtle">
                Contact Support
              </Button>
            </div>
          </motion.div>
        </motion.div>
      </motion.div>
    </div>
  );
};
