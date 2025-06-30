/**
 * useAI Hook - Complete AI Features Integration
 * Provides easy access to all AI features with error handling and state management.
 */

import { useState, useCallback, useEffect } from 'react';
import { AIService, type MagicPoll, type AssistantMessage, type ResponseCard, type ConsensusAnalysis } from '../services/aiService';

export interface AIState {
  isLoading: boolean;
  error?: string;
  gracefulMode: boolean;
  costStatus: {
    budgetUsed: number;
    budgetLimit: number;
    remainingQuota: number;
    currentTier: string;
  };
}

export interface UseAIReturn {
  // State
  state: AIState;
  
  // Assistant functions
  sendAssistantMessage: (message: string, context?: any) => Promise<AssistantMessage | null>;
  getContextualSuggestions: (context?: any) => Promise<ResponseCard[]>;
  sendFeedback: (interactionId: string, rating: number, text?: string) => Promise<void>;
  
  // Magic Polls functions
  createMagicPoll: (pollData: any) => Promise<MagicPoll | null>;
  getTripPolls: (tripId?: string) => Promise<MagicPoll[]>;
  votePoll: (pollId: string, selectedOptions: string[]) => Promise<void>;
  getPollResults: (pollId: string) => Promise<any>;
  
  // Consensus functions
  getConsensusAnalysis: (tripId: string) => Promise<ConsensusAnalysis | null>;
  getConsensusRecommendation: (tripId: string, decisionType: string) => Promise<any>;
  
  // Itinerary functions
  generateItinerary: (tripId: string, preferences: any, constraints: any) => Promise<string | null>;
  getItineraryStatus: (taskId: string) => Promise<any>;
  
  // Utility functions
  refreshCostStatus: () => Promise<void>;
  clearError: () => void;
}

export const useAI = (context?: {
  tripId?: string;
  familyId?: string;
  currentPage?: string;
}): UseAIReturn => {
  const [state, setState] = useState<AIState>({
    isLoading: false,
    gracefulMode: false,
    costStatus: {
      budgetUsed: 0,
      budgetLimit: 100,
      remainingQuota: 100,
      currentTier: 'basic'
    }
  });

  // Helper function to handle AI errors
  const handleAIError = useCallback((error: any) => {
    const errorInfo = AIService.handleAIError(error);
    
    setState(prev => ({
      ...prev,
      error: errorInfo.message,
      gracefulMode: errorInfo.fallbackAction === 'basic_mode' || errorInfo.fallbackAction === 'manual_mode',
      isLoading: false
    }));

    return null;
  }, []);

  // Helper function to update loading state
  const withLoading = useCallback(async <T>(operation: () => Promise<T>): Promise<T | null> => {
    setState(prev => ({ ...prev, isLoading: true, error: undefined }));
    
    try {
      const result = await operation();
      setState(prev => ({ ...prev, isLoading: false }));
      return result;
    } catch (error) {
      return handleAIError(error);
    }
  }, [handleAIError]);

  // Assistant functions
  const sendAssistantMessage = useCallback(async (message: string, customContext?: any) => {
    return withLoading(async () => {
      const mentionRequest = {
        message,
        context: { ...context, ...customContext }
      };
      return await AIService.sendAssistantMessage(mentionRequest);
    });
  }, [context, withLoading]);

  const getContextualSuggestions = useCallback(async (customContext?: any): Promise<ResponseCard[]> => {
    const result = await withLoading(async () => {
      return await AIService.getContextualSuggestions({ ...context, ...customContext });
    });
    return result || [];
  }, [context, withLoading]);

  const sendFeedback = useCallback(async (interactionId: string, rating: number, text?: string): Promise<void> => {
    await withLoading(async () => {
      await AIService.sendAssistantFeedback(interactionId, rating, text);
      return undefined;
    });
  }, [withLoading]);

  // Magic Polls functions
  const createMagicPoll = useCallback(async (pollData: any) => {
    return withLoading(async () => {
      return await AIService.createMagicPoll({
        ...pollData,
        tripId: pollData.tripId || context?.tripId
      });
    });
  }, [context, withLoading]);

  const getTripPolls = useCallback(async (tripId?: string): Promise<MagicPoll[]> => {
    const targetTripId = tripId || context?.tripId;
    if (!targetTripId) {
      setState(prev => ({ ...prev, error: 'Trip ID required for polls' }));
      return [];
    }

    const result = await withLoading(async () => {
      return await AIService.getTripPolls(targetTripId);
    });
    return result || [];
  }, [context, withLoading]);

  const votePoll = useCallback(async (pollId: string, selectedOptions: string[]): Promise<void> => {
    await withLoading(async () => {
      await AIService.votePoll({ pollId, selectedOptions });
      return undefined;
    });
  }, [withLoading]);

  const getPollResults = useCallback(async (pollId: string) => {
    return withLoading(async () => {
      return await AIService.getPollResults(pollId);
    });
  }, [withLoading]);

  // Consensus functions
  const getConsensusAnalysis = useCallback(async (tripId?: string) => {
    const targetTripId = tripId || context?.tripId;
    if (!targetTripId) {
      setState(prev => ({ ...prev, error: 'Trip ID required for consensus analysis' }));
      return null;
    }

    return withLoading(async () => {
      return await AIService.getConsensusAnalysis(targetTripId);
    });
  }, [context, withLoading]);

  const getConsensusRecommendation = useCallback(async (tripId?: string, decisionType?: string) => {
    const targetTripId = tripId || context?.tripId;
    if (!targetTripId) {
      setState(prev => ({ ...prev, error: 'Trip ID required for consensus recommendation' }));
      return null;
    }

    return withLoading(async () => {
      return await AIService.getConsensusRecommendation(targetTripId, decisionType || 'general');
    });
  }, [context, withLoading]);

  // Itinerary functions
  const generateItinerary = useCallback(async (tripId?: string, preferences?: any, constraints?: any) => {
    const targetTripId = tripId || context?.tripId;
    if (!targetTripId) {
      setState(prev => ({ ...prev, error: 'Trip ID required for itinerary generation' }));
      return null;
    }

    return withLoading(async () => {
      return await AIService.generateItinerary({
        tripId: targetTripId,
        preferences: preferences || {},
        constraints: constraints || {}
      });
    });
  }, [context, withLoading]);

  const getItineraryStatus = useCallback(async (taskId: string) => {
    return withLoading(async () => {
      return await AIService.getItineraryStatus(taskId);
    });
  }, [withLoading]);

  // Utility functions
  const refreshCostStatus = useCallback(async () => {
    try {
      const costStatus = await AIService.getAICostStatus();
      setState(prev => ({
        ...prev,
        costStatus,
        gracefulMode: costStatus.gracefulMode
      }));
    } catch (error) {
      console.error('Failed to refresh cost status:', error);
    }
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: undefined }));
  }, []);

  // Load initial cost status
  useEffect(() => {
    refreshCostStatus();
  }, [refreshCostStatus]);

  return {
    state,
    
    // Assistant
    sendAssistantMessage,
    getContextualSuggestions,
    sendFeedback,
    
    // Magic Polls
    createMagicPoll,
    getTripPolls,
    votePoll,
    getPollResults,
    
    // Consensus
    getConsensusAnalysis,
    getConsensusRecommendation,
    
    // Itinerary
    generateItinerary,
    getItineraryStatus,
    
    // Utilities
    refreshCostStatus,
    clearError
  };
};

export default useAI;
