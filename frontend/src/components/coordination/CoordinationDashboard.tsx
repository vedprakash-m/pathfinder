/**
 * Smart Coordination Dashboard Component
 * 
 * Solves Pain Point #2: "Too much manual coordination required between families"
 * 
 * Features:
 * - Real-time automation status
 * - Smart notification management
 * - Family response tracking
 * - One-click coordination actions
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Text,
  Badge,
  Button,
  Spinner,
  MessageBar,
  Title3,
  Title2,
  Body1,
  Caption1
} from '@fluentui/react-components';
import {
  CheckmarkCircle24Regular,
  Warning24Regular,
  Clock24Regular,
  Send24Regular,
  PeopleTeam24Regular,
  CalendarLtr24Regular
} from '@fluentui/react-icons';

interface CoordinationEvent {
  event_type: string;
  timestamp: string;
  actions_executed: string[];
  family_id?: string;
}

interface CoordinationStatus {
  trip_id: string;
  automation_active: boolean;
  recent_events: CoordinationEvent[];
  pending_actions: string[];
  notification_summary: {
    sent_today: number;
    pending: number;
    failed: number;
  };
}

interface CoordinationDashboardProps {
  tripId: string;
  onTriggerEvent?: (eventType: string, contextData: any) => void;
}

export const CoordinationDashboard: React.FC<CoordinationDashboardProps> = ({
  tripId,
  onTriggerEvent
}) => {
  const [coordinationStatus, setCoordinationStatus] = useState<CoordinationStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggeringEvent, setTriggeringEvent] = useState<string | null>(null);

  // Fetch coordination status
  useEffect(() => {
    fetchCoordinationStatus();
  }, [tripId]);

  const fetchCoordinationStatus = async () => {
    try {
      setLoading(true);
      // In production, this would make actual API call
      // const response = await fetch(`/api/v1/coordination/status/${tripId}`);
      // const data = await response.json();
      
      // Simulated data for demonstration
      const simulatedData: CoordinationStatus = {
        trip_id: tripId,
        automation_active: true,
        recent_events: [
          {
            event_type: "family_joined",
            timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(), // 15 minutes ago
            actions_executed: ["welcome_notification_sent", "preference_collection_triggered"]
          },
          {
            event_type: "consensus_updated",
            timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(), // 45 minutes ago
            actions_executed: ["dashboard_updated", "organizer_notified"]
          },
          {
            event_type: "preferences_updated",
            timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(), // 1.5 hours ago
            actions_executed: ["consensus_analyzed", "conflict_check_completed"]
          }
        ],
        pending_actions: [
          "Check family readiness for Johnson family",
          "Schedule coordination meeting if consensus < 60%",
          "Generate itinerary when consensus > 80%"
        ],
        notification_summary: {
          sent_today: 7,
          pending: 2,
          failed: 0
        }
      };

      setCoordinationStatus(simulatedData);
      setError(null);
    } catch (err) {
      setError('Failed to load coordination status');
      console.error('Error fetching coordination status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerEvent = async (eventType: string, contextData: any = {}) => {
    try {
      setTriggeringEvent(eventType);
      
      // In production, this would make actual API call
      // const response = await fetch('/api/v1/coordination/trigger-event', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     event_type: eventType,
      //     trip_id: tripId,
      //     context_data: contextData
      //   })
      // });
      
      // Simulate successful trigger
      console.log(`Triggering coordination event: ${eventType}`, contextData);
      
      if (onTriggerEvent) {
        onTriggerEvent(eventType, contextData);
      }
      
      // Refresh status after triggering event
      setTimeout(() => {
        fetchCoordinationStatus();
        setTriggeringEvent(null);
      }, 1000);
      
    } catch (err) {
      setError(`Failed to trigger ${eventType} event`);
      console.error('Error triggering coordination event:', err);
      setTriggeringEvent(null);
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const eventTime = new Date(timestamp);
    const diffMs = now.getTime() - eventTime.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return eventTime.toLocaleDateString();
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'family_joined':
        return <PeopleTeam24Regular />;
      case 'consensus_updated':
        return <CheckmarkCircle24Regular />;
      case 'preferences_updated':
        return <Send24Regular />;
      default:
        return <Clock24Regular />;
    }
  };

  const getEventTitle = (eventType: string) => {
    switch (eventType) {
      case 'family_joined':
        return 'Family Joined';
      case 'consensus_updated':
        return 'Consensus Updated';
      case 'preferences_updated':
        return 'Preferences Updated';
      default:
        return 'Coordination Event';
    }
  };

  if (loading) {
    return (
      <Card>
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <Spinner label="Loading coordination status..." />
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
          onClick={fetchCoordinationStatus}
          style={{ marginLeft: '10px' }}
        >
          Retry
        </Button>
      </MessageBar>
    );
  }

  if (!coordinationStatus) {
    return null;
  }

  const automationHealthScore = Math.min(
    100,
    Math.max(
      0,
      (coordinationStatus.notification_summary.sent_today * 10) + 
      (coordinationStatus.pending_actions.length > 0 ? 70 : 90) -
      (coordinationStatus.notification_summary.failed * 20)
    )
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Title2>Smart Coordination</Title2>
        <Badge
          appearance={coordinationStatus.automation_active ? "filled" : "outline"}
          color={coordinationStatus.automation_active ? "brand" : "danger"}
        >
          {coordinationStatus.automation_active ? 'Active' : 'Inactive'}
        </Badge>
      </div>

      {/* Automation Health */}
      <Card>
        <div style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <div>
              {automationHealthScore >= 80 ? 
                <CheckmarkCircle24Regular /> : 
                <Warning24Regular />
              }
            </div>
            <Title3>Automation Health</Title3>
            <Badge color={automationHealthScore >= 80 ? "success" : automationHealthScore >= 60 ? "warning" : "danger"}>
              {automationHealthScore}%
            </Badge>
          </div>
          
            color={automationHealthScore >= 80 ? "success" : automationHealthScore >= 60 ? "warning" : "danger"}
          
          <Caption1 style={{ marginTop: '8px' }}>
            {automationHealthScore >= 80 && "Coordination running smoothly"}
            {automationHealthScore >= 60 && automationHealthScore < 80 && "Some coordination issues detected"}
            {automationHealthScore < 60 && "Coordination needs attention"}
          </Caption1>
        </div>
      </Card>

      {/* Notification Summary */}
      <Card>
        <div style={{ padding: '16px' }}>
          <Title3 style={{ marginBottom: '12px' }}>Today's Notifications</Title3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
            <div style={{ textAlign: 'center' }}>
              <Text style={{ fontSize: '24px', fontWeight: 'bold', color: '#107C10' }}>
                {coordinationStatus.notification_summary.sent_today}
              </Text>
              <Caption1>Sent</Caption1>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <Text style={{ fontSize: '24px', fontWeight: 'bold', color: '#FF8C00' }}>
                {coordinationStatus.notification_summary.pending}
              </Text>
              <Caption1>Pending</Caption1>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <Text style={{ fontSize: '24px', fontWeight: 'bold', color: '#D13438' }}>
                {coordinationStatus.notification_summary.failed}
              </Text>
              <Caption1>Failed</Caption1>
            </div>
          </div>
        </div>
      </Card>

      {/* Recent Events */}
      <Card>
        <div style={{ padding: '16px' }}>
          <Title3 style={{ marginBottom: '12px' }}>Recent Automation Events</Title3>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {coordinationStatus.recent_events.map((event, index) => (
              <div key={index} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                <div style={{ color: '#0078D4', marginTop: '2px' }}>
                  {getEventIcon(event.event_type)}
                </div>
                
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Body1 style={{ fontWeight: "600" }}>{getEventTitle(event.event_type)}</Body1>
                    <Caption1>{formatTimeAgo(event.timestamp)}</Caption1>
                  </div>
                  
                  <Caption1 style={{ color: '#6C6C6C', marginTop: '4px' }}>
                    Actions: {event.actions_executed.join(', ')}
                  </Caption1>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Pending Actions */}
      {coordinationStatus.pending_actions.length > 0 && (
        <Card>
          <div style={{ padding: '16px' }}>
            <Title3 style={{ marginBottom: '12px' }}>Pending Actions</Title3>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {coordinationStatus.pending_actions.map((action, index) => (
                <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Clock24Regular style={{ color: '#FF8C00', fontSize: '16px' }} />
                  <Body1>{action}</Body1>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Manual Coordination Actions */}
      <Card>
        <div style={{ padding: '16px' }}>
          <Title3 style={{ marginBottom: '12px' }}>Manual Coordination</Title3>
          <Caption1 style={{ marginBottom: '16px' }}>
            Trigger coordination events manually for testing or special situations.
          </Caption1>
          
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <Button
              appearance="secondary"
              icon={<PeopleTeam24Regular />}
              disabled={triggeringEvent === 'family_joined'}
              onClick={() => handleTriggerEvent('family_joined', { 
                trip_name: 'Test Trip',
                family_count: 3 
              })}
            >
              {triggeringEvent === 'family_joined' ? <Spinner size="tiny" /> : 'Simulate Family Joined'}
            </Button>
            
            <Button
              appearance="secondary"
              icon={<Send24Regular />}
              disabled={triggeringEvent === 'preferences_updated'}
              onClick={() => handleTriggerEvent('preferences_updated', {
                trip_name: 'Test Trip',
                consensus_score: 0.75,
                score_change: 0.15
              })}
            >
              {triggeringEvent === 'preferences_updated' ? <Spinner size="tiny" /> : 'Test Consensus Update'}
            </Button>
            
            <Button
              appearance="secondary"
              icon={<CalendarLtr24Regular />}
              disabled={triggeringEvent === 'schedule_meeting'}
              onClick={() => handleTriggerEvent('schedule_meeting', {
                meeting_type: 'consensus',
                consensus_score: 0.45
              })}
            >
              {triggeringEvent === 'schedule_meeting' ? <Spinner size="tiny" /> : 'Schedule Meeting'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Success message when event is triggered */}
      {!triggeringEvent && coordinationStatus.recent_events.length > 0 && (
        <MessageBar intent="success">
          Smart coordination is actively managing family communication and reducing manual overhead.
        </MessageBar>
      )}
    </div>
  );
};

export default CoordinationDashboard; 