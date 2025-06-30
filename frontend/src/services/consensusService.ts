/**
 * Consensus Engine Service
 * Integrates with backend Consensus Engine API for family decision making
 */

import { apiService } from './api';

export interface ConsensusRequest {
  trip_id: string;
  include_family_details?: boolean;
}

export interface VoteRequest {
  voting_item_id: string;
  vote_choice: string;
}

export interface ConsensusAnalysis {
  trip_id: string;
  consensus_score: number;
  status: 'building' | 'emerging' | 'strong' | 'complete' | 'conflicted';
  agreed_preferences: Record<string, any>;
  conflicts: Array<{
    type: string;
    description: string;
    involved_families: string[];
    severity: 'low' | 'medium' | 'high';
  }>;
  recommendations: Array<{
    action: string;
    description: string;
    priority: number;
  }>;
  family_positions: Record<string, {
    family_id: string;
    family_name: string;
    preferences: Record<string, any>;
    flexibility_score: number;
  }>;
}

export interface CompromiseSuggestion {
  id: string;
  title: string;
  description: string;
  affected_preferences: string[];
  family_impact: Record<string, {
    satisfaction_score: number;
    concerns: string[];
  }>;
  implementation_steps: string[];
  confidence_score: number;
}

export interface ConflictResolution {
  conflict_id: string;
  resolution_type: 'compromise' | 'vote' | 'alternate' | 'defer';
  description: string;
  proposed_solution: any;
  family_responses: Record<string, {
    status: 'pending' | 'accepted' | 'rejected';
    comments?: string;
  }>;
}

export class ConsensusService {
  /**
   * Get consensus analysis for a trip
   */
  static async getConsensusAnalysis(request: ConsensusRequest): Promise<ConsensusAnalysis> {
    try {
      const response = await apiService.post<ConsensusAnalysis>('/consensus/analyze', request);
      return response.data;
    } catch (error) {
      console.error('Failed to get consensus analysis:', error);
      throw new Error('Failed to analyze consensus');
    }
  }

  /**
   * Submit a family vote for a decision
   */
  static async submitVote(tripId: string, voteRequest: VoteRequest): Promise<void> {
    try {
      await apiService.post(`/consensus/trips/${tripId}/vote`, voteRequest, {
        invalidateUrlPatterns: ['consensus', 'trips']
      });
    } catch (error) {
      console.error('Failed to submit vote:', error);
      throw new Error('Failed to submit vote');
    }
  }

  /**
   * Get compromise suggestions for conflicted decisions
   */
  static async getCompromiseSuggestions(tripId: string): Promise<CompromiseSuggestion[]> {
    try {
      const response = await apiService.get<CompromiseSuggestion[]>(
        `/consensus/trips/${tripId}/compromises`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get compromise suggestions:', error);
      return [];
    }
  }

  /**
   * Accept a compromise suggestion
   */
  static async acceptCompromise(tripId: string, compromiseId: string): Promise<void> {
    try {
      await apiService.post(`/consensus/trips/${tripId}/compromises/${compromiseId}/accept`, {}, {
        invalidateUrlPatterns: ['consensus', 'trips']
      });
    } catch (error) {
      console.error('Failed to accept compromise:', error);
      throw new Error('Failed to accept compromise');
    }
  }

  /**
   * Reject a compromise suggestion with feedback
   */
  static async rejectCompromise(
    tripId: string,
    compromiseId: string,
    feedback?: string
  ): Promise<void> {
    try {
      await apiService.post(
        `/consensus/trips/${tripId}/compromises/${compromiseId}/reject`,
        { feedback },
        {
          invalidateUrlPatterns: ['consensus', 'trips']
        }
      );
    } catch (error) {
      console.error('Failed to reject compromise:', error);
      throw new Error('Failed to reject compromise');
    }
  }

  /**
   * Get active conflict resolutions for a trip
   */
  static async getConflictResolutions(tripId: string): Promise<ConflictResolution[]> {
    try {
      const response = await apiService.get<ConflictResolution[]>(
        `/consensus/trips/${tripId}/conflicts`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get conflict resolutions:', error);
      return [];
    }
  }

  /**
   * Respond to a conflict resolution
   */
  static async respondToConflict(
    tripId: string,
    conflictId: string,
    response: 'accepted' | 'rejected',
    comments?: string
  ): Promise<void> {
    try {
      await apiService.post(
        `/consensus/trips/${tripId}/conflicts/${conflictId}/respond`,
        { response, comments },
        {
          invalidateUrlPatterns: ['consensus', 'trips']
        }
      );
    } catch (error) {
      console.error('Failed to respond to conflict:', error);
      throw new Error('Failed to respond to conflict');
    }
  }

  /**
   * Generate new consensus insights based on current state
   */
  static async generateInsights(tripId: string): Promise<{
    insights: string[];
    action_items: Array<{
      title: string;
      description: string;
      priority: 'low' | 'medium' | 'high';
      assigned_to?: string;
    }>;
  }> {
    try {
      const response = await apiService.post<{
        insights: string[];
        action_items: Array<{
          title: string;
          description: string;
          priority: 'low' | 'medium' | 'high';
          assigned_to?: string;
        }>;
      }>(`/consensus/trips/${tripId}/insights`, {});
      return response.data;
    } catch (error) {
      console.error('Failed to generate consensus insights:', error);
      throw new Error('Failed to generate insights');
    }
  }

  /**
   * Get consensus history for a trip
   */
  static async getConsensusHistory(tripId: string): Promise<Array<{
    timestamp: string;
    event_type: string;
    description: string;
    consensus_score_change: number;
    involved_families: string[];
  }>> {
    try {
      const response = await apiService.get<Array<{
        timestamp: string;
        event_type: string;
        description: string;
        consensus_score_change: number;
        involved_families: string[];
      }>>(`/consensus/trips/${tripId}/history`);
      return response.data;
    } catch (error) {
      console.error('Failed to get consensus history:', error);
      return [];
    }
  }
}

export default ConsensusService;
