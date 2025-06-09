import React from 'react';
import { motion } from 'framer-motion';
import {
  CalendarIcon,
  ClockIcon,
  MapPinIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CurrencyDollarIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { format, addDays, differenceInDays } from 'date-fns';
import { RoleGuard, useRolePermissions, UserRole } from '../auth/RoleBasedRoute';

interface ItineraryActivity {
  id: string;
  title: string;
  description: string;
  location: string;
  start_time: string;
  end_time: string;
  category: 'activity' | 'meal' | 'transportation' | 'accommodation' | 'other';
  estimated_cost: number;
  notes?: string;
  is_confirmed: boolean;
  suggested_by?: string;
}

interface ItineraryDay {
  date: string;
  activities: ItineraryActivity[];
}

interface TripItineraryProps {
  tripId: string;
  startDate: string;
  endDate: string;
  itinerary: ItineraryDay[];
  onAddActivity: (dayDate: string, activity: Omit<ItineraryActivity, 'id'>) => void;
  onUpdateActivity: (activityId: string, updates: Partial<ItineraryActivity>) => void;
  onDeleteActivity: (activityId: string) => void;
  onGenerateItinerary: () => void;
}

const getCategoryColor = (category: string): string => {
  const colors = {
    activity: 'bg-blue-100 text-blue-800',
    meal: 'bg-orange-100 text-orange-800',
    transportation: 'bg-green-100 text-green-800',
    accommodation: 'bg-purple-100 text-purple-800',
    other: 'bg-gray-100 text-gray-800',
  };
  return colors[category as keyof typeof colors] || colors.other;
};

const ActivityCard: React.FC<{
  activity: ItineraryActivity;
  onEdit: () => void;
  onDelete: () => void;
}> = ({ activity, onEdit, onDelete }) => {
  const { canManageTrips } = useRolePermissions();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
    >
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(activity.category)} capitalize`}>
                {activity.category}
              </span>
              {activity.suggested_by && (
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  Suggested
                </span>
              )}
            </div>
            <h4 className="text-lg font-semibold text-gray-900 mb-1">{activity.title}</h4>
            <div className="flex items-center gap-4 text-gray-600 mb-2">
              <div className="flex items-center gap-1">
                <ClockIcon className="w-4 h-4" />
                <span className="text-sm">
                  {activity.start_time} - {activity.end_time}
                </span>
              </div>
              {activity.location && (
                <div className="flex items-center gap-1">
                  <MapPinIcon className="w-4 h-4" />
                  <span className="text-sm">{activity.location}</span>
                </div>
              )}
              {activity.estimated_cost > 0 && (
                <div className="flex items-center gap-1">
                  <CurrencyDollarIcon className="w-4 h-4" />
                  <span className="text-sm">${activity.estimated_cost.toFixed(2)}</span>
                </div>
              )}
            </div>
            {activity.description && (
              <p className="text-sm text-gray-600 mb-2">{activity.description}</p>
            )}
            {activity.notes && (
              <p className="text-xs text-gray-500 italic">{activity.notes}</p>
            )}
            {activity.suggested_by && (
              <p className="text-xs text-gray-500">Suggested by {activity.suggested_by}</p>
            )}
          </div>
          <RoleGuard allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}>
            <div className="flex items-center gap-2 ml-4">
              {canManageTrips() && (
                <>
                  <button
                    onClick={onEdit}
                    className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                    title="Edit activity"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={onDelete}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                    title="Delete activity"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </>
              )}
            </div>
          </RoleGuard>
        </div>
      </div>
    </motion.div>
  );
};

const TripItinerary: React.FC<TripItineraryProps> = ({
  startDate,
  endDate,
  itinerary,
  onAddActivity,
  onDeleteActivity,
  onGenerateItinerary,
}) => {
  const { canManageTrips } = useRolePermissions();
  
  const days = [];
  const start = new Date(startDate);
  const end = new Date(endDate);
  const totalDays = differenceInDays(end, start) + 1;

  for (let i = 0; i < totalDays; i++) {
    const dayDate = format(addDays(start, i), 'yyyy-MM-dd');
    const existingDay = itinerary.find((day: ItineraryDay) => day.date === dayDate);
    days.push(existingDay || { date: dayDate, activities: [] });
  }

  if (itinerary.length === 0) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Trip Itinerary</h2>
              <p className="text-gray-600 mt-1">
                Plan your activities for {format(new Date(startDate), 'MMM d')} - {format(new Date(endDate), 'MMM d, yyyy')}
              </p>
            </div>
            <RoleGuard allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}>
              {canManageTrips() && (
                <button
                  onClick={onGenerateItinerary}
                  className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all"
                >
                  <SparklesIcon className="w-5 h-5" />
                  Generate AI Itinerary
                </button>
              )}
            </RoleGuard>
          </div>
        </div>

        <div className="text-center py-12 bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="w-24 h-24 bg-blue-50 rounded-full mx-auto mb-6 flex items-center justify-center">
            <CalendarIcon className="w-12 h-12 text-blue-600" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Itinerary Yet</h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Start planning your trip by generating an AI-powered itinerary or manually adding activities for each day.
          </p>
          <RoleGuard allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}>
            <div className="flex gap-4 justify-center">
              {canManageTrips() && (
                <button
                  onClick={onGenerateItinerary}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all"
                >
                  <SparklesIcon className="w-5 h-5 inline mr-2" />
                  Generate with AI
                </button>
              )}
            </div>
          </RoleGuard>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Trip Itinerary</h2>
            <p className="text-gray-600 mt-1">
              {format(new Date(startDate), 'MMM d')} - {format(new Date(endDate), 'MMM d, yyyy')} • {totalDays} days
            </p>
          </div>
          <RoleGuard allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}>
            {canManageTrips() && (
              <button
                onClick={onGenerateItinerary}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all"
              >
                <SparklesIcon className="w-5 h-5" />
                Regenerate Itinerary
              </button>
            )}
          </RoleGuard>
        </div>
      </div>

      <div className="space-y-6">
        {days.map((day: ItineraryDay) => (
          <div key={day.date} className="bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="bg-gray-50 rounded-t-lg px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {format(new Date(day.date), 'EEEE, MMMM d, yyyy')}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {day.activities.length} activities planned
                  </p>
                </div>
                <RoleGuard allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}>
                  {canManageTrips() && (
                    <button
                      onClick={() => onAddActivity(day.date, {
                        title: 'New Activity',
                        description: '',
                        location: '',
                        start_time: '09:00',
                        end_time: '10:00',
                        category: 'activity',
                        estimated_cost: 0,
                        is_confirmed: false,
                      })}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <PlusIcon className="w-4 h-4" />
                      Add Activity
                    </button>
                  )}
                </RoleGuard>
              </div>
            </div>

            <div className="p-6">
              {day.activities.length === 0 ? (
                <div className="text-center py-8 border-2 border-dashed border-gray-200 rounded-lg">
                  <p className="text-gray-500 text-sm">No activities planned for this day</p>
                  <p className="text-gray-400 text-xs">Add your first activity to get started</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {day.activities
                    .sort((a, b) => new Date(`2000-01-01T${a.start_time}`).getTime() - new Date(`2000-01-01T${b.start_time}`).getTime())
                    .map((activity) => (
                      <ActivityCard
                        key={activity.id}
                        activity={activity}
                        onEdit={() => {}}
                        onDelete={() => onDeleteActivity(activity.id)}
                      />
                    ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TripItinerary;
