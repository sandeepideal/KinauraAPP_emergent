import React, { useState, useEffect } from 'react';
import './AnimatedBackground.css';

const AnimatedBackground = ({ scope = 'global', enabled = true, intensity = 2, palette = 'gold600' }) => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [cssSupported, setCssSupported] = useState(true);

  useEffect(() => {
    // Check for reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  useEffect(() => {
    // Test CSS animation support
    const testEl = document.createElement('div');
    testEl.style.animation = 'test 1s linear';
    setCssSupported(testEl.style.animation !== '');
  }, []);

  // Don't render if disabled
  if (!enabled) return null;

  // Fallback for unsupported browsers
  if (!cssSupported) {
    return <div className="ka-bg-fallback" aria-hidden="true" />;
  }

  return (
    <div 
      className="ka-bg" 
      aria-hidden="true"
      data-intensity={intensity}
      data-palette={palette}
      data-scope={scope}
    >
      <svg 
        viewBox="0 0 100 100" 
        preserveAspectRatio="xMidYMid slice"
        role="presentation"
      >
        <defs>
          {/* Default gold gradient */}
          <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#CFA544" />
            <stop offset="100%" stopColor="#B88E35" />
          </linearGradient>
          
          {/* Gold 500 variant */}
          <linearGradient id="goldGrad500" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#D4AF37" />
            <stop offset="100%" stopColor="#C8A25A" />
          </linearGradient>
          
          {/* Gold 600 variant */}
          <linearGradient id="goldGrad600" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#CFA544" />
            <stop offset="100%" stopColor="#B88E35" />
          </linearGradient>
        </defs>
        
        {/* Kintsugi-inspired diagonal strokes */}
        <g>
          <path 
            className="line" 
            d="M-10,25 Q20,5 45,15 T110,8" 
            strokeWidth="1.8"
          />
          <path 
            className="line" 
            d="M-5,55 Q25,35 50,45 T105,52" 
            strokeWidth="2.2"
          />
          <path 
            className="line" 
            d="M-15,85 Q15,65 40,75 T120,78" 
            strokeWidth="2.0"
          />
          <path 
            className="line" 
            d="M-8,35 Q30,20 65,25 T115,30" 
            strokeWidth="1.5"
          />
        </g>
      </svg>
    </div>
  );
};

export default AnimatedBackground;