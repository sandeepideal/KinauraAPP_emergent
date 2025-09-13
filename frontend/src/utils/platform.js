// Platform detection and mobile-specific utilities
import { Capacitor } from '@capacitor/core';
import { StatusBar, Style } from '@capacitor/status-bar';
import { Keyboard } from '@capacitor/keyboard';
import { App } from '@capacitor/app';

export class PlatformUtils {
  // Platform detection
  static isNative() {
    return Capacitor.isNativePlatform();
  }

  static isWeb() {
    return Capacitor.getPlatform() === 'web';
  }

  static isIOS() {
    return Capacitor.getPlatform() === 'ios';
  }

  static isAndroid() {
    return Capacitor.getPlatform() === 'android';
  }

  static isMobile() {
    return this.isIOS() || this.isAndroid();
  }

  // Admin access restrictions - HARD LOCK for mobile
  static isAdminAccessAllowed() {
    // SECURITY: Always return false for mobile platforms (hard lock)
    if (this.isNative() || this.isIOS() || this.isAndroid()) {
      console.log('🔒 Admin access HARD LOCKED: Mobile platform detected');
      return false;
    }
    
    // Only allow admin access on web platform
    console.log('✅ Admin access allowed: Web platform');
    return this.isWeb();
  }

  // Security helper: Should admin components be loaded?
  static shouldLoadAdminComponents() {
    const adminAllowed = this.isAdminAccessAllowed();
    
    if (!adminAllowed) {
      console.warn('🚫 Admin components excluded from bundle on mobile platform');
    }
    
    return adminAllowed;
  }

  // Handle unauthorized admin access attempts
  static handleUnauthorizedAdminAccess() {
    if (!this.isAdminAccessAllowed()) {
      console.warn('🔒 Unauthorized admin access attempt blocked');
      
      if (this.isNative()) {
        // Mobile: Redirect to mobile-specific 403 page
        return '/403-mobile';
      } else {
        // Web: Standard 403 page
        return '/403';
      }
    }
    
    return null;
  }

  // Get authentication storage type for platform
  static getAuthStorageType() {
    if (this.isNative()) {
      return 'secure_storage'; // Use Capacitor Secure Storage
    } else {
      return 'http_cookies'; // Use HttpOnly cookies
    }
  }

  // Mobile-specific configurations
  static async initializeMobile() {
    if (!this.isNative()) return;

    try {
      // Configure status bar
      if (this.isIOS() || this.isAndroid()) {
        await StatusBar.setStyle({ style: Style.Light });
        await StatusBar.setBackgroundColor({ color: '#C8A25A' }); // KinAura gold
      }

      // Configure keyboard behavior
      if (this.isNative()) {
        Keyboard.addListener('keyboardWillShow', () => {
          // Handle keyboard show if needed
        });
        
        Keyboard.addListener('keyboardWillHide', () => {
          // Handle keyboard hide if needed
        });
      }

      // Handle app lifecycle events
      App.addListener('appStateChange', ({ isActive }) => {
        console.log('App state changed. Is active?', isActive);
      });

      App.addListener('appUrlOpen', (event) => {
        console.log('App opened with URL:', event.url);
      });

    } catch (error) {
      console.error('Error initializing mobile platform:', error);
    }
  }

  // Get platform-specific configurations
  static getConfig() {
    return {
      platform: Capacitor.getPlatform(),
      isNative: this.isNative(),
      isWeb: this.isWeb(),
      isMobile: this.isMobile(),
      allowAdmin: this.isAdminAccessAllowed(),
      // Mobile-optimized settings
      touchFriendly: this.isMobile(),
      showMobileMenu: this.isMobile(),
      compactLayout: this.isMobile()
    };
  }

  // Navigation helpers
  static getStartRoute() {
    // Mobile users start with patient dashboard
    if (this.isMobile()) {
      return 'dashboard';
    }
    // Web users can access full functionality
    return 'hero';
  }

  // Feature availability
  static getAvailableFeatures() {
    const baseFeatures = [
      'dashboard',
      'questionnaires', 
      'bookings',
      'longevity-scoreboard',
      'patient-resources',
      'concierge'
    ];

    const adminFeatures = [
      'admin-dashboard',
      'admin-patients',
      'admin-questionnaires',
      'admin-services',
      'admin-notifications'
    ];

    return {
      patient: baseFeatures,
      admin: this.isAdminAccessAllowed() ? adminFeatures : [],
      all: this.isAdminAccessAllowed() ? [...baseFeatures, ...adminFeatures] : baseFeatures
    };
  }

  // UI optimizations
  static getUIConfig() {
    return {
      // Button sizes for touch
      buttonSize: this.isMobile() ? 'large' : 'medium',
      // Spacing for mobile
      spacing: this.isMobile() ? 'comfortable' : 'normal',
      // Font sizes
      fontSize: this.isMobile() ? 'mobile' : 'desktop',
      // Navigation style
      navigation: this.isMobile() ? 'bottom-tabs' : 'sidebar',
      // Form layouts
      formLayout: this.isMobile() ? 'stacked' : 'grid'
    };
  }

  // Haptic feedback (mobile only)
  static async hapticFeedback(type = 'light') {
    if (!this.isNative()) return;

    try {
      const { Haptics, ImpactStyle } = await import('@capacitor/haptics');
      
      const style = {
        light: ImpactStyle.Light,
        medium: ImpactStyle.Medium, 
        heavy: ImpactStyle.Heavy
      }[type] || ImpactStyle.Light;

      await Haptics.impact({ style });
    } catch (error) {
      console.error('Haptic feedback error:', error);
    }
  }

  // Safe area handling
  static getSafeAreaInsets() {
    if (!this.isNative()) {
      return { top: 0, bottom: 0, left: 0, right: 0 };
    }

    // Get safe area from CSS env() variables (set by Capacitor)
    return {
      top: 'env(safe-area-inset-top, 0px)',
      bottom: 'env(safe-area-inset-bottom, 0px)', 
      left: 'env(safe-area-inset-left, 0px)',
      right: 'env(safe-area-inset-right, 0px)'
    };
  }

  // Mobile-optimized alert/confirm
  static async showAlert(title, message, buttons = ['OK']) {
    if (this.isNative()) {
      // Use native alert if available
      try {
        const { Dialog } = await import('@capacitor/dialog');
        return await Dialog.alert({
          title,
          message,
          buttonTitle: buttons[0] || 'OK'
        });
      } catch (error) {
        console.error('Native dialog error:', error);
      }
    }
    
    // Fallback to web alert
    return window.alert(`${title}\n\n${message}`);
  }

  static async showConfirm(title, message, okButton = 'OK', cancelButton = 'Cancel') {
    if (this.isNative()) {
      try {
        const { Dialog } = await import('@capacitor/dialog');
        const result = await Dialog.confirm({
          title,
          message,
          okButtonTitle: okButton,
          cancelButtonTitle: cancelButton
        });
        return result.value;
      } catch (error) {
        console.error('Native dialog error:', error);
      }
    }

    // Fallback to web confirm
    return window.confirm(`${title}\n\n${message}`);
  }
}

// Export singleton instance
export default PlatformUtils;