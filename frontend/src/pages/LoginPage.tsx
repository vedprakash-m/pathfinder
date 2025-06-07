import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { motion } from 'framer-motion';
import {
  Card,
  CardHeader,
  Button,
  Title1,
  Body1,
  Body2,
  Input,
  Field,
} from '@fluentui/react-components';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useFormValidation } from '@/hooks/useFormValidation';
import { loginSchema } from '@/utils/validation';
import { Auth0Debug } from '@/components/debug/Auth0Debug';

export const LoginPage: React.FC = () => {
  const { 
    loginWithRedirect, 
    isAuthenticated, 
    isLoading, 
    error: auth0Error
  } = useAuth0();

  const [isEmailLogin, setIsEmailLogin] = useState(false);

  // Initialize form validation
  const {
    formData,
    updateFormData,
    validateAll,
    getFieldState,
    handleBlur,
    resetForm
  } = useFormValidation(loginSchema, {
    email: '',
    password: '',
  });

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateAll()) {
      return;
    }
    
    try {
      console.log('🔄 Attempting login with redirect...');
      // Use Auth0 redirect with email hint
      await loginWithRedirect({
        authorizationParams: {
          login_hint: formData.email as string,
        },
      });
    } catch (error) {
      console.error('❌ Login error:', error);
      // Show user-friendly error message
      alert(`Login failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // Toggle between login methods
  const toggleLoginMethod = () => {
    setIsEmailLogin(!isEmailLogin);
    resetForm();
  };

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  // Show loading spinner while Auth0 is initializing
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        {/* Debug info - remove in production */}
        <Auth0Debug />
        
        <Card className="shadow-2xl border-0">
          <CardHeader className="text-center pb-4">
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <div className="w-16 h-16 bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                  />
                </svg>
              </div>
              <Title1 className="text-neutral-900 mb-2">Welcome to Pathfinder</Title1>
              <Body1 className="text-neutral-600">
                Sign in to start planning your next adventure
              </Body1>
            </motion.div>
          </CardHeader>

          <div className="p-6 space-y-6">
            {auth0Error && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="p-4 bg-error-50 border border-error-200 rounded-lg"
              >
                <Body2 className="text-error-700">
                  Authentication error: {auth0Error.message}
                </Body2>
              </motion.div>
            )}

            {isEmailLogin ? (
              <form onSubmit={handleSubmit} className="space-y-4">
                <Field 
                  label="Email Address"
                  required
                  validationState={getFieldState('email').validationState}
                  validationMessage={getFieldState('email').error}
                >
                  <Input
                    type="email"
                    placeholder="Your email address"
                    value={formData.email as string}
                    onChange={(e) => updateFormData({ email: e.target.value })}
                    onBlur={() => handleBlur('email')}
                  />
                </Field>
                
                <Field 
                  label="Password"
                  required
                  validationState={getFieldState('password').validationState}
                  validationMessage={getFieldState('password').error}
                >
                  <Input
                    type="password"
                    placeholder="Your password"
                    value={formData.password as string}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateFormData({ password: e.target.value })}
                    onBlur={() => handleBlur('password')}
                  />
                </Field>

                <div className="flex justify-between mt-2">
                  <Body2 className="text-primary-600 hover:text-primary-700 cursor-pointer">
                    Forgot password?
                  </Body2>
                  <Body2 
                    className="text-primary-600 hover:text-primary-700 cursor-pointer"
                    onClick={toggleLoginMethod}
                  >
                    Use social login
                  </Body2>
                </div>

                <Button
                  appearance="primary"
                  size="large"
                  className="w-full py-3 mt-2"
                  type="submit"
                >
                  Sign In
                </Button>
              </form>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="space-y-4"
              >
                <Button
                  appearance="primary"
                  size="large"
                  className="w-full py-3"
                  onClick={async () => {
                    try {
                      console.log('🔄 Attempting social login...');
                      await loginWithRedirect();
                    } catch (error) {
                      console.error('❌ Social login error:', error);
                      alert(`Login failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
                    }
                  }}
                >
                  Sign In / Sign Up
                </Button>

                <div className="text-center">
                  <Body2 
                    className="text-primary-600 hover:text-primary-700 cursor-pointer"
                    onClick={toggleLoginMethod}
                  >
                    Use email and password instead
                  </Body2>
                </div>
              </motion.div>
            )}

            <div className="text-center">
              <Body2 className="text-neutral-500">
                By signing in, you agree to our{' '}
                <a href="#" className="text-primary-600 hover:text-primary-700">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="#" className="text-primary-600 hover:text-primary-700">
                  Privacy Policy
                </a>
              </Body2>
            </div>
          </div>
        </Card>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-8 text-center"
        >
          <Body2 className="text-neutral-600">
            New to family trip planning?{' '}
            <a href="#" className="text-primary-600 hover:text-primary-700 font-medium">
              Learn how Pathfinder works
            </a>
          </Body2>
        </motion.div>
      </motion.div>
    </div>
  );
};