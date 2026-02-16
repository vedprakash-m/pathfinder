/**
 * AI Service - Complete Frontend Integration
 * Implements end-to-end AI features connectivity per GAP 3 requirements.
 */

import { apiService } from './api';

// Types for AI features
export interface AIResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  processingTimeMs?: number;
}

export interface ResponseCard {
  id: string;
  cardType: string;
  title: string;
  content: Record<string, unknown>;
  actions?: Array<{
    label: string;
    action: string;
    data?: Record<string, unknown>;
  }>;
  isDismissed?: boolean;
}

// Pathfinder Assistant Types
export interface AssistantMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  interactionId?: string;
  responseCards?: ResponseCard[];
  processingTimeMs?: number;
}

export interface MentionRequest {
  message: string;
  context: {
    tripId?: string;
    familyId?: string;
    currentPage?: string;
    tripData?: Record<string, unknown>;
  };
}

// Magic Polls Types
export interface PollOption {
  value: string;
  label?: string;
  description?: string;
  metadata?: Record<string, unknown>;
  aiInsights?: Record<string, unknown>;
}

export interface MagicPoll {
  id: string;
  title: string;
  description?: string;
  pollType: string;
  options: PollOption[];
  status: 'active' | 'completed' | 'expired' | 'cancelled';
  expiresAt?: string;
  createdAt: string;
  creatorId: string;
  tripId: string;
}

export interface CreatePollRequest {
  tripId: string;
  title: string;
  description?: string;
  pollType: string;
  options: PollOption[];
  expiresHours?: number;
}

export interface VoteRequest {
  pollId: string;
  selectedOptions: string[];
}

export interface PollResults {
  totalResponses: number;
  results: Array<{
    option: string;
    votes: number;
    percentage: number;
    details: PollOption;
  }>;
}

// Consensus Engine Types
export interface ConsensusAnalysis {
  summary: string;
  patterns: string[];
  conflicts: Array<{
    type: string;
    description: string;
    options: string[];
  }>;
  consensusLevel: number;
}

export interface ConsensusRecommendation {
  recommendedChoice: string;
  voteCount: number;
  totalVotes: number;
  consensusStrength: number;
  reasoning: string;
}

// Itinerary Generation Types
export interface ItineraryRequest {
  tripId: string;
  preferences: {
    activityTypes?: string[];
    budgetRange?: [number, number];
    pace?: 'relaxed' | 'moderate' | 'packed';
    interests?: string[];
  };
  constraints: {
    mobilityRequirements?: string[];
    dietaryRestrictions?: string[];
    ageRanges?: string[];
  };
}

export interface GeneratedItinerary {
  id: string;
  tripId: string;
  days: Array<{
    date: string;
    activities: Array<{
      id: string;
      name: string;
      description: string;
      startTime: string;
      endTime: string;
      location: string;
      category: string;
      cost?: number;
      aiReasoning?: string;
    }>;
  }>;
  totalEstimatedCost: number;
  aiSummary: string;
  confidenceScore: number;
}

export class AIService {
  /**
   * Pathfinder Assistant - Natural Language Trip Assistance
   */
  static async sendAssistantMessage(request: MentionRequest): Promise<AssistantMessage> {
    try {
      const response = await apiService.post<{
        success: boolean;
        data: {
          interaction_id: string;
          response: string;
          response_cards?: ResponseCard[];
          processing_time_ms?: number;
        };
      }>('/assistant/mention', {
        message: request.message,
        context: request.context,
        trip_id: request.context.tripId,
        family_id: request.context.familyId
      });

      if (!response.data.success) {
        throw new Error('Assistant request failed');
      }

      return {
        id: response.data.data.interaction_id,
        content: response.data.data.response,
        isUser: false,
        timestamp: new Date(),
        interactionId: response.data.data.interaction_id,
        responseCards: response.data.data.response_cards || [],
        processingTimeMs: response.data.data.processing_time_ms
      };
    } catch (error) {
      console.error('Failed to send assistant message:', error);
      throw new Error('Failed to get assistant response');
    }
  }

  static async getContextualSuggestions(context: {
    tripId?: string;
    familyId?: string;
    currentPage?: string;
  }): Promise<ResponseCard[]> {
    try {
      const response = await apiService.get<{
        suggestions: ResponseCard[];
      }>('/assistant/suggestions', {
        params: {
          page: context.currentPage,
          trip_id: context.tripId
        }
      });

      return response.data.suggestions || [];
    } catch (error) {
      console.error('Failed to get contextual suggestions:', error);
      return [];
    }
  }

  static async sendAssistantFeedback(interactionId: string, rating: number, feedbackText?: string): Promise<void> {
    try {
      await apiService.post('/assistant/feedback', {
        interaction_id: interactionId,
        rating,
        feedback_text: feedbackText
      });
    } catch (error) {
      console.error('Failed to send assistant feedback:', error);
      throw new Error('Failed to send feedback');
    }
  }

