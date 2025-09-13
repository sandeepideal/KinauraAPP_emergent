// Environment Configuration Validator for KinAura Mobile App
// Ensures all required environment variables are present and valid

class EnvironmentValidator {
  constructor() {
    this.requiredVars = [
      'REACT_APP_BACKEND_URL',
      'REACT_APP_FIREBASE_API_KEY',
      'REACT_APP_FIREBASE_PROJECT_ID',
      'REACT_APP_FIREBASE_APP_ID'
    ];
    
    this.productionRequiredVars = [
      ...this.requiredVars,
      'REACT_APP_FIREBASE_MESSAGING_SENDER_ID',
      'REACT_APP_FIREBASE_VAPID_KEY',
      'REACT_APP_APPLE_CLIENT_ID',
      'REACT_APP_FACEBOOK_APP_ID'
    ];
    
    this.environment = process.env.REACT_APP_ENVIRONMENT || process.env.NODE_ENV || 'development';
    this.isProduction = this.environment === 'production';
  }

  validate() {
    console.log(`🔧 Validating environment: ${this.environment}`);
    
    const varsToCheck = this.isProduction ? this.productionRequiredVars : this.requiredVars;
    const missing = [];
    const invalid = [];

    // Check for missing variables
    for (const varName of varsToCheck) {
      const value = process.env[varName];
      
      if (!value) {
        missing.push(varName);
      } else if (this.isProduction && value.includes('your-') || value.includes('change_this')) {
        invalid.push(`${varName}: Contains placeholder value`);
      }
    }

    // Additional validation checks
    this.validateSpecificVars(invalid);

    // Report results
    if (missing.length > 0) {
      console.error('❌ Missing required environment variables:');
      missing.forEach(varName => console.error(`   - ${varName}`));
    }

    if (invalid.length > 0) {
      console.error('❌ Invalid environment variable values:');
      invalid.forEach(issue => console.error(`   - ${issue}`));
    }

    const isValid = missing.length === 0 && invalid.length === 0;

    if (isValid) {
      console.log('✅ Environment validation passed');
      this.logEnvironmentInfo();
    } else {
      const errorMessage = `Environment validation failed: ${missing.length} missing, ${invalid.length} invalid`;
      console.error(`❌ ${errorMessage}`);
      
      if (this.isProduction) {
        throw new Error(`Production build aborted: ${errorMessage}`);
      }
    }

    return isValid;
  }

  validateSpecificVars(invalid) {
    // Validate backend URL format
    const backendUrl = process.env.REACT_APP_BACKEND_URL;
    if (backendUrl) {
      if (this.isProduction && !backendUrl.startsWith('https://')) {
        invalid.push('REACT_APP_BACKEND_URL: Must use HTTPS in production');
      }
      if (backendUrl.endsWith('/')) {
        invalid.push('REACT_APP_BACKEND_URL: Should not end with trailing slash');
      }
    }

    // Validate Firebase project ID format
    const firebaseProjectId = process.env.REACT_APP_FIREBASE_PROJECT_ID;
    if (firebaseProjectId && (firebaseProjectId.includes(' ') || firebaseProjectId.includes('_'))) {
      invalid.push('REACT_APP_FIREBASE_PROJECT_ID: Invalid format (no spaces or underscores)');
    }

    // Validate Apple client ID format
    const appleClientId = process.env.REACT_APP_APPLE_CLIENT_ID;
    if (appleClientId && !appleClientId.startsWith('com.kinauramed.kinaura')) {
      invalid.push('REACT_APP_APPLE_CLIENT_ID: Must match bundle identifier');
    }
  }

  logEnvironmentInfo() {
    console.log('📱 Environment Configuration:');
    console.log(`   Backend URL: ${process.env.REACT_APP_BACKEND_URL}`);
    console.log(`   Firebase Project: ${process.env.REACT_APP_FIREBASE_PROJECT_ID}`);
    console.log(`   Environment: ${this.environment}`);
    console.log(`   Apple Client ID: ${process.env.REACT_APP_APPLE_CLIENT_ID}`);
    console.log(`   WebSocket: ${process.env.REACT_APP_ENABLE_WEBSOCKET ? 'Enabled' : 'Disabled'}`);
  }

  getFirebaseConfig() {
    this.validate();
    
    return {
      apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
      authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
      projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
      storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
      messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
      appId: process.env.REACT_APP_FIREBASE_APP_ID,
      vapidKey: process.env.REACT_APP_FIREBASE_VAPID_KEY
    };
  }

  getApiConfig() {
    this.validate();
    
    return {
      baseURL: process.env.REACT_APP_BACKEND_URL,
      timeout: this.isProduction ? 30000 : 10000,
      enableWebSocket: process.env.REACT_APP_ENABLE_WEBSOCKET === 'true',
      wsURL: process.env.REACT_APP_WS_URL || process.env.REACT_APP_BACKEND_URL?.replace('http', 'ws'),
    };
  }
}

// Global environment validator instance
const envValidator = new EnvironmentValidator();

// Validate environment on module load
if (typeof window !== 'undefined') {
  // Only run in browser environment
  envValidator.validate();
}

export default envValidator;
export { EnvironmentValidator };