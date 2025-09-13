# KinAura Mobile App Deployment Guide
## Complete iOS & Android Distribution with Codemagic

---

## 🎯 Overview

This guide provides complete instructions for deploying the KinAura mobile application to iOS App Store and Google Play Store using Codemagic CI/CD.

### 📱 App Information
- **App Name**: KinAura
- **Bundle ID**: com.kinauramed.kinaura
- **Package Name**: com.kinauramed.kinaura
- **Version**: 1.0.0
- **Platforms**: iOS 12+, Android API 24+

---

## 🚀 Quick Start Deployment

### Prerequisites Checklist
- [ ] Apple Developer Account ($99/year)
- [ ] Google Play Console Account ($25 one-time)
- [ ] Codemagic Account (connected to GitHub)
- [ ] App Store Connect access
- [ ] Code signing certificates

---

## 📋 Step-by-Step Setup

### 1. **Codemagic Account Setup**

1. **Sign up at Codemagic**: https://codemagic.io/
2. **Connect GitHub Repository**:
   - Go to Applications → Add Application
   - Connect to your KinAura repository
   - Select the repository containing your app

3. **Configure Environment Variables**:
   ```bash
   # Required Environment Variables in Codemagic
   REACT_APP_BACKEND_URL=https://golden-health-1.preview.emergentagent.com
   REACT_APP_WS_URL=wss://golden-health-1.preview.emergentagent.com
   REACT_APP_ENABLE_WEBSOCKET=true
   REACT_APP_FIREBASE_API_KEY=your-firebase-api-key
   REACT_APP_FIREBASE_PROJECT_ID=your-firebase-project-id
   REACT_APP_APPLE_CLIENT_ID=com.kinauramed.kinaura
   REACT_APP_FACEBOOK_APP_ID=your-facebook-app-id
   ```

### 2. **iOS Setup & Distribution**

#### **A. Apple Developer Account Configuration**

1. **App Store Connect Setup**:
   - Create new app in App Store Connect
   - Set Bundle ID: `com.kinauramed.kinaura`
   - Upload app icon (1024x1024px)
   - Fill app information and description

2. **Code Signing in Codemagic**:
   - Go to Teams → iOS code signing
   - Connect to App Store Connect
   - Automatic code signing is enabled in `codemagic.yaml`

#### **B. iOS Build Configuration**

The enhanced `codemagic.yaml` includes:
- ✅ **Production Environment Variables**
- ✅ **Automatic Code Signing**
- ✅ **App Icon & Splash Screen Generation**
- ✅ **Version Management**
- ✅ **App Store Metadata Generation**
- ✅ **Multiple Distribution Options**

#### **C. iOS Build Process**

1. **Start Build**:
   - Push code to `main` branch or manually trigger
   - Select `ios-workflow` in Codemagic
   - Build takes ~15-20 minutes

2. **Distribution Options**:
   - **Development**: Direct download for testing (current setup)
   - **TestFlight**: Change `distribution_type: ad_hoc` in yaml
   - **App Store**: Change `distribution_type: app_store` in yaml

### 3. **Android Setup & Distribution**

#### **A. Google Play Console Configuration**

1. **Create App in Play Console**:
   - Package name: `com.kinauramed.kinaura`
   - Upload app icon and screenshots
   - Set up app content rating and target audience

2. **Generate Android Keystore**:
   ```bash
   # Create keystore locally then upload to Codemagic
   keytool -genkey -v -keystore kinaura-release-key.keystore \
     -alias kinaura-key-alias -keyalg RSA -keysize 2048 -validity 10000
   ```

3. **Upload Keystore to Codemagic**:
   - Go to Teams → Android code signing
   - Upload keystore file
   - Set `keystore_reference` in environment

#### **B. Android Build Process**

1. **Build Process**:
   - Generates both APK (testing) and AAB (Play Store)
   - Automatic version code based on timestamp
   - ProGuard mapping files for debugging

2. **Distribution**:
   - **APK**: Direct download for sideloading/testing
   - **AAB**: Upload to Google Play Console

### 4. **Development Workflow Setup**

The configuration includes a separate `ios-dev-workflow` for:
- ✅ **Fast development builds** (60 min max)
- ✅ **Triggered on `develop` branch pushes**
- ✅ **Development bundle ID** (`com.kinauramed.kinaura.dev`)
- ✅ **Quick testing and iteration**

---

## 🔧 Advanced Configuration

### **Environment-Specific Builds**

#### **Production Build** (App Store/Play Store):
```yaml
REACT_APP_BACKEND_URL: "https://api.kinauramed.com"  # Your production API
REACT_APP_WS_URL: "wss://api.kinauramed.com"
REACT_APP_ENABLE_WEBSOCKET: "true"
```

