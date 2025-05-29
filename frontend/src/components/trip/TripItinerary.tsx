import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardHeader, Title2, Title3, Body1, Body2, Badge, Button, Input, Field, Textarea } from '@fluentui/react-components';
import {
  CalendarIcon,
  ClockIcon,
  MapPinIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  StarIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline';
import { format, addDays, differenceInDays } from 'date-fns';

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

const getCategoryColor = (category: string) => {
  switch (category) {
    case 'activity':
      return 'success';
    case 'meal':
      return 'warning';
    case 'transportation':
      return 'informative';
    case 'accommodation':
      return 'important';
    default:
      return 'subtle';
  }
};

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'activity':
      return <StarIcon className="w-4 h-4" />;
    case 'meal':
      return <UserGroupIcon className="w-4 h-4" />;
    case 'transportation':
      return <MapPinIcon className="w-4 h-4" />;
    case 'accommodation':
      return <ClockIcon className="w-4 h-4" />;
    default:
      return <CalendarIcon className="w-4 h-4" />;
  }
};

const ActivityCard: React.FC<{
  activity: ItineraryActivity;
  onEdit: () => void;
  onDelete: () => void;
}> = ({ activity, onEdit, onDelete }) => {
  const formatTime = (time: string) => {
    return format(new Date(time), 'h:mm a');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="mb-3 hover:shadow-md transition-shadow">
        <div className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <Badge 
                  color={getCategoryColor(activity.category)}
                  icon={getCategoryIcon(activity.category)}
                  className="capitalize"
                >
                  {activity.category}
                </Badge>
                {!activity.is_confirmed && (
                  <Badge color="warning" size="small">Suggested</Badge>
                )}
              </div>
              
              <Title3 className="text-neutral-900 mb-1">{activity.title}</Title3>
              
              <div className="flex items-center gap-4 text-neutral-600 mb-2">
                <div className="flex items-center gap-1">
                  <ClockIcon className="w-4 h-4" />
                  <Body2>
                    {formatTime(activity.start_time)} - {formatTime(activity.end_time)}
                  </Body2>
                </div>
                
                {activity.location && (
                  <div className="flex items-center gap-1">
                    <MapPinIcon className="w-4 h-4" />
                    <Body2>{activity.location}</Body2>
                  </div>
                )}
                
                {activity.estimated_cost > 0 && (
                  <div className="flex items-center gap-1">
                    <CurrencyDollarIcon className="w-4 h-4" />
                    <Body2>${activity.estimated_cost.toFixed(2)}</Body2>
                  </div>
                )}
              </div>
              
              {activity.description && (
                <Body2 className="text-neutral-600 mb-2">{activity.description}</Body2>
              )}
              
              {activity.notes && (
                <Body2 className="text-neutral-500 text-sm italic">{activity.notes}</Body2>
              )}
              
              {activity.suggested_by && (
                <Body2 className="text-neutral-500 text-sm">
                  Suggested by {activity.suggested_by}
                </Body2>
              )}
            </div>
            
            <div className="flex items-center gap-2 ml-4">
              <Button
                appearance="outline"
                size="small"
                icon={<PencilIcon className="w-3 h-3" />}
                onClick={onEdit}
              >
                Edit
              </Button>
              <Button
                appearance="outline"
                size="small"
                icon={<TrashIcon className="w-3 h-3" />}
                onClick={onDelete}
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

const DayCard: React.FC<{
  day: ItineraryDay;
  onAddActivity: (activity: Omit<ItineraryActivity, 'id'>) => void;
  onUpdateActivity: (activityId: string, updates: Partial<ItineraryActivity>) => void;
  onDeleteActivity: (activityId: string) => void;
}> = ({ day, onAddActivity, onUpdateActivity, onDeleteActivity }) => {
  const [isAddingActivity, setIsAddingActivity] = useState(false);
  const [newActivity, setNewActivity] = useState({
    title: '',
    description: '',
    location: '',
    start_time: '',
    end_time: '',
    category: 'activity' as const,
    estimated_cost: 0,
    notes: '',
    is_confirmed: true,
  });

  const dayDate = new Date(day.date);
  const totalCost = day.activities.reduce((sum, activity) => sum + activity.estimated_cost, 0);

  const handleAddActivity = () => {
    if (newActivity.title.trim() && newActivity.start_time && newActivity.end_time) {
      onAddActivity({
        ...newActivity,
        start_time: `${day.date}T${newActivity.start_time}:00`,
        end_time: `${day.date}T${newActivity.end_time}:00`,
      });
      setNewActivity({
        title: '',
        description: '',
        location: '',
        start_time: '',
        end_time: '',
        category: 'activity',
        estimated_cost: 0,
        notes: '',
        is_confirmed: true,
      });
      setIsAddingActivity(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <Title2>{format(dayDate, 'EEEE, MMMM do')}</Title2>
              <Body2 className="text-neutral-600">
                {day.activities.length} activities • ${totalCost.toFixed(2)} estimated cost
              </Body2>
            </div>
            <Button
              appearance="primary"
              size="small"
              icon={<PlusIcon className="w-4 h-4" />}
              onClick={() => setIsAddingActivity(true)}
            >
              Add Activity
            </Button>
          </div>
        </CardHeader>
        
        <div className="p-6">
          {/* Add Activity Form */}
          {isAddingActivity && (
            <Card className="mb-4 p-4 border-2 border-dashed border-primary-200">
              <Title3 className="mb-4">Add New Activity</Title3>
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <Field label="Activity Title" required>
                  <Input
                    value={newActivity.title}
                    onChange={(e) => setNewActivity({ ...newActivity, title: e.target.value })}
                    placeholder="What are you doing?"
                  />
                </Field>
                
                <Field label="Category">
                  <select
                    value={newActivity.category}
                    onChange={(e) => setNewActivity({ ...newActivity, category: e.target.value as any })}
                    className="w-full px-3 py-2 border border-neutral-300 rounded-md"
                  >
                    <option value="activity">Activity</option>
                    <option value="meal">Meal</option>
                    <option value="transportation">Transportation</option>
                    <option value="accommodation">Accommodation</option>
                    <option value="other">Other</option>
                  </select>
                </Field>
                
                <Field label="Start Time" required>
                  <Input
                    type="time"
                    value={newActivity.start_time}
                    onChange={(e) => setNewActivity({ ...newActivity, start_time: e.target.value })}
                  />
                </Field>
                
                <Field label="End Time" required>
                  <Input
                    type="time"
                    value={newActivity.end_time}
                    onChange={(e) => setNewActivity({ ...newActivity, end_time: e.target.value })}
                  />
                </Field>
                
                <Field label="Location">
                  <Input
                    value={newActivity.location}
                    onChange={(e) => setNewActivity({ ...newActivity, location: e.target.value })}
                    placeholder="Where is this happening?"
                  />
                </Field>
                
                <Field label="Estimated Cost">
                  <Input
                    type="number"
                    value={newActivity.estimated_cost.toString()}
                    onChange={(e) => setNewActivity({ ...newActivity, estimated_cost: parseFloat(e.target.value) || 0 })}
                    contentBefore={<CurrencyDollarIcon className="w-4 h-4" />}
                  />
                </Field>
              </div>
              
              <Field label="Description" className="mb-4">
                <Textarea
                  value={newActivity.description}
                  onChange={(e) => setNewActivity({ ...newActivity, description: e.target.value })}
                  placeholder="Describe the activity..."
                  rows={2}
                />
              </Field>
              
              <div className="flex gap-2">
                <Button onClick={handleAddActivity}>Add Activity</Button>
                <Button appearance="outline" onClick={() => setIsAddingActivity(false)}>Cancel</Button>
              </div>
            </Card>
          )}

          {/* Activities List */}
          <div>
            {day.activities.length === 0 ? (
              <div className="text-center py-8 border-2 border-dashed border-neutral-200 rounded-lg">
                <CalendarIcon className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
                <Body1 className="text-neutral-600 mb-2">No activities planned</Body1>
                <Body2 className="text-neutral-500">Add activities to this day</Body2>
              </div>
            ) : (
              <div className="space-y-2">
                {day.activities
                  .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
                  .map((activity) => (
                    <ActivityCard
                      key={activity.id}
                      activity={activity}
                      onEdit={() => {/* TODO: Implement edit */}}
                      onDelete={() => onDeleteActivity(activity.id)}
                    />
                  ))}
              </div>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

export const TripItinerary: React.FC<TripItineraryProps> = ({
  tripId,
  startDate,
  endDate,
  itinerary,
  onAddActivity,
  onUpdateActivity,
  onDeleteActivity,
  onGenerateItinerary,
}) => {
  const tripDays = differenceInDays(new Date(endDate), new Date(startDate)) + 1;
  
  // Create day structure
  const days: ItineraryDay[] = [];
  for (let i = 0; i < tripDays; i++) {
    const dayDate = format(addDays(new Date(startDate), i), 'yyyy-MM-dd');
    const existingDay = itinerary.find(day => day.date === dayDate);
    days.push(existingDay || { date: dayDate, activities: [] });
  }

  const totalActivities = days.reduce((sum, day) => sum + day.activities.length, 0);
  const totalCost = days.reduce((sum, day) => 
    sum + day.activities.reduce((daySum, activity) => daySum + activity.estimated_cost, 0), 0
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="space-y-6"
    >
      {/* Itinerary Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <Title2>Trip Itinerary</Title2>
              <Body2 className="text-neutral-600">
                {tripDays} days • {totalActivities} activities • ${totalCost.toFixed(2)} estimated cost
              </Body2>
            </div>
            <Button
              appearance="primary"
              icon={<StarIcon className="w-4 h-4" />}
              onClick={onGenerateItinerary}
            >
              Generate AI Itinerary
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Days */}
      {days.map((day) => (
        <DayCard
          key={day.date}
          day={day}
          onAddActivity={(activity) => onAddActivity(day.date, activity)}
          onUpdateActivity={onUpdateActivity}
          onDeleteActivity={onDeleteActivity}
        />
      ))}

      {/* Empty State */}
      {totalActivities === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-center py-12"
        >
          <div className="w-24 h-24 bg-primary-50 rounded-full mx-auto mb-6 flex items-center justify-center">
            <CalendarIcon className="w-12 h-12 text-primary-600" />
          </div>
          <Title2 className="text-neutral-900 mb-4">No itinerary yet</Title2>
          <Body1 className="text-neutral-600 mb-8 max-w-md mx-auto">
            Create a detailed itinerary for your trip or let our AI generate one for you based on your preferences.
          </Body1>
          <div className="flex gap-4 justify-center">
            <Button
              appearance="primary"
              size="large"
              icon={<StarIcon className="w-5 h-5" />}
              onClick={onGenerateItinerary}
            >
              Generate AI Itinerary
            </Button>
            <Button
              appearance="outline"
              size="large"
              icon={<PlusIcon className="w-5 h-5" />}
            >
              Add Activity Manually
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};
