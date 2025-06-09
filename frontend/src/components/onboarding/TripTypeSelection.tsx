import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Mountain, 
  Palmtree, 
  Car, 
  Sparkles, 
  Clock, 
  Users, 
  MapPin,
  ChevronRight 
} from 'lucide-react';
import { TripType } from './OnboardingFlow';

interface TripOption {
  id: TripType;
  title: string;
  subtitle: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  gradient: string;
  features: string[];
  duration: string;
  groupSize: string;
}

const tripOptions: TripOption[] = [
  {
    id: 'weekend-getaway',
    title: 'Weekend Getaway',
    subtitle: 'Quick escape from routine',
    description: 'Perfect for busy families looking for a refreshing short break',
    icon: <Car className="h-8 w-8" />,
    color: 'blue',
    gradient: 'from-blue-500 to-cyan-500',
    features: ['2-3 days', 'Local attractions', 'Relaxing activities', 'Easy travel'],
    duration: '2-3 days',
    groupSize: '2-6 people'
  },
  {
    id: 'family-vacation',
    title: 'Family Vacation',
    subtitle: 'Memorable adventures together',
    description: 'Extended trips with activities for all ages and interests',
    icon: <Users className="h-8 w-8" />,
    color: 'purple',
    gradient: 'from-purple-500 to-pink-500',
    features: ['5-14 days', 'Multi-generational', 'Diverse activities', 'Memory making'],
    duration: '1-2 weeks',
    groupSize: '4-12 people'
  },
  {
    id: 'adventure-trip',
    title: 'Adventure Trip',
    subtitle: 'Thrilling experiences await',
    description: 'For families who love outdoor activities and new challenges',
    icon: <Mountain className="h-8 w-8" />,
    color: 'green',
    gradient: 'from-green-500 to-teal-500',
    features: ['Outdoor activities', 'Physical challenges', 'Nature exploration', 'Skill building'],
    duration: '3-10 days',
    groupSize: '2-8 people'
  }
];

interface TripTypeSelectionProps {
  onSelect: (tripType: TripType) => void;
}

const TripTypeSelection: React.FC<TripTypeSelectionProps> = ({ onSelect }) => {
  const [hoveredOption, setHoveredOption] = useState<TripType | null>(null);
  const [selectedOption, setSelectedOption] = useState<TripType | null>(null);

  const handleSelect = (tripType: TripType) => {
    setSelectedOption(tripType);
    // Small delay for visual feedback
    setTimeout(() => {
      onSelect(tripType);
    }, 300);
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-gray-800 mb-4">
          What kind of trip are you dreaming of?
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Choose a trip type to see how Pathfinder creates personalized itineraries 
          and helps your family make decisions together.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        {tripOptions.map((option) => (
          <motion.div
            key={option.id}
            className={`relative bg-white rounded-xl shadow-lg border-2 transition-all duration-300 cursor-pointer overflow-hidden ${
              selectedOption === option.id 
                ? 'border-green-500 shadow-xl' 
                : hoveredOption === option.id 
                  ? 'border-gray-300 shadow-xl' 
                  : 'border-gray-100 hover:border-gray-200'
            }`}
            onHoverStart={() => setHoveredOption(option.id)}
            onHoverEnd={() => setHoveredOption(null)}
            onClick={() => handleSelect(option.id)}
            whileHover={{ y: -4 }}
            whileTap={{ scale: 0.98 }}
          >
            {/* Gradient Header */}
            <div className={`bg-gradient-to-r ${option.gradient} p-6 text-white relative`}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {option.icon}
                  <div>
                    <h3 className="text-xl font-bold">{option.title}</h3>
                    <p className="text-sm opacity-90">{option.subtitle}</p>
                  </div>
                </div>
                <ChevronRight className="h-5 w-5 opacity-70" />
              </div>
              
              {/* Decorative elements */}
              <div className="absolute top-2 right-6 opacity-20">
                <Sparkles className="h-6 w-6" />
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              <p className="text-gray-600 mb-6 leading-relaxed">
                {option.description}
              </p>

              {/* Trip Details */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Clock className="h-4 w-4" />
                  <span>{option.duration}</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Users className="h-4 w-4" />
                  <span>{option.groupSize}</span>
                </div>
              </div>

              {/* Features */}
              <div className="space-y-2">
                <h4 className="font-semibold text-gray-800 text-sm mb-3">What's included:</h4>
                {option.features.map((feature, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full bg-gradient-to-r ${option.gradient}`} />
                    <span className="text-sm text-gray-600">{feature}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Selection indicator */}
            <motion.div
              className={`absolute inset-0 bg-green-500 bg-opacity-10 flex items-center justify-center ${
                selectedOption === option.id ? 'opacity-100' : 'opacity-0'
              }`}
              animate={{ opacity: selectedOption === option.id ? 1 : 0 }}
            >
              <motion.div
                className="bg-green-500 text-white p-3 rounded-full"
                initial={{ scale: 0 }}
                animate={{ scale: selectedOption === option.id ? 1 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronRight className="h-6 w-6" />
              </motion.div>
            </motion.div>
          </motion.div>
        ))}
      </div>

      {/* Call to action */}
      <div className="text-center mt-12">
        <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
          <MapPin className="h-4 w-4" />
          <span>Click any option to see a sample trip in action</span>
        </div>
      </div>
    </div>
  );
};

export default TripTypeSelection;
