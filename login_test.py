#!/usr/bin/env python3
"""
KinAura Login Testing
Test login functionality with the registered user
"""

import requests
import sys
import json

class LoginTester:
    def __init__(self):
        self.backend_url = "https://golden-health-1.preview.emergentagent.com"
        self.api_url = f"{self.backend_url}/api"
        self.frontend_url = "https://golden-health-1.preview.emergentagent.com"
        
        # User's data from registration test
        self.login_data = {
            "email": "dimaggio.mit@gmail.com",
            "password": "TestPassword123!"
        }

    def test_login(self):
        """Test login with registered user"""
        print("🔍 Testing Login with Registered User...")
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Origin': self.frontend_url
            }
            
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=self.login_data,
                headers=headers,
                timeout=10
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"   ✅ Login successful")
                print(f"   User: {response_data.get('user', {}).get('full_name')}")
                print(f"   Email: {response_data.get('user', {}).get('email')}")
                print(f"   Token: {response_data.get('access_token', '')[:20]}...")
                
                # Test authenticated endpoint
                token = response_data.get('access_token')
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
                        print(f"   ✅ Token validation successful")
                        user_data = me_response.json()
                        print(f"   Authenticated as: {user_data.get('full_name')}")
                    else:
                        print(f"   ❌ Token validation failed: {me_response.status_code}")
                
                return True
            else:
                try:
                    error_data = response.json()
                    print(f"   ❌ Login failed: {error_data}")
                except:
                    print(f"   ❌ Login failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Login error: {str(e)}")
            return False

    def test_social_login(self):
        """Test social login functionality"""
        print("\n🔍 Testing Social Login...")
        
        social_data = {
            "provider": "google",
            "access_token": "mock_google_token",
            "full_name": "Marco Di Maggio Social",
            "email": "dimaggio.social.test@gmail.com"
        }
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Origin': self.frontend_url
            }
            
            response = requests.post(
                f"{self.api_url}/auth/social-login",
                json=social_data,
                headers=headers,
                timeout=10
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"   ✅ Social login successful")
                print(f"   User: {response_data.get('user', {}).get('full_name')}")
                return True
            else:
                try:
                    error_data = response.json()
                    print(f"   ❌ Social login failed: {error_data}")
                except:
                    print(f"   ❌ Social login failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Social login error: {str(e)}")
            return False

    def run_tests(self):
        """Run all login tests"""
        print("🚀 KinAura Login Testing")
        print("=" * 50)
        
        tests_passed = 0
        total_tests = 2
        
        if self.test_login():
            tests_passed += 1
            
        if self.test_social_login():
            tests_passed += 1
        
        print("\n" + "=" * 50)
        print(f"📊 LOGIN TEST SUMMARY")
        print("=" * 50)
        print(f"Tests Passed: {tests_passed}/{total_tests}")
        print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
        
        if tests_passed == total_tests:
            print("\n✅ ALL LOGIN TESTS PASSED")
        else:
            print("\n⚠️  SOME LOGIN TESTS FAILED")
        
        return tests_passed == total_tests

if __name__ == "__main__":
    tester = LoginTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)