  /**
   * Magic Polls - AI-Powered Decision Making
   */
  static async createMagicPoll(request: CreatePollRequest): Promise<MagicPoll> {
    try {
      const response = await apiService.post<{
        success: boolean;
        data: MagicPoll;
      }>('/polls/magic', {
        trip_id: request.tripId,
        title: request.title,
        description: request.description,
        poll_type: request.pollType,
        options: request.options,
        expires_hours: request.expiresHours || 72
      });

      if (!response.data.success) {
        throw new Error('Magic poll creation failed');
      }

      return response.data.data;
    } catch (error) {
      console.error('Failed to create magic poll:', error);
      throw new Error('Failed to create poll');
    }
  }

  static async getTripPolls(tripId: string): Promise<MagicPoll[]> {
    try {
      const response = await apiService.get<{
        polls: MagicPoll[];
      }>(`/polls/trip/${tripId}`);

      return response.data.polls || [];
    } catch (error) {
      console.error('Failed to get trip polls:', error);
      return [];
    }
  }

  static async votePoll(request: VoteRequest): Promise<void> {
    try {
      await apiService.post(`/polls/${request.pollId}/vote`, {
        selected_options: request.selectedOptions
      });
    } catch (error) {
      console.error('Failed to vote on poll:', error);
      throw new Error('Failed to submit vote');
    }
  }

  static async getPollResults(pollId: string): Promise<PollResults> {
    try {
      const response = await apiService.get<PollResults>(`/polls/${pollId}/results`);
      return response.data;
    } catch (error) {
      console.error('Failed to get poll results:', error);
      throw new Error('Failed to get poll results');
    }
  }

  /**
   * Consensus Engine - Smart Decision Making
   */
  static async getConsensusAnalysis(tripId: string): Promise<ConsensusAnalysis> {
    try {
      const response = await apiService.get<{
        success: boolean;
        data: ConsensusAnalysis;
      }>(`/consensus/analysis/${tripId}`);

      if (!response.data.success) {
        throw new Error('Consensus analysis failed');
      }

      return response.data.data;
    } catch (error) {
      console.error('Failed to get consensus analysis:', error);
      throw new Error('Failed to analyze consensus');
    }
  }

  static async getConsensusRecommendation(tripId: string, decisionType: string): Promise<ConsensusRecommendation> {
    try {
      const response = await apiService.post<{
        success: boolean;
        data: ConsensusRecommendation;
      }>(`/consensus/recommend/${tripId}`, {
        decision_type: decisionType
      });

      if (!response.data.success) {
        throw new Error('Consensus recommendation failed');
      }

      return response.data.data;
    } catch (error) {
      console.error('Failed to get consensus recommendation:', error);
      throw new Error('Failed to get recommendation');
    }
  }

  /**
   * AI Itinerary Generation
   */
  static async generateItinerary(request: ItineraryRequest): Promise<string> {
    try {
      const response = await apiService.post<{
        success: boolean;
        data: {
          task_id: string;
        };
      }>('/ai/itinerary/generate', {
        trip_id: request.tripId,
        preferences: request.preferences,
        constraints: request.constraints
      });

      if (!response.data.success) {
        throw new Error('Itinerary generation failed');
      }

      return response.data.data.task_id;
    } catch (error) {
      console.error('Failed to generate itinerary:', error);
      throw new Error('Failed to start itinerary generation');
    }
  }

  static async getItineraryStatus(taskId: string): Promise<{
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress?: number;
    result?: GeneratedItinerary;
    error?: string;
  }> {
    try {
      const response = await apiService.get(`/ai/itinerary/status/${taskId}`);
      return response.data as {
        status: 'pending' | 'processing' | 'completed' | 'failed';
        progress?: number;
        result?: GeneratedItinerary;
        error?: string;
      };
    } catch (error) {
      console.error('Failed to get itinerary status:', error);
      throw new Error('Failed to get generation status');
    }
  }

  /**
   * AI Cost Management & Graceful Degradation
   */
  static async getAICostStatus(): Promise<{
    budgetUsed: number;
    budgetLimit: number;
    remainingQuota: number;
    currentTier: string;
    gracefulMode: boolean;
  }> {
    try {
      const response = await apiService.get('/ai/cost/status');
      return response.data as {
        budgetUsed: number;
        budgetLimit: number;
        remainingQuota: number;
        currentTier: string;
        gracefulMode: boolean;
      };
    } catch (error) {
      console.error('Failed to get AI cost status:', error);
      return {
        budgetUsed: 0,
        budgetLimit: 100,
        remainingQuota: 100,
        currentTier: 'basic',
        gracefulMode: false
      };
    }
  }

  /**
   * Error Handling and Graceful Degradation
   */
  static handleAIError(error: unknown): {
    message: string;
    fallbackAction?: string;
    retryable: boolean;
  } {
    const axiosError = error as { response?: { status?: number } };
    if (axiosError.response?.status === 429) {
      return {
        message: 'AI usage limit reached. Please try again later or use manual options.',
        fallbackAction: 'manual_mode',
        retryable: true
      };
    }

    if (axiosError.response?.status === 503) {
      return {
        message: 'AI services temporarily unavailable. Using basic features.',
        fallbackAction: 'basic_mode',
        retryable: true
      };
    }

    return {
      message: 'An error occurred with AI features. Please try again.',
      fallbackAction: 'retry',
      retryable: true
    };
  }
}

export default AIService;
