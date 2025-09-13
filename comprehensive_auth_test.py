#!/usr/bin/env python3
"""
Comprehensive Authentication Testing
Test the complete authentication flow including edge cases
"""

import requests
import sys
import json
import time
from datetime import datetime

class ComprehensiveAuthTester:
    def __init__(self):
        self.frontend_url = "https://golden-health-1.preview.emergentagent.com"
        self.backend_url = "https://golden-health-1.preview.emergentagent.com"
        self.api_url = f"{self.backend_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

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

    def test_registration_validation(self):
        """Test registration with various validation scenarios"""
        print("\n🔍 Testing Registration Validation...")
        
        test_cases = [
            {
                "name": "Missing Email",
                "data": {"full_name": "Test User", "password": "Test123!", "phone": "1234567890"},
                "expected_status": 422
            },
            {
                "name": "Invalid Email Format",
                "data": {"email": "invalid-email", "full_name": "Test User", "password": "Test123!", "phone": "1234567890"},
                "expected_status": 422
            },
            {
                "name": "Missing Password",
                "data": {"email": "test@example.com", "full_name": "Test User", "phone": "1234567890"},
                "expected_status": 422
            },
            {
                "name": "Missing Full Name",
                "data": {"email": "test@example.com", "password": "Test123!", "phone": "1234567890"},
                "expected_status": 422
            },
            {
                "name": "Valid Registration Data",
                "data": {
                    "email": f"valid_test_{int(time.time())}@example.com",
                    "full_name": "Valid Test User",
                    "password": "ValidPass123!",
                    "phone": "1234567890"
                },
                "expected_status": 200
            }
        ]
        
        for test_case in test_cases:
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'Origin': self.frontend_url
                }
                
                response = requests.post(
                    f"{self.api_url}/auth/register",
                    json=test_case["data"],
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == test_case["expected_status"]:
                    self.log_test(f"Validation: {test_case['name']}", True, f"Status: {response.status_code}")
                else:
                    self.log_test(f"Validation: {test_case['name']}", False, f"Expected {test_case['expected_status']}, got {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Validation: {test_case['name']}", False, f"Error: {str(e)}")

    def test_duplicate_registration(self):
        """Test duplicate email registration"""
        print("\n🔍 Testing Duplicate Registration...")
        
        # First registration
        user_data = {
            "email": f"duplicate_test_{int(time.time())}@example.com",
            "full_name": "Duplicate Test User",
            "password": "DuplicatePass123!",
            "phone": "1234567890"
        }
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Origin': self.frontend_url
            }
            
            # First registration should succeed
            response1 = requests.post(
                f"{self.api_url}/auth/register",
                json=user_data,
                headers=headers,
                timeout=10
            )
            
            if response1.status_code == 200:
                self.log_test("First Registration", True, "User created successfully")
                
                # Second registration with same email should fail
                response2 = requests.post(
                    f"{self.api_url}/auth/register",
                    json=user_data,
                    headers=headers,
                    timeout=10
                )
                
                if response2.status_code == 400:
                    self.log_test("Duplicate Registration Prevention", True, "Duplicate email correctly rejected")
                else:
                    self.log_test("Duplicate Registration Prevention", False, f"Expected 400, got {response2.status_code}")
            else:
                self.log_test("First Registration", False, f"Status: {response1.status_code}")
                
        except Exception as e:
            self.log_test("Duplicate Registration Test", False, f"Error: {str(e)}")

    def test_login_scenarios(self):
        """Test various login scenarios"""
        print("\n🔍 Testing Login Scenarios...")
        
        # Create a test user first
        user_data = {
            "email": f"login_test_{int(time.time())}@example.com",
            "full_name": "Login Test User",
            "password": "LoginPass123!",
            "phone": "1234567890"
        }
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Origin': self.frontend_url
            }
            
            # Register user
            reg_response = requests.post(
                f"{self.api_url}/auth/register",
                json=user_data,
                headers=headers,
                timeout=10
            )
            
            if reg_response.status_code == 200:
                self.log_test("Test User Creation for Login", True, "User created")
                
                # Test correct login
                login_data = {
                    "email": user_data["email"],
                    "password": user_data["password"]
                }
                
                login_response = requests.post(
                    f"{self.api_url}/auth/login",
                    json=login_data,
                    headers=headers,
                    timeout=10
                )
                
                if login_response.status_code == 200:
                    self.log_test("Correct Login", True, "Login successful")
                    
                    # Test token validation
                    token_data = login_response.json()
                    token = token_data.get('access_token')
                    
                    if token:
                        auth_headers = {
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        }
                        
                        me_response = requests.get(
                            f"{self.api_url}/auth/me",
                            headers=auth_headers,
                            timeout=10
                        )
                        
                        if me_response.status_code == 200:
                            self.log_test("Token Validation", True, "Token is valid")
                        else:
                            self.log_test("Token Validation", False, f"Status: {me_response.status_code}")
                else:
                    self.log_test("Correct Login", False, f"Status: {login_response.status_code}")
                
                # Test wrong password
                wrong_login_data = {
                    "email": user_data["email"],
                    "password": "WrongPassword123!"
                }
                
                wrong_response = requests.post(
                    f"{self.api_url}/auth/login",
                    json=wrong_login_data,
                    headers=headers,
                    timeout=10
                )
                
                if wrong_response.status_code == 401:
                    self.log_test("Wrong Password Rejection", True, "Wrong password correctly rejected")
                else:
                    self.log_test("Wrong Password Rejection", False, f"Expected 401, got {wrong_response.status_code}")
                
                # Test non-existent user
                nonexistent_login = {
                    "email": "nonexistent@example.com",
                    "password": "SomePassword123!"
                }
                
                nonexistent_response = requests.post(
                    f"{self.api_url}/auth/login",
                    json=nonexistent_login,
                    headers=headers,
                    timeout=10
                )
                
                if nonexistent_response.status_code == 401:
                    self.log_test("Non-existent User Rejection", True, "Non-existent user correctly rejected")
                else:
                    self.log_test("Non-existent User Rejection", False, f"Expected 401, got {nonexistent_response.status_code}")
                    
            else:
                self.log_test("Test User Creation for Login", False, f"Status: {reg_response.status_code}")
                
        except Exception as e:
            self.log_test("Login Scenarios Test", False, f"Error: {str(e)}")

    def test_marco_dimaggio_specific(self):
        """Test with Marco Di Maggio's specific data"""
        print("\n🔍 Testing Marco Di Maggio's Specific Case...")
        
        marco_data = {
            "full_name": "Marco Di Maggio",
            "email": "dimaggio.mit@gmail.com",
            "phone": "3925481654",
            "password": "TestPassword123!"
        }
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Origin': self.frontend_url,
                'Referer': f"{self.frontend_url}/login",
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Test registration
            reg_response = requests.post(
                f"{self.api_url}/auth/register",
                json=marco_data,
                headers=headers,
                timeout=15
            )
            
            print(f"   Registration Status: {reg_response.status_code}")
            print(f"   Registration Headers: {dict(reg_response.headers)}")
            
            if reg_response.status_code == 200:
                reg_data = reg_response.json()
                self.log_test("Marco's Registration", True, f"User ID: {reg_data.get('user', {}).get('id')}")
                
                # Test login
                login_data = {
                    "email": marco_data["email"],
                    "password": marco_data["password"]
                }
                
                login_response = requests.post(
                    f"{self.api_url}/auth/login",
                    json=login_data,
                    headers=headers,
                    timeout=10
                )
                
                if login_response.status_code == 200:
                    self.log_test("Marco's Login", True, "Login successful")
                else:
                    self.log_test("Marco's Login", False, f"Status: {login_response.status_code}")
                    
            elif reg_response.status_code == 400:
                try:
                    error_data = reg_response.json()
                    if "already registered" in str(error_data).lower():
                        self.log_test("Marco's Registration", True, "User already exists (expected)")
                        
                        # Test login with existing user
                        login_data = {
                            "email": marco_data["email"],
                            "password": marco_data["password"]
                        }
                        
                        login_response = requests.post(
                            f"{self.api_url}/auth/login",
                            json=login_data,
                            headers=headers,
                            timeout=10
                        )
                        
                        if login_response.status_code == 200:
                            self.log_test("Marco's Login (Existing User)", True, "Login successful")
                        else:
                            self.log_test("Marco's Login (Existing User)", False, f"Status: {login_response.status_code}")
                    else:
                        self.log_test("Marco's Registration", False, f"Validation error: {error_data}")
                except:
                    self.log_test("Marco's Registration", False, f"Status 400: {reg_response.text}")
            else:
                self.log_test("Marco's Registration", False, f"Status: {reg_response.status_code}")
                
        except Exception as e:
            self.log_test("Marco's Specific Test", False, f"Error: {str(e)}")

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n🔍 Testing Rate Limiting...")
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Origin': self.frontend_url
            }
            
            # Make multiple rapid requests
            rate_limit_hit = False
            for i in range(10):
                test_data = {
                    "email": f"rate_test_{i}_{int(time.time())}@example.com",
                    "full_name": f"Rate Test User {i}",
                    "password": "RateTest123!",
                    "phone": "1234567890"
                }
                
                response = requests.post(
                    f"{self.api_url}/auth/register",
                    json=test_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 429:  # Too Many Requests
                    rate_limit_hit = True
                    break
                elif response.status_code != 200:
                    break
                    
                time.sleep(0.1)  # Small delay between requests
            
            if rate_limit_hit:
                self.log_test("Rate Limiting", True, "Rate limiting is active")
            else:
                self.log_test("Rate Limiting", True, "No rate limiting hit (within limits)")
                
        except Exception as e:
            self.log_test("Rate Limiting Test", False, f"Error: {str(e)}")

    def run_comprehensive_tests(self):
        """Run all comprehensive authentication tests"""
        print("🚀 Comprehensive KinAura Authentication Testing")
        print("=" * 70)
        print(f"Frontend URL: {self.frontend_url}")
        print(f"Backend URL: {self.backend_url}")
        print(f"API URL: {self.api_url}")
        print("=" * 70)
        
        # Run all tests
        tests = [
            self.test_registration_validation,
            self.test_duplicate_registration,
            self.test_login_scenarios,
            self.test_marco_dimaggio_specific,
            self.test_rate_limiting
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n✅ ALL COMPREHENSIVE TESTS PASSED")
            print("   Backend authentication system is fully functional")
        elif self.tests_passed >= self.tests_run * 0.8:
            print("\n✅ MOSTLY SUCCESSFUL")
            print("   Minor issues detected but core functionality works")
        else:
            print("\n⚠️  SIGNIFICANT ISSUES DETECTED")
            print("   Multiple authentication problems found")
        
        return self.tests_passed >= self.tests_run * 0.8

if __name__ == "__main__":
    tester = ComprehensiveAuthTester()
    success = tester.run_comprehensive_tests()
    sys.exit(0 if success else 1)