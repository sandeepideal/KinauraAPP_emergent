import React, { useState, useEffect, useRef } from 'react';
import { designTokens } from '../designTokens';

const KinAuraLogo = ({ 
  heroRef = null, 
  className = '', 
  onClick = null,
  variant = 'adaptive' // 'adaptive', 'light', 'dark'
}) => {
  const [currentSize, setCurrentSize] = useState(designTokens.sizes.logoHDesktop);
  const logoRef = useRef(null);

  // Responsive size calculation
  useEffect(() => {
    const updateSize = () => {
      const width = window.innerWidth;
      if (width < designTokens.breakpoints.tablet) {
        setCurrentSize(designTokens.sizes.logoHMobile);
      } else if (width < designTokens.breakpoints.desktop) {
        setCurrentSize(designTokens.sizes.logoHTablet);
      } else {
        setCurrentSize(designTokens.sizes.logoHDesktop);
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Calculate responsive padding
  const getResponsivePadding = () => {
    const width = window.innerWidth;
    if (width < designTokens.breakpoints.tablet) {
      return designTokens.space.headerPadMobile;
    } else if (width < designTokens.breakpoints.desktop) {
      return designTokens.space.headerPadTablet;
    } else {
      return designTokens.space.headerPadDesktop;
    }
  };

  const padding = getResponsivePadding();

  return (
    <div
      ref={logoRef}
      className={`
        fixed top-0 left-0 z-50 
        transition-opacity duration-150 ease-in-out
        hover:opacity-85
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      style={{
        padding: `${padding}px`,
        minWidth: '80px', // Increased from 44px
        minHeight: '80px', // Increased from 44px
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'flex-start'
      }}
      onClick={onClick}
    >
      <img
        src="/brand/kinaura-symbol.svg"
        alt="KinAura"
        className="ka-logo"
        style={{
          height: `${currentSize * 2.5}px`,
          width: 'auto'
        }}
      />
    </div>
  );
};

export default KinAuraLogo;