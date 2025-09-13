import React, { useState, useRef, useEffect } from 'react';

/**
 * OptimizedImage component with modern format support and lazy loading
 */
const OptimizedImage = ({
  src,
  alt,
  width,
  height,
  className = '',
  loading = 'lazy', // 'eager' for above-the-fold images
  priority = false,
  sizes = '100vw',
  fallbackSrc,
  onLoad,
  onError,
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const imgRef = useRef();

  // Generate optimized src URLs
  const generateSrcSet = (originalSrc) => {
    // In a real app, this would generate different sizes and formats
    // For now, we'll use the original but could implement WebP/AVIF conversion
    const baseUrl = originalSrc.split('?')[0];
    
    // You could implement a service that converts images to different formats
    // const webpUrl = `${baseUrl}?format=webp`;
    // const avifUrl = `${baseUrl}?format=avif`;
    
    return {
      original: originalSrc,
      // webp: webpUrl,
      // avif: avifUrl
    };
  };

  const srcSet = generateSrcSet(src);

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (loading === 'eager' || priority) {
      setIsInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      {
        rootMargin: '50px', // Load 50px before entering viewport
        threshold: 0.1
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, [loading, priority]);

  const handleLoad = (e) => {
    setIsLoaded(true);
    onLoad?.(e);
  };

  const handleError = (e) => {
    setHasError(true);
    onError?.(e);
  };

  // Respect reduced motion preferences
  const shouldReduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  return (
    <div 
      ref={imgRef}
      className={`relative overflow-hidden ${className}`}
      style={{ 
        width: width || 'auto',
        height: height || 'auto'
      }}
    >
      {/* Placeholder/Loading skeleton */}
      {(!isLoaded && isInView) && (
        <div 
          className={`
            absolute inset-0 bg-ka-muted animate-pulse
            ${shouldReduceMotion ? '' : 'animate-shimmer'}
          `}
          style={{
            width: width || '100%',
            height: height || '100%'
          }}
        />
      )}

      {/* Optimized Picture element with multiple formats */}
      {isInView && (
        <picture>
          {/* Future: AVIF format for maximum compression */}
          {/* <source srcSet={srcSet.avif} type="image/avif" /> */}
          
          {/* Future: WebP format for better compression */}
          {/* <source srcSet={srcSet.webp} type="image/webp" /> */}
          
          {/* Fallback to original format */}
          <img
            src={hasError ? (fallbackSrc || src) : srcSet.original}
            alt={alt}
            width={width}
            height={height}
            loading={loading}
            sizes={sizes}
            className={`
              transition-opacity duration-300
              ${isLoaded ? 'opacity-100' : 'opacity-0'}
            `}
            onLoad={handleLoad}
            onError={handleError}
            {...props}
          />
        </picture>
      )}

      {/* Error state */}
      {hasError && !fallbackSrc && (
        <div className="absolute inset-0 flex items-center justify-center bg-ka-muted text-ka-text-2">
          <div className="text-center">
            <svg 
              className="w-8 h-8 mx-auto mb-2 text-ka-text-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" 
              />
            </svg>
            <span className="text-sm">Failed to load image</span>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Logo component with preloading for critical images
 */
export const OptimizedLogo = ({ className = '', size = 32, priority = true }) => (
  <OptimizedImage
    src="/brand/kinaura-symbol.svg"
    alt="KinAura"
    width={size}
    height={size}
    loading={priority ? 'eager' : 'lazy'}
    priority={priority}
    className={`ka-logo ${className}`}
    fallbackSrc="/logo192.png" // Fallback to local logo if available
  />
);

/**
 * Hero image component optimized for LCP
 */
export const OptimizedHeroImage = ({ 
  src, 
  alt, 
  className = '', 
  priority = true 
}) => (
  <OptimizedImage
    src={src}
    alt={alt}
    loading={priority ? 'eager' : 'lazy'}
    priority={priority}
    sizes="100vw"
    className={className}
  />
);

export default OptimizedImage;