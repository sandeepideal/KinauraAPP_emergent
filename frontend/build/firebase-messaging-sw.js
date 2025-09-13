// Firebase messaging service worker for background push notifications

// Import Firebase scripts
importScripts('https://www.gstatic.com/firebasejs/11.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/11.0.0/firebase-messaging-compat.js');

// Firebase configuration (same as in main app)
const firebaseConfig = {
  apiKey: "placeholder_api_key",
  authDomain: "placeholder.firebaseapp.com", 
  projectId: "placeholder-project",
  storageBucket: "placeholder.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:placeholder"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize Firebase Cloud Messaging
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('Background Message received: ', payload);
  
  const notificationTitle = payload.notification?.title || 'KinAura Notification';
  const notificationOptions = {
    body: payload.notification?.body || 'You have a new notification',
    icon: '/logo192.png',
    badge: '/logo192.png',
    tag: 'kinaura-appointment',
    data: payload.data || {},
    actions: [
      {
        action: 'view',
        title: 'View Details',
        icon: '/logo192.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ],
    requireInteraction: true
  };

  // Show notification
  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click events
self.addEventListener('notificationclick', (event) => {
  console.log('Notification click received:', event);
  
  event.notification.close();
  
  const action = event.action;
  const notificationData = event.notification.data;
  
  if (action === 'dismiss') {
    return;
  }
  
  // Handle notification click - open the app
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then((clientList) => {
      // Check if app is already open
      for (const client of clientList) {
        if (client.url.includes('localhost') || client.url.includes('kinaura')) {
          // Focus existing window and navigate if needed
          if (notificationData.appointment_id) {
            client.postMessage({
              type: 'NOTIFICATION_CLICK',
              data: notificationData
            });
          }
          return client.focus();
        }
      }
      
      // Open new window if none exists
      let targetUrl = '/';
      if (notificationData.appointment_id) {
        targetUrl = `/bookings?highlight=${notificationData.appointment_id}`;
      }
      
      return clients.openWindow(targetUrl);
    })
  );
});

// Handle message events from main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Service worker lifecycle events
self.addEventListener('install', (event) => {
  console.log('Firebase SW installed');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('Firebase SW activated');
  event.waitUntil(self.clients.claim());
});