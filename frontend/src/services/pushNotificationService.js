// Enhanced Push Notification Service for KinAura Mobile App
// Supports both native mobile (Capacitor) and web push notifications

import { Capacitor } from '@capacitor/core';
import { PushNotifications } from '@capacitor/push-notifications';
import { LocalNotifications } from '@capacitor/local-notifications';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';
import envValidator from '../utils/environmentValidator';

class EnhancedPushNotificationService {
  constructor() {
    this.isNative = Capacitor.isNativePlatform();
    this.platform = Capacitor.getPlatform();
    this.messaging = null;
    this.registrationToken = null;
    this.notificationHandlers = [];
    
    console.log(`📱 Push notifications initializing for platform: ${this.platform}`);
  }

  async initialize() {
    try {
      if (this.isNative) {
        await this.initializeNativePush();
      } else {
        await this.initializeWebPush();
      }
      
      console.log('✅ Push notification service initialized successfully');
      return true;
    } catch (error) {
      console.error('❌ Push notification initialization failed:', error);
      return false;
    }
  }

  async initializeNativePush() {
    console.log('🔔 Initializing native push notifications...');
    
    // Request permissions
    const permissionResult = await PushNotifications.requestPermissions();
    
    if (permissionResult.receive === 'granted') {
      console.log('✅ Push notification permissions granted');
      
      // Register for push notifications
      await PushNotifications.register();
      
      // Listen for registration token
      PushNotifications.addListener('registration', (token) => {
        console.log('📱 Native push registration token:', token.value);
        this.registrationToken = token.value;
        this.registerTokenWithBackend(token.value, 'native');
      });
      
      // Listen for registration errors
      PushNotifications.addListener('registrationError', (error) => {
        console.error('❌ Native push registration error:', error);
      });
      
      // Listen for incoming notifications
      PushNotifications.addListener('pushNotificationReceived', (notification) => {
        console.log('📨 Push notification received:', notification);
        this.handleNotificationReceived(notification);
      });
      
      // Listen for notification taps
      PushNotifications.addListener('pushNotificationActionPerformed', (notification) => {
        console.log('👆 Push notification tapped:', notification);
        this.handleNotificationTapped(notification);
      });
      
    } else {
      console.warn('⚠️ Push notification permissions denied');
    }
  }

  async initializeWebPush() {
    console.log('🌐 Initializing web push notifications...');
    
    try {
      // Get Firebase messaging instance
      const { getMessaging } = await import('firebase/messaging');
      const { app } = await import('../firebase');
      
      if (!app) {
        throw new Error('Firebase app not initialized');
      }
      
      this.messaging = getMessaging(app);
      
      // Check for service worker support
      if ('serviceWorker' in navigator && 'Notification' in window) {
        // Request notification permission
        const permission = await Notification.requestPermission();
        
        if (permission === 'granted') {
          console.log('✅ Web push notification permissions granted');
          
          // Get registration token
          const token = await this.getWebPushToken();
          if (token) {
            this.registrationToken = token;
            this.registerTokenWithBackend(token, 'web');
          }
          
          // Listen for foreground messages
          onMessage(this.messaging, (payload) => {
            console.log('📨 Foreground web push received:', payload);
            this.handleNotificationReceived(payload);
          });
          
        } else {
          console.warn('⚠️ Web push notification permissions denied');
        }
      } else {
        console.warn('⚠️ Web push notifications not supported');
      }
      
    } catch (error) {
      console.error('❌ Web push initialization failed:', error);
    }
  }

  async getWebPushToken() {
    try {
      const config = envValidator.getFirebaseConfig();
      
      if (!config.vapidKey) {
        console.warn('⚠️ VAPID key not configured for web push');
        return null;
      }
      
      // Register service worker
      const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
      console.log('✅ Service worker registered');
      
      // Get token
      const token = await getToken(this.messaging, {
        vapidKey: config.vapidKey,
        serviceWorkerRegistration: registration
      });
      
      if (token) {
        console.log('📱 Web push token generated');
        return token;
      } else {
        console.warn('⚠️ No web push token available');
        return null;
      }
      
    } catch (error) {
      console.error('❌ Web push token generation failed:', error);
      return null;
    }
  }

