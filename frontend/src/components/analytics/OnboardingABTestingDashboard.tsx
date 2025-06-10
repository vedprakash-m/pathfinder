import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  FlaskConical, 
  TrendingUp, 
  Target, 
  Plus,
  Play,
  Pause,
  Settings
} from 'lucide-react';

interface ABTest {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'running' | 'paused' | 'completed';
  variants: ABTestVariant[];
  metrics: ABTestMetrics;
  startDate: string;
  endDate?: string;
  trafficAllocation: number;
  hypothesis: string;
  successMetric: string;
}

interface ABTestVariant {
  id: string;
  name: string;
  description: string;
  traffic: number;
  conversions: number;
  sessions: number;
  conversionRate: number;
  isControl: boolean;
}

interface ABTestMetrics {
  totalSessions: number;
  totalConversions: number;
  overallConversionRate: number;
  statisticalSignificance: number;
  winningVariant?: string;
  confidenceLevel: number;
}

const OnboardingABTestingDashboard: React.FC = () => {
  const [tests, setTests] = useState<ABTest[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchABTests();
  }, []);

  const fetchABTests = async () => {
    setIsLoading(true);
    try {
      // Mock data for demonstration
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockTests: ABTest[] = [
        {
          id: 'test-1',
          name: 'Welcome Message Variants',
          description: 'Testing different welcome message copy to improve engagement',
          status: 'running',
          hypothesis: 'More personalized welcome messages will increase user engagement and completion rates',
          successMetric: 'Onboarding completion rate',
          trafficAllocation: 100,
          startDate: '2025-06-01',
          variants: [
            {
              id: 'control',
              name: 'Control (Current)',
              description: 'Original welcome message',
              traffic: 50,
              sessions: 512,
              conversions: 410,
              conversionRate: 80.1,
              isControl: true,
            },
            {
              id: 'variant-a',
              name: 'Personalized Message',
              description: 'Welcome message with user name and family context',
              traffic: 50,
              sessions: 498,
              conversions: 423,
              conversionRate: 84.9,
              isControl: false,
            },
          ],
          metrics: {
            totalSessions: 1010,
            totalConversions: 833,
            overallConversionRate: 82.5,
            statisticalSignificance: 95.2,
            winningVariant: 'variant-a',
            confidenceLevel: 95,
          },
        },
        {
          id: 'test-2',
          name: 'Trip Type Card Design',
          description: 'Testing visual design of trip type selection cards',
          status: 'running',
          hypothesis: 'More visual trip type cards will reduce selection time and improve user experience',
          successMetric: 'Time to trip type selection',
          trafficAllocation: 50,
          startDate: '2025-06-05',
          variants: [
            {
              id: 'control',
              name: 'Text-based Cards',
              description: 'Current text-based trip type cards',
              traffic: 50,
              sessions: 234,
              conversions: 187,
              conversionRate: 79.9,
              isControl: true,
            },
            {
              id: 'variant-b',
              name: 'Visual Cards',
              description: 'Image-rich trip type cards with destinations',
              traffic: 50,
              sessions: 241,
              conversions: 203,
              conversionRate: 84.2,
              isControl: false,
            },
          ],
          metrics: {
            totalSessions: 475,
            totalConversions: 390,
            overallConversionRate: 82.1,
            statisticalSignificance: 87.3,
            confidenceLevel: 90,
          },
        },
        {
          id: 'test-3',
          name: 'Sample Trip Generation Speed',
          description: 'Testing different loading times for sample trip generation',
          status: 'completed',
          hypothesis: 'Faster perceived loading will reduce drop-offs during trip generation',
          successMetric: 'Sample trip completion rate',
          trafficAllocation: 100,
          startDate: '2025-05-20',
          endDate: '2025-05-30',
          variants: [
            {
              id: 'control',
              name: 'Normal Speed (3s)',
              description: 'Current 3-second generation time',
              traffic: 33,
              sessions: 412,
              conversions: 325,
              conversionRate: 78.9,
              isControl: true,
            },
            {
              id: 'variant-c',
              name: 'Fast Speed (1.5s)',
              description: 'Reduced to 1.5 seconds with instant feedback',
              traffic: 33,
              sessions: 398,
              conversions: 334,
              conversionRate: 83.9,
              isControl: false,
            },
            {
              id: 'variant-d',
              name: 'Progressive Loading',
              description: 'Show trip details progressively as they load',
              traffic: 34,
              sessions: 401,
              conversions: 347,
              conversionRate: 86.5,
              isControl: false,
            },
          ],
          metrics: {
            totalSessions: 1211,
            totalConversions: 1006,
            overallConversionRate: 83.1,
            statisticalSignificance: 99.1,
            winningVariant: 'variant-d',
            confidenceLevel: 99,
          },
        },
      ];
      
      setTests(mockTests);
    } catch (error) {
      console.error('Failed to fetch A/B tests:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: ABTest['status']) => {
    switch (status) {
      case 'running': return 'text-green-600 bg-green-100';
      case 'paused': return 'text-yellow-600 bg-yellow-100';
      case 'completed': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getVariantPerformance = (variant: ABTestVariant, isWinning: boolean) => {
    if (isWinning) return 'border-green-500 bg-green-50';
    if (variant.isControl) return 'border-gray-300 bg-white';
    return 'border-gray-200 bg-white';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <FlaskConical className="h-8 w-8 animate-pulse text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading A/B tests...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">A/B Testing Dashboard</h1>
          <p className="text-gray-600 mt-2">Optimize onboarding flow through systematic experimentation</p>
        </div>
        
        <button 
          onClick={() => console.log('Create test modal - to be implemented')}
          className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 flex items-center space-x-2"
        >
          <Plus className="h-5 w-5" />
          <span>Create Test</span>
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <FlaskConical className="h-8 w-8 text-blue-500" />
            <span className="text-sm text-green-600 font-medium">+2 this week</span>
          </div>
          <p className="text-2xl font-bold text-gray-800">{tests.length}</p>
          <p className="text-gray-600 text-sm">Total Tests</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <Play className="h-8 w-8 text-green-500" />
          </div>
          <p className="text-2xl font-bold text-gray-800">{tests.filter(t => t.status === 'running').length}</p>
          <p className="text-gray-600 text-sm">Running Tests</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <Target className="h-8 w-8 text-purple-500" />
          </div>
          <p className="text-2xl font-bold text-gray-800">
            {tests.filter(t => t.metrics.statisticalSignificance >= 95).length}
          </p>
          <p className="text-gray-600 text-sm">Significant Results</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <TrendingUp className="h-8 w-8 text-orange-500" />
          </div>
          <p className="text-2xl font-bold text-gray-800">
            +{((tests.find(t => t.id === 'test-3')?.variants.find(v => v.id === 'variant-d')?.conversionRate || 0) - 
                (tests.find(t => t.id === 'test-3')?.variants.find(v => v.isControl)?.conversionRate || 0)).toFixed(1)}%
          </p>
          <p className="text-gray-600 text-sm">Best Improvement</p>
        </div>
      </div>

      {/* Test Results */}
      <div className="space-y-6">
        {tests.map((test) => (
          <motion.div
            key={test.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl shadow-sm border p-6"
          >
            <div className="flex justify-between items-start mb-6">
              <div>
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-xl font-semibold text-gray-800">{test.name}</h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(test.status)}`}>
                    {test.status}
                  </span>
                </div>
                <p className="text-gray-600 mb-3">{test.description}</p>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>Started: {test.startDate}</span>
                  {test.endDate && <span>Ended: {test.endDate}</span>}
                  <span>Traffic: {test.trafficAllocation}%</span>
                </div>
              </div>
              <div className="flex space-x-2">
                {test.status === 'running' && (
                  <button className="p-2 text-gray-500 hover:text-gray-700">
                    <Pause className="h-5 w-5" />
                  </button>
                )}
                <button className="p-2 text-gray-500 hover:text-gray-700">
                  <Settings className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Test Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-800">{test.metrics.totalSessions.toLocaleString()}</div>
                <div className="text-sm text-gray-600">Total Sessions</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-800">{test.metrics.overallConversionRate.toFixed(1)}%</div>
                <div className="text-sm text-gray-600">Overall Conversion</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-800">{test.metrics.statisticalSignificance.toFixed(1)}%</div>
                <div className="text-sm text-gray-600">Statistical Significance</div>
              </div>
            </div>

            {/* Variants */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {test.variants.map((variant) => {
                const isWinning = test.metrics.winningVariant === variant.id;
                return (
                  <div
                    key={variant.id}
                    className={`p-4 rounded-lg border-2 ${getVariantPerformance(variant, isWinning)}`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-800">{variant.name}</h4>
                      {isWinning && <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Winner</span>}
                      {variant.isControl && <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">Control</span>}
                    </div>
                    <p className="text-sm text-gray-600 mb-4">{variant.description}</p>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Sessions</span>
                        <span className="text-sm font-medium">{variant.sessions.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Conversions</span>
                        <span className="text-sm font-medium">{variant.conversions.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Conversion Rate</span>
                        <span className={`text-sm font-bold ${isWinning ? 'text-green-600' : 'text-gray-800'}`}>
                          {variant.conversionRate.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Hypothesis and Results */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h5 className="font-medium text-blue-900 mb-2">Hypothesis</h5>
              <p className="text-sm text-blue-800 mb-3">{test.hypothesis}</p>
              {test.metrics.winningVariant && (
                <div>
                  <h5 className="font-medium text-blue-900 mb-2">Result</h5>
                  <p className="text-sm text-blue-800">
                    Variant "{test.variants.find(v => v.id === test.metrics.winningVariant)?.name}" 
                    performed best with {test.metrics.statisticalSignificance.toFixed(1)}% confidence.
                    {test.status === 'completed' && ' Recommend implementing this variant.'}
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default OnboardingABTestingDashboard;
