// KinAura Design Tokens
export const designTokens = {
  brand: {
    gold: "#C8A25A",
    charcoal: "#222428",
    cream: "#F5F3F0",
    logoOnDark: "#FFFFFF",
    logoOnLight: "#222428"
  },
  elevation: {
    overlayGlow: "0 1px 8px rgba(0,0,0,0.35)"
  },
  space: {
    headerPadMobile: 16,
    headerPadTablet: 20, 
    headerPadDesktop: 24
  },
  sizes: {
    logoHMobile: 28,
    logoHTablet: 32,
    logoHDesktop: 40
  },
  breakpoints: {
    mobile: 0,
    tablet: 768,
    desktop: 1024
  }
};

// Utility function to get accessible logo color based on background luminance
export const getAccessibleLogoColor = (heroSampleLuminance) => {
  // If luminance is below 0.5, background is dark, use light logo
  return heroSampleLuminance < 0.5 ? 'logoOnDark' : 'logoOnLight';
};

// Utility function to calculate luminance from RGB
export const calculateLuminance = (r, g, b) => {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
};

// Utility function to sample hero background color at logo position
export const sampleHeroLuminance = (heroElement) => {
  if (!heroElement) return 0.5; // Default to medium luminance
  
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 32;
    canvas.height = 32;
    
    // Sample area where logo would be positioned (top-left)
    const rect = heroElement.getBoundingClientRect();
    const sampleX = designTokens.space.headerPadDesktop;
    const sampleY = designTokens.space.headerPadDesktop;
    
    // This is a simplified approach - in a real implementation,
    // you might use more sophisticated image analysis
    const computedStyle = window.getComputedStyle(heroElement);
    const bgColor = computedStyle.backgroundColor;
    
    if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)') {
      // Extract RGB values from computed background color
      const rgbMatch = bgColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
      if (rgbMatch) {
        const [, r, g, b] = rgbMatch.map(Number);
        return calculateLuminance(r, g, b);
      }
    }
    
    // Fallback: analyze based on background image or default
    return 0.5; // Medium luminance fallback
  } catch (error) {
    console.warn('Hero luminance sampling failed:', error);
    return 0.5; // Safe fallback
  }
};

export default designTokens;