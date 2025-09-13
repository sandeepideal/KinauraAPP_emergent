#!/usr/bin/env python3
"""
KinAura Authentication System Testing
Tests the complete authentication flow including registration, login, and database verification
"""

import requests
import sys
import json
import uuid
from datetime import datetime, timedelta
import pymongo
import os
from dotenv import load_dotenv

class KinAuraAuthTester:
    def __init__(self):
        # Load environment variables
        load_dotenv('/app/backend/.env')
        
        # Get URLs from environment
        self.frontend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://golden-health-1.preview.emergentagent.com')
        self.base_url = self.frontend_url
        self.api_url = f"{self.base_url}/api"
        
        # MongoDB connection for database verification
        self.mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/kinaura_wellness')
        self.db_name = os.getenv('DB_NAME', 'test_database')
        
        # Test tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.test_users = []  # Track created users for cleanup
        
        print(f"🔧 KinAura Authentication System Tester")
        print(f"   Backend URL: {self.base_url}")
        print(f"   API URL: {self.api_url}")
        print(f"   MongoDB URL: {self.mongo_url}")
        print(f"   Database: {self.db_name}")

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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

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
                    if isinstance(response_data, dict) and len(str(response_data)) < 1000:
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

    def connect_to_database(self):
        """Connect to MongoDB to verify database operations"""
        try:
            self.mongo_client = pymongo.MongoClient(self.mongo_url)
            self.db = self.mongo_client[self.db_name]
            
            # Test connection
            self.db.admin.command('ping')
            print(f"✅ Connected to MongoDB database: {self.db_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {str(e)}")
            return False

    def verify_user_in_database(self, email, expected_fields=None):
        """Verify user exists in database with expected fields"""
        try:
            user = self.db.users.find_one({"email": email}, {"_id": 0})
            if user:
                print(f"   ✅ User found in database: {email}")
                print(f"   📋 User ID: {user.get('id')}")
                print(f"   📋 Full Name: {user.get('full_name')}")
                print(f"   📋 Role: {user.get('role', 'member')}")
                print(f"   📋 Membership Tier: {user.get('membership_tier', 'not_member')}")
                
                if expected_fields:
                    missing_fields = [field for field in expected_fields if field not in user]
                    if missing_fields:
                        print(f"   ❌ Missing expected fields: {missing_fields}")
                        return False
                    else:
                        print(f"   ✅ All expected fields present")
                
                return True
            else:
                print(f"   ❌ User not found in database: {email}")
                return False
        except Exception as e:
            print(f"   ❌ Database verification error: {str(e)}")
            return False

    def test_cors_configuration(self):
        """Test CORS configuration by making a preflight request"""
        print(f"\n🔍 Testing CORS Configuration...")
        
        # Test preflight request
        try:
            response = requests.options(
                f"{self.api_url}/auth/register",
                headers={
                    'Origin': self.frontend_url,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                timeout=10
            )
            
            print(f"   Preflight Status: {response.status_code}")
            
            # Check CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            print(f"   CORS Headers: {cors_headers}")
            
            # Verify CORS is properly configured
            if (response.status_code in [200, 204] and 
                cors_headers['Access-Control-Allow-Origin'] and
                'POST' in cors_headers.get('Access-Control-Allow-Methods', '')):
                print(f"   ✅ CORS properly configured for frontend communication")
                return True
            else:
                print(f"   ❌ CORS configuration issues detected")
                return False
                
        except Exception as e:
            print(f"   ❌ CORS test failed: {str(e)}")
            return False

    def test_user_registration_complete(self):
        """Test complete user registration flow"""
        print(f"\n🔍 Testing Complete User Registration Flow...")
        
        # Generate unique test user data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        test_email = f"test_reg_{timestamp}@kinaura.com"
        
        test_user_data = {
            "email": test_email,
            "password": "SecurePass123!",
            "full_name": "Test Registration User",
            "phone": "+39 123 456 7890"
        }
        
        # Step 1: Test registration endpoint
        success, response = self.run_test(
            "User Registration API",
            "POST",
            "/auth/register",
            200,
            data=test_user_data
        )
        
        if not success:
            return False
        
        # Step 2: Verify response format
        required_response_fields = ['access_token', 'token_type', 'user']
        missing_fields = [field for field in required_response_fields if field not in response]
        
        if missing_fields:
            print(f"   ❌ Missing response fields: {missing_fields}")
            return False
        else:
            print(f"   ✅ Registration response has all required fields")
        
        # Step 3: Verify token format
        access_token = response.get('access_token')
        if access_token and len(access_token) > 20:
            print(f"   ✅ Access token generated: {access_token[:20]}...")
        else:
            print(f"   ❌ Invalid or missing access token")
            return False
        
        # Step 4: Verify user data in response
        user_data = response.get('user', {})
        expected_user_fields = ['id', 'email', 'full_name', 'role', 'membership_tier']
        missing_user_fields = [field for field in expected_user_fields if field not in user_data]
        
        if missing_user_fields:
            print(f"   ❌ Missing user fields in response: {missing_user_fields}")
            return False
        else:
            print(f"   ✅ User data in response has all required fields")
        
        # Step 5: Verify user in database
        if hasattr(self, 'db'):
            db_success = self.verify_user_in_database(
                test_email, 
                expected_fields=['id', 'email', 'full_name', 'hashed_password', 'role', 'membership_tier']
            )
            if not db_success:
                return False
        
        # Store user for cleanup and further testing
        self.test_users.append({
            'email': test_email,
            'password': test_user_data['password'],
            'token': access_token,
            'user_id': user_data.get('id')
        })
        
        print(f"   ✅ Complete user registration flow successful")
        return True

    def test_user_login_complete(self):
        """Test complete user login flow"""
        print(f"\n🔍 Testing Complete User Login Flow...")
        
        if not self.test_users:
            print(f"   ❌ No test users available for login test")
            return False
        
        # Use the first registered test user
        test_user = self.test_users[0]
        
        login_data = {
            "email": test_user['email'],
            "password": test_user['password']
        }
        
        # Step 1: Test login endpoint
        success, response = self.run_test(
            "User Login API",
            "POST",
            "/auth/login",
            200,
            data=login_data
        )
        
        if not success:
            return False
        
        # Step 2: Verify response format (same as registration)
        required_response_fields = ['access_token', 'token_type', 'user']
        missing_fields = [field for field in required_response_fields if field not in response]
        
        if missing_fields:
            print(f"   ❌ Missing response fields: {missing_fields}")
            return False
        else:
            print(f"   ✅ Login response has all required fields")
        
        # Step 3: Verify new token is generated
        new_token = response.get('access_token')
        if new_token and new_token != test_user['token']:
            print(f"   ✅ New access token generated on login")
        else:
            print(f"   ❌ Token issue - same token or missing")
            return False
        
        # Step 4: Test authenticated endpoint with new token
        auth_success, auth_response = self.run_test(
            "Authenticated User Info",
            "GET",
            "/auth/me",
            200,
            headers={'Authorization': f'Bearer {new_token}'}
        )
        
        if auth_success:
            print(f"   ✅ Authentication with login token successful")
            print(f"   📋 Authenticated as: {auth_response.get('full_name')} ({auth_response.get('email')})")
        else:
            print(f"   ❌ Authentication with login token failed")
            return False
        
        print(f"   ✅ Complete user login flow successful")
        return True

    def test_invalid_registration_scenarios(self):
        """Test various invalid registration scenarios"""
        print(f"\n🔍 Testing Invalid Registration Scenarios...")
        
        test_scenarios = [
            {
                "name": "Duplicate Email Registration",
                "data": {
                    "email": self.test_users[0]['email'] if self.test_users else "duplicate@test.com",
                    "password": "NewPass123!",
                    "full_name": "Duplicate User",
                    "phone": "+39 123 456 7890"
                },
                "expected_status": 400,
                "description": "Should reject duplicate email"
            },
            {
                "name": "Missing Required Fields",
                "data": {
                    "email": "incomplete@test.com",
                    # Missing password, full_name
                },
                "expected_status": 422,
                "description": "Should reject incomplete data"
            },
            {
                "name": "Invalid Email Format",
                "data": {
                    "email": "invalid-email-format",
                    "password": "ValidPass123!",
                    "full_name": "Invalid Email User",
                    "phone": "+39 123 456 7890"
                },
                "expected_status": 422,
                "description": "Should reject invalid email format"
            },
            {
                "name": "Weak Password",
                "data": {
                    "email": "weakpass@test.com",
                    "password": "123",
                    "full_name": "Weak Password User",
                    "phone": "+39 123 456 7890"
                },
                "expected_status": [422, 400],  # Could be either validation error
                "description": "Should reject weak password"
            }
        ]
        
        all_passed = True
        for scenario in test_scenarios:
            success, response = self.run_test(
                scenario["name"],
                "POST",
                "/auth/register",
                scenario["expected_status"],
                data=scenario["data"]
            )
            
            if success:
                print(f"   ✅ {scenario['description']}")
            else:
                print(f"   ❌ {scenario['description']} - Test failed")
                all_passed = False
        
        return all_passed

    def test_invalid_login_scenarios(self):
        """Test various invalid login scenarios"""
        print(f"\n🔍 Testing Invalid Login Scenarios...")
        
        test_scenarios = [
            {
                "name": "Wrong Password",
                "data": {
                    "email": self.test_users[0]['email'] if self.test_users else "test@test.com",
                    "password": "WrongPassword123!"
                },
                "expected_status": 401,
                "description": "Should reject wrong password"
            },
            {
                "name": "Non-existent User",
                "data": {
                    "email": "nonexistent@test.com",
                    "password": "AnyPassword123!"
                },
                "expected_status": 401,
                "description": "Should reject non-existent user"
            },
            {
                "name": "Missing Credentials",
                "data": {
                    "email": "test@test.com"
                    # Missing password
                },
                "expected_status": 422,
                "description": "Should reject missing password"
            },
            {
                "name": "Empty Credentials",
                "data": {
                    "email": "",
                    "password": ""
                },
                "expected_status": 422,
                "description": "Should reject empty credentials"
            }
        ]
        
        all_passed = True
        for scenario in test_scenarios:
            success, response = self.run_test(
                scenario["name"],
                "POST",
                "/auth/login",
                scenario["expected_status"],
                data=scenario["data"]
            )
            
            if success:
                print(f"   ✅ {scenario['description']}")
            else:
                print(f"   ❌ {scenario['description']} - Test failed")
                all_passed = False
        
        return all_passed

    def test_token_validation(self):
        """Test JWT token validation"""
        print(f"\n🔍 Testing JWT Token Validation...")
        
        if not self.test_users:
            print(f"   ❌ No test users available for token validation")
            return False
        
        valid_token = self.test_users[0]['token']
        
        # Test 1: Valid token
        success, response = self.run_test(
            "Valid Token Authentication",
            "GET",
            "/auth/me",
            200,
            headers={'Authorization': f'Bearer {valid_token}'}
        )
        
        if not success:
            return False
        
        # Test 2: Invalid token
        success, response = self.run_test(
            "Invalid Token Authentication",
            "GET",
            "/auth/me",
            401,
            headers={'Authorization': 'Bearer invalid_token_here'}
        )
        
        if not success:
            print(f"   ❌ Invalid token should be rejected")
            return False
        
        # Test 3: Missing token
        success, response = self.run_test(
            "Missing Token Authentication",
            "GET",
            "/auth/me",
            401
        )
        
        if not success:
            print(f"   ❌ Missing token should be rejected")
            return False
        
        # Test 4: Malformed Authorization header
        success, response = self.run_test(
            "Malformed Authorization Header",
            "GET",
            "/auth/me",
            401,
            headers={'Authorization': 'InvalidFormat token_here'}
        )
        
        if not success:
            print(f"   ❌ Malformed authorization header should be rejected")
            return False
        
        print(f"   ✅ JWT token validation working correctly")
        return True

    def test_social_login_functionality(self):
        """Test social login functionality"""
        print(f"\n🔍 Testing Social Login Functionality...")
        
        # Test Google social login
        google_data = {
            "provider": "google",
            "access_token": "mock_google_token_12345",
            "full_name": "Google Test User",
            "email": f"google_test_{datetime.now().strftime('%H%M%S')}@gmail.com"
        }
        
        success, response = self.run_test(
            "Google Social Login",
            "POST",
            "/auth/social-login",
            200,
            data=google_data
        )
        
        if not success:
            return False
        
        # Verify response format
        if 'access_token' in response and 'user' in response:
            user_data = response['user']
            print(f"   ✅ Google user created: {user_data.get('full_name')} ({user_data.get('email')})")
            print(f"   📋 Role: {user_data.get('role')}")
            print(f"   📋 Social Provider: {user_data.get('social_provider')}")
            
            # Verify in database if connected
            if hasattr(self, 'db'):
                self.verify_user_in_database(google_data['email'])
        else:
            print(f"   ❌ Social login response missing required fields")
            return False
        
        # Test admin social login (should get admin role)
        admin_data = {
            "provider": "admin",
            "access_token": "admin_token_12345",
            "full_name": "Admin Test User",
            "email": f"admin_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        }
        
        success, response = self.run_test(
            "Admin Social Login",
            "POST",
            "/auth/social-login",
            200,
            data=admin_data
        )
        
        if success:
            user_data = response['user']
            if user_data.get('role') == 'admin':
                print(f"   ✅ Admin role correctly assigned")
            else:
                print(f"   ❌ Admin role not assigned, got: {user_data.get('role')}")
                return False
        else:
            return False
        
        print(f"   ✅ Social login functionality working correctly")
        return True

    def test_database_integration(self):
        """Test database integration and data persistence"""
        print(f"\n🔍 Testing Database Integration...")
        
        if not hasattr(self, 'db'):
            print(f"   ❌ Database connection not available")
            return False
        
        # Test 1: Count users in database
        try:
            user_count = self.db.users.count_documents({})
            print(f"   📊 Total users in database: {user_count}")
            
            # Test 2: Verify test users exist
            test_user_count = 0
            for test_user in self.test_users:
                user = self.db.users.find_one({"email": test_user['email']})
                if user:
                    test_user_count += 1
            
            print(f"   📊 Test users found in database: {test_user_count}/{len(self.test_users)}")
            
            # Test 3: Verify password hashing
            if self.test_users:
                test_user = self.db.users.find_one({"email": self.test_users[0]['email']})
                if test_user and 'hashed_password' in test_user:
                    hashed_password = test_user['hashed_password']
                    if hashed_password != self.test_users[0]['password']:
                        print(f"   ✅ Password properly hashed (not stored in plain text)")
                    else:
                        print(f"   ❌ Password stored in plain text - security issue!")
                        return False
                else:
                    print(f"   ❌ Hashed password not found in database")
                    return False
            
            # Test 4: Verify required fields are present
            sample_user = self.db.users.find_one({})
            if sample_user:
                required_fields = ['id', 'email', 'full_name', 'role', 'membership_tier', 'created_at']
                missing_fields = [field for field in required_fields if field not in sample_user]
                if missing_fields:
                    print(f"   ❌ Missing required fields in database: {missing_fields}")
                    return False
                else:
                    print(f"   ✅ All required fields present in database records")
            
            print(f"   ✅ Database integration working correctly")
            return True
            
        except Exception as e:
            print(f"   ❌ Database integration test failed: {str(e)}")
            return False

    def cleanup_test_data(self):
        """Clean up test users created during testing"""
        print(f"\n🧹 Cleaning up test data...")
        
        if hasattr(self, 'db') and self.test_users:
            try:
                test_emails = [user['email'] for user in self.test_users]
                result = self.db.users.delete_many({"email": {"$in": test_emails}})
                print(f"   🗑️  Deleted {result.deleted_count} test users from database")
            except Exception as e:
                print(f"   ⚠️  Failed to cleanup test data: {str(e)}")

    def run_all_tests(self):
        """Run all authentication tests"""
        print(f"\n🚀 Starting KinAura Authentication System Tests")
        print(f"=" * 60)
        
        # Connect to database for verification
        db_connected = self.connect_to_database()
        
        # Run all tests
        tests = [
            ("CORS Configuration", self.test_cors_configuration),
            ("User Registration Complete Flow", self.test_user_registration_complete),
            ("User Login Complete Flow", self.test_user_login_complete),
            ("Invalid Registration Scenarios", self.test_invalid_registration_scenarios),
            ("Invalid Login Scenarios", self.test_invalid_login_scenarios),
            ("JWT Token Validation", self.test_token_validation),
            ("Social Login Functionality", self.test_social_login_functionality),
        ]
        
        if db_connected:
            tests.append(("Database Integration", self.test_database_integration))
        
        passed_tests = 0
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name} - PASSED")
                else:
                    print(f"❌ {test_name} - FAILED")
            except Exception as e:
                print(f"❌ {test_name} - ERROR: {str(e)}")
        
        # Cleanup
        if db_connected:
            self.cleanup_test_data()
        
        # Final results
        print(f"\n" + "=" * 60)
        print(f"🏁 AUTHENTICATION TESTING COMPLETE")
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "0%")
        print(f"🧪 Test Suites: {passed_tests}/{len(tests)} passed")
        
        # Summary for main agent
        if passed_tests == len(tests) and self.tests_passed == self.tests_run:
            print(f"\n🎉 ALL AUTHENTICATION TESTS PASSED!")
            print(f"✅ User registration API working correctly")
            print(f"✅ User login API working correctly") 
            print(f"✅ Database user creation verified")
            print(f"✅ Response format includes access_token and user data")
            print(f"✅ CORS configuration allows frontend communication")
            return True
        else:
            print(f"\n⚠️  SOME AUTHENTICATION TESTS FAILED")
            print(f"❌ Issues found that need to be addressed")
            return False

def main():
    """Main function to run authentication tests"""
    tester = KinAuraAuthTester()
    success = tester.run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()