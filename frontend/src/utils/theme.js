import { createContext, useContext, useState, useEffect } from 'react';

// Theme context
const ThemeContext = createContext();

// Theme provider component
export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    // Check localStorage first, then system preference
    const savedTheme = localStorage.getItem('kinaura-theme');
    if (savedTheme) {
      return savedTheme;
    }
    
    // Default to light theme
    return 'light';
  });

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('kinaura-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  const value = {
    theme,
    setTheme,
    toggleTheme,
    isLight: theme === 'light',
    isDark: theme === 'dark'
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook to use theme context
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Theme tokens accessor for JavaScript usage (e.g., charts)
export const getThemeTokens = () => {
  const root = document.documentElement;
  const computedStyle = getComputedStyle(root);
  
  return {
    colors: {
      gold: {
        50: computedStyle.getPropertyValue('--ka-gold-50').trim(),
        100: computedStyle.getPropertyValue('--ka-gold-100').trim(),
        200: computedStyle.getPropertyValue('--ka-gold-200').trim(),
        300: computedStyle.getPropertyValue('--ka-gold-300').trim(),
        400: computedStyle.getPropertyValue('--ka-gold-400').trim(),
        500: computedStyle.getPropertyValue('--ka-gold-500').trim(),
        600: computedStyle.getPropertyValue('--ka-gold-600').trim(),
        700: computedStyle.getPropertyValue('--ka-gold-700').trim(),
        800: computedStyle.getPropertyValue('--ka-gold-800').trim(),
        900: computedStyle.getPropertyValue('--ka-gold-900').trim(),
      },
      ivory: {
        100: computedStyle.getPropertyValue('--ka-ivory-100').trim(),
        200: computedStyle.getPropertyValue('--ka-ivory-200').trim(),
        300: computedStyle.getPropertyValue('--ka-ivory-300').trim(),
        400: computedStyle.getPropertyValue('--ka-ivory-400').trim(),
      },
      stone: {
        100: computedStyle.getPropertyValue('--ka-stone-100').trim(),
        200: computedStyle.getPropertyValue('--ka-stone-200').trim(),
        300: computedStyle.getPropertyValue('--ka-stone-300').trim(),
      },
      ink: {
        50: computedStyle.getPropertyValue('--ka-ink-50').trim(),
        100: computedStyle.getPropertyValue('--ka-ink-100').trim(),
        200: computedStyle.getPropertyValue('--ka-ink-200').trim(),
        900: computedStyle.getPropertyValue('--ka-ink-900').trim(),
      },
      text: computedStyle.getPropertyValue('--ka-text').trim(),
      text2: computedStyle.getPropertyValue('--ka-text-2').trim(),
      textMuted: computedStyle.getPropertyValue('--ka-text-muted').trim(),
      brand: computedStyle.getPropertyValue('--ka-brand').trim(),
      accent: computedStyle.getPropertyValue('--ka-accent').trim(),
      bg: computedStyle.getPropertyValue('--ka-bg').trim(),
      panel: computedStyle.getPropertyValue('--ka-panel').trim(),
      muted: computedStyle.getPropertyValue('--ka-muted').trim(),
    },
    gradients: {
      gold: computedStyle.getPropertyValue('--ka-grad-gold').trim(),
      goldSubtle: computedStyle.getPropertyValue('--ka-grad-gold-subtle').trim(),
      goldBorder: computedStyle.getPropertyValue('--ka-grad-gold-border').trim(),
    },
    shadows: {
      soft: computedStyle.getPropertyValue('--ka-shadow-soft').trim(),
      elevated: computedStyle.getPropertyValue('--ka-shadow-elevated').trim(),
      modal: computedStyle.getPropertyValue('--ka-shadow-modal').trim(),
    },
    radius: {
      xs: computedStyle.getPropertyValue('--ka-radius-xs').trim(),
      sm: computedStyle.getPropertyValue('--ka-radius-sm').trim(),
      md: computedStyle.getPropertyValue('--ka-radius-md').trim(),
      lg: computedStyle.getPropertyValue('--ka-radius-lg').trim(),
      xl: computedStyle.getPropertyValue('--ka-radius-xl').trim(),
      pill: computedStyle.getPropertyValue('--ka-radius-pill').trim(),
    },
    space: {
      0: computedStyle.getPropertyValue('--ka-space-0').trim(),
      1: computedStyle.getPropertyValue('--ka-space-1').trim(),
      2: computedStyle.getPropertyValue('--ka-space-2').trim(),
      3: computedStyle.getPropertyValue('--ka-space-3').trim(),
      4: computedStyle.getPropertyValue('--ka-space-4').trim(),
      5: computedStyle.getPropertyValue('--ka-space-5').trim(),
      6: computedStyle.getPropertyValue('--ka-space-6').trim(),
      8: computedStyle.getPropertyValue('--ka-space-8').trim(),
      10: computedStyle.getPropertyValue('--ka-space-10').trim(),
      12: computedStyle.getPropertyValue('--ka-space-12').trim(),
      16: computedStyle.getPropertyValue('--ka-space-16').trim(),
    },
    fonts: {
      heading: computedStyle.getPropertyValue('--ka-font-heading').trim(),
      body: computedStyle.getPropertyValue('--ka-font-body').trim(),
    },
    fontSize: {
      xs: computedStyle.getPropertyValue('--ka-fs-xs').trim(),
      sm: computedStyle.getPropertyValue('--ka-fs-sm').trim(),
      md: computedStyle.getPropertyValue('--ka-fs-md').trim(),
      lg: computedStyle.getPropertyValue('--ka-fs-lg').trim(),
      xl: computedStyle.getPropertyValue('--ka-fs-xl').trim(),
      '2xl': computedStyle.getPropertyValue('--ka-fs-2xl').trim(),
      '3xl': computedStyle.getPropertyValue('--ka-fs-3xl').trim(),
      '4xl': computedStyle.getPropertyValue('--ka-fs-4xl').trim(),
      '5xl': computedStyle.getPropertyValue('--ka-fs-5xl').trim(),
    },
    duration: {
      fast: computedStyle.getPropertyValue('--ka-dur-fast').trim(),
      default: computedStyle.getPropertyValue('--ka-dur').trim(),
      slow: computedStyle.getPropertyValue('--ka-dur-slow').trim(),
    },
    easing: {
      default: computedStyle.getPropertyValue('--ka-ease').trim(),
      out: computedStyle.getPropertyValue('--ka-ease-out').trim(),
    }
  };
};

// Utility function to create theme-aware styles for charts and dynamic content
export const createChartTheme = () => {
  const tokens = getThemeTokens();
  
  return {
    background: tokens.colors.bg,
    textColor: tokens.colors.text,
    grid: {
      line: {
        stroke: tokens.colors.stone[200],
      },
    },
    axis: {
      domain: {
        line: {
          stroke: tokens.colors.stone[300],
          strokeWidth: 1,
        },
      },
      legend: {
        text: {
          fontSize: parseInt(tokens.fontSize.sm),
          fill: tokens.colors.textMuted,
        },
      },
      ticks: {
        line: {
          stroke: tokens.colors.stone[300],
          strokeWidth: 1,
        },
        text: {
          fontSize: parseInt(tokens.fontSize.xs),
          fill: tokens.colors.textMuted,
        },
      },
    },
    legends: {
      text: {
        fontSize: parseInt(tokens.fontSize.sm),
        fill: tokens.colors.text,
      },
    },
    tooltip: {
      container: {
        background: tokens.colors.panel,
        color: tokens.colors.text,
        fontSize: tokens.fontSize.sm,
        borderRadius: tokens.radius.sm,
        boxShadow: tokens.shadows.elevated,
      },
    },
  };
};

// Component class name utilities
export const cn = (...classes) => {
  return classes.filter(Boolean).join(' ');
};

// Theme-aware component variants
export const buttonVariants = {
  primary: 'ka-button',
  outline: 'ka-button ka-outline',
  ghost: 'ka-button bg-transparent border-0 text-ka-brand hover:bg-ka-ivory-200',
};

export const cardVariants = {
  default: 'ka-card',
  elevated: 'ka-card ka-card--elevated',
  flat: 'ka-card border-0 shadow-none',
};

// Responsive utilities
export const breakpoints = {
  sm: '(min-width: 480px)',
  md: '(min-width: 768px)',
  lg: '(min-width: 1024px)',
  xl: '(min-width: 1280px)',
};

export const useMediaQuery = (query) => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }
    const listener = () => setMatches(media.matches);
    media.addListener(listener);
    return () => media.removeListener(listener);
  }, [matches, query]);

  return matches;
};