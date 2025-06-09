import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ThumbsUp, 
  ThumbsDown, 
  Users, 
  Trophy,
  Sparkles,
  ChevronRight,
  Zap,
  CheckCircle2
} from 'lucide-react';

interface FamilyMember {
  id: string;
  name: string;
  avatar: string;
  role: string;
}

interface Activity {
  id: string;
  name: string;
  description: string;
  image: string;
  votes: { [memberId: string]: 'up' | 'down' | null };
  comments: { memberId: string; message: string; timestamp: Date }[];
  consensusScore: number;
}

interface DecisionScenario {
  id: string;
  title: string;
  description: string;
  activities: Activity[];
  currentStep: 'voting' | 'discussion' | 'resolution';
}

const sampleFamily: FamilyMember[] = [
  { id: 'dad', name: 'David', avatar: '👨‍💼', role: 'Dad' },
  { id: 'mom', name: 'Sarah', avatar: '👩‍💻', role: 'Mom' },
  { id: 'teen', name: 'Alex', avatar: '🧑‍🎓', role: 'Teen (16)' },
];

const decisionScenario: DecisionScenario = {
  id: 'dinner-choice',
  title: 'Where should we have dinner tonight?',
  description: 'Your family needs to decide on a restaurant for tonight. See how everyone\'s preferences are balanced!',
  activities: [
    {
      id: 'italian',
      name: 'Mario\'s Italian Bistro',
      description: 'Authentic Italian cuisine with fresh pasta and wood-fired pizza',
      image: '🍝',
      votes: { dad: null, mom: null, teen: null },
      comments: [],
      consensusScore: 0
    },
    {
      id: 'asian',
      name: 'Sakura Sushi & Grill',
      description: 'Fresh sushi, hibachi grills, and modern Asian fusion',
      image: '🍣',
      votes: { dad: null, mom: null, teen: null },
      comments: [],
      consensusScore: 0
    },
    {
      id: 'american',
      name: 'The Local Burger Co.',
      description: 'Gourmet burgers, craft fries, and local craft beers',
      image: '🍔',
      votes: { dad: null, mom: null, teen: null },
      comments: [],
      consensusScore: 0
    }
  ],
  currentStep: 'voting'
};

interface InteractiveConsensusDemoProps {
  onComplete: () => void;
}

