import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Card,
  CardHeader,
  Button,
  Title1,
  Title2,
  Body1,
  Body2,
  Input,
  Textarea,
  Dropdown,
  Option,
  Switch,
  Field,
} from '@fluentui/react-components';
// Import heroicons
import { CalendarIcon, MapIcon, UserGroupIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { tripService } from '@/services/tripService';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useFormValidation } from '@/hooks/useFormValidation';
import { createTripSchema } from '@/utils/validation';
import type { CreateTripRequest, ApiResponse, Trip } from '@/types';

const TripPreferences: React.FC<{
  preferences: any;
  onChange: (preferences: any) => void;
}> = ({ preferences, onChange }) => {
  const updatePreference = (key: string, value: any) => {
    onChange({
      ...preferences,
      [key]: value
    });
  };

  return (
    <div className="space-y-4">
      <div className="grid sm:grid-cols-2 gap-4">
        <Field label="Travel Style">
          <Dropdown
            placeholder="Select travel style"
            value={preferences.travelStyle || ''}
            onOptionSelect={(_, data) => updatePreference('travelStyle', data.optionValue)}
          >
            <Option value="luxury">Luxury</Option>
            <Option value="mid-range">Mid-range</Option>
            <Option value="budget">Budget</Option>
            <Option value="backpacking">Backpacking</Option>
          </Dropdown>
        </Field>

        <Field label="Accommodation Type">
          <Dropdown
            placeholder="Select accommodation"
            value={preferences.accommodationType || ''}
            onOptionSelect={(_, data) => updatePreference('accommodationType', data.optionValue)}
          >
            <Option value="hotel">Hotel</Option>
            <Option value="resort">Resort</Option>
            <Option value="vacation-rental">Vacation Rental</Option>
            <Option value="hostel">Hostel</Option>
            <Option value="camping">Camping</Option>
          </Dropdown>
        </Field>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <Field label="Activity Level">
          <Dropdown
            placeholder="Select activity level"
            value={preferences.activityLevel || ''}
            onOptionSelect={(_, data) => updatePreference('activityLevel', data.optionValue)}
          >
            <Option value="relaxed">Relaxed</Option>
            <Option value="moderate">Moderate</Option>
            <Option value="active">Active</Option>
            <Option value="adventure">Adventure</Option>
          </Dropdown>
        </Field>

        <Field label="Group Size">
          <Input
            type="number"
            placeholder="Number of people"
            value={preferences.groupSize || ''}
            onChange={(e) => updatePreference('groupSize', parseInt(e.target.value) || 0)}
          />
        </Field>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Body2>Include kid-friendly activities</Body2>
          <Switch
            checked={preferences.kidFriendly || false}
            onChange={(e) => updatePreference('kidFriendly', e.currentTarget.checked)}
          />
        </div>
        
        <div className="flex items-center justify-between">
          <Body2>Accessible accommodations</Body2>
          <Switch
            checked={preferences.accessible || false}
            onChange={(e) => updatePreference('accessible', e.currentTarget.checked)}
          />
        </div>
        
        <div className="flex items-center justify-between">
          <Body2>Include cultural experiences</Body2>
          <Switch
            checked={preferences.cultural || false}
            onChange={(e) => updatePreference('cultural', e.currentTarget.checked)}
          />
        </div>
      </div>
    </div>
  );
};

