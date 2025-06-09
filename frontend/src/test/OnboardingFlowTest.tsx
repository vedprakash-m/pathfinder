import React from 'react';
import { OnboardingFlow } from '../components/onboarding/OnboardingFlow';

// Simple test component to verify onboarding flow works
const OnboardingFlowTest: React.FC = () => {
  const handleComplete = (data: any) => {
    console.log('Onboarding completed with data:', data);
    alert('Onboarding flow completed successfully!');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <OnboardingFlow onComplete={handleComplete} />
    </div>
  );
};

export default OnboardingFlowTest;
