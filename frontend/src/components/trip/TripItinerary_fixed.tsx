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
  category: string;
  estimated_cost?: number;
  booking_url?: string;
  notes?: string;
}

interface DayItinerary {
  date: string;
  activities: ItineraryActivity[];
}

interface TripItineraryProps {
  startDate: string;
  endDate: string;
  itinerary: DayItinerary[];
  onAddActivity: (dayDate: string, activity: any) => void;
  onDeleteActivity: (dayDate: string, activityId: string) => void;
  onGenerateItinerary: () => void;
}

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
            <h4 className="font-medium text-gray-900 mb-1">{activity.title}</h4>
            <p className="text-sm text-gray-600 mb-2">{activity.description}</p>
          </div>
          <RoleGuard allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}>
            <div className="flex space-x-1 ml-4">
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

        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <div className="flex items-center">
            <ClockIcon className="w-4 h-4 mr-1" />
            <span>{activity.start_time} - {activity.end_time}</span>
          </div>
          <div className="flex items-center">
            <MapPinIcon className="w-4 h-4 mr-1" />
            <span>{activity.location}</span>
          </div>
          {activity.estimated_cost && (
            <div className="flex items-center">
              <CurrencyDollarIcon className="w-4 h-4 mr-1" />
              <span>${activity.estimated_cost}</span>
            </div>
          )}
        </div>

        {activity.notes && (
          <div className="mt-3 p-2 bg-gray-50 rounded text-sm text-gray-600">
            {activity.notes}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export const TripItinerary: React.FC<TripItineraryProps> = ({
  startDate,
  endDate,
  itinerary,
  onAddActivity,
  onDeleteActivity,
  onGenerateItinerary,
}) => {
  const { canManageTrips } = useRolePermissions();

  // Generate all days between start and end date
  const generateDays = () => {
    const days = [];
    const start = new Date(startDate);
    const end = new Date(endDate);
    const totalDays = differenceInDays(end, start) + 1;

    for (let i = 0; i < totalDays; i++) {
      const currentDate = addDays(start, i);
      const dateString = format(currentDate, 'yyyy-MM-dd');
      const dayItinerary = itinerary.find(day => day.date === dateString);
      
      days.push({
        date: dateString,
        displayDate: format(currentDate, 'EEEE, MMMM d'),
        activities: dayItinerary?.activities || []
      });
    }
    
    return days;
  };

  const days = generateDays();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Trip Itinerary</h2>
          <p className="text-gray-600 mt-1">
            {format(new Date(startDate), 'MMM d')} - {format(new Date(endDate), 'MMM d, yyyy')}
          </p>
        </div>
        <RoleGuard allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}>
          {canManageTrips() && (
            <button
              onClick={onGenerateItinerary}
              className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <SparklesIcon className="w-4 h-4 mr-2" />
              Generate with AI
            </button>
          )}
        </RoleGuard>
      </div>

      {/* Daily Itinerary */}
      <div className="space-y-8">
        {days.map((day, dayIndex) => (
          <div key={day.date} className="bg-gray-50 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <CalendarIcon className="w-5 h-5 text-gray-400 mr-2" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Day {dayIndex + 1} - {day.displayDate}
                </h3>
              </div>
              <RoleGuard allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}>
                {canManageTrips() && (
                  <button
                    onClick={() => onAddActivity(day.date, {})}
                    className="flex items-center px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    <PlusIcon className="w-4 h-4 mr-1" />
                    Add Activity
                  </button>
                )}
              </RoleGuard>
            </div>

            <div className="space-y-3">
              {day.activities.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CalendarIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No activities planned for this day</p>
                  <RoleGuard allowedRoles={[UserRole.FAMILY_ADMIN, UserRole.TRIP_ORGANIZER, UserRole.SUPER_ADMIN]}>
                    {canManageTrips() && (
                      <button
                        onClick={() => onAddActivity(day.date, {})}
                        className="mt-2 text-blue-600 hover:text-blue-700 text-sm"
                      >
                        Add your first activity
                      </button>
                    )}
                  </RoleGuard>
                </div>
              ) : (
                day.activities.map((activity) => (
                  <ActivityCard
                    key={activity.id}
                    activity={activity}
                    onEdit={() => {
                      // Handle edit - this would typically open a modal or form
                      console.log('Edit activity:', activity.id);
                    }}
                    onDelete={() => onDeleteActivity(day.date, activity.id)}
                  />
                ))
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
