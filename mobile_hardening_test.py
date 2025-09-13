import requests
import sys
import json
import uuid
import time
import websocket
import threading
from datetime import datetime, timedelta

class MobileHardeningTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.ws_url = f"{base_url.replace('https://', 'wss://').replace('http://', 'ws://')}/ws"
        self.token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.mobile_origins = [
            "capacitor://localhost",
            "ionic://localhost", 
            "http://localhost",
            "https://localhost"
        ]
        
    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, origin=None):
        """Run a single API test with mobile origin support"""
        url = f"{self.api_url}{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if origin:
            test_headers['Origin'] = origin
            
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if origin:
            print(f"   Origin: {origin}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)
            elif method == 'OPTIONS':
                response = requests.options(url, headers=test_headers, timeout=10)

            # Handle multiple expected status codes
            if isinstance(expected_status, list):
                success = response.status_code in expected_status
            else:
                success = response.status_code == expected_status
                
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Check CORS headers for mobile origins
                if origin and origin.startswith(('capacitor://', 'ionic://')):
                    cors_headers = {
                        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                        'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                    }
                    print(f"   CORS Headers: {cors_headers}")
                
                # Check security headers
                security_headers = {
                    'X-Content-Type-Options': response.headers.get('X-Content-Type-Options'),
                    'X-Frame-Options': response.headers.get('X-Frame-Options'),
                    'X-XSS-Protection': response.headers.get('X-XSS-Protection'),
                    'Referrer-Policy': response.headers.get('Referrer-Policy')
                }
                if any(security_headers.values()):
                    print(f"   Security Headers: {security_headers}")
                
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    return success, response_data, response.headers
                except:
                    return success, {}, response.headers
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    return False, error_data, response.headers
                except:
                    print(f"   Error: {response.text}")
                    return False, {}, response.headers

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            return False, {}, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}, {}

    def test_cors_preflight_requests(self):
        """Test CORS preflight requests with mobile origins"""
        print("\n🔍 Testing CORS Preflight Requests for Mobile Origins...")
        
        test_endpoints = [
            "/auth/login",
            "/auth/register", 
            "/services",
            "/chat",
            "/patient/appointments/book"
        ]
        
        all_success = True
        for origin in self.mobile_origins:
            print(f"\n   Testing origin: {origin}")
            
            for endpoint in test_endpoints:
                # Test OPTIONS preflight request
                success, response, headers = self.run_test(
                    f"CORS Preflight - {endpoint}",
                    "OPTIONS",
                    endpoint,
                    [200, 204],
                    headers={
                        'Access-Control-Request-Method': 'POST',
                        'Access-Control-Request-Headers': 'Content-Type, Authorization'
                    },
                    origin=origin
                )
                
                if success:
                    # Verify CORS headers are present
                    cors_origin = headers.get('Access-Control-Allow-Origin')
                    cors_methods = headers.get('Access-Control-Allow-Methods')
                    cors_headers = headers.get('Access-Control-Allow-Headers')
                    
                    if cors_origin and cors_methods and cors_headers:
                        print(f"   ✅ CORS headers present for {endpoint}")
                    else:
                        print(f"   ❌ Missing CORS headers for {endpoint}")
                        all_success = False
                else:
                    all_success = False
        
        return all_success

    def test_environment_validation(self):
        """Test backend environment parsing and validation"""
        print("\n🔍 Testing Environment Validation...")
        
        # Test that CORS_ORIGINS is properly parsed from JSON format
        success, response, headers = self.run_test(
            "Environment Health Check",
            "GET",
            "/health",
            200
        )
        
        if success:
            # Check if environment variables are properly loaded
            env_status = response.get('environment', {})
            cors_config = env_status.get('cors_origins_count', 0)
            
            if cors_config > 0:
                print(f"   ✅ CORS origins properly configured ({cors_config} origins)")
            else:
                print(f"   ❌ CORS origins not properly configured")
                return False
        
        # Test database connection
        db_status = response.get('database', {})
        if db_status.get('connected'):
            print(f"   ✅ Database connection validated")
        else:
            print(f"   ❌ Database connection failed")
            return False
            
        return success

    def test_push_notification_infrastructure(self):
        """Test push notification token registration endpoints"""
        print("\n🔍 Testing Push Notification Infrastructure...")
        
        # First, create a test user and get token
        if not self.token:
            self.setup_test_user()
        
        if not self.token:
            print("❌ No user token available for push notification testing")
            return False
        
        # Test token registration for different platforms
        platforms = ["web", "ios", "android"]
        all_success = True
        
        for platform in platforms:
            token_data = {
                "token": f"test_push_token_{platform}_{int(time.time())}",
                "platform": platform,
                "device_id": f"test_device_{platform}_{uuid.uuid4()}",
                "device_name": f"Test {platform.title()} Device"
            }
            
            success, response, headers = self.run_test(
                f"Register Push Token - {platform}",
                "POST",
                "/notifications/register-token",
                200,
                data=token_data
            )
            
            if success:
                print(f"   ✅ Push token registered for {platform}")
            else:
                print(f"   ❌ Failed to register push token for {platform}")
                all_success = False
        
        # Test sending a test notification
        if self.admin_token:
            notification_data = {
                "title": "Mobile Test Notification",
                "body": "Testing mobile push notification infrastructure",
                "user_id": self.get_current_user_id(),
                "notification_type": "general"
            }
            
            success, response, headers = self.run_test(
                "Send Test Push Notification",
                "POST",
                "/admin/notifications/push/send",
                200,
                data=notification_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print(f"   ✅ Test push notification sent successfully")
            else:
                print(f"   ❌ Failed to send test push notification")
                all_success = False
        
        return all_success

    def test_mobile_api_compatibility(self):
        """Test all endpoints work with mobile CORS origins"""
        print("\n🔍 Testing Mobile API Compatibility...")
        
        if not self.token:
            self.setup_test_user()
        
        # Test key endpoints with mobile origins
        test_cases = [
            {"endpoint": "/services", "method": "GET", "expected": 200},
            {"endpoint": "/auth/me", "method": "GET", "expected": 200},
            {"endpoint": "/chat", "method": "POST", "expected": 200, "data": {"message": "Test mobile chat", "session_id": str(uuid.uuid4())}},
            {"endpoint": "/patient/notifications/proactive", "method": "GET", "expected": 200},
            {"endpoint": "/shop/products", "method": "GET", "expected": 200},
            {"endpoint": "/shop/collections", "method": "GET", "expected": 200}
        ]
        
        all_success = True
        for origin in ["capacitor://localhost", "ionic://localhost"]:
            print(f"\n   Testing with origin: {origin}")
            
            for test_case in test_cases:
                success, response, headers = self.run_test(
                    f"Mobile API - {test_case['endpoint']}",
                    test_case["method"],
                    test_case["endpoint"],
                    test_case["expected"],
                    data=test_case.get("data"),
                    origin=origin
                )
                
                if not success:
                    all_success = False
        
        return all_success

    def test_security_headers(self):
        """Test security headers in mobile API responses"""
        print("\n🔍 Testing Security Headers for Mobile Apps...")
        
        test_endpoints = [
            "/services",
            "/auth/me",
            "/shop/products"
        ]
        
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Referrer-Policy"
        ]
        
        all_success = True
        for endpoint in test_endpoints:
            success, response, headers = self.run_test(
                f"Security Headers - {endpoint}",
                "GET",
                endpoint,
                200,
                origin="capacitor://localhost"
            )
            
            if success:
                missing_headers = []
                for header in required_headers:
                    if header not in headers:
                        missing_headers.append(header)
                
                if missing_headers:
                    print(f"   ❌ Missing security headers: {missing_headers}")
                    all_success = False
                else:
                    print(f"   ✅ All security headers present")
                    
                # Check CSP header for HTML responses
                content_type = headers.get('Content-Type', '')
                if 'text/html' in content_type:
                    csp = headers.get('Content-Security-Policy')
                    if csp:
                        print(f"   ✅ CSP header present: {csp[:50]}...")
                    else:
                        print(f"   ❌ CSP header missing for HTML content")
            else:
                all_success = False
        
        return all_success

    def test_performance_mobile_optimization(self):
        """Test API response times for mobile optimization"""
        print("\n🔍 Testing API Performance for Mobile Optimization...")
        
        performance_endpoints = [
            {"endpoint": "/services", "max_time": 2.0},
            {"endpoint": "/shop/products", "max_time": 3.0},
            {"endpoint": "/shop/collections", "max_time": 2.0},
            {"endpoint": "/patient/notifications/proactive", "max_time": 1.5}
        ]
        
        all_success = True
        for test_case in performance_endpoints:
            start_time = time.time()
            
            success, response, headers = self.run_test(
                f"Performance - {test_case['endpoint']}",
                "GET",
                test_case["endpoint"],
                200,
                origin="capacitor://localhost"
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if success:
                if response_time <= test_case["max_time"]:
                    print(f"   ✅ Response time: {response_time:.2f}s (within {test_case['max_time']}s limit)")
                else:
                    print(f"   ❌ Response time: {response_time:.2f}s (exceeds {test_case['max_time']}s limit)")
                    all_success = False
            else:
                all_success = False
        
        return all_success

    def test_websocket_mobile_compatibility(self):
        """Test WebSocket connectivity with mobile origins"""
        print("\n🔍 Testing WebSocket Mobile Compatibility...")
        
        try:
            # Test WebSocket connection with mobile-like parameters
            ws_url = f"{self.ws_url}/content-sync?connection_id=mobile_test_{uuid.uuid4()}&user_id=test_user&subscribe_to=services,products"
            
            print(f"   Connecting to: {ws_url}")
            
            # Create WebSocket connection
            ws = websocket.create_connection(
                ws_url,
                timeout=10,
                header=[
                    "Origin: capacitor://localhost",
                    "User-Agent: KinAura-Mobile/1.0"
                ]
            )
            
            print(f"   ✅ WebSocket connection established")
            
            # Test receiving welcome message
            welcome_msg = ws.recv()
            welcome_data = json.loads(welcome_msg)
            
            if welcome_data.get('type') == 'welcome':
                print(f"   ✅ Welcome message received: {welcome_data}")
                
                # Test subscription management
                subscribe_msg = {
                    "type": "subscribe",
                    "content_types": ["knowledge_base", "products"]
                }
                ws.send(json.dumps(subscribe_msg))
                
                # Wait for subscription confirmation
                time.sleep(1)
                
                # Test heartbeat
                heartbeat_received = False
                for _ in range(5):  # Wait up to 5 seconds for heartbeat
                    try:
                        msg = ws.recv()
                        data = json.loads(msg)
                        if data.get('type') == 'heartbeat':
                            print(f"   ✅ Heartbeat received")
                            heartbeat_received = True
                            break
                    except:
                        time.sleep(1)
                        continue
                
                if not heartbeat_received:
                    print(f"   ❌ No heartbeat received")
                
            else:
                print(f"   ❌ Invalid welcome message: {welcome_data}")
                return False
            
            ws.close()
            print(f"   ✅ WebSocket connection closed successfully")
            return True
            
        except Exception as e:
            print(f"   ❌ WebSocket connection failed: {str(e)}")
            return False

    def test_mobile_authentication_flows(self):
        """Test mobile-compatible authentication flows"""
        print("\n🔍 Testing Mobile Authentication Flows...")
        
        # Test 1: Social login with mobile origin
        mobile_social_data = {
            "provider": "google",
            "access_token": f"mobile_test_token_{int(time.time())}",
            "full_name": "Mobile Test User",
            "email": f"mobile_test_{int(time.time())}@kinaura.com"
        }
        
        success, response, headers = self.run_test(
            "Mobile Social Login",
            "POST",
            "/auth/social-login",
            200,
            data=mobile_social_data,
            origin="capacitor://localhost"
        )
        
        if not success:
            print("   ❌ Mobile social login failed")
            return False
        
        mobile_token = response.get('access_token')
        if mobile_token:
            print(f"   ✅ Mobile authentication token received")
            
            # Test 2: Token validation with mobile origin
            success, user_data, headers = self.run_test(
                "Mobile Token Validation",
                "GET",
                "/auth/me",
                200,
                headers={'Authorization': f'Bearer {mobile_token}'},
                origin="capacitor://localhost"
            )
            
            if success:
                print(f"   ✅ Mobile token validation successful")
                print(f"   User: {user_data.get('full_name')} ({user_data.get('email')})")
            else:
                print(f"   ❌ Mobile token validation failed")
                return False
        else:
            print(f"   ❌ No authentication token received")
            return False
        
        # Test 3: Regular email/password registration with mobile origin
        mobile_register_data = {
            "email": f"mobile_register_{int(time.time())}@kinaura.com",
            "password": "MobileTest123!",
            "full_name": "Mobile Register User",
            "phone": "+1234567890"
        }
        
        success, response, headers = self.run_test(
            "Mobile Email Registration",
            "POST",
            "/auth/register",
            200,
            data=mobile_register_data,
            origin="capacitor://localhost"
        )
        
        if success:
            print(f"   ✅ Mobile email registration successful")
        else:
            print(f"   ❌ Mobile email registration failed")
            return False
        
        return True

    def setup_test_user(self):
        """Setup test user for authenticated requests"""
        user_data = {
            "provider": "google",
            "access_token": f"test_token_{int(time.time())}",
            "full_name": "Mobile Test User",
            "email": f"mobile_test_{int(time.time())}@kinaura.com"
        }
        
        success, response, headers = self.run_test(
            "Setup Test User",
            "POST",
            "/auth/social-login",
            200,
            data=user_data
        )
        
        if success:
            self.token = response.get('access_token')
            print(f"   ✅ Test user setup complete")
        
        # Setup admin user
        admin_data = {
            "provider": "admin",
            "access_token": "admin_token",
            "full_name": "Dr. Mobile Admin",
            "email": f"admin_mobile_{int(time.time())}@kinaura.com"
        }
        
        success, response, headers = self.run_test(
            "Setup Admin User",
            "POST",
            "/auth/social-login",
            200,
            data=admin_data
        )
        
        if success:
            self.admin_token = response.get('access_token')
            print(f"   ✅ Admin user setup complete")

    def get_current_user_id(self):
        """Get current user ID for testing"""
        if not self.token:
            return None
        
        success, response, headers = self.run_test(
            "Get Current User ID",
            "GET",
            "/auth/me",
            200
        )
        
        if success:
            return response.get('id')
        return None

    def run_all_tests(self):
        """Run all mobile hardening tests"""
        print("🚀 Starting Mobile App Hardening Tests...")
        print(f"   Base URL: {self.base_url}")
        print(f"   Testing mobile origins: {self.mobile_origins}")
        
        # Setup test users
        self.setup_test_user()
        
        # Run all test categories
        test_results = {
            "CORS Preflight Requests": self.test_cors_preflight_requests(),
            "Environment Validation": self.test_environment_validation(),
            "Push Notification Infrastructure": self.test_push_notification_infrastructure(),
            "Mobile API Compatibility": self.test_mobile_api_compatibility(),
            "Security Headers": self.test_security_headers(),
            "Performance Mobile Optimization": self.test_performance_mobile_optimization(),
            "WebSocket Mobile Compatibility": self.test_websocket_mobile_compatibility(),
            "Mobile Authentication Flows": self.test_mobile_authentication_flows()
        }
        
        # Print summary
        print("\n" + "="*80)
        print("📊 MOBILE HARDENING TEST RESULTS")
        print("="*80)
        
        passed_categories = 0
        total_categories = len(test_results)
        
        for category, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} - {category}")
            if result:
                passed_categories += 1
        
        print(f"\n📈 Overall Results:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Test Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"   Categories Passed: {passed_categories}/{total_categories}")
        print(f"   Category Success Rate: {(passed_categories/total_categories)*100:.1f}%")
        
        if passed_categories == total_categories:
            print("\n🎉 ALL MOBILE HARDENING TESTS PASSED!")
            print("   The mobile app configuration is production-ready.")
        else:
            print(f"\n⚠️  {total_categories - passed_categories} categories need attention.")
            print("   Review failed tests before mobile deployment.")
        
        return passed_categories == total_categories

if __name__ == "__main__":
    tester = MobileHardeningTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)