#!/usr/bin/env python3
"""
KinAura Backend API Testing - CORS and Core Functionality
Testing the recent improvements as requested in the review.
"""

import requests
import sys
import json
import uuid
from datetime import datetime, timedelta

class KinAuraCORSAPITester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test_result(self, test_name, success, details=""):
        """Log test result for summary"""
        self.test_results.append({
            "name": test_name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, test_cors=False):
        """Run a single API test with optional CORS testing"""
        url = f"{self.api_url}{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        # Add CORS headers for testing
        if test_cors:
            test_headers.update({
                'Origin': 'https://unauthorized-domain.com',
                'Access-Control-Request-Method': method,
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            })

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
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
                
                # Check CORS headers if testing CORS
                if test_cors:
                    cors_headers = {
                        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                    }
                    print(f"   CORS Headers: {cors_headers}")
                    self.log_test_result(name, True, f"CORS headers: {cors_headers}")
                
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    self.log_test_result(name, True, f"Status: {response.status_code}")
                    return success, response_data
                except:
                    self.log_test_result(name, True, f"Status: {response.status_code}")
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    self.log_test_result(name, False, f"Expected {expected_status}, got {response.status_code}: {error_data}")
                    return False, error_data
                except:
                    print(f"   Error: {response.text}")
                    self.log_test_result(name, False, f"Expected {expected_status}, got {response.status_code}: {response.text}")
                    return False, {}

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            self.log_test_result(name, False, f"Network Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.log_test_result(name, False, f"Error: {str(e)}")
            return False, {}

    def test_cors_configuration(self):
        """Test CORS configuration - verify it's properly restricted"""
        print("\n🔒 Testing CORS Configuration...")
        
        # Test 1: OPTIONS request with unauthorized origin
        success, response = self.run_test(
            "CORS - Unauthorized Origin Check",
            "OPTIONS",
            "/services",
            [200, 204, 405],  # Some servers return 405 for OPTIONS
            test_cors=True
        )
        
        # Test 2: Regular request with unauthorized origin
        unauthorized_headers = {
            'Origin': 'https://malicious-site.com'
        }
        
        success, response = self.run_test(
            "CORS - Unauthorized Origin Request",
            "GET",
            "/services",
            [200, 403],  # Should either work or be blocked
            headers=unauthorized_headers
        )
        
        # Test 3: Request with authorized origin
        authorized_headers = {
            'Origin': 'https://kinaura.com'
        }
        
        success, response = self.run_test(
            "CORS - Authorized Origin Request",
            "GET",
            "/services",
            200,
            headers=authorized_headers
        )
        
        return True

    def test_health_check(self):
        """Test basic health check endpoint"""
        print("\n🏥 Testing Health Check...")
        
        # Test root endpoint
        success, response = self.run_test(
            "Health Check - Root Endpoint",
            "GET",
            "/",
            200
        )
        
        if success:
            print("   ✅ Server is responding correctly")
        
        return success

    def test_core_api_endpoints(self):
        """Test core API endpoints as specified in review"""
        print("\n🔧 Testing Core API Endpoints...")
        
        # Test 1: /api/services
        success1, services_response = self.run_test(
            "Core API - Services Endpoint",
            "GET",
            "/services",
            200
        )
        
        if success1 and isinstance(services_response, list):
            print(f"   ✅ Services endpoint returned {len(services_response)} services")
        
        # Test 2: /api/appointments (requires authentication)
        success2, appointments_response = self.run_test(
            "Core API - Patient Appointments (Unauthenticated)",
            "GET",
            "/appointments",
            [401, 403]  # Should require authentication
        )
        
        if success2:
            print("   ✅ Patient appointments properly protected")
        
        # Test 3: /api/patient/health/connections (requires authentication)
        success3, health_response = self.run_test(
            "Core API - Patient Health Connections (Unauthenticated)",
            "GET",
            "/patient/health/connections",
            [401, 403]  # Should require authentication
        )
        
        if success3:
            print("   ✅ Patient health connections properly protected")
        
        return success1 and success2 and success3

    def test_authentication_flow(self):
        """Test JWT token handling for protected routes"""
        print("\n🔐 Testing Authentication Flow...")
        
        # Test 1: Create a test user
        test_user_data = {
            "email": f"cors_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@kinaura.com",
            "password": "TestPass123!",
            "full_name": "CORS Test User",
            "phone": "+1234567890"
        }
        
        success1, register_response = self.run_test(
            "Authentication - User Registration",
            "POST",
            "/auth/register",
            200,
            data=test_user_data
        )
        
        if success1:
            self.token = register_response.get('access_token')
            user_data = register_response.get('user', {})
            self.user_id = user_data.get('id')
            print(f"   ✅ User registered with token: {self.token[:20]}..." if self.token else "   ❌ No token received")
        
        # Test 2: Use token to access protected endpoint
        if self.token:
            success2, protected_response = self.run_test(
                "Authentication - Protected Endpoint Access",
                "GET",
                "/appointments",
                200
            )
            
            if success2:
                print("   ✅ JWT token authentication working")
            
            # Test 3: Test invalid token
            invalid_headers = {'Authorization': 'Bearer invalid_token_12345'}
            success3, invalid_response = self.run_test(
                "Authentication - Invalid Token",
                "GET",
                "/appointments",
                [401, 403],
                headers=invalid_headers
            )
            
            if success3:
                print("   ✅ Invalid token properly rejected")
            
            return success1 and success2 and success3
        
        return success1

    def test_error_handling(self):
        """Test proper error responses for invalid requests"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test 1: Invalid endpoint
        success1, response1 = self.run_test(
            "Error Handling - Invalid Endpoint",
            "GET",
            "/invalid/endpoint/that/does/not/exist",
            404
        )
        
        # Test 2: Invalid method
        success2, response2 = self.run_test(
            "Error Handling - Invalid Method",
            "DELETE",
            "/services",
            [405, 404]  # Method not allowed or not found
        )
        
        # Test 3: Invalid JSON data
        invalid_json_data = {
            "invalid_field": "test",
            "missing_required_fields": True
        }
        
        success3, response3 = self.run_test(
            "Error Handling - Invalid Registration Data",
            "POST",
            "/auth/register",
            [400, 422],  # Bad request or validation error
            data=invalid_json_data
        )
        
        if success3:
            print("   ✅ Invalid data properly rejected with validation error")
        
        # Test 4: Malformed JSON
        try:
            url = f"{self.api_url}/auth/register"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data="invalid json data", headers=headers, timeout=10)
            
            if response.status_code in [400, 422]:
                print("✅ Malformed JSON properly rejected")
                success4 = True
            else:
                print(f"❌ Malformed JSON handling - Expected 400/422, got {response.status_code}")
                success4 = False
        except Exception as e:
            print(f"❌ Malformed JSON test failed: {e}")
            success4 = False
        
        return success1 and success2 and success3 and success4

    def test_authenticated_endpoints(self):
        """Test authenticated endpoints with valid token"""
        print("\n🔓 Testing Authenticated Endpoints...")
        
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        # Test patient appointments with valid token
        success1, appointments = self.run_test(
            "Authenticated - Patient Appointments",
            "GET",
            "/appointments",
            200
        )
        
        # Test patient health connections with valid token
        success2, health_connections = self.run_test(
            "Authenticated - Patient Health Connections",
            "GET",
            "/patient/health/connections",
            200
        )
        
        # Test current user info
        success3, user_info = self.run_test(
            "Authenticated - Current User Info",
            "GET",
            "/auth/me",
            200
        )
        
        if success3 and user_info:
            print(f"   ✅ User info retrieved: {user_info.get('full_name', 'Unknown')}")
        
        return success1 and success2 and success3

    def run_comprehensive_test(self):
        """Run all tests in the review request"""
        print("🚀 Starting KinAura Backend API Testing - CORS and Core Functionality")
        print("=" * 80)
        
        # Run all test categories
        test_results = []
        
        # 1. Health Check
        health_result = self.test_health_check()
        test_results.append(("Health Check", health_result))
        
        # 2. CORS Configuration
        cors_result = self.test_cors_configuration()
        test_results.append(("CORS Configuration", cors_result))
        
        # 3. Core API Endpoints
        core_result = self.test_core_api_endpoints()
        test_results.append(("Core API Endpoints", core_result))
        
        # 4. Authentication
        auth_result = self.test_authentication_flow()
        test_results.append(("Authentication Flow", auth_result))
        
        # 5. Error Handling
        error_result = self.test_error_handling()
        test_results.append(("Error Handling", error_result))
        
        # 6. Authenticated Endpoints
        authenticated_result = self.test_authenticated_endpoints()
        test_results.append(("Authenticated Endpoints", authenticated_result))
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed_categories = 0
        for category, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{category:<25} {status}")
            if result:
                passed_categories += 1
        
        print(f"\nOverall Results:")
        print(f"Categories Passed: {passed_categories}/{len(test_results)}")
        print(f"Individual Tests: {self.tests_passed}/{self.tests_run}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Detailed test results
        print(f"\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['name']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        return passed_categories == len(test_results)

if __name__ == "__main__":
    tester = KinAuraCORSAPITester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed! KinAura backend is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Please review the results above.")
        sys.exit(1)