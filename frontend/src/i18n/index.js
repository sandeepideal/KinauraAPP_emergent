import enTranslations from './en.json';
import itTranslations from './it.json';

const translations = {
  en: enTranslations,
  it: itTranslations
};

/**
 * Simple translation function
 * @param {string} key - Translation key in dot notation (e.g., 'common.loading')
 * @param {string} language - Language code ('en' or 'it')
 * @param {object} interpolations - Object with values to interpolate
 * @returns {string} Translated string
 */
export const t = (key, language = 'en', interpolations = {}) => {
  const keys = key.split('.');
  let value = translations[language];
  
  // Navigate through nested object
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      // Fallback to English if key not found in current language
      value = translations.en;
      for (const fallbackKey of keys) {
        if (value && typeof value === 'object' && fallbackKey in value) {
          value = value[fallbackKey];
        } else {
          return key; // Return key if not found in fallback either
        }
      }
      break;
    }
  }
  
  // If value is not a string, return the key
  if (typeof value !== 'string') {
    return key;
  }
  
  // Handle interpolations
  let result = value;
  Object.keys(interpolations).forEach(interpolationKey => {
    const placeholder = `{{${interpolationKey}}}`;
    result = result.replace(new RegExp(placeholder, 'g'), interpolations[interpolationKey]);
  });
  
  return result;
};

/**
 * Hook-like function to get translation function with current language
 * @param {string} language - Current language
 * @returns {function} Translation function with bound language
 */
export const useTranslation = (language = 'en') => {
  return (key, interpolations = {}) => t(key, language, interpolations);
};

/**
 * Detect browser language and return supported language code
 * @returns {string} Language code ('en' or 'it')
 */
export const detectLanguage = () => {
  const browserLang = navigator.language || navigator.languages?.[0] || 'en';
  const langCode = browserLang.split('-')[0];
  
  // Return 'it' if Italian, otherwise default to 'en'
  return langCode === 'it' ? 'it' : 'en';
};

/**
 * Get available languages
 * @returns {Array} Array of language objects
 */
export const getAvailableLanguages = () => [
  { code: 'en', name: 'English', nativeName: 'English' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano' }
];

export default t;