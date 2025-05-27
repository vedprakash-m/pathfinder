import React from 'react';
import { useParams, Link, Navigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Card,
  CardHeader,
  CardContent,
  Button,
  Title1,
  Title2,
  Title3,
  Body1,
  Body2,
  Badge,
  Tab,
  TabList,
} from '@fluentui/react-components';
import {
  CalendarIcon,
  MapPinIcon,
  UsersIcon,
  CurrencyDollarIcon,
  PencilIcon,
  ShareIcon,
  ChatBubbleLeftRightIcon,
} from '@heroicons/react/24/outline';
import { tripService } from '@/services/tripService';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { TripStatus } from '@/types';

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

const TripHeader: React.FC<{ trip: any }> = ({ trip }) => {
  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <Card className="mb-8">
        <CardHeader>
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <Title1 className="text-neutral-900">{trip.name}</Title1>
                <StatusBadge status={trip.status} />
              </div>
              
              <div className="flex flex-wrap items-center gap-4 text-neutral-600 mb-4">
                <div className="flex items-center gap-2">
                  <MapPinIcon className="w-5 h-5" />
                  <Body1>{trip.destination}</Body1>
                </div>
                <div className="flex items-center gap-2">
                  <CalendarIcon className="w-5 h-5" />
                  <Body1>
                    {formatDate(trip.start_date)} - {formatDate(trip.end_date)}
                  </Body1>
                </div>
                <div className="flex items-center gap-2">
                  <UsersIcon className="w-5 h-5" />
                  <Body1>
                    {trip.confirmed_families} of {trip.family_count} families
                  </Body1>
                </div>
                {trip.budget_total && (
                  <div className="flex items-center gap-2">
                    <CurrencyDollarIcon className="w-5 h-5" />
                    <Body1>${trip.budget_total.toLocaleString()} budget</Body1>
                  </div>
                )}
              </div>

              {daysUntil > 0 && trip.status !== 'completed' && trip.status !== 'cancelled' && (
                <div className="flex items-center gap-2 text-primary-600 mb-4">
                  <Body1 className="font-medium">
                    {daysUntil === 1 ? 'Trip starts tomorrow!' : `Trip starts in ${daysUntil} days`}
                  </Body1>
                </div>
              )}

              {trip.description && (
                <Body1 className="text-neutral-600">{trip.description}</Body1>
              )}
            </div>

            <div className="flex gap-3">
              <Button
                appearance="outline"
                icon={<ShareIcon className="w-4 h-4" />}
              >
                Share
              </Button>
              <Button
                appearance="outline"
                icon={<ChatBubbleLeftRightIcon className="w-4 h-4" />}
              >
                Chat
              </Button>
              <Button
                appearance="primary"
                icon={<PencilIcon className="w-4 h-4" />}
              >
                Edit Trip
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>
    </motion.div>
  );
};

const TripOverview: React.FC<{ trip: any }> = ({ trip }) => {
  return (
    <div className="grid lg:grid-cols-3 gap-6">
      {/* Trip Details */}
      <div className="lg:col-span-2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <Card className="mb-6">
            <CardHeader>
              <Title2>Trip Details</Title2>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Body2 className="font-medium text-neutral-700">Description</Body2>
                  <Body1 className="text-neutral-600 mt-1">
                    {trip.description || 'No description provided'}
                  </Body1>
                </div>
                
                <div>
                  <Body2 className="font-medium text-neutral-700">Duration</Body2>
                  <Body1 className="text-neutral-600 mt-1">
                    {Math.ceil((new Date(trip.end_date).getTime() - new Date(trip.start_date).getTime()) / (1000 * 60 * 60 * 24))} days
                  </Body1>
                </div>

                {trip.preferences && (
                  <div>
                    <Body2 className="font-medium text-neutral-700">Preferences</Body2>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {Object.entries(trip.preferences).map(([key, value]) => (
                        <Badge key={key} className="capitalize">
                          {key}: {String(value)}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Itinerary Placeholder */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <Title2>Itinerary</Title2>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Body1 className="text-neutral-600 mb-4">
                  No itinerary created yet
                </Body1>
                <Button appearance="primary">
                  Create Itinerary
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Sidebar */}
      <div>
        {/* Participating Families */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <Card className="mb-6">
            <CardHeader>
              <Title3>Participating Families</Title3>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-center py-4">
                  <Body1 className="text-neutral-600">
                    {trip.confirmed_families} confirmed families
                  </Body1>
                </div>
                <Button appearance="outline" className="w-full">
                  Invite Family
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Budget Summary */}
        {trip.budget_total && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <Card>
              <CardHeader>
                <Title3>Budget Summary</Title3>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <Body2 className="text-neutral-600">Total Budget</Body2>
                    <Body2 className="font-medium">${trip.budget_total.toLocaleString()}</Body2>
                  </div>
                  <div className="flex justify-between items-center">
                    <Body2 className="text-neutral-600">Per Family</Body2>
                    <Body2 className="font-medium">
                      ${Math.round(trip.budget_total / Math.max(1, trip.family_count)).toLocaleString()}
                    </Body2>
                  </div>
                  <Button appearance="outline" className="w-full mt-4">
                    Manage Budget
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export const TripDetailPage: React.FC = () => {
  const { tripId } = useParams<{ tripId: string }>();

  const { data: trip, isLoading, error } = useQuery({
    queryKey: ['trip', tripId],
    queryFn: () => tripService.getTripById(tripId!),
    enabled: !!tripId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (!tripId) {
    return <Navigate to="/trips" replace />;
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error || !trip) {
    return (
      <div className="text-center py-12">
        <Title2 className="text-error-600 mb-4">Trip Not Found</Title2>
        <Body1 className="text-neutral-600 mb-6">
          The trip you're looking for doesn't exist or you don't have access to it.
        </Body1>
        <Link to="/trips">
          <Button appearance="primary">Back to Trips</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Breadcrumb */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex items-center gap-2 text-neutral-600"
      >
        <Link to="/trips" className="hover:text-primary-600">
          <Body2>Trips</Body2>
        </Link>
        <Body2>/</Body2>
        <Body2 className="text-neutral-900">{trip.name}</Body2>
      </motion.div>

      {/* Trip Header */}
      <TripHeader trip={trip} />

      {/* Tab Navigation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <TabList defaultSelectedValue="overview">
          <Tab value="overview">Overview</Tab>
          <Tab value="itinerary">Itinerary</Tab>
          <Tab value="families">Families</Tab>
          <Tab value="budget">Budget</Tab>
          <Tab value="chat">Chat</Tab>
        </TabList>
      </motion.div>

      {/* Trip Content */}
      <TripOverview trip={trip} />
    </div>
  );
};
