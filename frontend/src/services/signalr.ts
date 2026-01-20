// SignalR Service for real-time messaging
// Uses Azure SignalR Service

import * as signalR from '@microsoft/signalr';
import { api } from '../lib/api';

export type SignalREventHandler = (data: unknown) => void;

interface NegotiateResponse {
  url: string;
  accessToken: string;
}

// Event types matching backend RealtimeEvents
export const RealtimeEvents = {
  // Trip events
  TRIP_UPDATED: 'tripUpdated',
  TRIP_DELETED: 'tripDeleted',

  // Collaboration events
  POLL_CREATED: 'pollCreated',
  POLL_UPDATED: 'pollUpdated',
  POLL_CLOSED: 'pollClosed',
  VOTE_RECEIVED: 'voteReceived',

  // Chat events
  MESSAGE_RECEIVED: 'messageReceived',
  TYPING_INDICATOR: 'typingIndicator',

  // Itinerary events
  ITINERARY_GENERATED: 'itineraryGenerated',
  ITINERARY_APPROVED: 'itineraryApproved',

  // Member events
  MEMBER_JOINED: 'memberJoined',
  MEMBER_LEFT: 'memberLeft',

  // Notification events
  NOTIFICATION: 'notification',
} as const;

export type RealtimeEventType = typeof RealtimeEvents[keyof typeof RealtimeEvents];

class SignalRService {
  private connection: signalR.HubConnection | null = null;
  private eventHandlers: Map<string, Set<SignalREventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private isConnecting = false;
  private groups: Set<string> = new Set();

  async connect(): Promise<void> {
    if (this.connection?.state === signalR.HubConnectionState.Connected) {
      console.log('SignalR already connected');
      return;
    }

    if (this.isConnecting) {
      console.log('SignalR connection in progress');
      return;
    }

    this.isConnecting = true;

    try {
      // Get negotiate info from backend
      const response = await api.post<NegotiateResponse>('/signalr/negotiate');

      if (!response.success || !response.data.url) {
        throw new Error('Failed to negotiate SignalR connection');
      }

      const { url, accessToken } = response.data;

      // Build connection
      this.connection = new signalR.HubConnectionBuilder()
        .withUrl(url, {
          accessTokenFactory: () => accessToken,
        })
        .withAutomaticReconnect({
          nextRetryDelayInMilliseconds: (retryContext) => {
            if (retryContext.previousRetryCount >= this.maxReconnectAttempts) {
              return null; // Stop retrying
            }
            // Exponential backoff: 0, 2s, 4s, 8s, 16s
            return Math.min(1000 * Math.pow(2, retryContext.previousRetryCount), 30000);
          },
        })
        .configureLogging(signalR.LogLevel.Information)
        .build();

      // Set up connection event handlers
      this.connection.onreconnecting((error) => {
        console.warn('SignalR reconnecting:', error);
        this.reconnectAttempts++;
      });

      this.connection.onreconnected((connectionId) => {
        console.log('SignalR reconnected:', connectionId);
        this.reconnectAttempts = 0;
        // Rejoin groups after reconnection
        this.groups.forEach((group) => this.joinGroup(group));
      });

      this.connection.onclose((error) => {
        console.warn('SignalR connection closed:', error);
        this.connection = null;
      });

      // Register event handlers
      this.registerDefaultHandlers();

      // Start connection
      await this.connection.start();
      console.log('SignalR connected');
      this.reconnectAttempts = 0;
    } catch (error) {
      console.error('SignalR connection failed:', error);
      throw error;
    } finally {
      this.isConnecting = false;
    }
  }

  async disconnect(): Promise<void> {
    if (this.connection) {
      // Leave all groups
      for (const group of this.groups) {
        await this.leaveGroup(group);
      }

      await this.connection.stop();
      this.connection = null;
      this.groups.clear();
      console.log('SignalR disconnected');
    }
  }

  private registerDefaultHandlers(): void {
    if (!this.connection) return;

    // Register handlers for all known event types
    Object.values(RealtimeEvents).forEach((eventType) => {
      this.connection!.on(eventType, (data: unknown) => {
        this.handleEvent(eventType, data);
      });
    });
  }

  private handleEvent(eventType: string, data: unknown): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in SignalR event handler for ${eventType}:`, error);
        }
      });
    }
  }

  on(eventType: RealtimeEventType | string, handler: SignalREventHandler): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.eventHandlers.get(eventType)?.delete(handler);
    };
  }

  off(eventType: RealtimeEventType | string, handler?: SignalREventHandler): void {
    if (handler) {
      this.eventHandlers.get(eventType)?.delete(handler);
    } else {
      this.eventHandlers.delete(eventType);
    }
  }

  async joinGroup(groupName: string): Promise<void> {
    try {
      await api.post(`/signalr/groups/${encodeURIComponent(groupName)}/join`);
      this.groups.add(groupName);
      console.log(`Joined SignalR group: ${groupName}`);
    } catch (error) {
      console.error(`Failed to join group ${groupName}:`, error);
      throw error;
    }
  }

  async leaveGroup(groupName: string): Promise<void> {
    try {
      await api.post(`/signalr/groups/${encodeURIComponent(groupName)}/leave`);
      this.groups.delete(groupName);
      console.log(`Left SignalR group: ${groupName}`);
    } catch (error) {
      console.error(`Failed to leave group ${groupName}:`, error);
      throw error;
    }
  }

  async send(groupName: string, eventType: string, data: unknown): Promise<void> {
    try {
      await api.post('/signalr/send', {
        group: groupName,
        target: eventType,
        data,
      });
    } catch (error) {
      console.error(`Failed to send message to ${groupName}:`, error);
      throw error;
    }
  }

  get isConnected(): boolean {
    return this.connection?.state === signalR.HubConnectionState.Connected;
  }

  get connectionState(): string {
    return this.connection?.state ?? 'Disconnected';
  }
}

// Export singleton instance
export const signalRService = new SignalRService();

// Hook for React components
export function useSignalR() {
  return signalRService;
}
