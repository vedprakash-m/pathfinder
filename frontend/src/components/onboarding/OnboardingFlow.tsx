import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, MapPin, Users, Compass } from 'lucide-react';
import TripTypeSelection from './TripTypeSelection';
import SampleTripDemo from './SampleTripDemo';
import InteractiveConsensusDemo from './InteractiveConsensusDemo';
import OnboardingComplete from './OnboardingComplete';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../lib/api';

export type TripType = 'weekend-getaway' | 'family-vacation' | 'adventure-trip';
export type OnboardingStep = 'welcome' | 'trip-type' | 'sample-trip' | 'consensus-demo' | 'complete';

interface OnboardingFlowProps {
  onComplete: (data: { tripType: TripType; completionTime: number }) => void;
}

const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('welcome');
  const [selectedTripType, setSelectedTripType] = useState<TripType | null>(null);
  const [sampleTripId, setSampleTripId] = useState<string | null>(null);
  const [startTime] = useState(Date.now());
  const { user } = useAuth();

  // Track onboarding analytics
  useEffect(() => {
    if (user) {
      api.post('/api/analytics/onboarding-start', {
        userId: user.id,
        timestamp: startTime,
        step: currentStep
      }).catch(console.error);
    }
  }, [user, startTime, currentStep]);

  const handleStepComplete = (step: OnboardingStep, data?: any) => {
    switch (step) {
      case 'welcome':
        setCurrentStep('trip-type');
        break;
      case 'trip-type':
        setSelectedTripType(data.tripType);
        setCurrentStep('sample-trip');
        break;
      case 'sample-trip':
        setSampleTripId(data.tripId);
        setCurrentStep('consensus-demo');
        break;
      case 'consensus-demo':
        setCurrentStep('complete');
        break;
      case 'complete':
        // Track completion analytics
        if (user) {
          api.post('/api/analytics/onboarding-complete', {
            userId: user.id,
            completionTime: Date.now() - startTime,
            tripType: selectedTripType,
            sampleTripId
          }).catch(console.error);
        }
        onComplete({
          tripType: selectedTripType!,
          completionTime: Date.now() - startTime
        });
        break;
    }
  };

  const handleSkip = () => {
    if (user) {
      api.post('/api/analytics/onboarding-skip', {
        userId: user.id,
        skipStep: currentStep,
        timeSpent: Date.now() - startTime
      }).catch(console.error);
    }
    onComplete({
      tripType: selectedTripType || 'family-vacation', // default fallback
      completionTime: Date.now() - startTime
    });
  };

  const stepVariants = {
    initial: { opacity: 0, x: 50 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -50 }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-6 w-6 text-blue-600" />
              <span className="text-lg font-semibold text-gray-800">Welcome to Pathfinder</span>
            </div>
            <button
              onClick={handleSkip}
              className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              Skip tour
            </button>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
              style={{
                width: `${
                  currentStep === 'welcome' ? 20 :
                  currentStep === 'trip-type' ? 40 :
                  currentStep === 'sample-trip' ? 60 :
                  currentStep === 'consensus-demo' ? 80 : 100
                }%`
              }}
            />
          </div>
        </div>

        {/* Step Content */}
        <AnimatePresence mode="wait">
          {currentStep === 'welcome' && (
            <motion.div
              key="welcome"
              variants={stepVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="text-center max-w-2xl mx-auto"
            >
              <div className="mb-8">
                <div className="flex justify-center mb-6">
                  <div className="bg-gradient-to-r from-blue-500 to-purple-500 p-6 rounded-full">
                    <Compass className="h-12 w-12 text-white" />
                  </div>
                </div>
                <h1 className="text-4xl font-bold text-gray-800 mb-4">
                  Welcome to Pathfinder
                </h1>
                <p className="text-xl text-gray-600 mb-8">
                  The AI-powered trip planner that brings families together through collaborative decision-making.
                  Let's show you how it works!
                </p>
                <div className="grid md:grid-cols-3 gap-6 mb-8">
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <MapPin className="h-8 w-8 text-blue-500 mb-3 mx-auto" />
                    <h3 className="font-semibold text-gray-800 mb-2">Smart Planning</h3>
                    <p className="text-sm text-gray-600">AI creates personalized itineraries based on your family's preferences</p>
                  </div>
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <Users className="h-8 w-8 text-purple-500 mb-3 mx-auto" />
                    <h3 className="font-semibold text-gray-800 mb-2">Family Consensus</h3>
                    <p className="text-sm text-gray-600">Everyone votes on activities and destinations for fair decisions</p>
                  </div>
                  <div className="bg-white p-6 rounded-lg shadow-sm border">
                    <Sparkles className="h-8 w-8 text-green-500 mb-3 mx-auto" />
                    <h3 className="font-semibold text-gray-800 mb-2">Real-time Collaboration</h3>
                    <p className="text-sm text-gray-600">Chat, share ideas, and plan together from anywhere</p>
                  </div>
                </div>
                <button
                  onClick={() => handleStepComplete('welcome')}
                  className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-600 hover:to-purple-600 transition-all transform hover:scale-105"
                >
                  Let's Get Started!
                </button>
              </div>
            </motion.div>
          )}

          {currentStep === 'trip-type' && (
            <motion.div
              key="trip-type"
              variants={stepVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <TripTypeSelection onSelect={(tripType) => handleStepComplete('trip-type', { tripType })} />
            </motion.div>
          )}

          {currentStep === 'sample-trip' && selectedTripType && (
            <motion.div
              key="sample-trip"
              variants={stepVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <SampleTripDemo
                tripType={selectedTripType}
                onComplete={(tripId) => handleStepComplete('sample-trip', { tripId })}
              />
            </motion.div>
          )}

          {currentStep === 'consensus-demo' && sampleTripId && (
            <motion.div
              key="consensus-demo"
              variants={stepVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <InteractiveConsensusDemo
                tripId={sampleTripId}
                onComplete={() => handleStepComplete('consensus-demo')}
              />
            </motion.div>
          )}

          {currentStep === 'complete' && (
            <motion.div
              key="complete"
              variants={stepVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <OnboardingComplete
                onFinish={() => handleStepComplete('complete')}
                completionTime={Date.now() - startTime}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default OnboardingFlow;
