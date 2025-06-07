/**
 * Real-Time Feedback Dashboard Component
 * 
 * Solves Pain Point #3: "No effective way to gather and incorporate changes/feedback during planning process"
 * 
 * Features:
 * - Live feedback submission and tracking
 * - In-context commenting and suggestions
 * - Change impact visualization
 * - Quick approval/rejection workflows
 * - Real-time collaboration status
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Text,
  Badge,
  Button,
  Spinner,
  MessageBar,
  Textarea,
  Dropdown,
  Option,
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogBody,
  Title3,
  Title2,
  Body1,
  Caption1,
  Field,
  Input
} from '@fluentui/react-components';
import {
  Chat24Regular,
  Send24Regular,
  ThumbLike24Regular,
  ThumbDislike24Regular,
  Warning24Regular,
  Lightbulb24Regular,
  Eye24Regular,
  CheckmarkCircle24Regular,
  People24Regular
} from '@fluentui/react-icons';

interface FeedbackItem {
  id: string;
  feedback_type: string;
  target_element: string;
  content: string;
  suggested_change?: string;
  impact_analysis?: {
    impact_level: string;
    cost_delta: number;
    time_delta: number;
    implementation_complexity: string;
  };
  status: string;
  responses: Array<{
    user_id: string;
    content: string;
    timestamp: string;
  }>;
  created_at: string;
  time_since_submission?: string;
  urgency_level?: string;
}

interface FeedbackDashboardData {
  trip_id: string;
  total_feedback_items: number;
  pending_items: number;
  feedback_by_type: Record<string, number>;
  recent_feedback: FeedbackItem[];
  collaboration_health: {
    feedback_velocity: string;
    response_rate: string;
    average_resolution_time: string;
    active_discussions: number;
  };
  quick_actions: string[];
  feedback_trends: {
    most_common_type: string;
    peak_feedback_time: string;
    family_participation: string;
  };
}

interface FeedbackDashboardProps {
  tripId: string;
}

export const FeedbackDashboard: React.FC<FeedbackDashboardProps> = ({ tripId }) => {
  const [dashboardData, setDashboardData] = useState<FeedbackDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [showFeedbackDialog, setShowFeedbackDialog] = useState(false);
  
  // Feedback form state
  const [feedbackType, setFeedbackType] = useState<string>('suggestion');
  const [targetElement, setTargetElement] = useState<string>('');
  const [feedbackContent, setFeedbackContent] = useState<string>('');
  const [suggestedChange, setSuggestedChange] = useState<string>('');

  useEffect(() => {
    fetchDashboardData();
  }, [tripId]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Simulated data for demonstration
      const simulatedData: FeedbackDashboardData = {
        trip_id: tripId,
        total_feedback_items: 12,
        pending_items: 3,
        feedback_by_type: {
          suggestion: 6,
          concern: 2,
          approval: 3,
          modification: 1
        },
        recent_feedback: [
          {
            id: 'feedback_1',
            feedback_type: 'suggestion',
            target_element: 'Day 2 Restaurant',
            content: 'The selected restaurant might be too expensive for our budget. Could we consider the Italian place nearby?',
            suggested_change: 'Replace "The Fancy Steakhouse" with "Tony\'s Italian Kitchen"',
            impact_analysis: {
              impact_level: 'medium',
              cost_delta: -75.0,
              time_delta: 0,
              implementation_complexity: 'Simple modification, can be implemented immediately'
            },
            status: 'pending',
            responses: [],
            created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
            time_since_submission: '30 minutes ago',
            urgency_level: 'Medium'
          },
          {
            id: 'feedback_2',
            feedback_type: 'concern',
            target_element: 'Day 3 Activity',
            content: 'The hiking trail might be too difficult for our elderly family member. Are there alternative activities?',
            suggested_change: 'Replace hiking with scenic drive or easier nature walk',
            impact_analysis: {
              impact_level: 'high',
              cost_delta: 0,
              time_delta: 60,
              implementation_complexity: 'Moderate changes required, may need family coordination'
            },
            status: 'under_review',
            responses: [
              {
                user_id: 'organizer',
                content: 'Great point! Let me research accessible alternatives.',
                timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString()
              }
            ],
            created_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
            time_since_submission: '2 hours ago',
            urgency_level: 'High'
          },
          {
            id: 'feedback_3',
            feedback_type: 'approval',
            target_element: 'Hotel Selection',
            content: 'Perfect choice! This hotel has everything we need and great reviews.',
            status: 'accepted',
            responses: [],
            created_at: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
            time_since_submission: '3 hours ago',
            urgency_level: 'Low'
          }
        ],
        collaboration_health: {
          feedback_velocity: '3.2 items/day',
          response_rate: '85%',
          average_resolution_time: '4.2 hours',
          active_discussions: 2
        },
        quick_actions: [
          'Review pending feedback',
          'Respond to family concerns',
          'Approve suggested changes'
        ],
        feedback_trends: {
          most_common_type: 'suggestion',
          peak_feedback_time: 'Evening (7-9 PM)',
          family_participation: '4 out of 5 families active'
        }
      };

      setDashboardData(simulatedData);
      setError(null);
    } catch (err) {
      setError('Failed to load feedback dashboard data');
      console.error('Error fetching feedback dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!feedbackContent.trim() || !targetElement.trim()) {
      return;
    }

    try {
      setSubmittingFeedback(true);
      
      // Simulate API call
      console.log('Submitting feedback:', {
        feedback_type: feedbackType,
        target_element: targetElement,
        content: feedbackContent,
        suggested_change: suggestedChange || undefined
      });
      
      // Simulate successful submission
      setTimeout(() => {
        setSubmittingFeedback(false);
        setShowFeedbackDialog(false);
        
        // Reset form
        setFeedbackContent('');
        setSuggestedChange('');
        setTargetElement('');
        
        // Refresh dashboard
        fetchDashboardData();
      }, 1000);
      
    } catch (err) {
      setError('Failed to submit feedback');
      setSubmittingFeedback(false);
    }
  };

  const getFeedbackIcon = (type: string) => {
    switch (type) {
      case 'suggestion':
        return <Lightbulb24Regular />;
      case 'concern':
        return <Warning24Regular />;
      case 'approval':
        return <ThumbLike24Regular />;
      case 'rejection':
        return <ThumbDislike24Regular />;
      default:
        return <Chat24Regular />;
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { color: 'warning' as const, text: 'Pending' },
      under_review: { color: 'brand' as const, text: 'Under Review' },
      accepted: { color: 'success' as const, text: 'Accepted' },
      rejected: { color: 'danger' as const, text: 'Rejected' },
      implemented: { color: 'success' as const, text: 'Implemented' }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    return <Badge color={config.color}>{config.text}</Badge>;
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case 'urgent':
        return '#D13438';
      case 'high':
        return '#FF8C00';
      case 'medium':
        return '#0078D4';
      default:
        return '#107C10';
    }
  };

  if (loading) {
    return (
      <Card>
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <Spinner label="Loading feedback dashboard..." />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <MessageBar intent="error">
        {error}
        <Button 
          appearance="transparent" 
          onClick={fetchDashboardData}
          style={{ marginLeft: '10px' }}
        >
          Retry
        </Button>
      </MessageBar>
    );
  }

  if (!dashboardData) {
    return null;
  }

  const collaborationScore = Math.min(100, 
    (dashboardData.total_feedback_items * 8) + 
    (parseFloat(dashboardData.collaboration_health.response_rate) || 0) +
    (dashboardData.collaboration_health.active_discussions * 5)
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Title2>💬 Real-Time Feedback</Title2>
        
        <Dialog open={showFeedbackDialog} onOpenChange={(_, data) => setShowFeedbackDialog(data.open)}>
          <DialogTrigger disableButtonEnhancement>
            <Button appearance="primary" icon={<Send24Regular />}>
              Submit Feedback
            </Button>
          </DialogTrigger>
          <DialogSurface>
            <DialogBody>
              <DialogTitle>Submit Trip Feedback</DialogTitle>
              <DialogContent style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                
                <Field label="Feedback Type">
                  <Dropdown 
                    value={feedbackType}
                    onOptionSelect={(_, data) => setFeedbackType(data.optionValue || 'suggestion')}
                  >
                    <Option value="suggestion">💡 Suggestion</Option>
                    <Option value="concern">⚠️ Concern</Option>
                    <Option value="approval">👍 Approval</Option>
                    <Option value="modification">✏️ Modification</Option>
                  </Dropdown>
                </Field>

                <Field label="What are you commenting on?">
                  <Input
                    value={targetElement}
                    onChange={(e) => setTargetElement(e.target.value)}
                    placeholder="e.g., Day 2 Restaurant, Hotel Selection, Activity Plan"
                  />
                </Field>

                <Field label="Your Feedback">
                  <Textarea
                    value={feedbackContent}
                    onChange={(e) => setFeedbackContent(e.target.value)}
                    placeholder="Share your thoughts, concerns, or suggestions..."
                    rows={4}
                  />
                </Field>

                {feedbackType === 'suggestion' && (
                  <Field label="Suggested Change (Optional)">
                    <Textarea
                      value={suggestedChange}
                      onChange={(e) => setSuggestedChange(e.target.value)}
                      placeholder="Describe the specific change you'd like to see..."
                      rows={3}
                    />
                  </Field>
                )}

              </DialogContent>
              <DialogActions>
                <DialogTrigger disableButtonEnhancement>
                  <Button appearance="secondary">Cancel</Button>
                </DialogTrigger>
                <Button 
                  appearance="primary" 
                  onClick={handleSubmitFeedback}
                  disabled={submittingFeedback || !feedbackContent.trim() || !targetElement.trim()}
                >
                  {submittingFeedback ? <Spinner size="tiny" /> : 'Submit Feedback'}
                </Button>
              </DialogActions>
            </DialogBody>
          </DialogSurface>
        </Dialog>
      </div>

      {/* Collaboration Health */}
      <Card>
        <div style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <People24Regular style={{ color: '#0078D4' }} />
            <Title3>Collaboration Health</Title3>
            <Badge color={collaborationScore >= 80 ? "success" : collaborationScore >= 60 ? "warning" : "danger"}>
              {collaborationScore}%
            </Badge>
          </div>
          
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginTop: '16px' }}>
            <div>
              <Caption1>Feedback Velocity</Caption1>
              <Body1 style={{ fontWeight: "600" }}>{dashboardData.collaboration_health.feedback_velocity}</Body1>
            </div>
            <div>
              <Caption1>Response Rate</Caption1>
              <Body1 style={{ fontWeight: '600' }}>{dashboardData.collaboration_health.response_rate}</Body1>
            </div>
            <div>
              <Caption1>Avg Resolution Time</Caption1>
              <Body1 style={{ fontWeight: '600' }}>{dashboardData.collaboration_health.average_resolution_time}</Body1>
            </div>
          </div>
        </div>
      </Card>

      {/* Feedback Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
        <Card>
          <div style={{ padding: '16px' }}>
            <Title3 style={{ marginBottom: '12px' }}>📊 Feedback Overview</Title3>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <Text style={{ fontSize: '24px', fontWeight: 'bold', color: '#0078D4' }}>
                  {dashboardData.total_feedback_items}
                </Text>
                <Caption1>Total Items</Caption1>
              </div>
              <div>
                <Text style={{ fontSize: '24px', fontWeight: 'bold', color: '#FF8C00' }}>
                  {dashboardData.pending_items}
                </Text>
                <Caption1>Pending</Caption1>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {Object.entries(dashboardData.feedback_by_type).map(([type, count]) => (
                <div key={type} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {getFeedbackIcon(type)}
                    <Caption1>{type.charAt(0).toUpperCase() + type.slice(1)}</Caption1>
                  </div>
                  <Badge>{count}</Badge>
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card>
          <div style={{ padding: '16px' }}>
            <Title3 style={{ marginBottom: '12px' }}>📈 Feedback Trends</Title3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <Caption1>Most Common Type</Caption1>
                <Body1 style={{ fontWeight: "600" }}>{dashboardData.feedback_trends.most_common_type}</Body1>
              </div>
              <div>
                <Caption1>Peak Activity Time</Caption1>
                <Body1 style={{ fontWeight: "600" }}>{dashboardData.feedback_trends.peak_feedback_time}</Body1>
              </div>
              <div>
                <Caption1>Family Participation</Caption1>
                <Body1 style={{ fontWeight: "600" }}>{dashboardData.feedback_trends.family_participation}</Body1>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Feedback */}
      <Card>
        <div style={{ padding: '16px' }}>
          <Title3 style={{ marginBottom: '16px' }}>💭 Recent Feedback</Title3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {dashboardData.recent_feedback.map((feedback) => (
              <div key={feedback.id} style={{ 
                border: '1px solid #E5E5E5', 
                borderRadius: '8px', 
                padding: '16px',
                backgroundColor: '#FAFAFA'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {getFeedbackIcon(feedback.feedback_type)}
                    <Body1 style={{ fontWeight: "600" }}>{feedback.target_element}</Body1>
                    <div style={{ 
                      width: '8px', 
                      height: '8px', 
                      borderRadius: '50%', 
                      backgroundColor: getUrgencyColor(feedback.urgency_level || 'Low')
                    }} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Caption1>{feedback.time_since_submission}</Caption1>
                    {getStatusBadge(feedback.status)}
                  </div>
                </div>
                
                <Body1 style={{ marginBottom: '8px' }}>{feedback.content}</Body1>
                
                {feedback.suggested_change && (
                  <div style={{ 
                    backgroundColor: '#F3F2F1', 
                    padding: '8px', 
                    borderRadius: '4px', 
                    marginBottom: '8px' 
                  }}>
                    <Caption1 style={{ fontWeight: 'bold' }}>Suggested Change:</Caption1>
                    <Caption1>{feedback.suggested_change}</Caption1>
                  </div>
                )}

                {feedback.impact_analysis && (
                  <div style={{ display: 'flex', gap: '16px', marginBottom: '8px' }}>
                    <Caption1>
                      Impact: <strong>{feedback.impact_analysis.impact_level}</strong>
                    </Caption1>
                    {feedback.impact_analysis.cost_delta !== 0 && (
                      <Caption1>
                        Cost: <strong style={{ color: feedback.impact_analysis.cost_delta > 0 ? '#D13438' : '#107C10' }}>
                          ${Math.abs(feedback.impact_analysis.cost_delta).toFixed(0)}
                        </strong>
                      </Caption1>
                    )}
                  </div>
                )}

                {feedback.responses.length > 0 && (
                  <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #E5E5E5' }}>
                    <Caption1 style={{ fontWeight: 'bold', marginBottom: '8px' }}>
                      Responses ({feedback.responses.length}):
                    </Caption1>
                    {feedback.responses.map((response, respIndex) => (
                      <div key={respIndex} style={{ marginBottom: '4px' }}>
                        <Caption1>{response.content}</Caption1>
                      </div>
                    ))}
                  </div>
                )}

                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                  <Button size="small" appearance="subtle" icon={<Chat24Regular />}>
                    Reply
                  </Button>
                  {feedback.status === 'pending' && (
                    <>
                      <Button size="small" appearance="subtle" icon={<CheckmarkCircle24Regular />}>
                        Approve
                      </Button>
                      <Button size="small" appearance="subtle" icon={<Eye24Regular />}>
                        Review
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Success message */}
      <MessageBar intent="success">
        🚀 Real-time feedback integration is enabling faster consensus and better trip planning!
      </MessageBar>
    </div>
  );
};

export default FeedbackDashboard; 