import React, { useState } from 'react';
import { useParams, Link, Navigate } from 'react-router-dom';
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
import { TripChat } from '@/components/chat/TripChat';
import { TripFamilies } from '@/components/trip/TripFamilies';
import { TripBudget } from '@/components/trip/TripBudget';
// import TripItinerary from '@/components/trip/TripItinerary';

// Temporary placeholder component for TripItinerary
const TripItinerary: React.FC<any> = ({ startDate, endDate, itinerary, onAddActivity: _onAddActivity, onDeleteActivity: _onDeleteActivity, onGenerateItinerary: _onGenerateItinerary }) => (
  <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
    <h3 className="text-lg font-semibold text-gray-900 mb-4">Trip Itinerary</h3>
    <p className="text-gray-600">Itinerary component temporarily disabled for build testing</p>
    <p className="text-sm text-gray-500 mt-2">
      Period: {startDate} to {endDate} | Activities: {itinerary?.length || 0}
    </p>
  </div>
);
import { RoleGuard, useRolePermissions, UserRole } from '@/components/auth/RoleBasedRoute';
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
  const { 
    isFamilyAdmin,
    user 
  } = useRolePermissions();
  
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

  const tripData = trip.data || trip; // Handle both ApiResponse<Trip> and Trip
  const daysUntil = getDaysUntilTrip(tripData.start_date);
  
  // Check if current user is the trip organizer (creator)
  const isCurrentUserTripOrganizer = tripData.created_by === user?.id;

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
                <Title1 className="text-neutral-900">{tripData.name}</Title1>
                <StatusBadge status={tripData.status} />
                {/* Role indicator */}
                {isCurrentUserTripOrganizer && (
                  <Badge color="informative">Trip Organizer</Badge>
                )}
                {isFamilyAdmin() && !isCurrentUserTripOrganizer && (
                  <Badge color="success">Family Admin</Badge>
                )}
              </div>
              
              <div className="flex flex-wrap items-center gap-4 text-neutral-600 mb-4">
                <div className="flex items-center gap-2">
                  <MapPinIcon className="w-5 h-5" />
                  <Body1>{tripData.destination}</Body1>
                </div>
                <div className="flex items-center gap-2">
                  <CalendarIcon className="w-5 h-5" />
                  <Body1>
                    {formatDate(tripData.start_date)} - {formatDate(tripData.end_date)}
                  </Body1>
                </div>
                <div className="flex items-center gap-2">
                  <UsersIcon className="w-5 h-5" />
                  <Body1>
                    {tripData.confirmed_families} of {tripData.family_count} families
                  </Body1>
                </div>
                {tripData.budget_total && (
                  <div className="flex items-center gap-2">
                    <CurrencyDollarIcon className="w-5 h-5" />
                    <Body1>${tripData.budget_total.toLocaleString()} budget</Body1>
                  </div>
                )}
              </div>

              {daysUntil > 0 && tripData.status !== 'completed' && tripData.status !== 'cancelled' && (
                <div className="flex items-center gap-2 text-primary-600 mb-4">
                  <Body1 className="font-medium">
                    {daysUntil === 1 ? 'Trip starts tomorrow!' : `Trip starts in ${daysUntil} days`}
                  </Body1>
                </div>
              )}

              {tripData.description && (
                <Body1 className="text-neutral-600">{tripData.description}</Body1>
              )}
            </div>

            <div className="flex gap-3">
              {/* Share button - available to all participants */}
              <Button
                appearance="outline"
                icon={<ShareIcon className="w-4 h-4" />}
              >
                Share
              </Button>
              
              {/* Chat button - available to all participants */}
              <Button
                appearance="outline"
                icon={<ChatBubbleLeftRightIcon className="w-4 h-4" />}
              >
                Chat
              </Button>
              
              {/* Edit Trip - Only Trip Organizers can edit trip settings */}
              <RoleGuard 
                allowedRoles={[UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}
                fallback={
                  /* Family Admins can edit family-specific settings */
                  isFamilyAdmin() ? (
                    <Button
                      appearance="outline"
                      icon={<PencilIcon className="w-4 h-4" />}
                    >
                      Edit Family Settings
                    </Button>
                  ) : null
                }
              >
                <Button
                  appearance="primary"
                  icon={<PencilIcon className="w-4 h-4" />}
                >
                  Edit Trip
                </Button>
              </RoleGuard>
            </div>
          </div>
        </CardHeader>
      </Card>
    </motion.div>
  );
};

