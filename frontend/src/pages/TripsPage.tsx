import React, { useState } from 'react';
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
  Input,
  Dropdown,
  Option,
} from '@fluentui/react-components';
import {
  PlusIcon,
  CalendarIcon,
  MapPinIcon,
  UsersIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import { tripService } from '@/services/tripService';
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

  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="h-full border-2 border-transparent hover:border-primary-100 transition-colors">
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
          <div className="p-6">
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

              {trip.budget_total && (
                <div className="pt-2 border-t border-neutral-200">
                  <Body2 className="text-neutral-600">
                    Budget: ${trip.budget_total.toLocaleString()}
                  </Body2>
                </div>
              )}

              {trip.description && (
                <div className="pt-2 border-t border-neutral-200">
                  <Body2 className="text-neutral-600 line-clamp-2">
                    {trip.description}
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

export const TripsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data: trips, isLoading, error } = useQuery({
    queryKey: ['trips'],
    queryFn: () => tripService.getUserTrips(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const tripsData = trips?.data?.items || [];
  
  const filteredTrips = tripsData.filter((trip: any) => {
    const matchesSearch = trip.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         trip.destination.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || trip.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const upcomingTrips = filteredTrips.filter((trip: any) => {
    const tripDate = new Date(trip.start_date);
    const today = new Date();
    return tripDate >= today && trip.status !== 'completed' && trip.status !== 'cancelled';
  });

  const pastTrips = filteredTrips.filter((trip: any) => {
    const tripDate = new Date(trip.start_date);
    const today = new Date();
    return tripDate < today || trip.status === 'completed';
  });

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
        <Title2 className="text-error-600 mb-4">Error Loading Trips</Title2>
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
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
      >
        <div>
          <Title1 className="text-neutral-900 mb-2">Your Trips</Title1>          <Body1 className="text-neutral-600">
            {tripsData?.length === 0
              ? "Start planning your first adventure"
              : `${tripsData?.length} ${tripsData?.length === 1 ? 'trip' : 'trips'} total`
            }
          </Body1>
        </div>
        <Link to="/trips/new">
          <Button
            appearance="primary"
            size="large"
            icon={<PlusIcon className="w-5 h-5" />}
          >
            Create Trip
          </Button>
        </Link>
      </motion.div>

      {/* Filters */}
      {tripsData && tripsData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <Card>
            <div className="p-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <Input
                    type="text"
                    placeholder="Search trips by name or destination..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    contentBefore={<MagnifyingGlassIcon className="w-4 h-4" />}
                  />
                </div>
                <div className="flex items-center gap-2">
                  <FunnelIcon className="w-4 h-4 text-neutral-600" />
                  <Dropdown
                    placeholder="Filter by status"
                    value={statusFilter}
                    onOptionSelect={(_, data) => setStatusFilter(data.optionValue || 'all')}
                  >
                    <Option value="all">All Status</Option>
                    <Option value="planning">Planning</Option>
                    <Option value="confirmed">Confirmed</Option>
                    <Option value="completed">Completed</Option>
                    <Option value="cancelled">Cancelled</Option>
                  </Dropdown>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Upcoming Trips */}
      {upcomingTrips.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Title2 className="mb-6">Upcoming Trips ({upcomingTrips.length})</Title2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {upcomingTrips.map((trip, index) => (
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

      {/* Past Trips */}
      {pastTrips.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <Title2 className="mb-6">Past Trips ({pastTrips.length})</Title2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {pastTrips.map((trip, index) => (
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
      {filteredTrips.length === 0 && tripsData && tripsData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-center py-12"
        >
          <Title2 className="text-neutral-900 mb-4">No trips found</Title2>
          <Body1 className="text-neutral-600 mb-6">
            Try adjusting your search or filters to find what you're looking for.
          </Body1>
          <Button 
            appearance="outline" 
            onClick={() => {
              setSearchTerm('');
              setStatusFilter('all');
            }}
          >
            Clear Filters
          </Button>
        </motion.div>
      )}

      {/* No Trips Empty State */}
      {tripsData?.length === 0 && (
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
