#!/usr/bin/env python3

import requests
import sys
import json
import uuid
import time
from datetime import datetime, timedelta

class MobileAppointmentTester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.patient_token = None
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
                response = requests.get(url, headers=test_headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=15)

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

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def setup_authentication(self):
        """Setup authentication"""
        # Create admin user
        admin_data = {
            "provider": "admin",
            "access_token": "mobile_admin_token",
            "full_name": "Dr. Mobile Admin",
            "email": f"mobile_admin_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        }
        
        success, response = self.run_test(
            "Admin Authentication",
            "POST",
            "/auth/social-login",
            200,
            data=admin_data
        )
        
        if success:
            self.admin_token = response.get('access_token')
        
        # Create patient user
        patient_data = {
            "provider": "google",
            "access_token": "mobile_patient_token",
            "full_name": "Mobile Test Patient",
            "email": f"mobile_patient_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        }
        
        success, response = self.run_test(
            "Patient Authentication",
            "POST",
            "/auth/social-login",
            200,
            data=patient_data
        )
        
        if success:
            self.patient_token = response.get('access_token')
            return True
        
        return False

    def test_appointment_endpoints(self):
        """Test appointment-related endpoints for mobile"""
        print("\n📅 TESTING APPOINTMENT ENDPOINTS FOR MOBILE")
        
        if not self.patient_token:
            print("❌ No patient token for appointment testing")
            return False
        
        # Test patient bookings endpoint
        success, response = self.run_test(
            "Patient Bookings List",
            "GET",
            "/patient/appointments/bookings",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        bookings_success = success
        if success:
            print(f"   ✅ Patient bookings endpoint working")
        
        # Get a service ID for availability testing
        success, services = self.run_test(
            "Get Services for Availability Test",
            "GET",
            "/services",
            200
        )
        
        service_id = None
        if success and isinstance(services, list) and len(services) > 0:
            service_id = services[0].get('id')
            print(f"   ✅ Using service ID: {service_id}")
        
        # Test service availability endpoint
        availability_success = False
        if service_id:
            success, response = self.run_test(
                "Service Availability for Mobile",
                "GET",
                f"/patient/appointments/availability/{service_id}",
                200,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            availability_success = success
            if success:
                print(f"   ✅ Service availability endpoint working")
        
        return bookings_success and availability_success

    def test_boutique_mobile_endpoints(self):
        """Test boutique endpoints specifically for mobile"""
        print("\n🛍️ TESTING BOUTIQUE ENDPOINTS FOR MOBILE")
        
        endpoints_passed = 0
        total_endpoints = 0
        
        # Test product catalog with filtering
        total_endpoints += 1
        success, response = self.run_test(
            "Products with Category Filter",
            "GET",
            "/shop/products?category=skincare",
            200
        )
        if success:
            endpoints_passed += 1
            print(f"   ✅ Product filtering working for mobile")
        
        # Test product search
        total_endpoints += 1
        success, response = self.run_test(
            "Product Search",
            "GET",
            "/shop/products?search=illuminating",
            200
        )
        if success:
            endpoints_passed += 1
            print(f"   ✅ Product search working for mobile")
        
        # Test protocol-based recommendations
        total_endpoints += 1
        success, response = self.run_test(
            "Protocol Recommendations",
            "GET",
            "/shop/recommendations?protocol=bright-and-even",
            200
        )
        if success:
            endpoints_passed += 1
            print(f"   ✅ Protocol recommendations working for mobile")
        
        print(f"\n📊 Boutique Mobile Endpoints: {endpoints_passed}/{total_endpoints} passed")
        return endpoints_passed == total_endpoints

    def test_chatbot_mobile_integration(self):
        """Test chatbot functionality for mobile apps"""
        print("\n🤖 TESTING CHATBOT FOR MOBILE INTEGRATION")
        
        if not self.patient_token:
            print("❌ No patient token for chatbot testing")
            return False
        
        mobile_queries = [
            {
                "message": "I want to book Morpheus8 treatment",
                "expected_keywords": ["morpheus8", "booking", "protocol"]
            },
            {
                "message": "What treatments help with cellulite?",
                "expected_keywords": ["cellulite", "treatment", "protocol"]
            },
            {
                "message": "Show me anti-aging options",
                "expected_keywords": ["anti-aging", "protocol", "treatment"]
            }
        ]
        
        chatbot_tests_passed = 0
        for query in mobile_queries:
            chat_data = {
                "message": query["message"],
                "session_id": str(uuid.uuid4())
            }
            
            success, response = self.run_test(
                f"Chatbot Query: {query['message'][:30]}...",
                "POST",
                "/chat",
                200,
                data=chat_data,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                chatbot_tests_passed += 1
                response_message = response.get('message', '').lower()
                keywords_found = sum(1 for keyword in query["expected_keywords"] if keyword in response_message)
                if keywords_found > 0:
                    print(f"   ✅ Relevant response with {keywords_found} matching keywords")
                else:
                    print(f"   ⚠️  Response may not be fully relevant")
        
        print(f"\n📊 Chatbot Mobile Tests: {chatbot_tests_passed}/{len(mobile_queries)} passed")
        return chatbot_tests_passed >= len(mobile_queries) * 0.8

    def test_push_notifications_mobile(self):
        """Test push notification system for mobile"""
        print("\n📲 TESTING PUSH NOTIFICATIONS FOR MOBILE")
        
        if not self.patient_token:
            print("❌ No patient token for push notification testing")
            return False
        
        # Test notification token registration
        token_data = {
            "token": "mobile_fcm_token_test_123",
            "platform": "ios",
            "device_id": "mobile_test_device_456",
            "device_name": "iPhone Mobile Test"
        }
        
        success, response = self.run_test(
            "Mobile Push Token Registration",
            "POST",
            "/patient/notifications/register-token",
            200,
            data=token_data,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        token_registration_success = success
        
        # Test getting patient notifications
        success, response = self.run_test(
            "Get Patient Notifications",
            "GET",
            "/patient/notifications/proactive",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        notifications_success = success
        if success:
            notifications = response.get('notifications', [])
            count = response.get('count', 0)
            print(f"   ✅ Notifications endpoint working - {count} notifications")
        
        return token_registration_success and notifications_success

    def test_error_handling_mobile(self):
        """Test error handling suitable for mobile consumption"""
        print("\n🚨 TESTING ERROR HANDLING FOR MOBILE")
        
        error_tests = [
            {
                "name": "Invalid Endpoint",
                "endpoint": "/invalid/endpoint",
                "method": "GET",
                "expected_status": 404
            },
            {
                "name": "Unauthorized Access",
                "endpoint": "/admin/dashboard",
                "method": "GET",
                "expected_status": 401
            },
            {
                "name": "Invalid JSON Data",
                "endpoint": "/auth/social-login",
                "method": "POST",
                "expected_status": 422,
                "data": {"invalid": "data"}
            }
        ]
        
        error_tests_passed = 0
        for test in error_tests:
            success, response = self.run_test(
                test["name"],
                test["method"],
                test["endpoint"],
                test["expected_status"],
                data=test.get("data")
            )
            
            if success:
                error_tests_passed += 1
                # Check if error response has proper structure for mobile
                if isinstance(response, dict) and 'detail' in response:
                    print(f"   ✅ Error response properly structured for mobile")
                else:
                    print(f"   ⚠️  Error response structure could be improved")
        
        print(f"\n📊 Error Handling Tests: {error_tests_passed}/{len(error_tests)} passed")
        return error_tests_passed >= len(error_tests) * 0.8

    def run_mobile_specific_tests(self):
        """Run mobile-specific backend tests"""
        print("🚀 Starting Mobile-Specific Backend Tests")
        print("=" * 70)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed")
            return False
        
        # Run mobile-specific tests
        test_results = {}
        
        test_results["appointment_endpoints"] = self.test_appointment_endpoints()
        test_results["boutique_mobile"] = self.test_boutique_mobile_endpoints()
        test_results["chatbot_mobile"] = self.test_chatbot_mobile_integration()
        test_results["push_notifications"] = self.test_push_notifications_mobile()
        test_results["error_handling"] = self.test_error_handling_mobile()
        
        # Calculate results
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print("\n" + "=" * 70)
        print("🎯 MOBILE-SPECIFIC TEST RESULTS")
        print("=" * 70)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\n📊 Results: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = MobileAppointmentTester()
    success = tester.run_mobile_specific_tests()
    sys.exit(0 if success else 1)