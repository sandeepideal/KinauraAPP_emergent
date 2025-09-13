# Google Calendar & Push Notifications Integration Setup Guide

## Overview
Your KinAura application now has fully integrated Google Calendar and Push Notifications functionality. This guide will walk you through obtaining the required API credentials to enable these features.

## Current Status
- ✅ **Backend Integration**: Fully implemented and tested
- ✅ **Frontend Integration**: Implemented with Firebase SDK
- ✅ **Error Handling**: Graceful degradation when credentials are missing
- ✅ **Appointment Booking**: Working with automatic slot generation
- ⏳ **API Credentials**: Need to be configured for full functionality

## Required Credentials

### 1. Google Calendar Integration

#### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" or select an existing project
3. Name your project (e.g., "KinAura Calendar Integration")
4. Note your **Project ID** for later use

#### Step 2: Enable Google Calendar API
1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Calendar API"
3. Click on it and press "Enable"

#### Step 3: Create Service Account
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Name: "KinAura Calendar Service"
4. Description: "Service account for KinAura appointment calendar integration"
5. Click "Create and Continue"
6. For roles, add: "Project > Editor" (or more restrictive calendar-specific roles)
7. Click "Continue" then "Done"

#### Step 4: Generate Service Account Key
1. Click on your newly created service account
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Choose "JSON" format
5. **Download and save this file securely**
6. **Replace** `/app/backend/google-service-account.json` with your downloaded file

### 2. Firebase Push Notifications

#### Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Name: "KinAura Notifications" (or use existing Google Cloud project)
4. Enable Google Analytics if desired
5. Click "Create project"

#### Step 2: Add Web App to Firebase
1. In Firebase project overview, click the web icon `</>`
2. App nickname: "KinAura Web App"
3. **Copy the Firebase configuration** - you'll need this for frontend
4. Click "Register app"

#### Step 3: Enable Cloud Messaging
1. In Firebase Console, go to "Project Settings" (gear icon)
2. Click on "Cloud Messaging" tab
3. Under "Web configuration", click "Generate key pair"
4. **Copy the VAPID key** - you'll need this

#### Step 4: Generate Service Account Key
1. In Firebase Console, go to "Project Settings" > "Service accounts"
2. Click "Generate new private key"
3. **Download and save this JSON file securely**
4. **Replace** `/app/backend/firebase-service-account.json` with your downloaded file

## Configuration Steps

### Backend Configuration (Required)

1. **Replace placeholder service account files:**
   ```bash
   # Replace these files with your actual credentials:
   /app/backend/google-service-account.json
   /app/backend/firebase-service-account.json
   ```

2. **Update backend environment variables in `/app/backend/.env`:**
   ```env
   # Keep existing variables and update these paths if needed
   GOOGLE_SERVICE_ACCOUNT_PATH=/app/backend/google-service-account.json
   FIREBASE_SERVICE_ACCOUNT_PATH=/app/backend/firebase-service-account.json
   ```

### Frontend Configuration (Required)

1. **Update frontend environment variables in `/app/frontend/.env`:**
   ```env
   # Replace placeholder values with your Firebase config
   REACT_APP_FIREBASE_API_KEY=your_actual_api_key
   REACT_APP_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   REACT_APP_FIREBASE_PROJECT_ID=your-project-id
   REACT_APP_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
   REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   REACT_APP_FIREBASE_APP_ID=your_app_id
   REACT_APP_FIREBASE_VAPID_KEY=your_vapid_key
   ```

2. **Update service worker Firebase config in `/app/frontend/public/firebase-messaging-sw.js`:**
   ```javascript
   // Replace the firebaseConfig object with your actual config
   const firebaseConfig = {
     apiKey: "your_actual_api_key",
     authDomain: "your-project.firebaseapp.com",
     projectId: "your-project-id",
     storageBucket: "your-project.appspot.com",
     messagingSenderId: "your_sender_id",
     appId: "your_app_id"
   };
   ```

## Restart Services

After updating all credentials:
```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

## Testing the Integration

### 1. Test Push Notifications
1. Log into your KinAura app as a patient
2. Grant notification permissions when prompted
3. Book an appointment
4. You should receive:
   - Immediate confirmation notification
   - Scheduled reminder notifications (24h and 2h before)

### 2. Test Google Calendar Integration
1. Complete an appointment booking and payment
2. Check the configured Google Calendar
3. You should see the appointment event created automatically
4. The patient should receive calendar invitations

### 3. Admin Testing
Use these admin endpoints to test manually:
- `POST /api/admin/calendar/create-event` - Create calendar events
- `POST /api/admin/generate-test-availability` - Generate appointment slots
- `POST /api/patient/notifications/send` - Send test notifications

## Security Notes

⚠️ **Important Security Considerations:**

1. **Service Account Files**: Never commit these to version control
2. **API Keys**: Keep Firebase keys secure and consider domain restrictions
3. **Access Control**: Review Firebase security rules
4. **Monitoring**: Monitor API usage and set up billing alerts

## Features Enabled

Once configured, your patients will enjoy:

### 🗓️ **Google Calendar Integration**
- Automatic calendar event creation upon appointment confirmation
- Calendar invitations sent to patients
- Event updates for appointment changes
- Automatic event deletion for cancellations

### 🔔 **Push Notifications**
- Instant appointment confirmation
- 24-hour reminder notifications
- 2-hour reminder notifications  
- Custom scheduling for different appointment types
- Support for web, iOS, and Android platforms

### 🔄 **Graceful Degradation**
- System continues working even if external services are unavailable
- Clear error messages for administrators
- Automatic fallback options

## Troubleshooting

### Common Issues:

1. **"Google Calendar service not available"**
   - Check service account file path and permissions
   - Verify Calendar API is enabled in Google Cloud

2. **"Firebase service not available"**
   - Check service account file path
   - Verify project ID matches in configuration

3. **Push notifications not working**
   - Verify VAPID key is correct
   - Check browser permissions
   - Ensure HTTPS is enabled for production

4. **No appointment slots available**
   - Use `/api/admin/generate-test-availability` endpoint
   - Check service availability settings in admin panel

## Support

If you encounter issues:
1. Check service logs: `tail -f /var/log/supervisor/backend.*.log`
2. Verify all credentials are properly formatted JSON
3. Test individual endpoints using the admin panel
4. Contact support with specific error messages

---

**Congratulations!** Your KinAura application now has enterprise-grade appointment management with calendar and notification integration. 🎉