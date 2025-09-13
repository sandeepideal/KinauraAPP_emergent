import React from 'react';
import { useTheme } from '../utils/theme';

const ThemeToggle = ({ className = "", size = "default" }) => {
  const { theme, toggleTheme, isLight } = useTheme();

  const sizeClasses = {
    small: "w-8 h-8 text-xs",
    default: "w-10 h-10 text-sm",
    large: "w-12 h-12 text-base"
  };

  return (
    <button
      onClick={toggleTheme}
      className={`
        ${sizeClasses[size]}
        theme-toggle
        flex items-center justify-center
        ${className}
      `}
      aria-label={`Switch to ${isLight ? 'dark' : 'light'} theme`}
      title={`Switch to ${isLight ? 'dark' : 'light'} theme`}
    >
      {isLight ? (
        // Moon icon for dark mode
        <svg 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="1.5" 
          className="ka-icon ka-icon--md"
        >
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      ) : (
        // Sun icon for light mode
        <svg 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="1.5" 
          className="ka-icon ka-icon--md"
        >
          <circle cx="12" cy="12" r="5" />
          <path d="m12 1-1-1 1 1zm0 22-1-1 1 1zm11-11-1-1 1 1zm-22 0-1-1 1 1zm15.5-6.5L17 4l-.5.5zM6.5 17.5 6 18l.5-.5zM4 6.5 4.5 6 4 6.5zm15 11-.5.5.5-.5z" />
        </svg>
      )}
    </button>
  );
};

export default ThemeToggle;