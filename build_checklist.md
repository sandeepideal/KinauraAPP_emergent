# KinAura Mobile Build Final Checklist

## Environment Configuration
- [ ] Frontend .env.development configured with all required variables
- [ ] Frontend .env.production configured with production values
- [ ] Backend .env.template documented with all required variables
- [ ] Environment validator implemented and working
- [ ] No placeholder values (your-api-key, change_this, etc.) in production

## CORS and Networking
- [ ] Backend CORS includes capacitor://localhost for mobile apps
- [ ] Backend CORS includes ionic://localhost (if needed)
- [ ] Production backend uses HTTPS with valid certificates
- [ ] Mobile apps configured for HTTPS in production

## iOS Configuration
- [ ] Bundle identifier: com.kinauramed.kinaura
- [ ] Info.plist includes all required permissions (camera, photos, location, etc.)
- [ ] Push notification capabilities enabled
- [ ] App Transport Security configured appropriately
- [ ] Apple Developer account and certificates ready
- [ ] Firebase iOS configuration (GoogleService-Info.plist)

## Android Configuration
- [ ] Package name: com.kinauramed.kinaura
- [ ] AndroidManifest.xml includes all required permissions
- [ ] Network security configuration for development/production
- [ ] Google Play Console account ready
- [ ] Android keystore created and secured
- [ ] Firebase Android configuration (google-services.json)

## Push Notifications
- [ ] Firebase project created (production and/or staging)
- [ ] iOS APNs configuration in Firebase
- [ ] Android FCM configuration in Firebase
- [ ] Push notification service implemented in app
- [ ] Test notifications working on both platforms

## Code Signing and CI/CD
- [ ] iOS: Distribution certificate and provisioning profile ready
- [ ] Android: Release keystore created and stored securely
- [ ] Codemagic workflows configured (production and development)
- [ ] Environment variables configured in Codemagic
- [ ] Build triggers set up (tags for production, branches for development)

## Testing and Validation
- [ ] Local React build successful
- [ ] Capacitor sync working for both platforms
- [ ] API connectivity verified from mobile apps
- [ ] Push notifications tested on physical devices
- [ ] All required permissions granted during testing
- [ ] App icons and splash screens configured

## App Store Preparation
- [ ] App Store Connect app created (iOS)
- [ ] Google Play Console app created (Android)
- [ ] App metadata and descriptions ready
- [ ] Screenshots and promotional materials prepared
- [ ] Privacy policy and support URLs configured

## Security Review
- [ ] No hardcoded secrets in code
- [ ] Production uses HTTPS exclusively
- [ ] Proper certificate pinning (if required)
- [ ] ATS exceptions removed for production iOS builds
- [ ] Android cleartext traffic disabled for production

Generated on: $(date)
