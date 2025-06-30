/**
 * Magic Polls Service
 * Integrates with backend Magic Polls API for AI-powered decision making
 */

import { apiService } from './api';

export interface PollOption {
  value: string;
  label?: string;
  description?: string;
  metadata?: Record<string, any>;
}

export interface CreatePollRequest {
  trip_id: string;
  title: string;
  description?: string;
  poll_type: string;
  options: PollOption[];
  expires_hours?: number;
}

export interface PollResponse {
  choice: string;
  preferences?: Record<string, any>;
  comments?: string;
}

export interface Poll {
  id: string;
  trip_id: string;
  title: string;
  description?: string;
  poll_type: string;
  options: PollOption[];
  status: 'active' | 'closed' | 'expired';
  expires_at: string;
  created_at: string;
  created_by: string;
  responses: PollResponseWithUser[];
  ai_generated: boolean;
  consensus_score?: number;
}

export interface PollResponseWithUser {
  id: string;
  user_id: string;
  family_id: string;
  choice: string;
  preferences?: Record<string, any>;
  comments?: string;
  created_at: string;
  user_name: string;
  family_name: string;
}

export interface GeneratePollOptionsRequest {
  trip_id: string;
  poll_type: string;
  context: Record<string, any>;
  prompt?: string;
}

export class MagicPollsService {
  /**
   * Create a new Magic Poll
   */
  static async createPoll(request: CreatePollRequest): Promise<Poll> {
    try {
      const response = await apiService.post<Poll>('/polls', request, {
        invalidateUrlPatterns: ['polls', 'trips']
      });

      return response.data;
    } catch (error) {
      console.error('Failed to create poll:', error);
      throw new Error('Failed to create poll');
    }
  }

  /**
   * Get all polls for a trip
   */
  static async getTripPolls(tripId: string): Promise<Poll[]> {
    try {
      const response = await apiService.get<Poll[]>(`/polls/trip/${tripId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get trip polls:', error);
      return [];
    }
  }

  /**
   * Get a specific poll by ID
   */
  static async getPoll(pollId: string): Promise<Poll> {
    try {
      const response = await apiService.get<Poll>(`/polls/${pollId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get poll:', error);
      throw new Error('Failed to get poll');
    }
  }

  /**
   * Submit a response to a poll
   */
  static async submitPollResponse(pollId: string, response: PollResponse): Promise<void> {
    try {
      await apiService.post(`/polls/${pollId}/respond`, response, {
        invalidateUrlPatterns: ['polls']
      });
    } catch (error) {
      console.error('Failed to submit poll response:', error);
      throw new Error('Failed to submit response');
    }
  }

  /**
   * Generate AI-powered poll options
   */
  static async generatePollOptions(request: GeneratePollOptionsRequest): Promise<PollOption[]> {
    try {
      const response = await apiService.post<{ options: PollOption[] }>(
        '/polls/generate-options',
        request
      );

      return response.data.options || [];
    } catch (error) {
      console.error('Failed to generate poll options:', error);
      return [];
    }
  }

  /**
   * Close a poll early
   */
  static async closePoll(pollId: string): Promise<void> {
    try {
      await apiService.post(`/polls/${pollId}/close`, {}, {
        invalidateUrlPatterns: ['polls']
      });
    } catch (error) {
      console.error('Failed to close poll:', error);
      throw new Error('Failed to close poll');
    }
  }

  /**
   * Delete a poll
   */
  static async deletePoll(pollId: string): Promise<void> {
    try {
      await apiService.delete(`/polls/${pollId}`, {
        invalidateUrlPatterns: ['polls', 'trips']
      });
    } catch (error) {
      console.error('Failed to delete poll:', error);
      throw new Error('Failed to delete poll');
    }
  }

  /**
   * Get poll analytics and consensus information
   */
  static async getPollAnalytics(pollId: string): Promise<{
    consensus_score: number;
    family_agreement: Record<string, number>;
    top_choices: Array<{ choice: string; percentage: number }>;
    insights: string[];
  }> {
    try {
      const response = await apiService.get<{
        consensus_score: number;
        family_agreement: Record<string, number>;
        top_choices: Array<{ choice: string; percentage: number }>;
        insights: string[];
      }>(`/polls/${pollId}/analytics`);
      return response.data;
    } catch (error) {
      console.error('Failed to get poll analytics:', error);
      throw new Error('Failed to get poll analytics');
    }
  }
}

export default MagicPollsService;
