#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class BasicKinAuraAPITester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)

            # Handle multiple expected status codes
            if isinstance(expected_status, list):
                success = response.status_code in expected_status
            else:
                success = response.status_code == expected_status
                
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    return False, error_data
                except:
                    print(f"   Error: {response.text}")
                    return False, {}

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint for basic connectivity"""
        success, response = self.run_test(
            "Backend Server Health Check",
            "GET",
            "/",
            200
        )
        
        if success:
            message = response.get('message', '')
            if 'KinAura' in message:
                print(f"   ✅ Backend server is healthy and responding correctly")
            else:
                print(f"   ⚠️  Unexpected response message: {message}")
        
        return success

    def test_services_endpoint(self):
        """Test services endpoint to verify backend is serving data"""
        success, response = self.run_test(
            "Services Endpoint Connectivity",
            "GET",
            "/services",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Services endpoint working - {len(response)} services available")
            
            # Check for expected services
            service_names = [service.get('name', '') for service in response]
            key_services = ['Ozone Therapy', 'NAD IV Therapy', 'PEMF Therapy']
            found_services = [svc for svc in key_services if svc in service_names]
            
            if len(found_services) >= 2:
                print(f"   ✅ Key services found: {found_services}")
            else:
                print(f"   ⚠️  Expected key services not found")
                
        return success

    def test_user_registration(self):
        """Test user registration functionality"""
        test_user_data = {
            "email": f"test_basic_{datetime.now().strftime('%Y%m%d_%H%M%S')}@kinaura.com",
            "password": "TestPass123!",
            "full_name": "Basic Test User",
            "phone": "+1234567890"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "/auth/register",
            200,
            data=test_user_data
        )
        
        if success:
            self.token = response.get('access_token')
            user_data = response.get('user', {})
            user_id = user_data.get('id')
            print(f"   ✅ User registered successfully with ID: {user_id}")
            print(f"   ✅ Access token received: {self.token[:20]}..." if self.token else "   ❌ No token received")
            
            # Verify user data structure
            required_fields = ['id', 'email', 'full_name', 'role', 'membership_tier']
            missing_fields = [field for field in required_fields if field not in user_data]
            if not missing_fields:
                print(f"   ✅ User data has all required fields")
            else:
                print(f"   ⚠️  Missing user fields: {missing_fields}")
        
        return success

    def test_social_login(self):
        """Test social login functionality"""
        social_data = {
            "provider": "google",
            "access_token": "mock_google_token",
            "full_name": "Social Test User",
            "email": f"social_basic_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        }
        
        success, response = self.run_test(
            "Social Login",
            "POST",
            "/auth/social-login",
            200,
            data=social_data
        )
        
        if success:
            token = response.get('access_token')
            user_data = response.get('user', {})
            print(f"   ✅ Social login successful")
            print(f"   ✅ User role: {user_data.get('role', 'unknown')}")
            print(f"   ✅ Membership tier: {user_data.get('membership_tier', 'unknown')}")
        
        return success

    def test_admin_social_login(self):
        """Test admin social login with role assignment"""
        admin_data = {
            "provider": "admin",
            "access_token": "admin_token",
            "full_name": "Dr. Marco Rossi",
            "email": f"admin_basic_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        }
        
        success, response = self.run_test(
            "Admin Social Login",
            "POST",
            "/auth/social-login",
            200,
            data=admin_data
        )
        
        if success:
            self.admin_token = response.get('access_token')
            user_data = response.get('user', {})
            print(f"   ✅ Admin login successful")
            
            # Verify admin role assignment
            if user_data.get('role') == 'admin':
                print(f"   ✅ Admin role properly assigned")
            else:
                print(f"   ❌ Admin role not assigned, got: {user_data.get('role')}")
                
            # Verify admin membership tier
            if user_data.get('membership_tier') == 'elite':
                print(f"   ✅ Admin membership tier set to elite")
            else:
                print(f"   ⚠️  Admin membership tier: {user_data.get('membership_tier')}")
        
        return success

    def test_authenticated_endpoint(self):
        """Test authenticated endpoint access"""
        if not self.token:
            print("❌ No token available for authenticated request")
            return False
            
        success, response = self.run_test(
            "Authenticated Endpoint Access",
            "GET",
            "/auth/me",
            200,
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        if success:
            print(f"   ✅ Token authentication working correctly")
            user_data = response
            if user_data.get('email'):
                print(f"   ✅ User data retrieved: {user_data.get('full_name')} ({user_data.get('email')})")
        
        return success

    def test_admin_endpoint_access(self):
        """Test admin endpoint access"""
        if not self.admin_token:
            print("❌ No admin token available for admin endpoint test")
            return False
            
        success, response = self.run_test(
            "Admin Endpoint Access",
            "GET",
            "/admin/dashboard",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   ✅ Admin authentication working correctly")
            if 'totalPatients' in response and 'totalServices' in response:
                print(f"   ✅ Dashboard data: {response.get('totalPatients')} patients, {response.get('totalServices')} services")
        
        return success

    def test_non_admin_access_control(self):
        """Test that regular users cannot access admin endpoints"""
        if not self.token:
            print("❌ No regular user token available for access control test")
            return False
            
        success, response = self.run_test(
            "Non-Admin Access Control",
            "GET",
            "/admin/dashboard",
            403,  # Expecting 403 Forbidden
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        if success:
            print(f"   ✅ Access control working - regular users denied admin access")
        else:
            print(f"   ❌ Access control failed - regular users should not access admin endpoints")
        
        return success

    def run_basic_tests(self):
        """Run all basic connectivity and authentication tests"""
        print("🚀 Starting Basic Backend Connectivity and Authentication Tests")
        print("=" * 70)
        
        # Test basic connectivity
        print("\n📡 TESTING BASIC CONNECTIVITY")
        connectivity_tests = [
            self.test_root_endpoint,
            self.test_services_endpoint
        ]
        
        connectivity_passed = 0
        for test in connectivity_tests:
            if test():
                connectivity_passed += 1
        
        print(f"\n📊 Connectivity Tests: {connectivity_passed}/{len(connectivity_tests)} passed")
        
        # Test authentication
        print("\n🔐 TESTING AUTHENTICATION SYSTEM")
        auth_tests = [
            self.test_user_registration,
            self.test_social_login,
            self.test_admin_social_login,
            self.test_authenticated_endpoint,
            self.test_admin_endpoint_access,
            self.test_non_admin_access_control
        ]
        
        auth_passed = 0
        for test in auth_tests:
            if test():
                auth_passed += 1
        
        print(f"\n📊 Authentication Tests: {auth_passed}/{len(auth_tests)} passed")
        
        # Overall results
        total_tests = len(connectivity_tests) + len(auth_tests)
        total_passed = connectivity_passed + auth_passed
        success_rate = (total_passed / total_tests) * 100
        
        print("\n" + "=" * 70)
        print(f"🎯 OVERALL RESULTS")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_tests - total_passed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("   🎉 EXCELLENT - Backend is working great!")
        elif success_rate >= 75:
            print("   ✅ GOOD - Backend is working well with minor issues")
        elif success_rate >= 50:
            print("   ⚠️  FAIR - Backend has some issues that need attention")
        else:
            print("   ❌ POOR - Backend has significant issues")
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = BasicKinAuraAPITester()
    success = tester.run_basic_tests()
    sys.exit(0 if success else 1)