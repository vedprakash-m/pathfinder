import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, Brain, Clock, HelpCircle } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

interface PollOption {
  value: string;
  label: string;
  description?: string;
}

interface PollType {
  value: string;
  label: string;
  description: string;
}

interface CreatePollFormProps {
  tripId: string;
  isOpen: boolean;
  onClose: () => void;
  onPollCreated: (poll: any) => void;
}

export const CreatePollForm: React.FC<CreatePollFormProps> = ({
  tripId,
  isOpen,
  onClose,
  onPollCreated
}) => {
  const { token } = useAuth();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [pollType, setPollType] = useState('');
  const [options, setOptions] = useState<PollOption[]>([
    { value: '', label: '', description: '' },
    { value: '', label: '', description: '' }
  ]);
  const [expiresHours, setExpiresHours] = useState(72);
  const [availablePollTypes, setAvailablePollTypes] = useState<PollType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isOpen) {
      fetchPollTypes();
    }
  }, [isOpen]);

  const fetchPollTypes = async () => {
    try {
      const response = await fetch('/api/v1/polls/types/available', {
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAvailablePollTypes(data.poll_types);
      }
    } catch (error) {
      console.error('Error fetching poll types:', error);
    }
  };

  const addOption = () => {
    setOptions([...options, { value: '', label: '', description: '' }]);
  };

  const removeOption = (index: number) => {
    if (options.length > 2) {
      setOptions(options.filter((_, i) => i !== index));
    }
  };

  const updateOption = (index: number, field: keyof PollOption, value: string) => {
    const updatedOptions = [...options];
    updatedOptions[index] = { ...updatedOptions[index], [field]: value };
    setOptions(updatedOptions);
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!pollType) {
      newErrors.pollType = 'Please select a poll type';
    }

    const validOptions = options.filter(opt => opt.value.trim() && opt.label.trim());
    if (validOptions.length < 2) {
      newErrors.options = 'At least 2 valid options are required';
    }

    if (expiresHours < 1 || expiresHours > 168) {
      newErrors.expiresHours = 'Expiry must be between 1 and 168 hours';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const validOptions = options.filter(opt => opt.value.trim() && opt.label.trim());
      
      const response = await fetch('/api/v1/polls', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          trip_id: tripId,
          title: title.trim(),
          description: description.trim() || undefined,
          poll_type: pollType,
          options: validOptions.map(opt => ({
            value: opt.value.trim(),
            label: opt.label.trim(),
            description: opt.description?.trim() || undefined
          })),
          expires_hours: expiresHours
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          onPollCreated(data.data);
          handleClose();
        } else {
          setErrors({ submit: data.message || 'Failed to create poll' });
        }
      } else {
        const errorData = await response.json();
        setErrors({ submit: errorData.detail || 'Failed to create poll' });
      }
    } catch (error) {
      console.error('Error creating poll:', error);
      setErrors({ submit: 'Network error. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setTitle('');
    setDescription('');
    setPollType('');
    setOptions([
      { value: '', label: '', description: '' },
      { value: '', label: '', description: '' }
    ]);
    setExpiresHours(72);
    setErrors({});
    onClose();
  };

  const getPollTypeTemplate = (type: string) => {
    const templates: Record<string, PollOption[]> = {
      destination_choice: [
        { value: 'beach', label: 'Beach Destination', description: 'Coastal location with beaches and water activities' },
        { value: 'mountains', label: 'Mountain Destination', description: 'Scenic mountain location with hiking and nature' },
        { value: 'city', label: 'City Destination', description: 'Urban location with cultural attractions and dining' }
      ],
      activity_preference: [
        { value: 'outdoor', label: 'Outdoor Activities', description: 'Hiking, sports, and nature activities' },
        { value: 'cultural', label: 'Cultural Activities', description: 'Museums, tours, and historical sites' },
        { value: 'relaxation', label: 'Relaxation Activities', description: 'Spa, beach time, and leisure' }
      ],
      budget_range: [
        { value: 'budget', label: 'Budget-Friendly ($50-100/day)', description: 'Economical options with basic amenities' },
        { value: 'moderate', label: 'Moderate ($100-200/day)', description: 'Balanced options with good amenities' },
        { value: 'luxury', label: 'Luxury ($200+/day)', description: 'Premium options with top amenities' }
      ],
      accommodation_type: [
        { value: 'hotel', label: 'Hotel', description: 'Traditional hotel with daily service' },
        { value: 'vacation_rental', label: 'Vacation Rental', description: 'Private home or apartment rental' },
        { value: 'resort', label: 'Resort', description: 'All-inclusive resort experience' }
      ]
    };

    return templates[type] || [];
  };

  const applyTemplate = () => {
    if (pollType) {
      const template = getPollTypeTemplate(pollType);
      if (template.length > 0) {
        setOptions(template);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
              <Brain className="h-6 w-6 text-blue-500" />
              <span>Create Magic Poll</span>
            </h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                Poll Title *
              </label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Choose our destination for the weekend trip"
                maxLength={255}
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600">{errors.title}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Description (Optional)
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Provide additional context for your poll..."
              />
            </div>

            {/* Poll Type */}
            <div>
              <label htmlFor="pollType" className="block text-sm font-medium text-gray-700 mb-2">
                Poll Type *
              </label>
              <select
                id="pollType"
                value={pollType}
                onChange={(e) => {
                  setPollType(e.target.value);
                  setErrors({ ...errors, pollType: '' });
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select a poll type...</option>
                {availablePollTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
              {pollType && (
                <div className="mt-2 flex items-center space-x-2">
                  <HelpCircle className="h-4 w-4 text-blue-500" />
                  <span className="text-sm text-blue-600">
                    {availablePollTypes.find(t => t.value === pollType)?.description}
                  </span>
                </div>
              )}
              {errors.pollType && (
                <p className="mt-1 text-sm text-red-600">{errors.pollType}</p>
              )}
            </div>

            {/* Template Button */}
            {pollType && getPollTypeTemplate(pollType).length > 0 && (
              <div>
                <button
                  type="button"
                  onClick={applyTemplate}
                  className="px-4 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors flex items-center space-x-2"
                >
                  <Brain className="h-4 w-4" />
                  <span>Use AI Template</span>
                </button>
              </div>
            )}

            {/* Options */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  Poll Options *
                </label>
                <button
                  type="button"
                  onClick={addOption}
                  className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 transition-colors flex items-center space-x-1"
                >
                  <Plus className="h-4 w-4" />
                  <span>Add Option</span>
                </button>
              </div>

              <div className="space-y-3">
                {options.map((option, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-medium text-gray-700">Option {index + 1}</span>
                      {options.length > 2 && (
                        <button
                          type="button"
                          onClick={() => removeOption(index)}
                          className="text-red-500 hover:text-red-700 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Value *
                        </label>
                        <input
                          type="text"
                          value={option.value}
                          onChange={(e) => updateOption(index, 'value', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Option value"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Display Label *
                        </label>
                        <input
                          type="text"
                          value={option.label}
                          onChange={(e) => updateOption(index, 'label', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Display label"
                        />
                      </div>
                    </div>

                    <div className="mt-3">
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Description (Optional)
                      </label>
                      <input
                        type="text"
                        value={option.description || ''}
                        onChange={(e) => updateOption(index, 'description', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Additional details about this option"
                      />
                    </div>
                  </div>
                ))}
              </div>

              {errors.options && (
                <p className="mt-1 text-sm text-red-600">{errors.options}</p>
              )}
            </div>

            {/* Expiry */}
            <div>
              <label htmlFor="expiresHours" className="block text-sm font-medium text-gray-700 mb-2">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4" />
                  <span>Poll Duration (Hours) *</span>
                </div>
              </label>
              <input
                type="number"
                id="expiresHours"
                value={expiresHours}
                onChange={(e) => setExpiresHours(parseInt(e.target.value) || 72)}
                min={1}
                max={168}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="mt-1 text-xs text-gray-500">
                Poll will automatically close after {expiresHours} hours (1-168 hours allowed)
              </p>
              {errors.expiresHours && (
                <p className="mt-1 text-sm text-red-600">{errors.expiresHours}</p>
              )}
            </div>

            {/* Submit Errors */}
            {errors.submit && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{errors.submit}</p>
              </div>
            )}

            {/* Buttons */}
            <div className="flex items-center justify-end space-x-3 pt-6 border-t">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
                disabled={isLoading}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-blue-300 transition-colors flex items-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Creating...</span>
                  </>
                ) : (
                  <>
                    <Brain className="h-4 w-4" />
                    <span>Create Magic Poll</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
