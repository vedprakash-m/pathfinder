import React, { Suspense } from 'react';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// Fallback component to show while routes are loading
const RouteLoadingFallback = () => (
  <div className="min-h-screen flex items-center justify-center bg-white">
    <LoadingSpinner size="large" />
  </div>
);

/**
 * Creates a lazily-loaded route component with a loading indicator
 * @param importFunc - Dynamic import function for the route component
 * @returns Lazily loaded route component with suspense
 */
export const lazyRoute = (importFunc: () => Promise<{ default: React.ComponentType<any> }>) => {
  const LazyComponent = React.lazy(importFunc);
  
  return (props: any) => (
    <Suspense fallback={<RouteLoadingFallback />}>
      <LazyComponent {...props} />
    </Suspense>
  );
};

// Pre-defined lazy route components
export const LazyDashboard = lazyRoute(() => import('@/pages/DashboardPage'));
export const LazyTrips = lazyRoute(() => import('@/pages/TripsPage'));
export const LazyCreateTrip = lazyRoute(() => import('@/pages/CreateTripPage'));
export const LazyTripDetail = lazyRoute(() => import('@/pages/TripDetailPage'));
export const LazyFamilies = lazyRoute(() => import('@/pages/FamiliesPage'));
export const LazyProfile = lazyRoute(() => import('@/pages/ProfilePage'));
export const LazySettings = lazyRoute(() => import('@/pages/SettingsPage'));
export const LazyNotifications = lazyRoute(() => import('@/pages/NotificationsPage'));

// Prefetch route to improve perceived performance for likely navigation targets
export const prefetchRoute = (importFunc: () => Promise<any>) => {
  // This will start loading the component in the background
  importFunc();
};
