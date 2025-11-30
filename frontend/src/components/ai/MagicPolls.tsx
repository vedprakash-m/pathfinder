import React, { useState, useEffect } from 'react';
import { Vote, BarChart3, Clock, Brain, CheckCircle, XCircle } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useWebSocket } from '@/hooks/useWebSocket';

interface PollOption {
  value: string;
  label?: string;
  description?: string;
  metadata?: any;
  ai_insights?: any;
}

interface MagicPoll {
  id: string;
  title: string;
  description?: string;
  poll_type: string;
  options: PollOption[];
  status: 'active' | 'completed' | 'expired' | 'cancelled';
  expires_at?: string;
  created_at: string;
  creator_id: string;
}

interface PollResults {
  total_responses: number;
  results: Array<{
    option: string;
    votes: number;
    percentage: number;
    details: PollOption;
  }>;
}

interface AIAnalysis {
  summary: string;
  patterns: string[];
  conflicts: Array<{
    type: string;
    description: string;
    options: string[];
  }>;
  consensus_level: number;
}

interface ConsensusRecommendation {
  recommended_choice: string;
  vote_count: number;
  total_votes: number;
  consensus_strength: number;
  confidence: 'high' | 'moderate' | 'low';
  rationale: string;
}

interface MagicPollsProps {
  tripId: string;
  className?: string;
  onPollCreate?: (poll: MagicPoll) => void;
  onPollResponse?: (pollId: string, response: any) => void;
}

