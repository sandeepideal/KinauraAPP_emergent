import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';

const LanguageToggle = ({ className = "", size = "default" }) => {
  const { language, switchLanguage } = useLanguage();

  const toggleLanguage = () => {
    const newLanguage = language === 'en' ? 'it' : 'en';
    switchLanguage(newLanguage);
  };

  const sizeClasses = {
    small: "w-8 h-8 text-xs",
    default: "w-10 h-10 text-sm", 
    large: "w-12 h-12 text-base"
  };

  return (
    <button
      onClick={toggleLanguage}
      className={`
        ${sizeClasses[size]}
        bg-white/10 hover:bg-white/20 
        border border-white/20 hover:border-white/30
        rounded-lg flex items-center justify-center
        text-white font-medium
        transition-all duration-200 ease-in-out
        backdrop-blur-sm
        ${className}
      `}
      aria-label={`Switch to ${language === 'en' ? 'Italian' : 'English'}`}
      title={`Switch to ${language === 'en' ? 'Italiano' : 'English'}`}
    >
      <div className="flex items-center space-x-1">
        <span className="text-xs opacity-60">
          {language === 'en' ? '🇺🇸' : '🇮🇹'}
        </span>
        <span className="font-semibold">
          {language === 'en' ? 'EN' : 'IT'}
        </span>
      </div>
    </button>
  );
};

// Alternative compact version for mobile/small spaces
export const CompactLanguageToggle = ({ className = "" }) => {
  const { language, switchLanguage } = useLanguage();

  const toggleLanguage = () => {
    const newLanguage = language === 'en' ? 'it' : 'en';
    switchLanguage(newLanguage);
  };

  return (
    <button
      onClick={toggleLanguage}
      className={`
        px-3 py-1.5 rounded-md
        bg-[#C8A25A]/10 hover:bg-[#C8A25A]/20
        border border-[#C8A25A]/30 hover:border-[#C8A25A]/50
        text-[#C8A25A] font-medium text-sm
        transition-all duration-200 ease-in-out
        ${className}
      `}
      aria-label={`Switch to ${language === 'en' ? 'Italian' : 'English'}`}
    >
      {language === 'en' ? 'IT' : 'EN'}
    </button>
  );
};

// Language toggle for dark themes
export const DarkLanguageToggle = ({ className = "" }) => {
  const { language, switchLanguage } = useLanguage();

  const toggleLanguage = () => {
    const newLanguage = language === 'en' ? 'it' : 'en';
    switchLanguage(newLanguage);
  };

  return (
    <button
      onClick={toggleLanguage}
      className={`
        w-10 h-10 rounded-lg
        bg-gray-800 hover:bg-gray-700
        border border-gray-600 hover:border-gray-500
        text-white font-medium text-sm
        transition-all duration-200 ease-in-out
        flex items-center justify-center
        ${className}
      `}
      aria-label={`Switch to ${language === 'en' ? 'Italian' : 'English'}`}
    >
      <div className="flex items-center space-x-1">
        <span className="text-xs">
          {language === 'en' ? '🇺🇸' : '🇮🇹'}
        </span>
        <span>
          {language === 'en' ? 'EN' : 'IT'}
        </span>
      </div>
    </button>
  );
};

export default LanguageToggle;