export const CreateTripPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const initialFormData = {
    name: '',
    description: '',
    destination: '',
    start_date: '',
    end_date: '',
    budget_total: 0,
    preferences: {},
    is_public: false,
  };

  const {
    formData,
    errors,
    updateFormData,
    validateAll,
    getFieldState,
    handleBlur
  } = useFormValidation(createTripSchema, initialFormData);

  const createTripMutation = useMutation({
    mutationFn: () => tripService.createTrip(formData as CreateTripRequest),
    onSuccess: (response: ApiResponse<Trip>) => {
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      if (response.data) {
        navigate(`/trips/${response.data.id}`);
      }
    },
    onError: (error: any) => {
      console.error('Error creating trip:', error);
      // Add a general error
      const updatedErrors = { ...errors, general: 'Failed to create trip. Please try again.' };
      // We're not using updateFormData because that would clear existing errors
      // This is a special case for API errors
      Object.assign(errors, updatedErrors);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateAll()) {
      return;
    }
    
    createTripMutation.mutate();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center"
      >
        <div className="w-16 h-16 bg-gradient-to-r from-primary-600 to-secondary-600 rounded-2xl mx-auto mb-4 flex items-center justify-center">
          <SparklesIcon className="w-8 h-8 text-white" />
        </div>
        <Title1 className="text-neutral-900 mb-2">Create a New Trip</Title1>
        <Body1 className="text-neutral-600 max-w-2xl mx-auto">
          Let our AI help you plan the perfect family adventure. Start by providing some basic details about your trip.
        </Body1>
      </motion.div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Information */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <MapIcon className="w-6 h-6 text-primary-600" />
                <Title2>Basic Information</Title2>
              </div>
            </CardHeader>
            <div className="p-4">
              <div className="space-y-6">
                <div className="grid sm:grid-cols-2 gap-6">
                  <Field
                    label="Trip Name"
                    required
                    validationState={getFieldState('name').validationState === 'error' ? 'error' : 'none'}
                    validationMessage={getFieldState('name').error}
                  >
                    <Input
                      placeholder="e.g., Family Trip to Hawaii"
                      value={formData.name}
                      onChange={(e) => updateFormData({ name: e.target.value })}
                      onBlur={() => handleBlur('name')}
                    />
                  </Field>

                  <Field
                    label="Destination"
                    required
                    validationState={getFieldState('destination').validationState === 'error' ? 'error' : 'none'}
                    validationMessage={getFieldState('destination').error}
                  >
                    <Input
                      placeholder="e.g., Maui, Hawaii"
                      value={formData.destination}
                      onChange={(e) => updateFormData({ destination: e.target.value })}
                      onBlur={() => handleBlur('destination')}
                    />
                  </Field>
                </div>

                <Field label="Description">
                  <Textarea
                    placeholder="Describe your trip goals, special occasions, or any specific requirements..."
                    value={formData.description || ''}
                    onChange={(e) => updateFormData({ description: e.target.value })}
                    rows={3}
                  />
                </Field>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Dates and Budget */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <CalendarIcon className="w-6 h-6 text-primary-600" />
                <Title2>Dates & Budget</Title2>
              </div>
            </CardHeader>
            <div className="p-4">
              <div className="grid sm:grid-cols-3 gap-6">
                <Field
                  label="Start Date"
                  required
                  validationState={getFieldState('start_date').validationState === 'error' ? 'error' : 'none'}
                  validationMessage={getFieldState('start_date').error}
                >
                  <Input
                    type="date"
                    value={formData.start_date as string}
                    onChange={(e) => updateFormData({ start_date: e.target.value })}
                    onBlur={() => handleBlur('start_date')}
                  />
                </Field>

                <Field
                  label="End Date"
                  required
                  validationState={getFieldState('end_date').validationState === 'error' ? 'error' : 'none'}
                  validationMessage={getFieldState('end_date').error}
                >
                  <Input
                    type="date"
                    value={formData.end_date as string}
                    onChange={(e) => updateFormData({ end_date: e.target.value })}
                    onBlur={() => handleBlur('end_date')}
                  />
                </Field>

                <Field
                  label="Total Budget ($)"
                  validationState={getFieldState('budget_total').validationState === 'error' ? 'error' : 'none'}
                  validationMessage={getFieldState('budget_total').error}
                >
                  <Input
                    type="number"
                    placeholder="0"
                    value={formData.budget_total?.toString() || ''}
                    onChange={(e) => updateFormData({ budget_total: parseFloat(e.target.value) || 0 })}
                    onBlur={() => handleBlur('budget_total')}
                  />
                </Field>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Preferences */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <UserGroupIcon className="w-6 h-6 text-primary-600" />
                <Title2>Trip Preferences</Title2>
              </div>
              <Body2 className="text-neutral-600">
                Help our AI create a personalized itinerary by sharing your preferences
              </Body2>
            </CardHeader>
            <div className="p-4">
              <TripPreferences
                preferences={formData.preferences}
                onChange={(preferences) => updateFormData({ preferences })}
              />
            </div>
          </Card>
        </motion.div>

        {/* Privacy Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <Card>
            <div className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <Body1 className="font-medium text-neutral-900">Make trip public</Body1>
                  <Body2 className="text-neutral-600">
                    Allow other families to discover and request to join this trip
                  </Body2>
                </div>
                <Switch
                  checked={formData.is_public}
                  onChange={(e) => updateFormData({ is_public: e.currentTarget.checked })}
                />
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Error Display */}
        {errors.general && (
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="p-4 bg-error-50 border border-error-200 rounded-lg"
          >
            <Body2 className="text-error-700">{errors.general}</Body2>
          </motion.div>
        )}

        {/* Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="flex justify-between items-center pt-6"
        >
          <Button
            appearance="outline"
            size="large"
            onClick={() => navigate('/trips')}
            disabled={createTripMutation.isPending}
          >
            Cancel
          </Button>
          
          <Button
            type="submit"
            appearance="primary"
            size="large"
            disabled={createTripMutation.isPending}
            icon={createTripMutation.isPending ? <LoadingSpinner size="small" /> : <SparklesIcon className="w-5 h-5" />}
          >
            {createTripMutation.isPending ? 'Creating Trip...' : 'Create Trip with AI'}
          </Button>
        </motion.div>
      </form>
    </div>
  );
};
