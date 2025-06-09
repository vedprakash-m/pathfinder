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

interface SampleFamily {
  id: string;
  name: string;
  role: string;
  avatar: string;
  preferences: string[];
}

interface Activity {
  id: string;
  name: string;
  description: string;
  duration: string;
  difficulty: 'Easy' | 'Moderate' | 'Challenging';
  category: string;
  rating: number;
  image: string;
  cost: string;
}

interface SampleTrip {
  id: string;
  title: string;
  destination: string;
  duration: string;
  description: string;
  family: SampleFamily[];
  itinerary: {
    day: number;
    title: string;
    activities: Activity[];
  }[];
  highlights: string[];
}

// Sample trip templates based on trip type
const sampleTrips: Record<TripType, SampleTrip> = {
  'weekend-getaway': {
    id: 'sample-weekend-1',
    title: 'Cozy Mountain Retreat',
    destination: 'Blue Ridge Mountains, VA',
    duration: '2 days, 1 night',
    description: 'A peaceful weekend escape with scenic views, local cuisine, and relaxing activities for the whole family.',
    family: [
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
    ],
    itinerary: [
      {
        day: 1,
        title: 'Arrival & Exploration',
        activities: [
          {
            id: 'activity-1',
            name: 'Scenic Drive to Lodge',
            description: 'Beautiful mountain views with photo stops along the way',
            duration: '2 hours',
            difficulty: 'Easy',
            category: 'Transportation',
            rating: 4.5,
            image: '🚗',
            cost: '$50'
          },
          {
            id: 'activity-2',
            name: 'Local Farmers Market',
            description: 'Sample local produce and artisan goods',
            duration: '1 hour',
            difficulty: 'Easy',
            category: 'Cultural',
            rating: 4.3,
            image: '🥕',
            cost: '$30'
          },
          {
            id: 'activity-3',
            name: 'Evening Bonfire',
            description: 'Cozy evening with s\'mores and stargazing',
            duration: '2 hours',
            difficulty: 'Easy',
            category: 'Relaxation',
            rating: 4.8,
            image: '🔥',
            cost: '$20'
          }
        ]
      },
      {
        day: 2,
        title: 'Adventure & Departure',
        activities: [
          {
            id: 'activity-4',
            name: 'Morning Hike',
            description: 'Easy trail with waterfall views perfect for photos',
            duration: '2 hours',
            difficulty: 'Moderate',
            category: 'Outdoor',
            rating: 4.6,
            image: '🥾',
            cost: 'Free'
          },
          {
            id: 'activity-5',
            name: 'Spa Time',
            description: 'Relaxing massage and wellness treatments',
            duration: '1.5 hours',
            difficulty: 'Easy',
            category: 'Wellness',
            rating: 4.7,
            image: '💆‍♀️',
            cost: '$120'
          }
        ]
      }
    ],
    highlights: ['Mountain views', 'Family bonding', 'Local experiences', 'Photo opportunities']
  },
  'family-vacation': {
    id: 'sample-family-1',
    title: 'Orlando Family Adventure',
    destination: 'Orlando, Florida',
    duration: '7 days, 6 nights',
    description: 'The ultimate family vacation with theme parks, attractions, and activities for all ages from toddlers to grandparents.',
    family: [
      {
        id: 'grandpa',
        name: 'Robert',
        role: 'Grandpa',
        avatar: '👴',
        preferences: ['Museums', 'Shows', 'Comfortable seating']
      },
      {
        id: 'dad',
        name: 'Mike',
        role: 'Dad',
        avatar: '👨‍👩‍👧‍👦',
        preferences: ['Thrill rides', 'Sports', 'Photography']
      },
      {
        id: 'mom',
        name: 'Lisa',
        role: 'Mom',
        avatar: '👩‍👩‍👧‍👦',
        preferences: ['Character meet & greets', 'Shows', 'Planning']
      },
      {
        id: 'teen',
        name: 'Emma',
        role: 'Teen (14)',
        avatar: '👧',
        preferences: ['Roller coasters', 'Shopping', 'Social media']
      },
      {
        id: 'kid',
        name: 'Jake',
        role: 'Kid (8)',
        avatar: '👦',
        preferences: ['Characters', 'Water rides', 'Arcade games']
      }
    ],
    itinerary: [
      {
        day: 1,
        title: 'Magic Kingdom Day',
        activities: [
          {
            id: 'activity-6',
            name: 'Character Breakfast',
            description: 'Meet Disney characters while enjoying breakfast',
            duration: '1.5 hours',
            difficulty: 'Easy',
            category: 'Dining',
            rating: 4.8,
            image: '🏰',
            cost: '$45/person'
          },
          {
            id: 'activity-7',
            name: 'Classic Attractions',
            description: 'Pirates, Haunted Mansion, and It\'s a Small World',
            duration: '4 hours',
            difficulty: 'Easy',
            category: 'Entertainment',
            rating: 4.7,
            image: '🎢',
            cost: 'Included'
          },
          {
            id: 'activity-8',
            name: 'Fireworks Show',
            description: 'Spectacular nighttime fireworks over the castle',
            duration: '30 minutes',
            difficulty: 'Easy',
            category: 'Entertainment',
            rating: 4.9,
            image: '🎆',
            cost: 'Included'
          }
        ]
      }
    ],
    highlights: ['Multi-generational fun', 'Character experiences', 'Thrill rides', 'Memory making']
  },
  'adventure-trip': {
    id: 'sample-adventure-1',
    title: 'Colorado Rockies Adventure',
    destination: 'Rocky Mountain National Park, CO',
    duration: '5 days, 4 nights',
    description: 'An action-packed adventure featuring hiking, wildlife viewing, and outdoor challenges in one of America\'s most beautiful national parks.',
    family: [
      {
        id: 'dad',
        name: 'Chris',
        role: 'Dad',
        avatar: '🧗‍♂️',
        preferences: ['Rock climbing', 'Photography', 'Camping']
      },
      {
        id: 'mom',
        name: 'Amy',
        role: 'Mom',
        avatar: '🚴‍♀️',
        preferences: ['Mountain biking', 'Wildlife viewing', 'Yoga']
      },
      {
        id: 'teen1',
        name: 'Jordan',
        role: 'Teen (17)',
        avatar: '🏔️',
        preferences: ['Extreme sports', 'Adventure challenges', 'Nature']
      },
      {
        id: 'teen2',
        name: 'Casey',
        role: 'Teen (15)',
        avatar: '🎒',
        preferences: ['Hiking', 'Photography', 'Outdoor cooking']
      }
    ],
    itinerary: [
      {
        day: 1,
        title: 'Alpine Adventure',
        activities: [
          {
            id: 'activity-9',
            name: 'Summit Hike',
            description: 'Challenging hike to mountain peak with panoramic views',
            duration: '6 hours',
            difficulty: 'Challenging',
            category: 'Hiking',
            rating: 4.9,
            image: '⛰️',
            cost: 'Free'
          },
          {
            id: 'activity-10',
            name: 'Wildlife Photography',
            description: 'Guided tour to spot elk, bighorn sheep, and mountain goats',
            duration: '3 hours',
            difficulty: 'Moderate',
            category: 'Wildlife',
            rating: 4.6,
            image: '📸',
            cost: '$75/person'
          }
        ]
      }
    ],
    highlights: ['Mountain summits', 'Wildlife encounters', 'Physical challenges', 'Natural beauty']
  }
};

