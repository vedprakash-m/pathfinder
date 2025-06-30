/**
 * Pathfinder Assistant Service
 * Integrates with backend assistant API for AI-powered trip planning assistance
 */

import { apiService } from './api';

export interface AssistantMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  interactionId?: string;
  responseCards?: ResponseCard[];
}

export interface ResponseCard {
  id: string;
  card_type: string;
  title: string;
  content: any;
  actions?: Array<{
    label: string;
    action: string;
  }>;
  is_dismissed: boolean;
}

export interface MentionRequest {
  message: string;
  context: {
    trip_id?: string;
    family_id?: string;
    current_page?: string;
    trip_data?: any;
  };
}

export interface FeedbackRequest {
  interaction_id: string;
  rating: number;
  feedback_text?: string;
}

export interface SuggestionsRequest {
  context: {
    trip_id?: string;
    family_id?: string;
    current_page?: string;
  };
  page?: string;
}

export class AssistantService {
  /**
   * Send a message to the Pathfinder Assistant
   */
  static async sendMessage(request: MentionRequest): Promise<AssistantMessage> {
    try {
      const response = await apiService.post<{
        interaction_id: string;
        response: string;
        response_cards?: ResponseCard[];
      }>('/assistant/mention', request);

      return {
        id: response.data.interaction_id,
        content: response.data.response,
        isUser: false,
        timestamp: new Date(),
        interactionId: response.data.interaction_id,
        responseCards: response.data.response_cards || []
      };
    } catch (error) {
      console.error('Failed to send message to assistant:', error);
      throw new Error('Failed to get assistant response');
    }
  }

  /**
   * Send feedback for an assistant interaction
   */
  static async sendFeedback(request: FeedbackRequest): Promise<void> {
    try {
      await apiService.post('/assistant/feedback', request);
    } catch (error) {
      console.error('Failed to send assistant feedback:', error);
      throw new Error('Failed to send feedback');
    }
  }

  /**
   * Get contextual suggestions
   */
  static async getSuggestions(request: SuggestionsRequest): Promise<ResponseCard[]> {
    try {
      const response = await apiService.post<{ suggestions: ResponseCard[] }>(
        '/assistant/suggestions',
        request
      );

      return response.data.suggestions || [];
    } catch (error) {
      console.error('Failed to get assistant suggestions:', error);
      return [];
    }
  }

  /**
   * Dismiss a response card
   */
  static async dismissCard(cardId: string): Promise<void> {
    try {
      await apiService.post(`/assistant/cards/${cardId}/dismiss`, {});
    } catch (error) {
      console.error('Failed to dismiss assistant card:', error);
      throw new Error('Failed to dismiss card');
    }
  }

  /**
   * Execute an action from a response card
   */
  static async executeCardAction(cardId: string, action: string, data?: any): Promise<any> {
    try {
      const response = await apiService.post(`/assistant/cards/${cardId}/action`, {
        action,
        data
      });

      return response.data;
    } catch (error) {
      console.error('Failed to execute assistant card action:', error);
      throw new Error('Failed to execute action');
    }
  }
}

export default AssistantService;
