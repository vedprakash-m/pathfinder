import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Card,
  CardHeader,
  Title2,
  Title3,
  Body1,
  Body2,
  // Badge,
  Button,
  Spinner,
} from '@fluentui/react-components';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  UserGroupIcon,
  ChartBarIcon,
  ChatBubbleBottomCenterTextIcon,
  ScaleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

interface ConsensusData {
  consensus_score: number;
  status: string;
  family_count: number;
  conflicts_summary: {
    total: number;
    critical: number;
    high: number;
  };
  next_steps: string[];
}

interface ConsensusDashboardProps {
  tripId: string;
  onActionNeeded?: (actionType: string) => void;
}

export const ConsensusDashboard: React.FC<ConsensusDashboardProps> = ({
  tripId,
  onActionNeeded,
}) => {
  const [loading, setLoading] = useState(true);
  const [consensusData, setConsensusData] = useState<ConsensusData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchConsensusData();
  }, [tripId]);

  const fetchConsensusData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/consensus/dashboard/${tripId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch consensus data');
      }

      const result = await response.json();
      setConsensusData(result.dashboard_data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load consensus data');
      console.error('Error fetching consensus data:', err);
    } finally {
      setLoading(false);
    }
  };

  const analyzeConsensus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/consensus/analyze/${tripId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to analyze consensus');
      }

      // Refresh the dashboard data
      await fetchConsensusData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze consensus');
    } finally {
      setLoading(false);
    }
  };

  const getConsensusColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    if (score >= 0.4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Strong Consensus':
        return <CheckCircleIcon className="w-6 h-6 text-green-600" />;
      case 'Needs Discussion':
        return <ChatBubbleBottomCenterTextIcon className="w-6 h-6 text-yellow-600" />;
      default:
        return <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />;
    }
  };

  if (loading) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <div className="flex items-center justify-center p-8">
          <Spinner size="large" />
          <Body1 className="ml-3">Analyzing family consensus...</Body1>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <div className="flex items-center gap-3">
            <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
            <Title2>Consensus Analysis Error</Title2>
          </div>
        </CardHeader>
        <div className="p-4">
          <Body1 className="text-red-600 mb-4">{error}</Body1>
          <Button onClick={fetchConsensusData}>Retry</Button>
        </div>
      </Card>
    );
  }

  if (!consensusData) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <Title2>Family Consensus</Title2>
        </CardHeader>
        <div className="p-4">
          <Body1 className="text-neutral-600 mb-4">
            No consensus data available. Click below to analyze family preferences.
          </Body1>
          <Button appearance="primary" onClick={analyzeConsensus}>
            Analyze Consensus
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-4xl mx-auto space-y-6"
    >
      {/* Main Consensus Score */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <ScaleIcon className="w-6 h-6 text-primary-600" />
            <Title2>Family Consensus Overview</Title2>
          </div>
        </CardHeader>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              {getStatusIcon(consensusData.status)}
              <div>
                <Title3>{consensusData.status}</Title3>
                <Body2 className="text-neutral-600">
                  {consensusData.family_count} families participating
                </Body2>
              </div>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-primary-600">
                {Math.round(consensusData.consensus_score * 100)}%
              </div>
              <Body2 className="text-neutral-600">Consensus Score</Body2>
            </div>
          </div>

          {/* Consensus Progress Bar */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <Body2 className="font-medium">Agreement Level</Body2>
              <Body2 className="text-neutral-600">
                {Math.round(consensusData.consensus_score * 100)}%
              </Body2>
            </div>
            <div className="w-full bg-neutral-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-300 ${getConsensusColor(consensusData.consensus_score)}`}
                style={{ width: `${consensusData.consensus_score * 100}%` }}
              />
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-neutral-50 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <UserGroupIcon className="w-5 h-5 text-neutral-600" />
                <div>
                  <Body1 className="font-medium">{consensusData.family_count}</Body1>
                  <Body2 className="text-neutral-600">Families</Body2>
                </div>
              </div>
            </div>
            
            <div className="bg-neutral-50 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <ExclamationTriangleIcon className="w-5 h-5 text-orange-600" />
                <div>
                  <Body1 className="font-medium">{consensusData.conflicts_summary.total}</Body1>
                  <Body2 className="text-neutral-600">Total Conflicts</Body2>
                </div>
              </div>
            </div>
            
            <div className="bg-neutral-50 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <ClockIcon className="w-5 h-5 text-red-600" />
                <div>
                  <Body1 className="font-medium">{consensusData.conflicts_summary.critical}</Body1>
                  <Body2 className="text-neutral-600">Critical Issues</Body2>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Next Steps */}
      {consensusData.next_steps.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <ChartBarIcon className="w-6 h-6 text-primary-600" />
              <Title2>Recommended Next Steps</Title2>
            </div>
          </CardHeader>
          <div className="p-6">
            <div className="space-y-3">
              {consensusData.next_steps.map((step, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center mt-0.5">
                    <span className="text-sm font-medium text-primary-600">{index + 1}</span>
                  </div>
                  <Body1 className="flex-1">{step}</Body1>
                </div>
              ))}
            </div>

            <div className="flex gap-3 mt-6">
              <Button appearance="primary" onClick={analyzeConsensus}>
                Re-analyze Consensus
              </Button>
              {consensusData.consensus_score >= 0.8 && (
                <Button
                  appearance="primary"
                  onClick={() => onActionNeeded?.('generate_itinerary')}
                >
                  Generate Itinerary
                </Button>
              )}
            </div>
          </div>
        </Card>
      )}
    </motion.div>
  );
}; 