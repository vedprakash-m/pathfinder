import React, { useRef, useEffect, useState } from 'react';
import { optimizeImage, lazyLoadImage } from '@/utils/performance';

interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  quality?: number;
  format?: 'webp' | 'jpeg' | 'png' | 'avif';
  placeholderSrc?: string;
  onLoad?: () => void;
  className?: string;
}

export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  width,
  height,
  quality = 80,
  format = 'webp',
  placeholderSrc,
  onLoad,
  className = '',
  ...props
}) => {
  const imageRef = useRef<HTMLImageElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState(false);
  
  // Optimize the image URL
  const optimizedSrc = optimizeImage(src, {
    width,
    height,
    quality,
    format,
  });
  
  useEffect(() => {
    if (!imageRef.current) return;
    
    const handleImageLoad = () => {
      setIsLoaded(true);
      if (onLoad) onLoad();
    };
    
    const handleImageError = () => {
      setError(true);
      console.error(`Failed to load image: ${optimizedSrc}`);
    };
    
    // Set up lazy loading
    const cleanup = lazyLoadImage(imageRef.current, optimizedSrc, handleImageLoad);
    
    // Add error handling
    if (imageRef.current) {
      imageRef.current.addEventListener('error', handleImageError);
    }
    
    return () => {
      if (cleanup) cleanup();
      if (imageRef.current) {
        imageRef.current.removeEventListener('error', handleImageError);
      }
    };
  }, [optimizedSrc, onLoad]);
  
  return (
    <div className={`relative overflow-hidden ${className}`} style={{ width, height }}>
      {!isLoaded && placeholderSrc && (
        <img
          src={placeholderSrc}
          alt={alt}
          className="absolute inset-0 w-full h-full object-cover transition-opacity"
          style={{ opacity: isLoaded ? 0 : 1 }}
        />
      )}
      
      <img
        ref={imageRef}
        alt={alt}
        className={`w-full h-full object-cover transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
        width={width}
        height={height}
        {...props}
      />
      
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-neutral-100 text-neutral-500">
          <span>Failed to load image</span>
        </div>
      )}
    </div>
  );
};

export default LazyImage;
