#!/usr/bin/env python3
"""
KinAura Registration Network Error Testing
Focused test for user's specific "Network Error" during registration submission
"""

import requests
import sys
import json
import time
from datetime import datetime

class RegistrationNetworkTester:
    def __init__(self):
        # Use the exact URLs from environment files
        self.frontend_url = "https://golden-health-1.preview.emergentagent.com"
        self.backend_url = "https://golden-health-1.preview.emergentagent.com"
        self.api_url = f"{self.backend_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
        # User's exact data from the review request
        self.user_data = {
            "full_name": "Marco Di Maggio",
            "email": "dimaggio.mit@gmail.com",
            "phone": "3925481654",
            "password": "TestPassword123!"  # Using a test password
        }

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")

    def test_backend_connectivity(self):
        """Test basic backend connectivity"""
        print("\n🔍 Testing Backend Connectivity...")
        
        try:
            # Test root endpoint
            response = requests.get(f"{self.backend_url}/", timeout=10)
            if response.status_code == 200:
                self.log_test("Backend Root Endpoint", True, f"Status: {response.status_code}")
            else:
                self.log_test("Backend Root Endpoint", False, f"Status: {response.status_code}")
                return False
                
            # Test API root
            response = requests.get(f"{self.api_url}/", timeout=10)
            if response.status_code == 200:
                self.log_test("API Root Endpoint", True, f"Status: {response.status_code}")
            else:
                self.log_test("API Root Endpoint", False, f"Status: {response.status_code}")
                return False
                
            return True
            
        except requests.exceptions.ConnectionError as e:
            self.log_test("Backend Connectivity", False, f"Connection Error: {str(e)}")
            return False
        except requests.exceptions.Timeout as e:
            self.log_test("Backend Connectivity", False, f"Timeout Error: {str(e)}")
            return False
        except Exception as e:
            self.log_test("Backend Connectivity", False, f"Error: {str(e)}")
            return False

    def test_cors_configuration(self):
        """Test CORS configuration for frontend domain"""
        print("\n🔍 Testing CORS Configuration...")
        
        try:
            # Test preflight request (OPTIONS)
            headers = {
                'Origin': self.frontend_url,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = requests.options(f"{self.api_url}/auth/register", headers=headers, timeout=10)
            
            # Check CORS headers in response
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            print(f"   CORS Headers: {cors_headers}")
            
            # Check if frontend origin is allowed
            allowed_origin = cors_headers.get('Access-Control-Allow-Origin')
            if allowed_origin == '*' or self.frontend_url in str(allowed_origin):
                self.log_test("CORS Origin Check", True, f"Frontend origin allowed: {allowed_origin}")
            else:
                self.log_test("CORS Origin Check", False, f"Frontend origin not allowed. Got: {allowed_origin}")
                return False
                
            # Check if POST method is allowed
            allowed_methods = cors_headers.get('Access-Control-Allow-Methods', '')
            if 'POST' in allowed_methods:
                self.log_test("CORS POST Method", True, f"POST method allowed")
            else:
                self.log_test("CORS POST Method", False, f"POST method not allowed. Got: {allowed_methods}")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Error: {str(e)}")
            return False

    def test_registration_endpoint_direct(self):
        """Test registration endpoint directly with user's exact data"""
        print("\n🔍 Testing Registration Endpoint with User's Data...")
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Origin': self.frontend_url,
                'Referer': self.frontend_url
            }
            
            print(f"   Testing with data: {self.user_data['full_name']}, {self.user_data['email']}, {self.user_data['phone']}")
            
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=self.user_data,
                headers=headers,
                timeout=15
            )
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"   Response Data: {response_data}")
                    
                    # Check for required fields in response
                    if 'access_token' in response_data and 'user' in response_data:
                        self.log_test("Registration Success", True, "User registered successfully with token")
                        return True
                    else:
                        self.log_test("Registration Response Format", False, "Missing access_token or user in response")
                        return False
                        
                except json.JSONDecodeError:
                    self.log_test("Registration Response", False, "Invalid JSON response")
                    return False
                    
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    if "already registered" in str(error_data).lower():
                        self.log_test("Registration (User Exists)", True, "User already exists - this is expected")
                        return True
                    else:
                        self.log_test("Registration Validation", False, f"Validation error: {error_data}")
                        return False
                except:
                    self.log_test("Registration Error", False, f"Status 400: {response.text}")
                    return False
                    
            else:
                try:
                    error_data = response.json()
                    self.log_test("Registration Failed", False, f"Status {response.status_code}: {error_data}")
                except:
                    self.log_test("Registration Failed", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            self.log_test("Registration Network Error", False, f"Connection failed: {str(e)}")
            return False
        except requests.exceptions.Timeout as e:
            self.log_test("Registration Timeout", False, f"Request timed out: {str(e)}")
            return False
        except Exception as e:
            self.log_test("Registration Error", False, f"Unexpected error: {str(e)}")
            return False

    def test_registration_with_different_emails(self):
        """Test registration with different email variations to isolate the issue"""
        print("\n🔍 Testing Registration with Email Variations...")
        
        test_emails = [
            f"test_user_{int(time.time())}@kinaura.com",
            f"marco.test_{int(time.time())}@gmail.com",
            f"dimaggio.test_{int(time.time())}@gmail.com"
        ]
        
        for email in test_emails:
            test_data = self.user_data.copy()
            test_data['email'] = email
            test_data['full_name'] = f"Test User {email.split('@')[0]}"
            
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'Origin': self.frontend_url
                }
                
                response = requests.post(
                    f"{self.api_url}/auth/register",
                    json=test_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log_test(f"Registration with {email}", True, "Success")
                elif response.status_code == 400:
                    try:
                        error_data = response.json()
                        if "already registered" in str(error_data).lower():
                            self.log_test(f"Registration with {email}", True, "User exists (expected)")
                        else:
                            self.log_test(f"Registration with {email}", False, f"Validation: {error_data}")
                    except:
                        self.log_test(f"Registration with {email}", False, f"Status 400: {response.text}")
                else:
                    self.log_test(f"Registration with {email}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Registration with {email}", False, f"Error: {str(e)}")

    def test_network_routing(self):
        """Test network routing and response times"""
        print("\n🔍 Testing Network Routing and Performance...")
        
        endpoints_to_test = [
            "/",
            "/api/",
            "/api/auth/register",
            "/api/services"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                start_time = time.time()
                
                if endpoint == "/api/auth/register":
                    # Use HEAD request for registration endpoint to avoid creating users
                    response = requests.head(f"{self.backend_url}{endpoint}", timeout=10)
                else:
                    response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if response.status_code in [200, 405]:  # 405 is OK for HEAD on POST endpoint
                    self.log_test(f"Route {endpoint}", True, f"Response time: {response_time:.2f}ms")
                else:
                    self.log_test(f"Route {endpoint}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Route {endpoint}", False, f"Error: {str(e)}")

    def test_api_response_headers(self):
        """Test API response headers for security and CORS"""
        print("\n🔍 Testing API Response Headers...")
        
        try:
            headers = {
                'Origin': self.frontend_url,
                'Content-Type': 'application/json'
            }
            
            # Test with a simple GET request first
            response = requests.get(f"{self.api_url}/services", headers=headers, timeout=10)
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers:")
            
            important_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods', 
                'Access-Control-Allow-Headers',
                'Content-Type',
                'X-Content-Type-Options',
                'X-Frame-Options'
            ]
            
            for header in important_headers:
                value = response.headers.get(header, 'Not Set')
                print(f"     {header}: {value}")
                
            # Check CORS headers specifically
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            if cors_origin:
                if cors_origin == '*' or self.frontend_url in cors_origin:
                    self.log_test("CORS Headers Present", True, f"Origin: {cors_origin}")
                else:
                    self.log_test("CORS Headers", False, f"Origin mismatch: {cors_origin}")
            else:
                self.log_test("CORS Headers", False, "No CORS headers found")
                
            return True
            
        except Exception as e:
            self.log_test("API Headers Test", False, f"Error: {str(e)}")
            return False

    def test_firewall_and_proxy_issues(self):
        """Test for potential firewall or proxy issues"""
        print("\n🔍 Testing for Firewall/Proxy Issues...")
        
        try:
            # Test different request methods
            methods_to_test = ['GET', 'POST', 'OPTIONS']
            
            for method in methods_to_test:
                try:
                    if method == 'GET':
                        response = requests.get(f"{self.api_url}/services", timeout=10)
                    elif method == 'POST':
                        # Use a simple POST that should return 422 (validation error)
                        response = requests.post(f"{self.api_url}/auth/register", json={}, timeout=10)
                    elif method == 'OPTIONS':
                        response = requests.options(f"{self.api_url}/auth/register", timeout=10)
                    
                    self.log_test(f"{method} Request", True, f"Status: {response.status_code}")
                    
                except requests.exceptions.ConnectionError:
                    self.log_test(f"{method} Request", False, "Connection blocked/refused")
                except requests.exceptions.Timeout:
                    self.log_test(f"{method} Request", False, "Request timeout")
                except Exception as e:
                    self.log_test(f"{method} Request", False, f"Error: {str(e)}")
            
            # Test with different User-Agent strings
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'KinAura-Frontend/1.0',
                'python-requests/2.28.1'
            ]
            
            for ua in user_agents:
                try:
                    headers = {'User-Agent': ua}
                    response = requests.get(f"{self.api_url}/services", headers=headers, timeout=10)
                    self.log_test(f"User-Agent: {ua[:20]}...", True, f"Status: {response.status_code}")
                except Exception as e:
                    self.log_test(f"User-Agent: {ua[:20]}...", False, f"Error: {str(e)}")
                    
        except Exception as e:
            self.log_test("Firewall/Proxy Test", False, f"Error: {str(e)}")

    def run_comprehensive_test(self):
        """Run all tests to diagnose the registration network error"""
        print("🚀 KinAura Registration Network Error Diagnosis")
        print("=" * 60)
        print(f"Frontend URL: {self.frontend_url}")
        print(f"Backend URL: {self.backend_url}")
        print(f"API URL: {self.api_url}")
        print(f"User Data: {self.user_data['full_name']} ({self.user_data['email']})")
        print("=" * 60)
        
        # Run all diagnostic tests
        tests = [
            self.test_backend_connectivity,
            self.test_cors_configuration,
            self.test_network_routing,
            self.test_api_response_headers,
            self.test_registration_endpoint_direct,
            self.test_registration_with_different_emails,
            self.test_firewall_and_proxy_issues
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DIAGNOSTIC SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n✅ ALL TESTS PASSED - Registration should work")
            print("   The network error might be a frontend issue or temporary.")
        elif self.tests_passed < self.tests_run * 0.5:
            print("\n❌ MAJOR ISSUES DETECTED")
            print("   Multiple backend/network issues found.")
        else:
            print("\n⚠️  SOME ISSUES DETECTED")
            print("   Partial functionality - check specific failures above.")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = RegistrationNetworkTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)