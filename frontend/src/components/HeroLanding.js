import React from 'react';
import HeroSection from './HeroSection';

const HeroLanding = ({ onNavigate }) => {
  const heroImageUrl = "https://customer-assets.emergentagent.com/job_kinaura-health/artifacts/huhxfd64_ChatGPT%20Image%20Aug%2014%2C%202025%2C%2012_52_16%20AM.png";

  return (
    <HeroSection 
      variant="image" 
      backgroundImage={heroImageUrl}
      showLogo={false}
      overlayOpacity={0.3}
    >
      <div className="flex flex-col items-center justify-center min-h-screen px-6 text-center relative">
        {/* Main Hero Content - Centered */}
        <div className="max-w-4xl mx-auto text-white mb-8">
          {/* Main Headline */}
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-light tracking-wide mb-8 leading-tight">
            <span className="text-white">KinAura</span>
          </h1>
          
          <h2 className="text-2xl md:text-3xl lg:text-4xl font-light mb-8 tracking-wide">
            Institute for Regenerative Wellness
          </h2>
          
          {/* Subtitle - Now clearly visible */}
          <p className="text-xl md:text-2xl lg:text-3xl font-light mb-8 max-w-4xl mx-auto leading-relaxed opacity-95">
            THE JOURNEY TO SELF-HEALING<br />
            & LONGEVITY THROUGH SCIENCE
          </p>
        </div>
        
        {/* Small Action Buttons at Bottom */}
        <div className="absolute bottom-20 left-1/2 transform -translate-x-1/2 w-full max-w-md">
          <div className="space-y-3 flex flex-col items-center">
            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4 items-center">
              <button
                onClick={() => onNavigate('services')}
                className="px-6 py-2 border border-white border-opacity-40 text-white rounded-full hover:bg-white hover:bg-opacity-10 transition-all duration-300 text-sm font-light tracking-wide backdrop-blur-sm bg-black bg-opacity-10"
              >
                EXPLORE SERVICES
              </button>
              
              <button
                onClick={() => onNavigate('services')}
                className="px-6 py-2 bg-white bg-opacity-10 text-white rounded-full hover:bg-opacity-20 transition-all duration-300 text-sm font-light tracking-wide backdrop-blur-sm border border-white border-opacity-20"
              >
                LEARN MORE
              </button>
            </div>
            
            {/* Login Button */}
            <button
              onClick={() => onNavigate('login')}
              className="px-6 py-2 bg-white bg-opacity-15 text-white rounded-full hover:bg-opacity-25 transition-all duration-300 text-sm font-light tracking-wide backdrop-blur-sm border border-white border-opacity-30 mt-2"
            >
              LOGIN / REGISTER
            </button>
          </div>
        </div>
        
        {/* Scroll Indicator - Moved up slightly */}
        <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 animate-bounce">
          <div className="w-4 h-6 border border-white border-opacity-40 rounded-full flex justify-center">
            <div className="w-0.5 h-1.5 bg-white bg-opacity-40 rounded-full mt-1 animate-pulse"></div>
          </div>
        </div>
        
        {/* Subtle Admin Access Button - Bottom Right */}
        <button
          onClick={() => onNavigate('login')}
          className="fixed bottom-6 right-6 w-10 h-10 bg-black bg-opacity-20 backdrop-blur-sm text-white rounded-full hover:bg-opacity-30 transition-all duration-300 flex items-center justify-center text-xs shadow-lg border border-white border-opacity-10"
          style={{ 
            zIndex: 10,
            backdropFilter: 'blur(10px)'
          }}
          title="Admin Access"
        >
          ⚙️
        </button>
      </div>
    </HeroSection>
  );
};

export default HeroLanding;