interface SampleTripDemoProps {
  tripType: TripType;
  onComplete: (tripId: string) => void;
}

const SampleTripDemo: React.FC<SampleTripDemoProps> = ({ tripType, onComplete }) => {
  const [isGenerating, setIsGenerating] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const [trip, setTrip] = useState<SampleTrip | null>(null);

  const generationSteps = [
    'Analyzing your preferences...',
    'Finding the perfect destination...',
    'Creating sample family profiles...',
    'Generating personalized itinerary...',
    'Adding interactive elements...'
  ];

  useEffect(() => {
    // Simulate trip generation process
    const generateTrip = async () => {
      for (let i = 0; i < generationSteps.length; i++) {
        setCurrentStep(i);
        await new Promise(resolve => setTimeout(resolve, 800));
      }
      
      setTrip(sampleTrips[tripType]);
      setIsGenerating(false);
    };

    generateTrip();
  }, [tripType]);

  const handleContinue = () => {
    if (trip) {
      onComplete(trip.id);
    }
  };

  if (isGenerating) {
    return (
      <div className="max-w-4xl mx-auto text-center">
        <div className="bg-white rounded-xl shadow-lg p-12">
          <div className="mb-8">
            <Loader2 className="h-12 w-12 animate-spin text-blue-500 mx-auto mb-6" />
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              Creating your sample trip...
            </h2>
            <p className="text-gray-600 mb-8">
              Watch as Pathfinder's AI builds a personalized itinerary just for you
            </p>
          </div>

          <div className="space-y-4">
            {generationSteps.map((step, index) => (
              <motion.div
                key={index}
                className={`flex items-center space-x-3 p-3 rounded-lg transition-all ${
                  index <= currentStep 
                    ? 'bg-blue-50 text-blue-700' 
                    : 'text-gray-400'
                }`}
                animate={{
                  opacity: index <= currentStep ? 1 : 0.5,
                  scale: index === currentStep ? 1.02 : 1
                }}
              >
                <div className={`w-3 h-3 rounded-full ${
                  index < currentStep 
                    ? 'bg-green-500' 
                    : index === currentStep 
                      ? 'bg-blue-500 animate-pulse' 
                      : 'bg-gray-300'
                }`} />
                <span className="font-medium">{step}</span>
                {index < currentStep && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="text-green-500"
                  >
                    ✓
                  </motion.div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!trip) return null;

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-4">
          Your Sample Trip is Ready!
        </h2>
        <p className="text-lg text-gray-600">
          Here's how Pathfinder creates personalized experiences for your family
        </p>
      </div>

      {/* Trip Overview */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden mb-8">
        <div className="bg-gradient-to-r from-blue-500 to-purple-500 p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold mb-2">{trip.title}</h3>
              <div className="flex items-center space-x-4 text-sm opacity-90">
                <div className="flex items-center space-x-1">
                  <MapPin className="h-4 w-4" />
                  <span>{trip.destination}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Clock className="h-4 w-4" />
                  <span>{trip.duration}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Users className="h-4 w-4" />
                  <span>{trip.family.length} travelers</span>
                </div>
              </div>
            </div>
            <Sparkles className="h-8 w-8 opacity-70" />
          </div>
        </div>
        
        <div className="p-6">
          <p className="text-gray-600 mb-6">{trip.description}</p>
          
          {/* Trip Highlights */}
          <div className="mb-6">
            <h4 className="font-semibold text-gray-800 mb-3">Trip Highlights:</h4>
            <div className="flex flex-wrap gap-2">
              {trip.highlights.map((highlight, index) => (
                <span
                  key={index}
                  className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm"
                >
                  {highlight}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Sample Family */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
        <h4 className="text-xl font-semibold text-gray-800 mb-4">Meet Your Sample Family</h4>
        <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4">
          {trip.family.map((member) => (
            <div key={member.id} className="text-center">
              <div className="text-4xl mb-2">{member.avatar}</div>
              <h5 className="font-semibold text-gray-800">{member.name}</h5>
              <p className="text-sm text-gray-500 mb-2">{member.role}</p>
              <div className="text-xs text-gray-400">
                {member.preferences.slice(0, 2).join(', ')}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Sample Itinerary */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
        <h4 className="text-xl font-semibold text-gray-800 mb-6">Sample Itinerary</h4>
        <div className="space-y-6">
          {trip.itinerary.map((day) => (
            <div key={day.day} className="border-l-4 border-blue-500 pl-6">
              <div className="flex items-center space-x-2 mb-3">
                <Calendar className="h-5 w-5 text-blue-500" />
                <h5 className="font-semibold text-gray-800">Day {day.day}: {day.title}</h5>
              </div>
              <div className="space-y-3">
                {day.activities.map((activity) => (
                  <div key={activity.id} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{activity.image}</span>
                        <div>
                          <h6 className="font-semibold text-gray-800">{activity.name}</h6>
                          <p className="text-sm text-gray-600">{activity.description}</p>
                        </div>
                      </div>
                      <div className="text-right text-sm text-gray-500">
                        <div>{activity.duration}</div>
                        <div>{activity.cost}</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span className={`px-2 py-1 rounded ${
                        activity.difficulty === 'Easy' ? 'bg-green-100 text-green-700' :
                        activity.difficulty === 'Moderate' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {activity.difficulty}
                      </span>
                      <div className="flex items-center space-x-1">
                        <Star className="h-3 w-3 fill-current text-yellow-500" />
                        <span>{activity.rating}</span>
                      </div>
                      <span>{activity.category}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Call to Action */}
      <div className="text-center">
        <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-8 mb-6">
          <h4 className="text-xl font-semibold text-gray-800 mb-4">
            This is just the beginning!
          </h4>
          <p className="text-gray-600 mb-6">
            Now let's see how your family would make decisions together using Pathfinder's consensus engine.
          </p>
          <button
            onClick={handleContinue}
            className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-600 hover:to-purple-600 transition-all transform hover:scale-105 flex items-center space-x-2 mx-auto"
          >
            <span>Try Interactive Voting</span>
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SampleTripDemo;
