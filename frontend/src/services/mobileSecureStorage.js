import { Capacitor } from '@capacitor/core';
import { Preferences } from '@capacitor/preferences';

// Secure Storage Service
class MobileSecureStorage {
  constructor() {
    this.isNative = Capacitor.isNativePlatform();
    this.storage = null;
    this.initialized = false;
  }

  async initialize() {
    if (!this.isNative) {
      // Web fallback - use sessionStorage
      this.storage = {
        get: async (key) => {
          try {
            return sessionStorage.getItem(key);
          } catch (error) {
            console.error('SessionStorage get error:', error);
            return null;
          }
        },
        set: async (key, value) => {
          try {
            sessionStorage.setItem(key, value);
            return true;
          } catch (error) {
            console.error('SessionStorage set error:', error);
            return false;
          }
        },
        remove: async (key) => {
          try {
            sessionStorage.removeItem(key);
            return true;
          } catch (error) {
            console.error('SessionStorage remove error:', error);
            return false;
          }
        },
        clear: async () => {
          try {
            sessionStorage.clear();
            return true;
          } catch (error) {
            console.error('SessionStorage clear error:', error);
            return false;
          }
        }
      };
      this.initialized = true;
      console.log('🔐 Web secure storage initialized (sessionStorage)');
      return true;
    }

    try {
      // Native storage using Capacitor Preferences
      this.storage = {
        get: async (key) => {
          try {
            const { value } = await Preferences.get({ key });
            return value;
          } catch (error) {
            console.error('Preferences get error:', error);
            return null;
          }
        },
        set: async (key, value) => {
          try {
            await Preferences.set({ key, value });
            return true;
          } catch (error) {
            console.error('Preferences set error:', error);
            return false;
          }
        },
        remove: async (key) => {
          try {
            await Preferences.remove({ key });
            return true;
          } catch (error) {
            console.error('Preferences remove error:', error);
            return false;
          }
        },
        clear: async () => {
          try {
            await Preferences.clear();
            return true;
          } catch (error) {
            console.error('Preferences clear error:', error);
            return false;
          }
        }
      };

      this.initialized = true;
      console.log('🔐 Native Preferences storage initialized');
      return true;
    } catch (error) {
      console.warn('⚠️ Preferences not available, falling back to encrypted localStorage');

      // Fallback to encrypted localStorage
      const CryptoJS = await import('crypto-js');
      const ENCRYPTION_KEY = 'kinaura-mobile-encryption-key-2024';

      this.storage = {
        get: async (key) => {
          try {
            const encrypted = localStorage.getItem(`secure_${key}`);
            if (!encrypted) return null;

            const decrypted = CryptoJS.AES.decrypt(encrypted, ENCRYPTION_KEY).toString(CryptoJS.enc.Utf8);
            return decrypted || null;
          } catch (error) {
            console.error('Encrypted localStorage get error:', error);
            return null;
          }
        },
        set: async (key, value) => {
          try {
            const encrypted = CryptoJS.AES.encrypt(value, ENCRYPTION_KEY).toString();
            localStorage.setItem(`secure_${key}`, encrypted);
            return true;
          } catch (error) {
            console.error('Encrypted localStorage set error:', error);
            return false;
          }
        },
        remove: async (key) => {
          try {
            localStorage.removeItem(`secure_${key}`);
            return true;
          } catch (error) {
            console.error('Encrypted localStorage remove error:', error);
            return false;
          }
        },
        clear: async () => {
          try {
            const keys = Object.keys(localStorage).filter(key => key.startsWith('secure_'));
            keys.forEach(key => localStorage.removeItem(key));
            return true;
          } catch (error) {
            console.error('Encrypted localStorage clear error:', error);
            return false;
          }
        }
      };

      this.initialized = true;
      console.log('🔐 Encrypted localStorage fallback initialized');
      return true;
    }
  }

  async storeTokens(accessToken, refreshToken) {
    if (!this.initialized) await this.initialize();

    try {
      await this.storage.set('access_token', accessToken);
      await this.storage.set('refresh_token', refreshToken);
      await this.storage.set('token_timestamp', new Date().toISOString());

      console.log('✅ Tokens stored securely');
      return true;
    } catch (error) {
      console.error('❌ Failed to store tokens:', error);
      return false;
    }
  }

  async getAccessToken() {
    if (!this.initialized) await this.initialize();
    return await this.storage.get('access_token');
  }

  async getRefreshToken() {
    if (!this.initialized) await this.initialize();
    return await this.storage.get('refresh_token');
  }

  async clearTokens() {
    if (!this.initialized) await this.initialize();

    try {
      await this.storage.remove('access_token');
      await this.storage.remove('refresh_token');
      await this.storage.remove('token_timestamp');

      console.log('✅ Tokens cleared from secure storage');
      return true;
    } catch (error) {
      console.error('❌ Failed to clear tokens:', error);
      return false;
    }
  }

  async refreshTokens(baseURL) {
    try {
      const refreshToken = await this.getRefreshToken();
      if (!refreshToken) throw new Error('No refresh token available');

      const response = await fetch(`${baseURL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.access_token && data.refresh_token) {
          await this.storeTokens(data.access_token, data.refresh_token);
          console.log('✅ Tokens refreshed successfully');
          return data.access_token;
        }
      }

      throw new Error('Token refresh failed');
    } catch (error) {
      console.error('❌ Token refresh failed:', error);
      await this.clearTokens();
      return null;
    }
  }

  async makeAuthenticatedRequest(url, options = {}) {
    if (!this.initialized) await this.initialize();

    try {
      let accessToken = await this.getAccessToken();

      let response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (response.status === 401 && accessToken) {
        console.log('🔄 Access token expired, attempting refresh...');

        const baseURL = url.split('/api/')[0];
        const newAccessToken = await this.refreshTokens(baseURL);

        if (newAccessToken) {
          response = await fetch(url, {
            ...options,
            headers: {
              ...options.headers,
              'Authorization': `Bearer ${newAccessToken}`
            }
          });
        }
      }

      return response;
    } catch (error) {
      console.error('❌ Authenticated request failed:', error);
      throw error;
    }
  }

  getStorageInfo() {
    return {
      platform: Capacitor.getPlatform(),
      isNative: this.isNative,
      initialized: this.initialized,
      storageType: this.isNative ? 'native_preferences' : 'web_session'
    };
  }
}

// Global instance
const mobileSecureStorage = new MobileSecureStorage();

export default mobileSecureStorage;
export { MobileSecureStorage };
