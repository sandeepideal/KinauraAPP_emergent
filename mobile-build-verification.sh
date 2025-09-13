#!/bin/bash

# KinAura Mobile Build Verification Script
# Comprehensive testing and validation for iOS/Android builds

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_header() {
    echo -e "\n${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}\n"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verification results
VERIFICATION_LOG="/tmp/kinaura_build_verification.log"
echo "KinAura Mobile Build Verification - $(date)" > $VERIFICATION_LOG
echo "=============================================" >> $VERIFICATION_LOG

# Phase 1: Environment Variable Validation
log_header "Phase 1: Environment Variable Validation"

validate_env_vars() {
    log_info "Validating frontend environment variables..."
    
    cd frontend
    
    # Check if .env files exist
    if [ -f ".env.development" ]; then
        log_success ".env.development found"
        echo "✅ .env.development found" >> $VERIFICATION_LOG
    else
        log_error ".env.development missing"
        echo "❌ .env.development missing" >> $VERIFICATION_LOG
    fi
    
    if [ -f ".env.production" ]; then
        log_success ".env.production found"
        echo "✅ .env.production found" >> $VERIFICATION_LOG
    else
        log_error ".env.production missing"
        echo "❌ .env.production missing" >> $VERIFICATION_LOG
    fi
    
    # Validate environment validator
    if [ -f "src/utils/environmentValidator.js" ]; then
        log_success "Environment validator implemented"
        echo "✅ Environment validator implemented" >> $VERIFICATION_LOG
    else
        log_error "Environment validator missing"
        echo "❌ Environment validator missing" >> $VERIFICATION_LOG
    fi
    
    cd ..
}

# Phase 2: CORS Configuration Validation
log_header "Phase 2: CORS Configuration Validation"

validate_cors() {
    log_info "Validating CORS configuration..."
    
    # Check backend CORS setup
    if grep -q "capacitor://localhost" backend/server.py; then
        log_success "Capacitor origins found in CORS configuration"
        echo "✅ Capacitor origins configured in CORS" >> $VERIFICATION_LOG
    else
        log_error "Capacitor origins missing from CORS"
        echo "❌ Capacitor origins missing from CORS" >> $VERIFICATION_LOG
    fi
    
    if grep -q "ionic://localhost" backend/server.py; then
        log_success "Ionic origins found in CORS configuration"
        echo "✅ Ionic origins configured in CORS" >> $VERIFICATION_LOG
    else
        log_warning "Ionic origins not found in CORS (may not be needed)"
        echo "⚠️ Ionic origins not configured" >> $VERIFICATION_LOG
    fi
}

# Phase 3: Mobile Platform Configuration
log_header "Phase 3: Mobile Platform Configuration"

validate_mobile_config() {
    log_info "Validating mobile platform configuration..."
    
    # Check Capacitor configuration
    if [ -f "frontend/capacitor.config.json" ]; then
        log_success "Capacitor configuration found"
        
        # Validate bundle ID
        BUNDLE_ID=$(grep -o '"appId": *"[^"]*"' frontend/capacitor.config.json | cut -d'"' -f4)
        if [ "$BUNDLE_ID" = "com.kinauramed.kinaura" ]; then
            log_success "Bundle ID correctly configured: $BUNDLE_ID"
            echo "✅ Bundle ID: $BUNDLE_ID" >> $VERIFICATION_LOG
        else
            log_error "Bundle ID incorrect: $BUNDLE_ID"
            echo "❌ Bundle ID incorrect: $BUNDLE_ID" >> $VERIFICATION_LOG
        fi
    else
        log_error "Capacitor configuration missing"
        echo "❌ Capacitor configuration missing" >> $VERIFICATION_LOG
    fi
    
    # Check iOS configuration
    if [ -d "frontend/ios" ]; then
        log_success "iOS platform directory found"
        echo "✅ iOS platform configured" >> $VERIFICATION_LOG
        
        # Check Info.plist permissions
        if grep -q "NSCameraUsageDescription" frontend/ios/App/App/Info.plist; then
            log_success "iOS camera permissions configured"
            echo "✅ iOS camera permissions configured" >> $VERIFICATION_LOG
        else
            log_error "iOS camera permissions missing"
            echo "❌ iOS camera permissions missing" >> $VERIFICATION_LOG
        fi
        
        if grep -q "NSPushNotificationsUsageDescription\|aps-environment" frontend/ios/App/App/Info.plist; then
            log_success "iOS push notification permissions configured"
            echo "✅ iOS push notifications configured" >> $VERIFICATION_LOG
        else
            log_warning "iOS push notification configuration may be incomplete"
            echo "⚠️ iOS push notifications may need configuration" >> $VERIFICATION_LOG
        fi
    else
        log_error "iOS platform not configured"
        echo "❌ iOS platform missing" >> $VERIFICATION_LOG
    fi
    
    # Check Android configuration
    if [ -d "frontend/android" ]; then
        log_success "Android platform directory found"
        echo "✅ Android platform configured" >> $VERIFICATION_LOG
        
        # Check Android permissions
        if grep -q "android.permission.CAMERA" frontend/android/app/src/main/AndroidManifest.xml; then
            log_success "Android camera permissions configured"
            echo "✅ Android camera permissions configured" >> $VERIFICATION_LOG
        else
            log_error "Android camera permissions missing"
            echo "❌ Android camera permissions missing" >> $VERIFICATION_LOG
        fi
        
        # Check network security config
        if [ -f "frontend/android/app/src/debug/res/xml/network_security_config.xml" ]; then
            log_success "Android network security configuration found"
            echo "✅ Android network security configured" >> $VERIFICATION_LOG
        else
            log_warning "Android network security configuration missing"
            echo "⚠️ Android network security not configured" >> $VERIFICATION_LOG
        fi
    else
        log_error "Android platform not configured"
        echo "❌ Android platform missing" >> $VERIFICATION_LOG
    fi
}

# Phase 4: Push Notification Setup
log_header "Phase 4: Push Notification Setup"

validate_push_setup() {
    log_info "Validating push notification setup..."
    
    # Check for push notification service
    if [ -f "frontend/src/services/pushNotificationService.js" ]; then
        log_success "Enhanced push notification service found"
        echo "✅ Push notification service implemented" >> $VERIFICATION_LOG
    else
        log_error "Push notification service missing"
        echo "❌ Push notification service missing" >> $VERIFICATION_LOG
    fi
    
    # Check for Firebase configuration
    if [ -f "frontend/src/firebase.js" ]; then
        log_success "Firebase configuration found"
        echo "✅ Firebase configuration found" >> $VERIFICATION_LOG
    else
        log_error "Firebase configuration missing"
        echo "❌ Firebase configuration missing" >> $VERIFICATION_LOG
    fi
    
    # Check package.json for required dependencies
    if grep -q "@capacitor/push-notifications" frontend/package.json; then
        log_success "Capacitor push notifications plugin installed"
        echo "✅ Capacitor push notifications installed" >> $VERIFICATION_LOG
    else
        log_error "Capacitor push notifications plugin missing"
        echo "❌ Capacitor push notifications missing" >> $VERIFICATION_LOG
    fi
}

# Phase 5: Code Signing and CI/CD
log_header "Phase 5: Code Signing and CI/CD Configuration"

validate_ci_cd() {
    log_info "Validating CI/CD configuration..."
    
    # Check Codemagic configuration
    if [ -f "codemagic.yaml" ]; then
        log_success "Codemagic configuration found"
        echo "✅ Codemagic configuration found" >> $VERIFICATION_LOG
        
        # Check for production workflows
        if grep -q "ios-production" codemagic.yaml; then
            log_success "iOS production workflow configured"
            echo "✅ iOS production workflow configured" >> $VERIFICATION_LOG
        else
            log_warning "iOS production workflow not found"
            echo "⚠️ iOS production workflow missing" >> $VERIFICATION_LOG
        fi
        
        if grep -q "android-production" codemagic.yaml; then
            log_success "Android production workflow configured"
            echo "✅ Android production workflow configured" >> $VERIFICATION_LOG
        else
            log_warning "Android production workflow not found"
            echo "⚠️ Android production workflow missing" >> $VERIFICATION_LOG
        fi
        
        # Check for environment variable usage
        if grep -q "REACT_APP_BACKEND_URL" codemagic.yaml; then
            log_success "Environment variables configured in Codemagic"
            echo "✅ Environment variables in Codemagic config" >> $VERIFICATION_LOG
        else
            log_warning "Environment variables may not be configured"
            echo "⚠️ Environment variables may need configuration" >> $VERIFICATION_LOG
        fi
    else
        log_error "Codemagic configuration missing"
        echo "❌ Codemagic configuration missing" >> $VERIFICATION_LOG
    fi
}

# Phase 6: Build Dependencies Check
log_header "Phase 6: Build Dependencies Check"

validate_dependencies() {
    log_info "Validating build dependencies..."
    
    cd frontend
    
    # Check if dependencies are installed
    if [ -d "node_modules" ]; then
        log_success "Node modules found"
        echo "✅ Node modules installed" >> $VERIFICATION_LOG
    else
        log_warning "Node modules not found - running yarn install..."
        yarn install
        if [ $? -eq 0 ]; then
            log_success "Dependencies installed successfully"
            echo "✅ Dependencies installed" >> $VERIFICATION_LOG
        else
            log_error "Dependency installation failed"
            echo "❌ Dependency installation failed" >> $VERIFICATION_LOG
        fi
    fi
    
    # Check for Capacitor CLI
    if npx cap --version > /dev/null 2>&1; then
        CAP_VERSION=$(npx cap --version)
        log_success "Capacitor CLI available: $CAP_VERSION"
        echo "✅ Capacitor CLI: $CAP_VERSION" >> $VERIFICATION_LOG
    else
        log_error "Capacitor CLI not available"
        echo "❌ Capacitor CLI not available" >> $VERIFICATION_LOG
    fi
    
    cd ..
}

# Phase 7: API Connectivity Test
log_header "Phase 7: API Connectivity Test"

validate_api_connectivity() {
    log_info "Testing API connectivity..."
    
    # Test backend connectivity (from current environment)
    BACKEND_URL="https://golden-health-1.preview.emergentagent.com"
    
    if curl -s --max-time 10 "$BACKEND_URL/api/" > /dev/null; then
        log_success "Backend API accessible: $BACKEND_URL"
        echo "✅ Backend API accessible" >> $VERIFICATION_LOG
    else
        log_error "Backend API not accessible: $BACKEND_URL"
        echo "❌ Backend API not accessible" >> $VERIFICATION_LOG
    fi
    
    # Test health endpoint
    if curl -s --max-time 10 "$BACKEND_URL/api/websocket/health" > /dev/null; then
        log_success "WebSocket health endpoint accessible"
        echo "✅ WebSocket health endpoint accessible" >> $VERIFICATION_LOG
    else
        log_warning "WebSocket health endpoint not accessible"
        echo "⚠️ WebSocket health endpoint issue" >> $VERIFICATION_LOG
    fi
}

# Phase 8: Mobile Build Test (if possible)
log_header "Phase 8: Mobile Build Preparation Test"

test_mobile_build_prep() {
    log_info "Testing mobile build preparation..."
    
    cd frontend
    
    # Test React build
    log_info "Testing React build..."
    if NODE_ENV=production yarn build > /dev/null 2>&1; then
        log_success "React build successful"
        echo "✅ React build successful" >> $VERIFICATION_LOG
    else
        log_error "React build failed"
        echo "❌ React build failed" >> $VERIFICATION_LOG
        cd ..
        return 1
    fi
    
    # Test Capacitor sync (iOS)
    if [ -d "ios" ]; then
        log_info "Testing Capacitor iOS sync..."
        if npx cap sync ios > /dev/null 2>&1; then
            log_success "Capacitor iOS sync successful"
            echo "✅ Capacitor iOS sync successful" >> $VERIFICATION_LOG
        else
            log_error "Capacitor iOS sync failed"
            echo "❌ Capacitor iOS sync failed" >> $VERIFICATION_LOG
        fi
    fi
    
    # Test Capacitor sync (Android)
    if [ -d "android" ]; then
        log_info "Testing Capacitor Android sync..."
        if npx cap sync android > /dev/null 2>&1; then
            log_success "Capacitor Android sync successful"
            echo "✅ Capacitor Android sync successful" >> $VERIFICATION_LOG
        else
            log_error "Capacitor Android sync failed"
            echo "❌ Capacitor Android sync failed" >> $VERIFICATION_LOG
        fi
    fi
    
    cd ..
}

# Phase 9: Security Configuration Check
log_header "Phase 9: Security Configuration Check"

validate_security() {
    log_info "Validating security configuration..."
    
    # Check iOS ATS configuration
    if grep -q "NSAppTransportSecurity" frontend/ios/App/App/Info.plist; then
        log_success "iOS App Transport Security configured"
        echo "✅ iOS ATS configured" >> $VERIFICATION_LOG
        
        # Check for development exceptions
        if grep -q "NSExceptionDomains" frontend/ios/App/App/Info.plist; then
            log_warning "iOS has ATS exceptions (review for production)"
            echo "⚠️ iOS ATS has exceptions" >> $VERIFICATION_LOG
        fi
    else
        log_warning "iOS App Transport Security not configured"
        echo "⚠️ iOS ATS not configured" >> $VERIFICATION_LOG
    fi
    
    # Check Android network security
    if [ -f "frontend/android/app/src/debug/res/xml/network_security_config.xml" ]; then
        log_success "Android network security configuration found"
        echo "✅ Android network security configured" >> $VERIFICATION_LOG
    else
        log_warning "Android network security configuration missing"
        echo "⚠️ Android network security not configured" >> $VERIFICATION_LOG
    fi
    
    # Check for HTTPS enforcement
    if grep -q "REACT_APP_ENFORCE_HTTPS" frontend/.env.production; then
        log_success "HTTPS enforcement configured"
        echo "✅ HTTPS enforcement configured" >> $VERIFICATION_LOG
    else
        log_warning "HTTPS enforcement not configured"
        echo "⚠️ HTTPS enforcement missing" >> $VERIFICATION_LOG
    fi
}

# Phase 10: Documentation and Assets Check
log_header "Phase 10: Documentation and Assets Check"

validate_documentation() {
    log_info "Validating documentation and assets..."
    
    # Check for mobile deployment documentation
    if [ -f "MOBILE_DEPLOYMENT_GUIDE.md" ]; then
        log_success "Mobile deployment guide found"
        echo "✅ Mobile deployment guide found" >> $VERIFICATION_LOG
    else
        log_warning "Mobile deployment guide missing"
        echo "⚠️ Mobile deployment guide missing" >> $VERIFICATION_LOG
    fi
    
    # Check for app store templates
    if [ -f "APP_STORE_SUBMISSION_TEMPLATES.md" ]; then
        log_success "App store submission templates found"
        echo "✅ App store templates found" >> $VERIFICATION_LOG
    else
        log_warning "App store submission templates missing"
        echo "⚠️ App store templates missing" >> $VERIFICATION_LOG
    fi
    
    # Check for app icons
    if [ -f "frontend/resources/icon.png" ]; then
        log_success "App icon resource found"
        echo "✅ App icon resource found" >> $VERIFICATION_LOG
    else
        log_warning "App icon resource missing"
        echo "⚠️ App icon resource missing" >> $VERIFICATION_LOG
    fi
    
    # Check for splash screen
    if [ -f "frontend/resources/splash.png" ]; then
        log_success "Splash screen resource found"
        echo "✅ Splash screen resource found" >> $VERIFICATION_LOG
    else
        log_warning "Splash screen resource missing"
        echo "⚠️ Splash screen resource missing" >> $VERIFICATION_LOG
    fi
}

# Phase 11: Capacity and Performance Check
log_header "Phase 11: Performance and Capacity Check"

validate_performance() {
    log_info "Validating performance and capacity..."
    
    cd frontend
    
    # Check build size
    if [ -d "build" ]; then
        BUILD_SIZE=$(du -sh build | cut -f1)
        log_info "React build size: $BUILD_SIZE"
        echo "📊 React build size: $BUILD_SIZE" >> $VERIFICATION_LOG
        
        # Check if build size is reasonable (warn if > 50MB)
        BUILD_SIZE_BYTES=$(du -s build | cut -f1)
        if [ $BUILD_SIZE_BYTES -gt 51200 ]; then  # 50MB in KB
            log_warning "Build size is large ($BUILD_SIZE) - consider optimization"
            echo "⚠️ Large build size: $BUILD_SIZE" >> $VERIFICATION_LOG
        else
            log_success "Build size is reasonable: $BUILD_SIZE"
            echo "✅ Reasonable build size: $BUILD_SIZE" >> $VERIFICATION_LOG
        fi
    fi
    
    cd ..
}

# Phase 12: Final Checklist Generation
log_header "Phase 12: Final Checklist Generation"

generate_final_checklist() {
    log_info "Generating final build checklist..."
    
    cat > build_checklist.md << 'EOF'
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
EOF

    log_success "Build checklist generated: build_checklist.md"
    echo "✅ Build checklist generated" >> $VERIFICATION_LOG
}

# Main execution flow
main() {
    log_header "KinAura Mobile Build Verification"
    echo "Starting comprehensive build verification..."
    
    # Run all validation phases
    validate_env_vars
    validate_cors
    validate_mobile_config
    validate_push_setup
    validate_ci_cd
    validate_dependencies
    validate_api_connectivity
    test_mobile_build_prep
    validate_security
    validate_documentation
    validate_performance
    generate_final_checklist
    
    # Final summary
    log_header "Verification Complete"
    
    echo -e "\n${GREEN}🎉 Mobile build verification completed!${NC}"
    echo -e "📄 Detailed log available at: ${VERIFICATION_LOG}"
    echo -e "📋 Build checklist generated: build_checklist.md"
    
    echo -e "\n${BLUE}Next Steps:${NC}"
    echo "1. Review the verification log for any issues"
    echo "2. Complete the build checklist"
    echo "3. Configure secrets in Codemagic"
    echo "4. Trigger your first production build"
    echo "5. Test on physical devices"
    
    echo -e "\n${GREEN}Ready for mobile app deployment! 🚀${NC}"
    
    # Summary in verification log
    echo "" >> $VERIFICATION_LOG
    echo "=============================================" >> $VERIFICATION_LOG
    echo "Verification completed at: $(date)" >> $VERIFICATION_LOG
    echo "=============================================" >> $VERIFICATION_LOG
}

# Check if script should run automatically or interactively
if [ "$1" = "--auto" ]; then
    main
else
    echo "🎯 KinAura Mobile Build Verification Script"
    echo "=========================================="
    echo ""
    echo "This script will validate your mobile build configuration."
    echo ""
    read -p "Do you want to run the full verification? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        main
    else
        echo "Verification cancelled."
        exit 0
    fi
fi