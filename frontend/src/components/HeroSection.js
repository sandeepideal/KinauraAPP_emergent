import React, { useRef, useEffect } from 'react';
import KinAuraLogo from './KinAuraLogo';
import { designTokens } from '../designTokens';

const HeroSection = ({ 
  children, 
  variant = 'cream', // 'cream', 'gradient', 'image'
  backgroundImage = null,
  showLogo = true,
  onLogoClick = null,
  className = '',
  overlayOpacity = 0.3
}) => {
  const heroRef = useRef(null);

  // Background variants
  const getBackgroundClasses = () => {
    switch (variant) {
      case 'gradient':
        return 'bg-gradient-to-br from-cream via-white to-gray-50';
      case 'image':
        return 'bg-cover bg-no-repeat bg-top';
      case 'cream':
      default:
        return 'bg-cream';
    }
  };

  const getBackgroundStyle = () => {
    if (variant === 'image' && backgroundImage) {
      return {
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: '50% 20%',
        backgroundRepeat: 'no-repeat'
      };
    }
    return {};
  };

  return (
    <div 
      ref={heroRef}
      className={`
        min-h-screen relative overflow-hidden
        ${getBackgroundClasses()}
        ${className}
      `}
      style={getBackgroundStyle()}
    >
      {/* Background overlay for better text readability on images */}
      {variant === 'image' && backgroundImage && (
        <div 
          className="absolute inset-0 bg-black"
          style={{ opacity: overlayOpacity }}
        />
      )}

      {/* Integrated Logo - positioned absolutely over hero */}
      {showLogo && (
        <KinAuraLogo 
          heroRef={heroRef}
          onClick={onLogoClick}
          variant={variant === 'image' ? 'light' : 'adaptive'}
        />
      )}

      {/* Kintsugi Background Lines - only show on non-image variants */}
      {variant !== 'image' && (
        <div className="kintsugi-lines">
          <svg viewBox="0 0 400 800" className="w-full h-full">
            <path d="M50,200 Q200,250 350,200 T600,250" className="kintsugi-gold"/>
            <path d="M0,400 Q150,350 300,400 T500,350" className="kintsugi-gold"/>
            <path d="M100,600 Q250,550 400,600 T700,550" className="kintsugi-gold"/>
          </svg>
        </div>
      )}

      {/* Hero Content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        {children}
      </div>
    </div>
  );
};

export default HeroSection;