/**
 * Performance utility functions for image loading and resource optimization
 */

/**
 * Image optimization and lazy loading helper
 * Uses native browser lazy loading with IntersectionObserver fallback
 */
export const optimizeImage = (src: string, options: {
  width?: number;
  height?: number;
  quality?: number;
  format?: 'webp' | 'jpeg' | 'png' | 'avif';
}) => {
  // Construct optimized image URL based on options
  // This can be adapted to work with your image CDN or optimization service
  let optimizedUrl = src;
  const params = new URLSearchParams();
  
  if (options.width) params.append('w', options.width.toString());
  if (options.height) params.append('h', options.height.toString());
  if (options.quality) params.append('q', options.quality.toString());
  if (options.format) params.append('fm', options.format);
  
  // Append query params if any were added
  if ([...params.entries()].length > 0) {
    optimizedUrl += `${src.includes('?') ? '&' : '?'}${params.toString()}`;
  }
  
  return optimizedUrl;
};

/**
 * Lazy load an image with IntersectionObserver
 * Creates a better user experience by loading images only when they're about to come into view
 */
export const lazyLoadImage = (imageRef: HTMLImageElement, src: string, onLoad?: () => void) => {
  if (!imageRef) return;
  
  // Use native lazy loading if supported
  if ('loading' in HTMLImageElement.prototype) {
    imageRef.loading = 'lazy';
    imageRef.src = src;
    if (onLoad) imageRef.addEventListener('load', onLoad);
    return;
  }
  
  // Fallback to IntersectionObserver
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement;
        img.src = src;
        if (onLoad) img.addEventListener('load', onLoad);
        observer.unobserve(img);
      }
    });
  }, {
    rootMargin: '200px', // Start loading when image is 200px from viewport
  });
  
  observer.observe(imageRef);
  
  return () => {
    if (imageRef) observer.unobserve(imageRef);
  };
};

/**
 * Dynamic import for component code splitting
 * @param importFunc - Dynamic import function for a component
 * @returns A lazy-loaded component
 */
export const lazyImport = (importFunc: () => Promise<any>) => {
  return React.lazy(importFunc);
};

/**
 * Measure component render time
 * Useful for identifying slow-rendering components
 */
export const withPerformanceTracking = (WrappedComponent: React.ComponentType<any>, componentName: string) => {
  return function PerformanceTrackedComponent(props: any) {
    const startTime = performance.now();
    
    React.useEffect(() => {
      const endTime = performance.now();
      console.log(`[Performance] ${componentName} rendered in ${endTime - startTime}ms`);
    }, []);
    
    return <WrappedComponent {...props} />;
  };
};

/**
 * Simple memoization function for expensive calculations
 */
export function memoize<T, R>(fn: (arg: T) => R): (arg: T) => R {
  const cache = new Map<T, R>();
  
  return (arg: T) => {
    if (cache.has(arg)) {
      return cache.get(arg)!;
    }
    
    const result = fn(arg);
    cache.set(arg, result);
    return result;
  };
}

// Import for React.lazy
import React from 'react';