const TripOverview: React.FC<{ trip: any }> = ({ trip }) => {
  const tripData = trip.data || trip; // Handle both ApiResponse<Trip> and Trip
  
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
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <Body2 className="font-medium text-neutral-700">Description</Body2>
                  <Body1 className="text-neutral-600 mt-1">
                    {tripData.description || 'No description provided'}
                  </Body1>
                </div>
                
                <div>
                  <Body2 className="font-medium text-neutral-700">Duration</Body2>
                  <Body1 className="text-neutral-600 mt-1">
                    {Math.ceil((new Date(tripData.end_date).getTime() - new Date(tripData.start_date).getTime()) / (1000 * 60 * 60 * 24))} days
                  </Body1>
                </div>

                {tripData.preferences && (
                  <div>
                    <Body2 className="font-medium text-neutral-700">Preferences</Body2>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {Object.entries(tripData.preferences).map(([key, value]) => (
                        <Badge key={key} className="capitalize">
                          {key}: {String(value)}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
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
            <div className="p-6">
              <div className="text-center py-8">
                <Body1 className="text-neutral-600 mb-4">
                  No itinerary created yet
                </Body1>
                <Button appearance="primary">
                  Create Itinerary
                </Button>
              </div>
            </div>
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
            <div className="p-6">
              <div className="space-y-3">
                <div className="text-center py-4">
                  <Body1 className="text-neutral-600">
                    {tripData.confirmed_families} confirmed families
                  </Body1>
                </div>
                <Button appearance="outline" className="w-full">
                  Invite Family
                </Button>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Budget Summary */}
        {tripData.budget_total && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <Card>
              <CardHeader>
                <Title3>Budget Summary</Title3>
              </CardHeader>
              <div className="p-6">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <Body2 className="text-neutral-600">Total Budget</Body2>
                    <Body2 className="font-medium">${tripData.budget_total.toLocaleString()}</Body2>
                  </div>
                  <div className="flex justify-between items-center">
                    <Body2 className="text-neutral-600">Per Family</Body2>
                    <Body2 className="font-medium">
                      ${Math.round(tripData.budget_total / Math.max(1, tripData.family_count)).toLocaleString()}
                    </Body2>
                  </div>
                  <Button appearance="outline" className="w-full mt-4">
                    Manage Budget
                  </Button>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export const TripDetailPage: React.FC = () => {
  const { tripId } = useParams<{ tripId: string }>();
  const [activeTab, setActiveTab] = useState('overview');

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

  // Mock data for demonstration - in real app this would come from API
  const mockFamilies = [
    {
      id: '1',
      name: 'The Smith Family',
      status: 'confirmed' as const,
      members: [
        { id: '1', name: 'John Smith', email: 'john@smith.com', role: 'parent' as const },
        { id: '2', name: 'Jane Smith', email: 'jane@smith.com', role: 'parent' as const },
        { id: '3', name: 'Tommy Smith', email: '', role: 'child' as const },
      ],
      preferences: { 'dietary': 'vegetarian', 'activity_level': 'moderate' }
    },
    {
      id: '2',
      name: 'The Johnson Family',
      status: 'pending' as const,
      members: [
        { id: '4', name: 'Mike Johnson', email: 'mike@johnson.com', role: 'parent' as const },
        { id: '5', name: 'Sarah Johnson', email: 'sarah@johnson.com', role: 'parent' as const },
      ],
      preferences: { 'activity_level': 'high', 'accommodation': 'hotel' }
    }
  ];

  const mockBudgetCategories = [
    { id: '1', name: 'Transportation', allocated: 2000, spent: 1500, color: '#0088FE' },
    { id: '2', name: 'Accommodation', allocated: 3000, spent: 2800, color: '#00C49F' },
    { id: '3', name: 'Food & Dining', allocated: 1500, spent: 800, color: '#FFBB28' },
    { id: '4', name: 'Activities', allocated: 1000, spent: 200, color: '#FF8042' },
  ];

  // Access trip data correctly
  const tripData = trip.data || trip;

  const mockItinerary = [
    {
      date: tripData.start_date,
      activities: [
        {
          id: '1',
          title: 'Airport Departure',
          description: 'Flight from hometown to destination',
          location: 'Local Airport',
          start_time: `${tripData.start_date}T08:00:00`,
          end_time: `${tripData.start_date}T10:00:00`,
          category: 'transportation' as const,
          estimated_cost: 500,
          is_confirmed: true,
        }
      ]
    }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <TripOverview trip={trip} />;
      case 'itinerary':
        return (
          <TripItinerary
            tripId={tripId}
            startDate={tripData.start_date}
            endDate={tripData.end_date}
            itinerary={mockItinerary}
            onAddActivity={(dayDate: string, activity: any) => {
              console.log('Add activity:', dayDate, activity);
            }}
            onUpdateActivity={(activityId: string, updates: any) => {
              console.log('Update activity:', activityId, updates);
            }}
            onDeleteActivity={(activityId: string) => {
              console.log('Delete activity:', activityId);
            }}
            onGenerateItinerary={() => {
              console.log('Generate AI itinerary');
            }}
          />
        );
      case 'families':
        return (
          <TripFamilies
            families={mockFamilies}
            tripId={tripId}
            onInviteFamily={() => {
              console.log('Invite family');
            }}
            onManageFamily={(familyId) => {
              console.log('Manage family:', familyId);
            }}
          />
        );
      case 'budget':
        return (
          <TripBudget
            tripId={tripId}
            totalBudget={tripData.budget_total || 7500}
            categories={mockBudgetCategories}
            expenses={[]}
            families={mockFamilies}
            onUpdateBudget={(newBudget) => {
              console.log('Update budget:', newBudget);
            }}
            onAddCategory={(category) => {
              console.log('Add category:', category);
            }}
            onUpdateCategory={(categoryId, updates) => {
              console.log('Update category:', categoryId, updates);
            }}
            onDeleteCategory={(categoryId) => {
              console.log('Delete category:', categoryId);
            }}
            onAddExpense={(expense) => {
              console.log('Add expense:', expense);
            }}
          />
        );
      case 'chat':
        return (
          <TripChat
            tripId={tripId}
            tripName={tripData.name}
          />
        );
      default:
        return <TripOverview trip={trip} />;
    }
  };

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
        <Body2 className="text-neutral-900">{tripData.name || 'Trip Details'}</Body2>
      </motion.div>

      {/* Trip Header */}
      <TripHeader trip={trip} />

      {/* Tab Navigation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <Card>
          <div className="p-4">
            <TabList selectedValue={activeTab} onTabSelect={(_, data) => setActiveTab(data.value as string)}>
              <Tab value="overview">Overview</Tab>
              <Tab value="itinerary">Itinerary</Tab>
              <Tab value="families">Families</Tab>
              <Tab value="budget">Budget</Tab>
              <Tab value="chat">Chat</Tab>
            </TabList>
          </div>
        </Card>
      </motion.div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {renderTabContent()}
      </motion.div>
    </div>
  );
};
