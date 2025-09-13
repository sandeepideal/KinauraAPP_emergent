// Firebase configuration and initialization with environment validation
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';
import envValidator from './utils/environmentValidator';

// Get validated Firebase configuration
const firebaseConfig = envValidator.getFirebaseConfig();

let messaging = null;
let app = null;

// Initialize Firebase with validation
try {
  if (firebaseConfig.apiKey && firebaseConfig.projectId) {
    app = initializeApp(firebaseConfig);
    console.log('✅ Firebase initialized successfully');
    
    // Initialize messaging for browsers that support it
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator && 'Notification' in window) {
      messaging = getMessaging(app);
      console.log('✅ Firebase messaging initialized');
    }
  } else {
    console.warn('⚠️ Firebase configuration incomplete - push notifications disabled');
  }
} catch (error) {
  console.warn('Firebase initialization failed:', error);
}

class PushNotificationService {
  constructor() {
    this.messaging = messaging;
    this.isSupported = this.checkSupport();
  }

  checkSupport() {
    return (
      typeof window !== 'undefined' &&
      'serviceWorker' in navigator &&
      'Notification' in window &&
      this.messaging !== null
    );
  }

  async requestPermission() {
    if (!this.isSupported) {
      return { granted: false, error: 'Push notifications not supported' };
    }

    try {
      const permission = await Notification.requestPermission();
      return { granted: permission === 'granted', permission };
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return { granted: false, error: error.message };
    }
  }

  async getNotificationToken() {
    if (!this.isSupported) {
      throw new Error('Push notifications not supported');
    }

    try {
      // Register service worker
      const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
      console.log('Service Worker registered:', registration);

      // Get FCM token
      const token = await getToken(this.messaging, {
        vapidKey: firebaseConfig.vapidKey,
        serviceWorkerRegistration: registration
      });

      if (token) {
        console.log('FCM Token generated:', token);
        return token;
      } else {
        throw new Error('No registration token available');
      }
    } catch (error) {
      console.error('Error getting notification token:', error);
      throw error;
    }
  }

  async registerTokenWithBackend(token, platform = 'web') {
    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
    const authToken = localStorage.getItem('token');

    if (!authToken) {
      throw new Error('User not authenticated');
    }

    try {
      // Generate a device ID based on browser info
      const deviceId = this.generateDeviceId();
      
      const response = await fetch(`${BACKEND_URL}/api/patient/notifications/register-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          token: token,
          platform: platform,
          device_id: deviceId,
          device_name: this.getDeviceName()
        })
      });

      if (!response.ok) {
        throw new Error('Failed to register token with backend');
      }

      const result = await response.json();
      console.log('Token registered with backend:', result);
      return result;
    } catch (error) {
      console.error('Error registering token with backend:', error);
      throw error;
    }
  }

  generateDeviceId() {
    // Generate a unique device ID based on browser characteristics
    const userAgent = navigator.userAgent;
    const screenInfo = `${screen.width}x${screen.height}`;
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const language = navigator.language;
    
    const fingerprint = `${userAgent}-${screenInfo}-${timezone}-${language}`;
    
    // Simple hash function to create a shorter ID
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
      const char = fingerprint.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return `web_${Math.abs(hash).toString(36)}`;
  }

  getDeviceName() {
    const userAgent = navigator.userAgent;
    
    if (userAgent.includes('Chrome')) return 'Chrome Browser';
    if (userAgent.includes('Firefox')) return 'Firefox Browser';
    if (userAgent.includes('Safari')) return 'Safari Browser';
    if (userAgent.includes('Edge')) return 'Edge Browser';
    
    return 'Web Browser';
  }

  setupMessageListener(callback) {
    if (!this.isSupported) {
      return;
    }

    // Listen for foreground messages
    onMessage(this.messaging, (payload) => {
      console.log('Foreground message received:', payload);
      
      if (callback) {
        callback(payload);
      } else {
        // Default notification display
        this.showNotification(payload.notification);
      }
    });
  }

  showNotification(notification) {
    if (!notification) return;

    // Show browser notification if permission is granted
    if (Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.body,
        icon: '/logo192.png', // You can customize this
        badge: '/logo192.png',
        tag: 'kinaura-notification',
        requireInteraction: false
      });
    }
  }

  async initializePushNotifications() {
    try {
      // Check if already initialized
      if (localStorage.getItem('push_notifications_initialized') === 'true') {
        return { success: true, message: 'Already initialized' };
      }

      // Request permission
      const permissionResult = await this.requestPermission();
      if (!permissionResult.granted) {
        return { success: false, error: 'Permission denied' };
      }

      // Get token
      const token = await this.getNotificationToken();
      
      // Register with backend
      await this.registerTokenWithBackend(token);
      
      // Set up message listener
      this.setupMessageListener();
      
      // Mark as initialized
      localStorage.setItem('push_notifications_initialized', 'true');
      localStorage.setItem('fcm_token', token);
      
      return { success: true, token };
      
    } catch (error) {
      console.error('Error initializing push notifications:', error);
      return { success: false, error: error.message };
    }
  }
}

// Create singleton instance
const pushNotificationService = new PushNotificationService();

export { pushNotificationService, messaging, app };
export default pushNotificationService;