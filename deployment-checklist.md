# KinAura Mobile Deployment Checklist

## Pre-Deployment Setup
- [ ] Apple Developer Account active ($99/year)
- [ ] Google Play Console account active ($25 one-time)
- [ ] Codemagic account connected to GitHub repository
- [ ] App Store Connect app created with bundle ID: com.kinauramed.kinaura
- [ ] Google Play Console app created with package name: com.kinauramed.kinaura

## Environment Configuration
- [ ] All environment variables set in Codemagic settings
- [ ] iOS code signing configured in Codemagic
- [ ] Android keystore uploaded to Codemagic
- [ ] Team access configured for relevant team members

## Assets & Metadata
- [ ] App icon (1024x1024) created and placed in resources/
- [ ] Splash screen (2732x2732) created and placed in resources/
- [ ] iPhone screenshots (6.5", 5.5", 12.9") created
- [ ] Android screenshots (phone, tablet) created
- [ ] App descriptions written for both stores
- [ ] Keywords and categories selected

## Testing & Quality Assurance
- [ ] App tested on physical iOS device
- [ ] App tested on physical Android device
- [ ] All core features working (booking, chatbot, auth)
- [ ] Content sync functionality verified
- [ ] Push notifications tested
- [ ] Social login tested (Apple, Google, Facebook)

## Build & Distribution
- [ ] iOS development build successful in Codemagic
- [ ] Android development build successful in Codemagic
- [ ] Production builds ready for store submission
- [ ] TestFlight beta testing completed (iOS)
- [ ] Internal testing completed (Android)

## Store Submission
- [ ] iOS app submitted to App Store Connect for review
- [ ] Android AAB uploaded to Play Console for review
- [ ] Privacy policy URL configured
- [ ] Support contact information provided
- [ ] Age rating and content warnings set appropriately

## Post-Launch
- [ ] Monitor app store reviews and ratings
- [ ] Track app analytics and performance
- [ ] Prepare for user feedback and updates
- [ ] Plan content update strategy using sync system

Generated on: Mon Aug 25 13:38:47 UTC 2025
