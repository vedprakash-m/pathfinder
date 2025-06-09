import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  Users, 
  Clock, 
  TrendingUp, 
  Target,
  Smartphone,
  Tablet,
  Monitor,
  RefreshCw
} from 'lucide-react';

interface OnboardingMetrics {
  totalSessions: number;
  completedSessions: number;
  conversionRate: number;
  averageCompletionTime: number;
  dropOffPoints: Record<string, number>;
  popularTripTypes: Record<string, number>;
  regenerationStats: {
    averageRegenerations: number;
    maxRegenerations: number;
  };
  deviceBreakdown: Record<string, number>;
  timeToFirstAction: number;
  timeToCompletion: number;
}

const OnboardingAnalyticsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<OnboardingMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');

  useEffect(() => {
    fetchMetrics();
  }, [selectedTimeRange]);

  const fetchMetrics = async () => {
    setIsLoading(true);
    try {
      // In a real app, this would fetch from API
      // For now, simulate with mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockMetrics: OnboardingMetrics = {
        totalSessions: 1234,
        completedSessions: 987,
        conversionRate: 79.9,
        averageCompletionTime: 42.3,
        dropOffPoints: {
          'trip-type': 15,
          'sample-trip': 8,
          'consensus-demo': 5,
        },
        popularTripTypes: {
          'family-vacation': 45,
          'weekend-getaway': 35,
          'adventure-trip': 20,
        },
        regenerationStats: {
          averageRegenerations: 1.2,
          maxRegenerations: 5,
        },
        deviceBreakdown: {
          mobile: 60,
          desktop: 30,
          tablet: 10,
        },
        timeToFirstAction: 12.5,
        timeToCompletion: 42.3,
      };
      
      setMetrics(mockMetrics);
    } catch (error) {
      console.error('Failed to fetch onboarding metrics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading onboarding analytics...</p>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Failed to load analytics data.</p>
        <button 
          onClick={fetchMetrics}
          className="mt-4 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Onboarding Analytics</h1>
          <p className="text-gray-600 mt-2">Track user engagement and conversion metrics for the golden path onboarding</p>
        </div>
        
        <select 
          value={selectedTimeRange}
          onChange={(e) => setSelectedTimeRange(e.target.value)}
          className="bg-white border border-gray-300 rounded-lg px-4 py-2"
        >
          <option value="1d">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
        </select>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white p-6 rounded-xl shadow-sm border"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="bg-blue-100 p-3 rounded-lg">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
            <span className="text-sm text-green-600 font-medium">+12%</span>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-800">{metrics.totalSessions.toLocaleString()}</p>
            <p className="text-gray-600 text-sm">Total Sessions</p>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white p-6 rounded-xl shadow-sm border"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="bg-green-100 p-3 rounded-lg">
              <Target className="h-6 w-6 text-green-600" />
            </div>
            <span className="text-sm text-green-600 font-medium">+5%</span>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-800">{metrics.conversionRate}%</p>
            <p className="text-gray-600 text-sm">Conversion Rate</p>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white p-6 rounded-xl shadow-sm border"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="bg-purple-100 p-3 rounded-lg">
              <Clock className="h-6 w-6 text-purple-600" />
            </div>
            <span className="text-sm text-green-600 font-medium">-8s</span>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-800">{metrics.averageCompletionTime}s</p>
            <p className="text-gray-600 text-sm">Avg. Completion Time</p>
            <p className="text-xs text-green-600 mt-1">Target: ≤60s</p>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white p-6 rounded-xl shadow-sm border"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="bg-orange-100 p-3 rounded-lg">
              <TrendingUp className="h-6 w-6 text-orange-600" />
            </div>
            <span className="text-sm text-orange-600 font-medium">{metrics.regenerationStats.averageRegenerations}x</span>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-800">{metrics.completedSessions.toLocaleString()}</p>
            <p className="text-gray-600 text-sm">Completed Sessions</p>
          </div>
        </motion.div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Trip Type Popularity */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white p-6 rounded-xl shadow-sm border"
        >
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Popular Trip Types</h3>
          <div className="space-y-4">
            {Object.entries(metrics.popularTripTypes).map(([type, percentage]) => (
              <div key={type} className="flex items-center justify-between">
                <span className="text-sm text-gray-600 capitalize">{type.replace('-', ' ')}</span>
                <div className="flex items-center space-x-3">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-800 w-8">{percentage}%</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Device Breakdown */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white p-6 rounded-xl shadow-sm border"
        >
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Device Breakdown</h3>
          <div className="space-y-4">
            {Object.entries(metrics.deviceBreakdown).map(([device, percentage]) => {
              const icon = device === 'mobile' ? Smartphone : device === 'tablet' ? Tablet : Monitor;
              const Icon = icon;
              return (
                <div key={device} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Icon className="h-4 w-4 text-gray-500" />
                    <span className="text-sm text-gray-600 capitalize">{device}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-800 w-8">{percentage}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>

      {/* Drop-off Analysis */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-white p-6 rounded-xl shadow-sm border mb-8"
      >
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Drop-off Points</h3>
        <div className="space-y-3">
          {Object.entries(metrics.dropOffPoints).map(([step, dropoffs]) => (
            <div key={step} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700 capitalize">{step.replace('-', ' ')}</span>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-red-600">{dropoffs} drop-offs</span>
                <span className="text-xs text-gray-500">({((dropoffs / metrics.totalSessions) * 100).toFixed(1)}%)</span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Insight:</strong> Most users complete the onboarding successfully. 
            Consider A/B testing different approaches for users who drop off at trip type selection.
          </p>
        </div>
      </motion.div>

      {/* Performance Metrics */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="bg-white p-6 rounded-xl shadow-sm border"
      >
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Performance Targets</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{metrics.timeToFirstAction}s</div>
            <div className="text-sm text-green-700">Time to First Action</div>
            <div className="text-xs text-green-600 mt-1">Target: ≤15s ✓</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{metrics.averageCompletionTime}s</div>
            <div className="text-sm text-green-700">Average Completion</div>
            <div className="text-xs text-green-600 mt-1">Target: ≤60s ✓</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{metrics.conversionRate}%</div>
            <div className="text-sm text-green-700">Conversion Rate</div>
            <div className="text-xs text-green-600 mt-1">Target: ≥75% ✓</div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default OnboardingAnalyticsDashboard;