#### **Staging Build** (TestFlight/Internal Testing):
```yaml
REACT_APP_BACKEND_URL: "https://staging.kinauramed.com"
REACT_APP_WS_URL: "wss://staging.kinauramed.com"
REACT_APP_ENABLE_WEBSOCKET: "true"
```

### **Custom App Icons & Branding**

1. **App Icon Requirements**:
   - iOS: 1024x1024px PNG (no alpha channel)
   - Android: 512x512px PNG
   - Place in `frontend/resources/icon.png`

2. **Splash Screen**:
   - 2732x2732px PNG recommended
   - Place in `frontend/resources/splash.png`

3. **Generate Assets**:
   ```bash
   cd frontend
   npx capacitor-assets generate
   ```

---

## 📊 Monitoring & Analytics

### **Build Monitoring**

1. **Codemagic Dashboard**:
   - Real-time build logs and status
   - Build history and artifacts
   - Email notifications on success/failure

2. **Slack Integration** (optional):
   ```yaml
   slack:
     channel: '#ios-builds'
     notify:
       success: true
       failure: true
   ```

### **App Performance Tracking**

The app includes:
- ✅ **Firebase Analytics** (configure with your project)
- ✅ **Crash Reporting** (automatic with Firebase)
- ✅ **Real-time Content Sync** (immediate updates without app store)
- ✅ **WebSocket Connection Monitoring**

---

## 🚦 Deployment Checklist

### **Before First Deployment**

- [ ] Set up Apple Developer Account and App Store Connect
- [ ] Create Google Play Console account and app listing
- [ ] Configure Codemagic with repository access
- [ ] Set all required environment variables
- [ ] Upload iOS code signing certificate
- [ ] Generate and upload Android keystore
- [ ] Test build process with development workflow

### **For Each Release**

- [ ] Update version numbers in `package.json`
- [ ] Test app functionality on both platforms
- [ ] Verify environment variables are correct
- [ ] Check app icons and splash screens
- [ ] Review App Store/Play Store metadata
- [ ] Trigger production builds
- [ ] Submit to stores for review

### **Post-Deployment**

- [ ] Monitor build success/failure notifications
- [ ] Test distributed apps on physical devices
- [ ] Submit to App Store Connect for review (iOS)
- [ ] Upload AAB to Play Console (Android)
- [ ] Monitor app store review process
- [ ] Prepare for user feedback and updates

---

## 🔧 Troubleshooting

### **Common iOS Issues**

1. **Code Signing Failures**:
   - Verify bundle identifier matches App Store Connect
   - Ensure certificates are not expired
   - Check team ID in Codemagic settings

2. **Build Failures**:
   - Check Xcode version compatibility
   - Verify CocoaPods installation
   - Review node.js version (using 18.17.0)

### **Common Android Issues**

1. **Keystore Problems**:
   - Ensure keystore is properly uploaded to Codemagic
   - Verify alias and passwords are correct
   - Check keystore validity period

2. **Gradle Build Failures**:
   - Clear Gradle cache in build settings
   - Verify Android SDK and build tools versions
   - Check for dependency conflicts

### **Content Sync Issues**

1. **WebSocket Connection**:
   - Falls back to polling if WebSocket unavailable
   - Verify `REACT_APP_WS_URL` is correct
   - Check backend WebSocket endpoint accessibility

2. **API Connectivity**:
   - Verify `REACT_APP_BACKEND_URL` is accessible
   - Check CORS configuration for mobile apps
   - Test API endpoints from mobile network

---

## 📞 Support & Resources

### **Documentation**
- [Codemagic Documentation](https://docs.codemagic.io/)
- [Capacitor Documentation](https://capacitorjs.com/docs)
- [App Store Connect Help](https://developer.apple.com/support/app-store-connect/)
- [Play Console Help](https://support.google.com/googleplay/android-developer/)

### **Getting Help**
- Codemagic Support: support@codemagic.io
- iOS Developer Support: https://developer.apple.com/support/
- Android Developer Support: https://developer.android.com/support

---

## 🎉 Success Metrics

After successful deployment, you'll have:

✅ **Automated Mobile CI/CD** - Push code, get apps automatically  
✅ **Multi-Platform Distribution** - iOS and Android from single codebase  
✅ **Real-time Content Updates** - Update content without app store submissions  
✅ **Professional App Store Presence** - Polished listings with metadata  
✅ **Development & Production Workflows** - Separate environments for testing  
✅ **Comprehensive Monitoring** - Build status, performance, and error tracking  

Your KinAura mobile applications will be available for download from both app stores with professional distribution and automatic content synchronization!