/**
 * Utilities for monitoring and reporting application performance
 */

// Types for performance metrics
export interface PerformanceMetrics {
  timeToFirstByte?: number;
  timeToFirstPaint?: number;
  timeToFirstContentfulPaint?: number;
  domContentLoaded?: number;
  domComplete?: number;
  loadEvent?: number;
  apiResponseTimes: Record<string, number[]>;
  componentRenderTimes: Record<string, number[]>;
  routeChangeLatencies: Record<string, number[]>;
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics = {
    apiResponseTimes: {},
    componentRenderTimes: {},
    routeChangeLatencies: {},
  };
  
  private routeChangeStartTime: number | null = null;
  private isEnabled = false;
  
  // Configurable sample rate to reduce performance overhead
  private sampleRate = 0.1; // Only log 10% of measurements
  
  // Initialize performance monitoring
  init() {
    if (typeof window === 'undefined' || !window.performance) {
      return;
    }
    
    this.isEnabled = true;
    this.collectNavigationTiming();
    this.observePaintTiming();
  }
  
  // Collect standard navigation timing metrics
  private collectNavigationTiming() {
    if (!this.isEnabled) return;
    
    window.addEventListener('load', () => {
      setTimeout(() => {
        const perfEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (perfEntry) {
          this.metrics.timeToFirstByte = perfEntry.responseStart;
          this.metrics.domContentLoaded = perfEntry.domContentLoadedEventEnd;
          this.metrics.domComplete = perfEntry.domComplete;
          this.metrics.loadEvent = perfEntry.loadEventEnd;
        }
      }, 0);
    });
  }
  
  // Observe paint timing metrics
  private observePaintTiming() {
    if (!this.isEnabled || !PerformanceObserver) return;
    
    try {
      const paintObserver = new PerformanceObserver((entries) => {
        entries.getEntries().forEach((entry) => {
          const paintMetric = entry as PerformancePaintTiming;
          
          if (paintMetric.name === 'first-paint') {
            this.metrics.timeToFirstPaint = paintMetric.startTime;
          }
          
          if (paintMetric.name === 'first-contentful-paint') {
            this.metrics.timeToFirstContentfulPaint = paintMetric.startTime;
          }
        });
      });
      
      paintObserver.observe({ entryTypes: ['paint'] });
    } catch (e) {
      console.error('Paint timing observation not supported', e);
    }
  }
  
  // Track API request timing
  trackApiRequest(endpoint: string, duration: number) {
    if (!this.isEnabled || Math.random() > this.sampleRate) return;
    
    if (!this.metrics.apiResponseTimes[endpoint]) {
      this.metrics.apiResponseTimes[endpoint] = [];
    }
    
    this.metrics.apiResponseTimes[endpoint].push(duration);
    
    // Keep only the last 10 measurements for each endpoint
    if (this.metrics.apiResponseTimes[endpoint].length > 10) {
      this.metrics.apiResponseTimes[endpoint].shift();
    }
  }
  
  // Track component render timing
  trackComponentRender(componentName: string, duration: number) {
    if (!this.isEnabled || Math.random() > this.sampleRate) return;
    
    if (!this.metrics.componentRenderTimes[componentName]) {
      this.metrics.componentRenderTimes[componentName] = [];
    }
    
    this.metrics.componentRenderTimes[componentName].push(duration);
    
    // Keep only the last 5 render times
    if (this.metrics.componentRenderTimes[componentName].length > 5) {
      this.metrics.componentRenderTimes[componentName].shift();
    }
  }
  
  // Start tracking route change
  startRouteChange() {
    if (!this.isEnabled) return;
    this.routeChangeStartTime = performance.now();
  }
  
  // Complete route change tracking
  completeRouteChange(route: string) {
    if (!this.isEnabled || !this.routeChangeStartTime) return;
    
    const duration = performance.now() - this.routeChangeStartTime;
    if (!this.metrics.routeChangeLatencies[route]) {
      this.metrics.routeChangeLatencies[route] = [];
    }
    
    this.metrics.routeChangeLatencies[route].push(duration);
    this.routeChangeStartTime = null;
  }
  
  // Get current metrics snapshot
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }
  
  // Log current metrics to console (for development)
  logMetrics() {
    if (!this.isEnabled) return;
    
    console.group('Performance Metrics');
    console.log('Navigation Timing:', {
      TTFB: this.formatTime(this.metrics.timeToFirstByte),
      FP: this.formatTime(this.metrics.timeToFirstPaint),
      FCP: this.formatTime(this.metrics.timeToFirstContentfulPaint),
      DCL: this.formatTime(this.metrics.domContentLoaded),
      Load: this.formatTime(this.metrics.loadEvent),
    });
    
    console.log('API Response Times (avg in ms):');
    Object.entries(this.metrics.apiResponseTimes).forEach(([endpoint, times]) => {
      const avg = times.reduce((sum, time) => sum + time, 0) / times.length;
      console.log(`  ${endpoint}: ${avg.toFixed(2)}ms`);
    });
    
    console.log('Component Render Times (avg in ms):');
    Object.entries(this.metrics.componentRenderTimes).forEach(([component, times]) => {
      const avg = times.reduce((sum, time) => sum + time, 0) / times.length;
      console.log(`  ${component}: ${avg.toFixed(2)}ms`);
    });
    
    console.log('Route Change Latencies (avg in ms):');
    Object.entries(this.metrics.routeChangeLatencies).forEach(([route, times]) => {
      const avg = times.reduce((sum, time) => sum + time, 0) / times.length;
      console.log(`  ${route}: ${avg.toFixed(2)}ms`);
    });
    
    console.groupEnd();
  }
  
  // Format time in ms with units
  private formatTime(time: number | undefined): string {
    if (time === undefined) return 'N/A';
    return `${time.toFixed(2)}ms`;
  }
}

// Create singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Export high-level API for easy use
export const initPerformanceMonitoring = () => performanceMonitor.init();
export const trackApiCall = (endpoint: string, duration: number) => 
  performanceMonitor.trackApiRequest(endpoint, duration);
export const trackComponentRender = (component: string, duration: number) => 
  performanceMonitor.trackComponentRender(component, duration);
export const startRouteChange = () => performanceMonitor.startRouteChange();
export const completeRouteChange = (route: string) => 
  performanceMonitor.completeRouteChange(route);
export const logPerformanceMetrics = () => performanceMonitor.logMetrics();