const InteractiveConsensusDemo: React.FC<InteractiveConsensusDemoProps> = ({ onComplete }) => {
  const [scenario, setScenario] = useState<DecisionScenario>(decisionScenario);
  const [currentMemberIndex, setCurrentMemberIndex] = useState(0);
  const [userVotes, setUserVotes] = useState<{ [activityId: string]: 'up' | 'down' | null }>({});
  const [showResults, setShowResults] = useState(false);

  const currentMember = sampleFamily[currentMemberIndex];

  // Simulate AI family member votes
  useEffect(() => {
    if (currentMemberIndex > 0 && currentMemberIndex < sampleFamily.length) {
      const timer = setTimeout(() => {
        simulateAIVote();
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [currentMemberIndex]);

  const simulateAIVote = () => {
    const member = sampleFamily[currentMemberIndex];
    const newScenario = { ...scenario };
    
    // Simulate different preferences for each family member
    newScenario.activities.forEach(activity => {
      let vote: 'up' | 'down' | null = null;
      
      if (member.id === 'mom') {
        // Mom prefers Italian and Asian cuisine
        if (activity.id === 'italian' || activity.id === 'asian') {
          vote = Math.random() > 0.3 ? 'up' : 'down';
        } else {
          vote = Math.random() > 0.7 ? 'up' : 'down';
        }
      } else if (member.id === 'teen') {
        // Teen prefers burgers and casual dining
        if (activity.id === 'american') {
          vote = 'up';
        } else if (activity.id === 'asian') {
          vote = Math.random() > 0.5 ? 'up' : 'down';
        } else {
          vote = 'down';
        }
      }
      
      activity.votes[member.id] = vote;
    });

    setScenario(newScenario);
    
    if (currentMemberIndex < sampleFamily.length - 1) {
      setTimeout(() => {
        setCurrentMemberIndex(currentMemberIndex + 1);
      }, 1000);
    } else {
      setTimeout(() => {
        calculateConsensus();
      }, 1000);
    }
  };

  const handleUserVote = (activityId: string, vote: 'up' | 'down') => {
    const newUserVotes = { ...userVotes, [activityId]: vote };
    setUserVotes(newUserVotes);
    
    const newScenario = { ...scenario };
    newScenario.activities.forEach(activity => {
      if (activity.id === activityId) {
        activity.votes[currentMember.id] = vote;
      }
    });
    
    setScenario(newScenario);
    
    // Check if user has voted on all activities
    const totalVotes = Object.values(newUserVotes).filter(v => v !== null).length;
    if (totalVotes === scenario.activities.length) {
      setTimeout(() => {
        setCurrentMemberIndex(1);
      }, 1000);
    }
  };

  const calculateConsensus = () => {
    const newScenario = { ...scenario };
    
    newScenario.activities.forEach(activity => {
      const votes = Object.values(activity.votes);
      const upVotes = votes.filter(v => v === 'up').length;
      const downVotes = votes.filter(v => v === 'down').length;
      const totalVotes = upVotes + downVotes;
      
      // Calculate consensus score (0-100)
      if (totalVotes === 0) {
        activity.consensusScore = 0;
      } else {
        const positiveRatio = upVotes / totalVotes;
        activity.consensusScore = Math.round(positiveRatio * 100);
      }
      
      // Add AI comments based on votes
      if (activity.votes.mom === 'up') {
        activity.comments.push({
          memberId: 'mom',
          message: 'Love this choice! Great reviews online.',
          timestamp: new Date()
        });
      }
      
      if (activity.votes.teen === 'up') {
        activity.comments.push({
          memberId: 'teen',
          message: 'Yes! My friends love this place 🔥',
          timestamp: new Date()
        });
      } else if (activity.votes.teen === 'down') {
        activity.comments.push({
          memberId: 'teen',
          message: 'Not really my vibe...',
          timestamp: new Date()
        });
      }
    });
    
    // Sort by consensus score
    newScenario.activities.sort((a, b) => b.consensusScore - a.consensusScore);
    
    setScenario(newScenario);
    setShowResults(true);
  };

  const getVoteCount = (activity: Activity, voteType: 'up' | 'down') => {
    return Object.values(activity.votes).filter(vote => vote === voteType).length;
  };

  const handleComplete = () => {
    onComplete();
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-800 mb-4">
          Experience Family Decision Making
        </h2>
        <p className="text-lg text-gray-600">
          See how Pathfinder helps families reach consensus through collaborative voting
        </p>
      </div>

      {/* Scenario Card */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
        <div className="flex items-center space-x-3 mb-4">
          <Users className="h-6 w-6 text-blue-500" />
          <h3 className="text-xl font-semibold text-gray-800">{scenario.title}</h3>
        </div>
        <p className="text-gray-600 mb-6">{scenario.description}</p>

        {/* Current Voter Indicator */}
        {!showResults && (
          <div className="bg-blue-50 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{currentMember.avatar}</span>
                <div>
                  <h4 className="font-semibold text-gray-800">
                    {currentMemberIndex === 0 ? 'Your turn!' : `${currentMember.name} is voting...`}
                  </h4>
                  <p className="text-sm text-gray-600">{currentMember.role}</p>
                </div>
              </div>
              {currentMemberIndex > 0 && (
                <div className="flex items-center space-x-2 text-blue-600">
                  <Sparkles className="h-4 w-4 animate-pulse" />
                  <span className="text-sm">AI Simulation</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Activities */}
        <div className="space-y-4">
          {scenario.activities.map((activity) => (
            <motion.div
              key={activity.id}
              className={`border rounded-lg p-4 transition-all ${
                showResults && activity.consensusScore === Math.max(...scenario.activities.map(a => a.consensusScore))
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              layout
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <span className="text-3xl">{activity.image}</span>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-800 mb-1">{activity.name}</h4>
                    <p className="text-sm text-gray-600 mb-3">{activity.description}</p>
                    
                    {/* Comments */}
                    {activity.comments.length > 0 && (
                      <div className="space-y-2 mb-3">
                        {activity.comments.map((comment, index) => (
                          <div key={index} className="flex items-center space-x-2 text-sm">
                            <span className="text-lg">
                              {sampleFamily.find(m => m.id === comment.memberId)?.avatar}
                            </span>
                            <span className="text-gray-700">{comment.message}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  {/* Voting Buttons */}
                  {!showResults && currentMemberIndex === 0 && (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleUserVote(activity.id, 'up')}
                        className={`p-2 rounded-full transition-all ${
                          userVotes[activity.id] === 'up'
                            ? 'bg-green-500 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-green-100 hover:text-green-600'
                        }`}
                        disabled={userVotes[activity.id] !== null}
                      >
                        <ThumbsUp className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleUserVote(activity.id, 'down')}
                        className={`p-2 rounded-full transition-all ${
                          userVotes[activity.id] === 'down'
                            ? 'bg-red-500 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-red-100 hover:text-red-600'
                        }`}
                        disabled={userVotes[activity.id] !== null}
                      >
                        <ThumbsDown className="h-4 w-4" />
                      </button>
                    </div>
                  )}

                  {/* Vote Count */}
                  <div className="flex items-center space-x-3 text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      <ThumbsUp className="h-4 w-4 text-green-500" />
                      <span>{getVoteCount(activity, 'up')}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <ThumbsDown className="h-4 w-4 text-red-500" />
                      <span>{getVoteCount(activity, 'down')}</span>
                    </div>
                  </div>

                  {/* Consensus Score */}
                  {showResults && (
                    <div className="text-right">
                      <div className={`text-2xl font-bold ${
                        activity.consensusScore >= 75 ? 'text-green-500' :
                        activity.consensusScore >= 50 ? 'text-yellow-500' :
                        'text-red-500'
                      }`}>
                        {activity.consensusScore}%
                      </div>
                      <div className="text-xs text-gray-500">consensus</div>
                      {activity.consensusScore === Math.max(...scenario.activities.map(a => a.consensusScore)) && (
                        <div className="flex items-center space-x-1 text-green-600 mt-1">
                          <Trophy className="h-4 w-4" />
                          <span className="text-xs font-semibold">Winner!</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Results Summary */}
      {showResults && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 mb-8"
        >
          <div className="flex items-center space-x-3 mb-4">
            <CheckCircle2 className="h-6 w-6 text-green-500" />
            <h3 className="text-xl font-semibold text-gray-800">Decision Reached!</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Based on everyone's votes and preferences, Pathfinder recommends <strong>{scenario.activities[0].name}</strong> 
            with a {scenario.activities[0].consensusScore}% family consensus score.
          </p>
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-semibold text-gray-800 mb-2">How consensus was calculated:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Weighted voting based on family member preferences</li>
              <li>• Comments and discussion factors included</li>
              <li>• AI considers individual and group satisfaction</li>
              <li>• Alternative suggestions provided for future decisions</li>
            </ul>
          </div>
        </motion.div>
      )}

      {/* Call to Action */}
      {showResults && (
        <div className="text-center">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <Zap className="h-6 w-6 text-yellow-500" />
              <h3 className="text-2xl font-bold text-gray-800">Amazing! You've experienced Pathfinder's magic</h3>
            </div>
            <p className="text-gray-600 mb-6">
              This collaborative decision-making works for restaurants, activities, destinations, and every aspect of your trip planning.
            </p>
            <button
              onClick={handleComplete}
              className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-600 hover:to-purple-600 transition-all transform hover:scale-105 flex items-center space-x-2 mx-auto"
            >
              <span>Complete Onboarding</span>
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveConsensusDemo;
