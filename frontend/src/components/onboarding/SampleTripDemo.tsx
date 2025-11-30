import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  MapPin, 
  Clock, 
  Users, 
  Star, 
  Calendar,
  Loader2,
  Sparkles,
  ChevronRight
} from 'lucide-react';
import { TripType } from './OnboardingFlow';
import { TripTemplateService, TripTemplate } from '../../services/tripTemplateService';
import { useOnboardingAnalytics } from '../../services/onboardingAnalytics';
import apiService from '../../services/api';

interface SampleFamily {
  id: string;
  name: string;
  role: string;
  avatar: string;
  preferences: string[];
}

interface SampleTripDemoProps {
  tripType: TripType;
  onComplete: (tripId: string) => void;
}

const SampleTripDemo: React.FC<SampleTripDemoProps> = ({ tripType, onComplete }) => {
  const [isGenerating, setIsGenerating] = useState(true);
  const [currentTemplate, setCurrentTemplate] = useState<TripTemplate | null>(null);
  const [animationStep, setAnimationStep] = useState(0);
  const analytics = useOnboardingAnalytics();

  // Sample family data for demonstration
  const sampleFamily: SampleFamily[] = [
    {
      id: 'dad',
      name: 'David',
      role: 'Dad',
      avatar: '👨‍💼',
      preferences: ['Photography', 'Hiking', 'Local cuisine']
    },
    {
      id: 'mom',
      name: 'Sarah',
      role: 'Mom',
      avatar: '👩‍💻',
      preferences: ['Spa activities', 'Shopping', 'Wine tasting']
    },
    {
      id: 'teen',
      name: 'Alex',
      role: 'Teen (16)',
      avatar: '🧑‍🎓',
      preferences: ['Adventure sports', 'Social media spots', 'Gaming']
    }
  ];

  const generationSteps = [
    'Analyzing family preferences...',
    'Finding best destinations...',
    'Creating personalized itinerary...',
    'Optimizing for group consensus...'
  ];

  useEffect(() => {
    // Generate sample trip using backend API
    const generateTrip = async () => {
      setIsGenerating(true);
      setAnimationStep(0);
      
      try {
        // Show generation steps
        for (let i = 0; i < generationSteps.length; i++) {
          setAnimationStep(i);
          await new Promise(resolve => setTimeout(resolve, 800));
        }
        
        // Try to call backend API first, fallback to template service
        let template: TripTemplate | null = null;
        
        try {
          // Convert tripType to backend format
          const backendTripType = tripType.replace('-', '_') as 'weekend_getaway' | 'family_vacation' | 'adventure_trip';
          
          // Call backend to create sample trip
          const response = await apiService.onboarding.createSampleTrip(backendTripType);
          
          if (response.success && response.data) {
            // Extract itinerary data from response
            const itineraryData = response.data.itinerary || {};
            const activities = Array.isArray(itineraryData.activities) ? itineraryData.activities : [];
            const durationDays = itineraryData.duration_days || 3;
            
            // Convert backend response to frontend template format
            template = {
              id: response.data.id || `sample_${Date.now()}`,
              type: tripType,
              title: response.data.title || 'Sample Trip',
              description: response.data.description || 'A wonderful trip created by Pathfinder AI',
              duration: `${durationDays} days`,
              location: response.data.destination || 'Unknown Location',
              groupSize: `${itineraryData.sample_families?.length || 2} families`,
              budget: response.data.budget ? `$${response.data.budget.toLocaleString()}` : '$1,000',
              highlights: activities.map((act: { name?: string; description?: string }) => act.name || act.description || '').slice(0, 4) || ['Great activities'],
              itinerary: activities.map((act: { name?: string; description?: string; difficulty?: string }, idx: number) => ({
                day: idx + 1,
                activities: [act.name || 'Activity'],
                description: act.description || ''
              })),
              tags: itineraryData.tags || ['AI Generated', 'Sample'],
              imageUrl: '',
              difficulty: (activities.length > 0 && activities[0].difficulty) || 'Easy' as const,
              bestSeason: ['Spring', 'Summer', 'Fall']
            };
            
            // Track successful API integration
            analytics.trackApiIntegration('sample_trip_created', true);
          }
        } catch (apiError) {
          console.warn('Backend API not available, using template service:', apiError);
          analytics.trackApiIntegration('sample_trip_created', false);
        }
        
        // Fallback to template service if API fails
        if (!template) {
          const fallbackTemplate = TripTemplateService.getRandomTemplate(tripType);
          template = fallbackTemplate || null;
        }
        
        if (template) {
          setCurrentTemplate(template);
          setIsGenerating(false);
        } else {
          setCurrentTemplate(null);
          setIsGenerating(false);
        }
      } catch (error) {
        console.error('Error generating trip:', error);
        // Fallback to template service
        const template = TripTemplateService.getRandomTemplate(tripType);
        if (template) {
          setCurrentTemplate(template);
          setIsGenerating(false);
        }
      }
    };

    generateTrip();
  }, [tripType, analytics]);

  const handleContinue = () => {
    if (currentTemplate) {
      onComplete(currentTemplate.id);
    }
  };

  const handleRegenerate = () => {
    const newTemplate = TripTemplateService.getRandomTemplate(tripType);
    if (newTemplate && newTemplate.id !== currentTemplate?.id) {
      setCurrentTemplate(newTemplate);
      analytics.trackTripRegeneration(newTemplate.id);
    }
  };

  if (isGenerating) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-8 sm:mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-3 sm:mb-4">
            Creating Your Sample Trip
          </h2>
          <p className="text-base sm:text-lg text-gray-600">
            Watch Pathfinder's AI analyze preferences and generate a personalized itinerary
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 sm:p-8 mb-8">
          <div className="flex items-center justify-center mb-6">
            <div className="relative">
              <Loader2 className="h-8 w-8 sm:h-12 sm:w-12 text-blue-500 animate-spin" />
              <Sparkles className="h-4 w-4 sm:h-6 sm:w-6 text-purple-500 absolute -top-1 -right-1" />
            </div>
          </div>

          <div className="space-y-4">
            {generationSteps.map((step, index) => (
              <motion.div
                key={index}
                className={`flex items-center space-x-3 p-3 rounded-lg transition-all duration-500 ${
                  index <= animationStep 
                    ? 'bg-blue-50 text-blue-800' 
                    : 'bg-gray-50 text-gray-500'
                }`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ 
                  opacity: index <= animationStep ? 1 : 0.5,
                  x: 0
                }}
              >
                <div className={`w-2 h-2 rounded-full ${
                  index <= animationStep ? 'bg-blue-500' : 'bg-gray-300'
                }`} />
                <span className="text-sm sm:text-base">{step}</span>
                {index === animationStep && (
                  <Loader2 className="h-4 w-4 animate-spin ml-auto" />
                )}
              </motion.div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold text-gray-800 mb-2">Sample Family Preferences:</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {sampleFamily.map((member) => (
                <div key={member.id} className="flex items-center space-x-2">
                  <span className="text-lg">{member.avatar}</span>
                  <div>
                    <div className="font-medium text-sm">{member.name}</div>
                    <div className="text-xs text-gray-600">
                      {member.preferences.slice(0, 2).join(', ')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!currentTemplate) {
    return (
      <div className="text-center">
        <p className="text-gray-600">No template available for this trip type.</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto px-4 sm:px-6"
    >
      <div className="text-center mb-6 sm:mb-8">
        <div className="flex items-center justify-center mb-3 sm:mb-4">
          <Sparkles className="h-5 w-5 text-green-500 mr-2" />
          <span className="text-green-600 font-semibold text-sm sm:text-base">Trip Generated!</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-2 sm:mb-3">
          {currentTemplate.title}
        </h2>
        <p className="text-base sm:text-lg text-gray-600">
          {currentTemplate.description}
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        {/* Trip Header */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-500 text-white p-4 sm:p-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
            <div className="flex items-center space-x-2">
              <MapPin className="h-4 w-4 sm:h-5 sm:w-5" />
              <div>
                <div className="text-xs opacity-80">Destination</div>
                <div className="font-semibold text-sm sm:text-base">{currentTemplate.location}</div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 sm:h-5 sm:w-5" />
              <div>
                <div className="text-xs opacity-80">Duration</div>
                <div className="font-semibold text-sm sm:text-base">{currentTemplate.duration}</div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Users className="h-4 w-4 sm:h-5 sm:w-5" />
              <div>
                <div className="text-xs opacity-80">Group Size</div>
                <div className="font-semibold text-sm sm:text-base">{currentTemplate.groupSize}</div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Star className="h-4 w-4 sm:h-5 sm:w-5" />
              <div>
                <div className="text-xs opacity-80">Difficulty</div>
                <div className="font-semibold text-sm sm:text-base">{currentTemplate.difficulty}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Trip Highlights */}
        <div className="p-4 sm:p-6 border-b">
          <h3 className="font-semibold text-gray-800 mb-3 text-base sm:text-lg">Trip Highlights</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
            {currentTemplate.highlights.map((highlight, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full" />
                <span className="text-sm sm:text-base text-gray-700">{highlight}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Sample Itinerary */}
        <div className="p-4 sm:p-6">
          <h3 className="font-semibold text-gray-800 mb-4 text-base sm:text-lg">Sample Itinerary</h3>
          <div className="space-y-4">
            {currentTemplate.itinerary.slice(0, 2).map((day, index) => (
              <div key={index} className="border rounded-lg p-3 sm:p-4">
                <div className="flex items-center space-x-2 mb-3">
                  <Calendar className="h-4 w-4 text-blue-500" />
                  <span className="font-semibold text-sm sm:text-base">Day {day.day}: {day.title}</span>
                </div>
                <div className="space-y-2">
                  {day.activities.slice(0, 2).map((activity, actIndex) => (
                    <div key={actIndex} className="bg-gray-50 rounded-lg p-2 sm:p-3">
                      <div className="flex justify-between items-start mb-1">
                        <h4 className="font-medium text-sm sm:text-base">{activity.name}</h4>
                        <span className="text-xs text-gray-500">{activity.duration}</span>
                      </div>
                      <p className="text-xs sm:text-sm text-gray-600">{activity.description}</p>
                      <div className="flex items-center space-x-4 mt-2">
                        <span className="text-xs text-gray-500">Cost: {activity.cost}</span>
                        <span className="text-xs text-gray-500">Ages: {activity.ageRecommendation}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="bg-gray-50 p-4 sm:p-6 flex flex-col sm:flex-row justify-between items-center space-y-3 sm:space-y-0">
          <button
            onClick={handleRegenerate}
            className="w-full sm:w-auto px-4 py-2 text-blue-600 hover:text-blue-800 transition-colors text-sm sm:text-base"
          >
            Generate Different Trip
          </button>
          <button
            onClick={handleContinue}
            className="w-full sm:w-auto bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-2 rounded-lg hover:shadow-lg transition-all flex items-center justify-center space-x-2 text-sm sm:text-base"
          >
            <span>See How Families Decide</span>
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default SampleTripDemo;
