// Onboarding Analytics Service
// Tracks user behavior and conversion metrics for the golden path onboarding

export interface OnboardingAnalytics {
  sessionId: string;
  userId?: string;
  startTime: number;
  currentStep: string;
  stepStartTime: number;
  tripTypeSelectionTime?: number;
  sampleTripGenerationTime?: number;
  completionTime?: number;
  totalDuration?: number;
  tripTypeSelected?: string;
  sampleTripGenerated?: string;
  regenerationCount: number;
  dropOffStep?: string;
  deviceType: 'mobile' | 'tablet' | 'desktop';
  completed: boolean;
}

export interface OnboardingMetrics {
  totalSessions: number;
  completedSessions: number;
  conversionRate: number;
  averageCompletionTime: number;
  dropOffPoints: Record<string, number>;
  popularTripTypes: Record<string, number>;
  regenerationStats: {
    averageRegenerations: number;
    maxRegenerations: number;
  };
  deviceBreakdown: Record<string, number>;
  timeToFirstAction: number; // Time to select first trip type
  timeToCompletion: number; // Time from start to completion
}

class OnboardingAnalyticsService {
  private static instance: OnboardingAnalyticsService;
  private analytics: OnboardingAnalytics;
  private isInitialized = false;

  private constructor() {
    this.analytics = this.initializeSession();
  }

  static getInstance(): OnboardingAnalyticsService {
    if (!OnboardingAnalyticsService.instance) {
      OnboardingAnalyticsService.instance = new OnboardingAnalyticsService();
    }
    return OnboardingAnalyticsService.instance;
  }

  private initializeSession(): OnboardingAnalytics {
    const sessionId = this.generateSessionId();
    const now = Date.now();
    
    return {
      sessionId,
      startTime: now,
      currentStep: 'trip-type-selection',
      stepStartTime: now,
      regenerationCount: 0,
      deviceType: this.detectDeviceType(),
      completed: false,
    };
  }