export const MagicPolls: React.FC<MagicPollsProps> = ({
  tripId,
  className = '',
  onPollCreate: _onPollCreate,
  onPollResponse
}) => {
  const { token } = useAuth();
  const [polls, setPolls] = useState<MagicPoll[]>([]);
  const [selectedPoll, setSelectedPoll] = useState<MagicPoll | null>(null);
  const [pollResults, setPollResults] = useState<PollResults | null>(null);
  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysis | null>(null);
  const [consensusRecommendation, setConsensusRecommendation] = useState<ConsensusRecommendation | null>(null);
  const [_isLoading, setIsLoading] = useState(false);
  const [_showCreateForm, setShowCreateForm] = useState(false);
  const [realtimeUpdateCount, setRealtimeUpdateCount] = useState(0);
  const [showRealtimeIndicator, setShowRealtimeIndicator] = useState(false);

  useEffect(() => {
    fetchTripPolls();
  }, [tripId]);

  // WebSocket integration for real-time poll updates
  const { messages: pollNotifications } = useWebSocket<{
    type: string;
    event: string;
    poll_id: string;
    voter_id?: string;
    data: any;
    timestamp: string;
  }>(['poll_notification'], [tripId]);

  // Handle real-time poll notifications
  useEffect(() => {
    if (pollNotifications.length > 0) {
      const latestNotification = pollNotifications[pollNotifications.length - 1];
      
      // Show real-time update indicator
      setShowRealtimeIndicator(true);
      setRealtimeUpdateCount(prev => prev + 1);
      
      // Hide indicator after 3 seconds
      const timer = setTimeout(() => {
        setShowRealtimeIndicator(false);
      }, 3000);
      
      switch (latestNotification.event) {
        case 'poll_created':
          // Refresh polls list when new poll is created
          fetchTripPolls();
          break;
        
        case 'poll_vote':
          // Update poll results in real-time when someone votes
          if (selectedPoll?.id === latestNotification.poll_id) {
            fetchPollDetails(latestNotification.poll_id);
          }
          // Also update the poll in the list
          setPolls(prevPolls => 
            prevPolls.map(poll => 
              poll.id === latestNotification.poll_id 
                ? { ...poll, ...latestNotification.data }
                : poll
            )
          );
          break;
        
        case 'poll_results':
          // Update AI analysis and results when available
          if (selectedPoll?.id === latestNotification.poll_id) {
            setAiAnalysis(latestNotification.data.ai_analysis);
            setConsensusRecommendation(latestNotification.data.consensus);
          }
          break;
        
        case 'poll_completed':
          // Update poll status and show final consensus
          if (selectedPoll?.id === latestNotification.poll_id) {
            setConsensusRecommendation(latestNotification.data);
            fetchPollDetails(latestNotification.poll_id);
          }
          fetchTripPolls();
          break;
      }
      
      return () => clearTimeout(timer);
    }
  }, [pollNotifications, selectedPoll, tripId]);

  const fetchTripPolls = async () => {
    try {
      const response = await fetch(`/api/v1/polls/trip/${tripId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPolls(data.polls);
      }
    } catch (error) {
      console.error('Error fetching polls:', error);
    }
  };

  const fetchPollDetails = async (pollId: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/v1/polls/${pollId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setPollResults(data.data.results);
          setAiAnalysis(data.data.ai_analysis);
          setConsensusRecommendation(data.data.consensus_recommendation);
        }
      }
    } catch (error) {
      console.error('Error fetching poll details:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const submitPollResponse = async (pollId: string, choice: string, preferences?: any) => {
    try {
      const response = await fetch(`/api/v1/polls/${pollId}/respond`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          response: {
            choice,
            preferences,
            comments: ''
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          // Refresh poll details
          await fetchPollDetails(pollId);
          await fetchTripPolls();
          
          if (onPollResponse) {
            onPollResponse(pollId, { choice, preferences });
          }
        }
      }
    } catch (error) {
      console.error('Error submitting poll response:', error);
    }
  };

  const formatTimeRemaining = (expiresAt: string) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diff = expiry.getTime() - now.getTime();
    
    if (diff <= 0) return 'Expired';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days} day${days > 1 ? 's' : ''} left`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m left`;
    } else {
      return `${minutes}m left`;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Vote className="h-5 w-5 text-green-500" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-blue-500" />;
      case 'expired':
        return <XCircle className="h-5 w-5 text-gray-500" />;
      case 'cancelled':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Vote className="h-5 w-5 text-gray-500" />;
    }
  };

  const getConsensusColor = (level: number) => {
    if (level >= 0.8) return 'text-green-600';
    if (level >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const PollCard: React.FC<{ poll: MagicPoll }> = ({ poll }) => (
    <div 
      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => {
        setSelectedPoll(poll);
        fetchPollDetails(poll.id);
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getStatusIcon(poll.status)}
          <h3 className="font-medium text-gray-900">{poll.title}</h3>
        </div>
        <span className={`px-2 py-1 text-xs rounded-full ${
          poll.status === 'active' ? 'bg-green-100 text-green-800' :
          poll.status === 'completed' ? 'bg-blue-100 text-blue-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {poll.status}
        </span>
      </div>
      
      {poll.description && (
        <p className="text-gray-600 text-sm mb-3">{poll.description}</p>
      )}
      
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span className="capitalize">{poll.poll_type.replace('_', ' ')}</span>
        {poll.expires_at && poll.status === 'active' && (
          <div className="flex items-center space-x-1">
            <Clock className="h-4 w-4" />
            <span>{formatTimeRemaining(poll.expires_at)}</span>
          </div>
        )}
      </div>
    </div>
  );

  const PollDetails: React.FC = () => {
    if (!selectedPoll) return null;

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">{selectedPoll.title}</h2>
          <button
            onClick={() => setSelectedPoll(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            ×
          </button>
        </div>

        {selectedPoll.description && (
          <p className="text-gray-600 mb-4">{selectedPoll.description}</p>
        )}

        {/* Poll Options */}
        <div className="mb-6">
          <h3 className="font-medium text-gray-900 mb-3">Options</h3>
          <div className="space-y-2">
            {selectedPoll.options.map((option, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium">{option.label || option.value}</span>
                    {option.description && (
                      <p className="text-sm text-gray-600 mt-1">{option.description}</p>
                    )}
                  </div>
                  {selectedPoll.status === 'active' && (
                    <button
                      onClick={() => submitPollResponse(selectedPoll.id, option.value)}
                      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                    >
                      Vote
                    </button>
                  )}
                </div>
                
                {/* AI Insights */}
                {option.ai_insights && (
                  <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                    <div className="flex items-center space-x-1 mb-1">
                      <Brain className="h-4 w-4 text-blue-500" />
                      <span className="text-xs font-medium text-blue-800">AI Insights</span>
                    </div>
                    <div className="text-xs text-blue-700">
                      {Object.entries(option.ai_insights).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="capitalize">{key.replace('_', ' ')}:</span>
                          <span>{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Results */}
        {pollResults && (
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Results ({pollResults.total_responses} responses)</span>
            </h3>
            <div className="space-y-2">
              {pollResults.results.map((result, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <span className="w-24 text-sm font-medium truncate">{result.option}</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${result.percentage}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-600 w-12 text-right">
                    {result.percentage}%
                  </span>
                  <span className="text-sm text-gray-500 w-8 text-right">
                    ({result.votes})
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI Analysis */}
        {aiAnalysis && (
          <div className="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
            <h3 className="font-medium text-purple-900 mb-3 flex items-center space-x-2">
              <Brain className="h-5 w-5" />
              <span>AI Analysis</span>
            </h3>
            
            <div className="text-sm text-purple-800 mb-3">
              <strong>Consensus Level:</strong>
              <span className={`ml-2 font-medium ${getConsensusColor(aiAnalysis.consensus_level)}`}>
                {Math.round(aiAnalysis.consensus_level * 100)}%
              </span>
            </div>
            
            <p className="text-purple-700 mb-3">{aiAnalysis.summary}</p>
            
            {aiAnalysis.conflicts && aiAnalysis.conflicts.length > 0 && (
              <div className="mb-3">
                <strong className="text-purple-900">Conflicts Identified:</strong>
                <ul className="list-disc list-inside mt-1 text-purple-700">
                  {aiAnalysis.conflicts.map((conflict, index) => (
                    <li key={index}>{conflict.description}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {aiAnalysis.patterns && aiAnalysis.patterns.length > 0 && (
              <div>
                <strong className="text-purple-900">Patterns:</strong>
                <ul className="list-disc list-inside mt-1 text-purple-700">
                  {aiAnalysis.patterns.map((pattern, index) => (
                    <li key={index}>{pattern}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Consensus Recommendation */}
        {consensusRecommendation && consensusRecommendation.recommended_choice && (
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <h3 className="font-medium text-green-900 mb-2 flex items-center space-x-2">
              <CheckCircle className="h-5 w-5" />
              <span>AI Recommendation</span>
            </h3>
            <div className="text-green-800">
              <p className="font-medium mb-1">
                Recommended: {consensusRecommendation.recommended_choice}
              </p>
              <p className="text-sm mb-2">
                {consensusRecommendation.vote_count} out of {consensusRecommendation.total_votes} votes 
                ({Math.round(consensusRecommendation.consensus_strength * 100)}% consensus)
              </p>
              <p className="text-sm">
                <strong>Confidence:</strong> {consensusRecommendation.confidence}
              </p>
              <p className="text-sm mt-2">{consensusRecommendation.rationale}</p>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Real-time update indicator */}
      {showRealtimeIndicator && (
        <div className="fixed top-4 right-4 z-50 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center space-x-2 animate-pulse">
          <div className="h-2 w-2 bg-white rounded-full animate-ping"></div>
          <span className="text-sm font-medium">Live Update</span>
        </div>
      )}
      
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
          <Vote className="h-6 w-6 text-blue-500" />
          <span>Magic Polls</span>
          {realtimeUpdateCount > 0 && (
            <span className="ml-2 px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
              {realtimeUpdateCount} live update{realtimeUpdateCount > 1 ? 's' : ''}
            </span>
          )}
        </h2>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Create Poll
        </button>
      </div>

      {selectedPoll ? (
        <PollDetails />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {polls.map((poll) => (
            <PollCard key={poll.id} poll={poll} />
          ))}
          
          {polls.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-500">
              <Vote className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium mb-2">No polls yet</h3>
              <p className="text-sm">Create your first Magic Poll to start making group decisions with AI assistance.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
