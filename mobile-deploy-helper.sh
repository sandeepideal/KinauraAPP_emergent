#!/bin/bash

# KinAura Mobile Deployment Helper Script
# This script helps prepare and validate mobile deployment configuration

set -e

echo "🎯 KinAura Mobile Deployment Helper"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the correct directory
if [ ! -f "codemagic.yaml" ]; then
    print_error "codemagic.yaml not found. Please run this script from the project root directory."
    exit 1
fi

print_status "Validating mobile deployment configuration..."

# Check Capacitor configuration
if [ -f "frontend/capacitor.config.json" ]; then
    print_success "Capacitor configuration found"
    
    # Check app ID
    APP_ID=$(grep -o '"appId": *"[^"]*"' frontend/capacitor.config.json | cut -d'"' -f4)
    if [ "$APP_ID" = "com.kinauramed.kinaura" ]; then
        print_success "App ID configured correctly: $APP_ID"
    else
        print_warning "App ID may need review: $APP_ID"
    fi
else
    print_error "Capacitor configuration not found"
    exit 1
fi

# Check mobile directories
if [ -d "frontend/ios" ] && [ -d "frontend/android" ]; then
    print_success "Mobile platform directories found"
else
    print_warning "Mobile platform directories missing. Run 'npx cap add ios android' to create them."
fi

# Check package.json for mobile scripts
if grep -q "capacitor:" frontend/package.json; then
    print_success "Capacitor scripts found in package.json"
else
    print_warning "Capacitor scripts not found in package.json"
fi

# Check for app icons and resources
if [ -f "frontend/resources/icon.png" ]; then
    print_success "App icon resource found"
else
    print_warning "App icon not found at frontend/resources/icon.png"
fi

if [ -f "frontend/resources/splash.png" ]; then
    print_success "Splash screen resource found"
else
    print_warning "Splash screen not found at frontend/resources/splash.png"
fi

# Environment Variables Check
print_status "Checking environment variables setup..."

ENV_VARS=(
    "REACT_APP_BACKEND_URL"
    "REACT_APP_WS_URL" 
    "REACT_APP_ENABLE_WEBSOCKET"
    "REACT_APP_FIREBASE_API_KEY"
    "REACT_APP_FIREBASE_PROJECT_ID"
    "REACT_APP_APPLE_CLIENT_ID"
    "REACT_APP_FACEBOOK_APP_ID"
)

print_warning "Make sure these environment variables are configured in Codemagic:"
for var in "${ENV_VARS[@]}"; do
    echo "  - $var"
done

# Codemagic YAML Validation
print_status "Validating Codemagic configuration..."

if grep -q "ios-workflow" codemagic.yaml; then
    print_success "iOS workflow configured"
fi

if grep -q "android-workflow" codemagic.yaml; then
    print_success "Android workflow configured"
fi

if grep -q "com.kinauramed.kinaura" codemagic.yaml; then
    print_success "Bundle identifier configured in Codemagic YAML"
fi

# Mobile Build Test Function
test_mobile_build() {
    print_status "Testing local mobile build preparation..."
    
    cd frontend
    
    # Install dependencies
    print_status "Installing dependencies..."
    if npm ci; then
        print_success "Dependencies installed"
    else
        print_error "Failed to install dependencies"
        return 1
    fi
    
    # Build React app
    print_status "Building React app..."
    if npm run build; then
        print_success "React app built successfully"
    else
        print_error "Failed to build React app"
        return 1
    fi
    
    # Sync with Capacitor
    print_status "Syncing with Capacitor..."
    if npx cap sync; then
        print_success "Capacitor sync completed"
    else
        print_error "Capacitor sync failed"
        return 1
    fi
    
    cd ..
    print_success "Local build test completed successfully"
}

# App Store Assets Check
check_app_store_assets() {
    print_status "Checking App Store assets..."
    
    # Check for app icon sizes
    ICON_SIZES=(16 20 29 32 40 50 57 58 60 64 72 76 80 87 100 114 120 128 144 152 167 180 512 1024)
    
    for size in "${ICON_SIZES[@]}"; do
        if [ -f "frontend/public/icon-${size}x${size}.png" ]; then
            print_success "Found icon-${size}x${size}.png"
        fi
    done
    
    # Check for screenshots directory
    if [ -d "app-store-assets" ]; then
        print_success "App store assets directory found"
    else
        print_warning "Consider creating an app-store-assets directory for screenshots and metadata"
    fi
}

# Generate deployment checklist
generate_checklist() {
    print_status "Generating deployment checklist..."
    
    cat << EOF > deployment-checklist.md
# KinAura Mobile Deployment Checklist

## Pre-Deployment Setup
- [ ] Apple Developer Account active (\$99/year)
- [ ] Google Play Console account active (\$25 one-time)
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

Generated on: $(date)
EOF

    print_success "Deployment checklist created: deployment-checklist.md"
}

# Generate environment template
generate_env_template() {
    print_status "Generating environment variables template..."
    
    cat << EOF > .env.mobile.template
# KinAura Mobile App Environment Variables Template
# Copy these to your Codemagic environment variables section

# Backend Configuration
REACT_APP_BACKEND_URL=https://golden-health-1.preview.emergentagent.com
REACT_APP_WS_URL=wss://golden-health-1.preview.emergentagent.com
REACT_APP_ENABLE_WEBSOCKET=true

# Firebase Configuration (replace with your actual values)
REACT_APP_FIREBASE_API_KEY=your-firebase-api-key-here
REACT_APP_FIREBASE_PROJECT_ID=your-firebase-project-id-here
REACT_APP_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=123456789012
REACT_APP_FIREBASE_APP_ID=1:123456789012:web:abcdef123456

# Social Login Configuration
REACT_APP_APPLE_CLIENT_ID=com.kinauramed.kinaura
REACT_APP_FACEBOOK_APP_ID=your-facebook-app-id-here
REACT_APP_GOOGLE_WEB_CLIENT_ID=your-google-client-id-here

# Analytics & Monitoring
REACT_APP_ANALYTICS_ENABLED=true
REACT_APP_CRASHLYTICS_ENABLED=true

# App Configuration
REACT_APP_APP_VERSION=1.0.0
REACT_APP_BUILD_TYPE=production
EOF

    print_success "Environment template created: .env.mobile.template"
}

# Main execution
main() {
    print_status "Starting KinAura mobile deployment validation..."
    
    # Run checks
    print_status "Running configuration checks..."
    
    # Offer to run tests
    echo ""
    read -p "Do you want to run a local build test? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_mobile_build
    fi
    
    # Check app store assets
    check_app_store_assets
    
    # Generate helper files
    generate_checklist
    generate_env_template
    
    echo ""
    print_success "Mobile deployment validation completed!"
    echo ""
    print_status "Next Steps:"
    echo "1. Review the deployment checklist: deployment-checklist.md"
    echo "2. Configure environment variables using: .env.mobile.template"
    echo "3. Set up Codemagic workflows with your repository"
    echo "4. Create app listings in App Store Connect and Play Console"
    echo "5. Upload code signing certificates and keystores"
    echo "6. Trigger your first build in Codemagic!"
    echo ""
    print_success "Happy deploying! 🚀"
}

# Run main function
main "$@"