  private generateSessionId(): string {
    return `onboarding-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private detectDeviceType(): 'mobile' | 'tablet' | 'desktop' {
    if (typeof window === 'undefined') return 'desktop';
    
    const width = window.innerWidth;
    if (width < 768) return 'mobile';
    if (width < 1024) return 'tablet';
    return 'desktop';
  }

  // Initialize tracking for a user
  startSession(userId?: string): void {
    this.analytics = this.initializeSession();
    if (userId) {
      this.analytics.userId = userId;
    }
    this.isInitialized = true;
    this.trackEvent('onboarding_started');
  }

  // Track when user selects trip type
  trackTripTypeSelection(tripType: string): void {
    if (!this.isInitialized) return;
    
    const now = Date.now();
    this.analytics.tripTypeSelected = tripType;
    this.analytics.tripTypeSelectionTime = now - this.analytics.stepStartTime;
    this.analytics.currentStep = 'sample-trip-generation';
    this.analytics.stepStartTime = now;
    
    this.trackEvent('trip_type_selected', { tripType, selectionTime: this.analytics.tripTypeSelectionTime });
  }

  // Track when sample trip is generated
  trackSampleTripGeneration(templateId: string): void {
    if (!this.isInitialized) return;
    
    const now = Date.now();
    this.analytics.sampleTripGenerated = templateId;
    this.analytics.sampleTripGenerationTime = now - this.analytics.stepStartTime;
    this.analytics.currentStep = 'trip-review';
    this.analytics.stepStartTime = now;
    
    this.trackEvent('sample_trip_generated', { 
      templateId, 
      generationTime: this.analytics.sampleTripGenerationTime 
    });
  }

  // Track when user regenerates a trip
  trackTripRegeneration(newTemplateId: string): void {
    if (!this.isInitialized) return;
    
    this.analytics.regenerationCount += 1;
    this.analytics.sampleTripGenerated = newTemplateId;
    
    this.trackEvent('trip_regenerated', { 
      newTemplateId, 
      regenerationCount: this.analytics.regenerationCount 
    });
  }

  // Track completion
  trackCompletion(): void {
    if (!this.isInitialized) return;
    
    const now = Date.now();
    this.analytics.completionTime = now - this.analytics.stepStartTime;
    this.analytics.totalDuration = now - this.analytics.startTime;
    this.analytics.completed = true;
    this.analytics.currentStep = 'completed';
    
    this.trackEvent('onboarding_completed', {
      totalDuration: this.analytics.totalDuration,
      tripTypeSelectionTime: this.analytics.tripTypeSelectionTime,
      sampleTripGenerationTime: this.analytics.sampleTripGenerationTime,
      completionTime: this.analytics.completionTime,
      regenerationCount: this.analytics.regenerationCount,
      tripType: this.analytics.tripTypeSelected,
      sampleTrip: this.analytics.sampleTripGenerated,
    });

    // Send final analytics
    this.sendAnalytics();
  }

  // Track drop-off
  trackDropOff(reason?: string): void {
    if (!this.isInitialized) return;
    
    this.analytics.dropOffStep = this.analytics.currentStep;
    
    this.trackEvent('onboarding_dropped_off', {
      dropOffStep: this.analytics.dropOffStep,
      timeSpent: Date.now() - this.analytics.startTime,
      reason,
    });

    // Send analytics even for incomplete sessions
    this.sendAnalytics();
  }

  // Get current session analytics
  getCurrentAnalytics(): OnboardingAnalytics {
    return { ...this.analytics };
  }

  // Check if user completed onboarding within target time (60 seconds)
  isWithinTargetTime(): boolean {
    if (!this.analytics.totalDuration) return false;
    return this.analytics.totalDuration <= 60000; // 60 seconds in milliseconds
  }

  // Private method to track individual events
  private trackEvent(eventName: string, properties?: Record<string, any>): void {
    const event = {
      event: eventName,
      sessionId: this.analytics.sessionId,
      userId: this.analytics.userId,
      timestamp: Date.now(),
      step: this.analytics.currentStep,
      deviceType: this.analytics.deviceType,
      ...properties,
    };

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log('📊 Onboarding Analytics Event:', event);
    }

    // In production, send to analytics service
    this.sendToAnalyticsService(event);
  }

  // Send analytics data to backend/analytics service
  private async sendAnalytics(): Promise<void> {
    try {
      const payload = {
        ...this.analytics,
        timestamp: Date.now(),
      };

      // In development, just log
      if (process.env.NODE_ENV === 'development') {
        console.log('📊 Final Onboarding Analytics:', payload);
        return;
      }

      // In production, send to analytics endpoint
      await fetch('/api/analytics/onboarding', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
    } catch (error) {
      console.error('Failed to send onboarding analytics:', error);
    }
  }

  private async sendToAnalyticsService(event: any): Promise<void> {
    try {
      if (process.env.NODE_ENV === 'development') {
        return; // Already logged to console
      }

      await fetch('/api/analytics/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(event),
      });
    } catch (error) {
      console.error('Failed to send analytics event:', error);
    }
  }

  // Public method for tracking custom events (used by A/B testing)
  public trackCustomEvent(eventName: string, properties?: Record<string, any>): void {
    this.trackEvent(eventName, properties);
  }
}

// Utility functions for A/B testing
export class OnboardingABTesting {
  private static readonly AB_TEST_KEY = 'pathfinder_onboarding_variant';
  private static readonly VARIANTS = ['control', 'variant_a', 'variant_b'] as const;
  
  static getVariant(): string {
    type Variant = typeof OnboardingABTesting.VARIANTS[number];
    
    // Check if user already has a variant assigned
    const stored = localStorage.getItem(this.AB_TEST_KEY);
    if (stored && this.VARIANTS.includes(stored as Variant)) {
      return stored as Variant;
    }

    // Assign new variant randomly
    const randomIndex = Math.floor(Math.random() * this.VARIANTS.length);
    const variant = this.VARIANTS[randomIndex];
    
    localStorage.setItem(this.AB_TEST_KEY, variant);
    return variant;
  }

  static trackVariant(variant: string): void {
    OnboardingAnalyticsService.getInstance().trackCustomEvent('ab_test_variant_assigned', { variant });
  }
}

// Export singleton instance
export const onboardingAnalytics = OnboardingAnalyticsService.getInstance();

// Hook for React components
export const useOnboardingAnalytics = () => {
  return {
    startSession: (userId?: string) => onboardingAnalytics.startSession(userId),
    trackTripTypeSelection: (tripType: string) => onboardingAnalytics.trackTripTypeSelection(tripType),
    trackSampleTripGeneration: (templateId: string) => onboardingAnalytics.trackSampleTripGeneration(templateId),
    trackTripRegeneration: (templateId: string) => onboardingAnalytics.trackTripRegeneration(templateId),
    trackCompletion: () => onboardingAnalytics.trackCompletion(),
    trackDropOff: (reason?: string) => onboardingAnalytics.trackDropOff(reason),
    getCurrentAnalytics: () => onboardingAnalytics.getCurrentAnalytics(),
    isWithinTargetTime: () => onboardingAnalytics.isWithinTargetTime(),
  };
};
