import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircle2, 
  Sparkles, 
  MapPin, 
  Users, 
  Calendar,
  MessageSquare,
  Star,
  Trophy,
  ArrowRight,
  Rocket
} from 'lucide-react';

interface Feature {
  icon: React.ReactNode;
  title: string;
  description: string;
  gradient: string;
}

const features: Feature[] = [
  {
    icon: <MapPin className="h-6 w-6" />,
    title: 'AI Trip Planning',
    description: 'Create personalized itineraries in seconds',
    gradient: 'from-blue-500 to-cyan-500'
  },
  {
    icon: <Users className="h-6 w-6" />,
    title: 'Family Consensus',
    description: 'Everyone gets a voice in trip decisions',
    gradient: 'from-purple-500 to-pink-500'
  },
  {
    icon: <MessageSquare className="h-6 w-6" />,
    title: 'Real-time Chat',
    description: 'Collaborate and share ideas instantly',
    gradient: 'from-green-500 to-teal-500'
  },
  {
    icon: <Calendar className="h-6 w-6" />,
    title: 'Smart Scheduling',
    description: 'Optimize your time with intelligent planning',
    gradient: 'from-orange-500 to-red-500'
  }
];

interface OnboardingCompleteProps {
  onFinish: () => void;
  completionTime: number;
}

const OnboardingComplete: React.FC<OnboardingCompleteProps> = ({ onFinish, completionTime }) => {
  const [showConfetti, setShowConfetti] = useState(false);
  const [currentTip, setCurrentTip] = useState(0);

  const tips = [
    'Pro tip: Use @mentions in trip chat to get specific family member attention',
    'You can create multiple trip templates for different types of getaways',
    'The consensus engine learns from your family\'s preferences over time',
    'Export your itinerary to calendar apps or share with travel companions'
  ];

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  useEffect(() => {
    setShowConfetti(true);
    const confettiTimer = setTimeout(() => setShowConfetti(false), 3000);
    
    const tipTimer = setInterval(() => {
      setCurrentTip((prev) => (prev + 1) % tips.length);
    }, 3000);

    return () => {
      clearTimeout(confettiTimer);
      clearInterval(tipTimer);
    };
  }, []);

  return (
    <div className="max-w-4xl mx-auto text-center">
      {/* Confetti Animation */}
      {showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-50">
          {[...Array(50)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
              initial={{
                x: Math.random() * window.innerWidth,
                y: -10,
                rotate: 0,
                opacity: 1
              }}
              animate={{
                y: window.innerHeight + 10,
                rotate: 360,
                opacity: 0
              }}
              transition={{
                duration: Math.random() * 3 + 2,
                ease: 'easeOut',
                delay: Math.random() * 2
              }}
            />
          ))}
        </div>
      )}

      {/* Success Header */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
        className="mb-8"
      >
        <div className="bg-gradient-to-r from-green-500 to-emerald-500 p-6 rounded-full w-24 h-24 mx-auto mb-6 flex items-center justify-center">
          <CheckCircle2 className="h-12 w-12 text-white" />
        </div>
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          🎉 Congratulations!
        </h1>
        <p className="text-xl text-gray-600 mb-2">
          You've completed the Pathfinder experience in just{' '}
          <span className="font-semibold text-blue-600">{formatTime(completionTime)}</span>
        </p>
        <p className="text-gray-500">
          You're now ready to plan amazing family trips with AI-powered collaboration
        </p>
      </motion.div>

      {/* Achievement Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white rounded-xl shadow-lg p-6 mb-8"
      >
        <h2 className="text-2xl font-semibold text-gray-800 mb-6">Your Onboarding Achievements</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="bg-blue-100 p-4 rounded-full w-16 h-16 mx-auto mb-3 flex items-center justify-center">
              <Trophy className="h-8 w-8 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-800">Trip Explorer</h3>
            <p className="text-sm text-gray-600">Discovered sample trip creation</p>
          </div>
          <div className="text-center">
            <div className="bg-purple-100 p-4 rounded-full w-16 h-16 mx-auto mb-3 flex items-center justify-center">
              <Users className="h-8 w-8 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-800">Consensus Builder</h3>
            <p className="text-sm text-gray-600">Mastered family decision making</p>
          </div>
          <div className="text-center">
            <div className="bg-green-100 p-4 rounded-full w-16 h-16 mx-auto mb-3 flex items-center justify-center">
              <Rocket className="h-8 w-8 text-green-600" />
            </div>
            <h3 className="font-semibold text-gray-800">Quick Learner</h3>
            <p className="text-sm text-gray-600">Completed in under 2 minutes</p>
          </div>
        </div>
      </motion.div>

      {/* Feature Highlights */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-white rounded-xl shadow-lg p-6 mb-8"
      >
        <h2 className="text-2xl font-semibold text-gray-800 mb-6">
          You now have access to all these features:
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.8 + index * 0.1 }}
              className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg"
            >
              <div className={`bg-gradient-to-r ${feature.gradient} p-3 rounded-lg text-white`}>
                {feature.icon}
              </div>
              <div className="text-left">
                <h3 className="font-semibold text-gray-800">{feature.title}</h3>
                <p className="text-sm text-gray-600">{feature.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Rotating Tips */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.0 }}
        className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 mb-8"
      >
        <div className="flex items-center justify-center space-x-2 mb-4">
          <Sparkles className="h-5 w-5 text-blue-500" />
          <h3 className="text-lg font-semibold text-gray-800">Pro Tips</h3>
        </div>
        <motion.p
          key={currentTip}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="text-gray-600"
        >
          {tips[currentTip]}
        </motion.p>
      </motion.div>

      {/* Next Steps */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2 }}
        className="bg-white rounded-xl shadow-lg p-8"
      >
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Ready to start planning?</h2>
        <p className="text-gray-600 mb-6">
          Create your first real trip or explore more sample templates to get inspired.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={onFinish}
            className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-600 hover:to-purple-600 transition-all transform hover:scale-105 flex items-center justify-center space-x-2"
          >
            <span>Start Planning My Trip</span>
            <ArrowRight className="h-5 w-5" />
          </button>
          
          <button
            onClick={onFinish}
            className="border-2 border-gray-300 text-gray-700 px-8 py-3 rounded-lg font-semibold hover:border-gray-400 hover:bg-gray-50 transition-all flex items-center justify-center space-x-2"
          >
            <span>Explore Dashboard</span>
          </button>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
            <div className="flex items-center space-x-1">
              <Star className="h-4 w-4 fill-current text-yellow-500" />
              <span>4.9/5 user rating</span>
            </div>
            <div>•</div>
            <div>Join 50,000+ families</div>
            <div>•</div>
            <div>1M+ trips planned</div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default OnboardingComplete;
