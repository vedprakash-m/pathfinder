import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Card,
  CardHeader,
  Button,
  Title1,
  Title2,
  Title3,
  Body1,
  Body2,
  Badge,
} from '@fluentui/react-components';
import {
  PlusIcon,
  CalendarIcon,
  MapPinIcon,
  UsersIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { tripService } from '@/services/tripService';
import { useTripStore, useAuthStore } from '@/store';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { Trip, TripStatus } from '@/types';

const StatusBadge: React.FC<{ status: TripStatus }> = ({ status }) => {
  const getStatusColor = (status: TripStatus) => {
    switch (status) {
      case 'planning':
        return 'warning';
      case 'confirmed':
        return 'success';
      case 'completed':
        return 'informative';
      case 'cancelled':
        return 'danger';
      default:
        return 'subtle';
    }
  };

  return (
    <Badge color={getStatusColor(status)} className="capitalize">
      {status}
    </Badge>
  );
};

const TripCard: React.FC<{ trip: Trip }> = ({ trip }) => {
  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getDaysUntilTrip = (startDate: string) => {
    const today = new Date();
    const tripDate = new Date(startDate);
    const diffTime = tripDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const daysUntil = getDaysUntilTrip(trip.start_date);

  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="h-full border-2 border-transparent hover:border-primary-100 transition-colors cursor-pointer">
        <Link to={`/trips/${trip.id}`} className="block">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <Title3 className="text-neutral-900 mb-1">{trip.name}</Title3>
                <div className="flex items-center gap-2 text-neutral-600 mb-2">
                  <MapPinIcon className="w-4 h-4" />
                  <Body2>{trip.destination}</Body2>
                </div>
              </div>
              <StatusBadge status={trip.status} />
            </div>
          </CardHeader>
          <div className="p-4">
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-neutral-600">
                <CalendarIcon className="w-4 h-4" />
                <Body2>
                  {formatDate(trip.start_date)} - {formatDate(trip.end_date)}
                </Body2>
              </div>
              
              <div className="flex items-center gap-2 text-neutral-600">
                <UsersIcon className="w-4 h-4" />
                <Body2>
                  {trip.confirmed_families} of {trip.family_count} families confirmed
                </Body2>
              </div>

              {daysUntil > 0 && trip.status !== 'completed' && trip.status !== 'cancelled' && (
                <div className="flex items-center gap-2 text-primary-600">
                  <ClockIcon className="w-4 h-4" />
                  <Body2 className="font-medium">
                    {daysUntil === 1 ? 'Tomorrow!' : `${daysUntil} days away`}
                  </Body2>
                </div>
              )}

              {trip.budget_total && (
                <div className="pt-2 border-t border-neutral-200">
                  <Body2 className="text-neutral-600">
                    Budget: ${trip.budget_total.toLocaleString()}
                  </Body2>
                </div>
              )}
            </div>
          </div>
        </Link>
      </Card>
    </motion.div>
  );
};

const QuickActions: React.FC = () => {
  return (
    <Card className="mb-8">
      <CardHeader>
        <Title2>Quick Actions</Title2>
      </CardHeader>
      <div className="p-4">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link to="/trips/new">
            <Button
              appearance="primary"
              size="large"
              className="w-full"
              icon={<PlusIcon className="w-5 h-5" />}
            >
              Create Trip
            </Button>
          </Link>
          <Link to="/trips">
            <Button
              appearance="outline"
              size="large"
              className="w-full"
            >
              View All Trips
            </Button>
          </Link>
          <Link to="/families">
            <Button
              appearance="outline"
              size="large"
              className="w-full"
            >
              Manage Families
            </Button>
          </Link>
          <Link to="/profile">
            <Button
              appearance="outline"
              size="large"
              className="w-full"
            >
              Profile Settings
            </Button>
          </Link>
        </div>
      </div>
    </Card>
  );
};

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const { setTrips } = useTripStore();

  const { data: tripsResponse, isLoading, error } = useQuery({
    queryKey: ['trips'],
    queryFn: () => tripService.getUserTrips(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const trips = tripsResponse?.data?.items || [];

  useEffect(() => {
    if (trips.length > 0) {
      setTrips(trips);
    }
  }, [trips, setTrips]);

  const upcomingTrips = trips.filter(trip => {
    const tripDate = new Date(trip.start_date);
    const today = new Date();
    return tripDate >= today && trip.status !== 'cancelled';
  });

  const recentTrips = trips.filter(trip => {
    const tripDate = new Date(trip.start_date);
    const today = new Date();
    return tripDate < today || trip.status === 'completed';
  }).slice(0, 4);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <Title2 className="text-error-600 mb-4">Error Loading Dashboard</Title2>
        <Body1 className="text-neutral-600 mb-6">
          We couldn't load your trips. Please try again.
        </Body1>
        <Button appearance="primary" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Title1 className="text-neutral-900 mb-2">
          Welcome back, {user?.name || 'Traveler'}!
        </Title1>
        <Body1 className="text-neutral-600">
          {trips.length === 0 
            ? "Ready to plan your first adventure?" 
            : `You have ${upcomingTrips.length} upcoming ${upcomingTrips.length === 1 ? 'trip' : 'trips'}`
          }
        </Body1>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <QuickActions />
      </motion.div>

      {/* Upcoming Trips */}
      {upcomingTrips.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="flex justify-between items-center mb-6">
            <Title2>Upcoming Trips</Title2>
            <Link to="/trips">
              <Button appearance="subtle">View All</Button>
            </Link>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {upcomingTrips.slice(0, 6).map((trip, index) => (
              <motion.div
                key={trip.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 + index * 0.1 }}
              >
                <TripCard trip={trip} />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Recent Trips */}
      {recentTrips.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <div className="flex justify-between items-center mb-6">
            <Title2>Recent Trips</Title2>
            <Link to="/trips">
              <Button appearance="subtle">View All</Button>
            </Link>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {recentTrips.map((trip, index) => (
              <motion.div
                key={trip.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.5 + index * 0.1 }}
              >
                <TripCard trip={trip} />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Empty State */}
      {trips.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-center py-12"
        >
          <div className="w-24 h-24 bg-primary-50 rounded-full mx-auto mb-6 flex items-center justify-center">
            <MapPinIcon className="w-12 h-12 text-primary-600" />
          </div>
          <Title2 className="text-neutral-900 mb-4">No trips yet</Title2>
          <Body1 className="text-neutral-600 mb-8 max-w-md mx-auto">
            Start planning your first family adventure with our AI-powered trip planner.
          </Body1>
          <Link to="/trips/new">
            <Button
              appearance="primary"
              size="large"
              icon={<PlusIcon className="w-5 h-5" />}
            >
              Plan Your First Trip
            </Button>
          </Link>
        </motion.div>
      )}
    </div>
  );
};