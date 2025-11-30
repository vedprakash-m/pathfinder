import React, { useState } from 'react';
import { Wand2, Loader2, Sparkles } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { ItineraryView } from './ItineraryView';

interface Family {
  name: string;
  members: Array<{
    age: number;
    dietary_restrictions?: string[];
    accessibility_needs?: string[];
  }>;
  preferences?: Record<string, unknown>;
}

interface GeneratorFormData {
  destination: string;
  duration_days: number;
  budget_total?: number;
  families: Family[];
  preferences: {
    accommodation_type?: string[];
    transportation_mode?: string[];
    activity_types?: string[];
    dining_preferences?: string[];
    special_requirements?: string[];
  };
}

interface ItineraryGeneratorProps {
  tripId: string;
  families?: Family[];
  className?: string;
  onGenerated?: (itinerary: unknown) => void;
}

export const ItineraryGenerator: React.FC<ItineraryGeneratorProps> = ({
  tripId,
  families = [],
  className = '',
  onGenerated
}) => {
  const { token } = useAuth();
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedItinerary, setGeneratedItinerary] = useState<unknown | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState<GeneratorFormData>({
    destination: '',
    duration_days: 7,
    budget_total: undefined,
    families: families.length > 0 ? families : [],
    preferences: {
      accommodation_type: ['family-friendly hotels'],
      transportation_mode: ['rental cars'],
      activity_types: [],
      dining_preferences: ['family restaurants'],
      special_requirements: []
    }
  });

  const handleGenerateItinerary = async () => {
    if (!formData.destination || !formData.duration_days) {
      setError('Please provide destination and duration');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/ai/generate-itinerary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          trip_id: tripId,
          destination: formData.destination,
          duration_days: formData.duration_days,
          families_data: formData.families,
          preferences: formData.preferences,
          budget_total: formData.budget_total
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setGeneratedItinerary(data.itinerary);
          if (onGenerated) {
            onGenerated(data.itinerary);
          }
        } else {
          setError(data.error || 'Failed to generate itinerary');
        }
      } else {
        setError('Failed to generate itinerary. Please try again.');
      }
    } catch (err) {
      console.error('Error generating itinerary:', err);
      setError('An error occurred while generating the itinerary');
    } finally {
      setIsGenerating(false);
    }
  };

  const updateFormData = (field: string, value: unknown) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const updatePreferences = (field: string, value: unknown) => {
    setFormData(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [field]: value
      }
    }));
  };

  if (generatedItinerary) {
    return (
      <div className={className}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
            <Sparkles className="h-6 w-6 text-purple-500" />
            <span>AI-Generated Itinerary</span>
          </h2>
          <button
            onClick={() => setGeneratedItinerary(null)}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
          >
            Generate New
          </button>
        </div>
        <ItineraryView 
          itinerary={generatedItinerary as Parameters<typeof ItineraryView>[0]['itinerary']}
          onPrint={() => window.print()}
          onExport={() => {
            const dataStr = JSON.stringify(generatedItinerary, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `itinerary-${tripId}.json`;
            link.click();
          }}
        />
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center space-x-2">
        <Wand2 className="h-6 w-6 text-purple-500" />
        <span>Generate AI Itinerary</span>
      </h2>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div className="space-y-6">
        {/* Basic Information */}
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Destination *
            </label>
            <input
              type="text"
              value={formData.destination}
              onChange={(e) => updateFormData('destination', e.target.value)}
              placeholder="e.g., Paris, France"
              className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={isGenerating}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Duration (days) *
            </label>
            <input
              type="number"
              min="1"
              max="30"
              value={formData.duration_days}
              onChange={(e) => updateFormData('duration_days', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={isGenerating}
            />
          </div>
        </div>

        {/* Budget */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Total Budget (optional)
          </label>
          <div className="relative">
            <span className="absolute left-3 top-2 text-gray-500">$</span>
            <input
              type="number"
              min="0"
              step="100"
              value={formData.budget_total || ''}
              onChange={(e) => updateFormData('budget_total', e.target.value ? parseFloat(e.target.value) : undefined)}
              placeholder="Leave empty for flexible budget"
              className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={isGenerating}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">Total budget for all families combined</p>
        </div>

        {/* Preferences */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Preferences</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Accommodation Type
              </label>
              <select
                multiple
                value={formData.preferences.accommodation_type}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value);
                  updatePreferences('accommodation_type', values);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={isGenerating}
                size={3}
              >
                <option value="family-friendly hotels">Family-Friendly Hotels</option>
                <option value="vacation rentals">Vacation Rentals</option>
                <option value="resorts">Resorts</option>
                <option value="boutique hotels">Boutique Hotels</option>
                <option value="bed and breakfast">Bed & Breakfast</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Transportation Mode
              </label>
              <select
                multiple
                value={formData.preferences.transportation_mode}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value);
                  updatePreferences('transportation_mode', values);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={isGenerating}
                size={3}
              >
                <option value="rental cars">Rental Cars</option>
                <option value="public transit">Public Transit</option>
                <option value="private transfers">Private Transfers</option>
                <option value="walking">Walking Tours</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Activity Types
              </label>
              <select
                multiple
                value={formData.preferences.activity_types}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value);
                  updatePreferences('activity_types', values);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={isGenerating}
                size={4}
              >
                <option value="outdoor">Outdoor Activities</option>
                <option value="cultural">Cultural Experiences</option>
                <option value="adventure">Adventure Sports</option>
                <option value="relaxation">Relaxation & Spa</option>
                <option value="educational">Educational Tours</option>
                <option value="entertainment">Entertainment</option>
              </select>
            </div>
          </div>
        </div>

        {/* Family Information */}
        {formData.families.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Family Information</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-700">
                <strong>{formData.families.length}</strong> {formData.families.length === 1 ? 'family' : 'families'} registered
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Total participants: <strong>
                  {formData.families.reduce((sum, family) => sum + family.members.length, 0)}
                </strong>
              </p>
            </div>
          </div>
        )}

        {/* Generate Button */}
        <div className="flex items-center justify-center pt-4">
          <button
            onClick={handleGenerateItinerary}
            disabled={isGenerating || !formData.destination || !formData.duration_days}
            className={`px-8 py-3 rounded-lg font-medium flex items-center space-x-2 transition-all ${
              isGenerating || !formData.destination || !formData.duration_days
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 shadow-lg hover:shadow-xl'
            }`}
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Generating with AI...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-5 w-5" />
                <span>Generate AI Itinerary</span>
              </>
            )}
          </button>
        </div>

        {isGenerating && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <p className="text-sm text-purple-800 text-center">
              Our AI is crafting a personalized itinerary for your multi-family trip...
              <br />
              <span className="text-xs">This may take 10-30 seconds</span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ItineraryGenerator;
