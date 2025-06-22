import React, { useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/store';
import { useAuth } from '@/contexts/AuthContext';

// Layout Components
import { MainLayout } from '@/components/layout/MainLayout';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import OnboardingGate from '@/components/auth/OnboardingGate';

// Role-based routing components (UX Implementation Plan Phase 1)
import { RoleBasedRoute, UserRole } from '@/components/auth/RoleBasedRoute';

// Lazy-loaded page components
import {
  LazyDashboard,
  LazyTrips,
  LazyCreateTrip,
  LazyTripDetail,
  LazyFamilies,
  LazyProfile,
} from '@/utils/lazyRoutes';

// Only eagerly load critical pages
import { HomePage } from '@/pages/HomePage';
import { LoginPage } from '@/pages/LoginPage';
import OnboardingPage from '@/pages/OnboardingPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { UnauthorizedPage } from '@/pages/auth/UnauthorizedPage';
import DebugPage from '@/pages/DebugPage';

// Performance monitoring
import {
  initPerformanceMonitoring,
  startRouteChange,
  completeRouteChange,
} from '@/utils/performanceMonitoring';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const authStore = useAuthStore();

  if (isLoading || authStore.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <OnboardingGate>
      {children}
    </OnboardingGate>
  );
};

// Public Route Component (redirect if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// Page transition variants
const pageVariants = {
  initial: { opacity: 0, y: 20 },
  in: { opacity: 1, y: 0 },
  out: { opacity: 0, y: -20 },
};

const pageTransition = {
  type: 'tween',
  ease: 'anticipate',
  duration: 0.3,
};

function App() {
  const { isLoading } = useAuth();
  const location = useLocation();

  // Initialize performance monitoring
  useEffect(() => {
    initPerformanceMonitoring();
  }, []);

  // Track route changes
  useEffect(() => {
    completeRouteChange(location.pathname);

    return () => {
      startRouteChange();
    };
  }, [location]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600">Loading Pathfinder...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <AnimatePresence mode="wait">
        <Routes>
          {/* Public Routes */}
          <Route
            path="/"
            element={
              <PublicRoute>
                <AuthLayout>
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <HomePage />
                  </motion.div>
                </AuthLayout>
              </PublicRoute>
            }
          />
          <Route
            path="/login"
            element={
              <PublicRoute>
                <AuthLayout>
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <LoginPage />
                  </motion.div>
                </AuthLayout>
              </PublicRoute>
            }
          />

          {/* Debug Route - for troubleshooting authentication issues */}
          <Route
            path="/debug"
            element={
              <motion.div
                initial="initial"
                animate="in"
                exit="out"
                variants={pageVariants}
                transition={pageTransition}
              >
                <DebugPage />
              </motion.div>
            }
          />

          {/* Onboarding Route */}
          <Route
            path="/onboarding"
            element={
              <ProtectedRoute>
                <motion.div
                  initial="initial"
                  animate="in"
                  exit="out"
                  variants={pageVariants}
                  transition={pageTransition}
                >
                  <OnboardingPage />
                </motion.div>
              </ProtectedRoute>
            }
          />

          {/* Debug Route - Development only */}
          <Route
            path="/debug"
            element={
              <motion.div
                initial="initial"
                animate="in"
                exit="out"
                variants={pageVariants}
                transition={pageTransition}
              >
                <DebugPage />
              </motion.div>
            }
          />

          {/* Protected Routes - Using lazy-loaded components */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <LazyDashboard />
                  </motion.div>
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/trips"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <LazyTrips />
                  </motion.div>
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/trips/new"
            element={
              <RoleBasedRoute allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}>
                <MainLayout>
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <LazyCreateTrip />
                  </motion.div>
                </MainLayout>
              </RoleBasedRoute>
            }
          />
          <Route
            path="/trips/:tripId"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <LazyTripDetail />
                  </motion.div>
                </MainLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/families"
            element={
              <RoleBasedRoute allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.SUPER_ADMIN]}>
                <MainLayout>
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <LazyFamilies />
                  </motion.div>
                </MainLayout>
              </RoleBasedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <LazyProfile />
                  </motion.div>
                </MainLayout>
              </ProtectedRoute>
            }
          />

          {/* Unauthorized Route */}
          <Route
            path="/unauthorized"
            element={
              <motion.div
                initial="initial"
                animate="in"
                exit="out"
                variants={pageVariants}
                transition={pageTransition}
              >
                <UnauthorizedPage />
              </motion.div>
            }
          />

          {/* 404 Route */}
          <Route
            path="*"
            element={
              <motion.div
                initial="initial"
                animate="in"
                exit="out"
                variants={pageVariants}
                transition={pageTransition}
              >
                <NotFoundPage />
              </motion.div>
            }
          />
        </Routes>
      </AnimatePresence>
    </div>
  );
}

export default App;