  async registerTokenWithBackend(token, platform) {
    try {
      const apiConfig = envValidator.getApiConfig();
      
      const response = await fetch(`${apiConfig.baseURL}/api/notifications/register-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(localStorage.getItem('token') && {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          })
        },
        body: JSON.stringify({
          token: token,
          platform: platform,
          device_info: {
            platform: this.platform,
            is_native: this.isNative,
            user_agent: navigator.userAgent
          }
        })
      });
      
      if (response.ok) {
        console.log('✅ Push token registered with backend');
      } else {
        console.error('❌ Failed to register push token with backend');
      }
      
    } catch (error) {
      console.error('❌ Token registration error:', error);
    }
  }

  async scheduleLocalNotification(title, body, delay = 0) {
    try {
      if (this.isNative) {
        // Check local notification permissions
        const permissions = await LocalNotifications.checkPermissions();
        
        if (permissions.display !== 'granted') {
          const request = await LocalNotifications.requestPermissions();
          if (request.display !== 'granted') {
            console.warn('⚠️ Local notification permissions denied');
            return false;
          }
        }
        
        // Schedule notification
        await LocalNotifications.schedule({
          notifications: [{
            title: title,
            body: body,
            id: Date.now(),
            schedule: delay > 0 ? { at: new Date(Date.now() + delay * 1000) } : undefined,
            sound: 'default',
            attachments: [],
            actionTypeId: 'KINAURA_ACTION',
            extra: {
              source: 'kinaura_app'
            }
          }]
        });
        
        console.log('✅ Local notification scheduled');
        return true;
        
      } else {
        // Web notification
        if (Notification.permission === 'granted') {
          const notification = new Notification(title, {
            body: body,
            icon: '/logo192.png',
            badge: '/logo192.png',
            tag: 'kinaura-notification',
            requireInteraction: false
          });
          
          setTimeout(() => notification.close(), 5000);
          console.log('✅ Web notification displayed');
          return true;
        }
      }
      
      return false;
      
    } catch (error) {
      console.error('❌ Local notification failed:', error);
      return false;
    }
  }

  handleNotificationReceived(notification) {
    console.log('📨 Processing received notification:', notification);
    
    // Extract notification data
    const notificationData = {
      title: notification.title || notification.notification?.title,
      body: notification.body || notification.notification?.body,
      data: notification.data || {},
      platform: this.platform,
      timestamp: new Date().toISOString()
    };
    
    // Call registered handlers
    this.notificationHandlers.forEach(handler => {
      try {
        handler(notificationData);
      } catch (error) {
        console.error('❌ Notification handler error:', error);
      }
    });
    
    // Show local notification if app is in foreground
    if (document.visibilityState === 'visible' && notificationData.title) {
      this.scheduleLocalNotification(notificationData.title, notificationData.body);
    }
  }

  handleNotificationTapped(notification) {
    console.log('👆 Processing notification tap:', notification);
    
    // Handle deep linking from notification
    const actionData = notification.actionId || notification.notification?.data;
    
    if (actionData) {
      // Dispatch custom event for app navigation
      window.dispatchEvent(new CustomEvent('notificationTapped', {
        detail: {
          action: actionData,
          notification: notification
        }
      }));
    }
  }

  addNotificationHandler(handler) {
    this.notificationHandlers.push(handler);
    
    return () => {
      const index = this.notificationHandlers.indexOf(handler);
      if (index > -1) {
        this.notificationHandlers.splice(index, 1);
      }
    };
  }

  async testNotification(title = 'KinAura Test', body = 'Push notifications are working!') {
    console.log('🧪 Testing push notifications...');
    
    const success = await this.scheduleLocalNotification(title, body);
    
    if (success) {
      console.log('✅ Test notification sent successfully');
    } else {
      console.error('❌ Test notification failed');
    }
    
    return success;
  }

  getRegistrationToken() {
    return this.registrationToken;
  }

  getServiceInfo() {
    return {
      platform: this.platform,
      isNative: this.isNative,
      hasToken: !!this.registrationToken,
      handlersCount: this.notificationHandlers.length
    };
  }
}

// Global push notification service instance
const pushNotificationService = new EnhancedPushNotificationService();

export default pushNotificationService;
export { EnhancedPushNotificationService };