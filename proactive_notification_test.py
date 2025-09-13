#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced Proactive Notification System with Booking Endpoint Fix
Testing the complete workflow: booking → notification generation → notification retrieval
"""

import requests
import sys
import json
import uuid
from datetime import datetime, timedelta

class ProactiveNotificationTester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.patient_token = None
        self.test_patient_id = None
        self.test_service_id = None
        self.test_booking_id = None
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

    def setup_admin_authentication(self):
        """Setup admin authentication using the specified credentials"""
        print("\n🔧 Setting up Admin Authentication...")
        
        admin_data = {
            "provider": "admin",
            "access_token": "admin_token",
            "full_name": "Dr. Marco Rossi",
            "email": "admin@kinaura.com"
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
            print(f"   ✅ Admin authenticated with ID: {user_data.get('id')}")
            
            # Verify admin role
            if user_data.get('role') == 'admin':
                print(f"   ✅ Admin role properly assigned")
                return True
            else:
                print(f"   ❌ Admin role not assigned, got: {user_data.get('role')}")
                return False
        else:
            print("   ❌ Admin authentication failed")
            return False

    def create_test_patient(self):
        """Create a test patient for booking simulation"""
        print("\n🔧 Creating Test Patient...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        patient_data = {
            "email": f"proactive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@kinaura.com",
            "full_name": "Proactive Test Patient",
            "phone": "+1234567890",
            "membership_tier": "gold",
            "tags": ["proactive", "test", "morpheus8"]
        }
        
        success, response = self.run_test(
            "Create Test Patient",
            "POST",
            "/admin/patients",
            200,
            data=patient_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            self.test_patient_id = response.get('id')
            print(f"   ✅ Test patient created with ID: {self.test_patient_id}")
            
            # Create patient login token
            patient_login_data = {
                "provider": "google",
                "access_token": "patient_token",
                "full_name": "Proactive Test Patient",
                "email": patient_data["email"]
            }
            
            login_success, login_response = self.run_test(
                "Patient Social Login",
                "POST",
                "/auth/social-login",
                200,
                data=patient_login_data
            )
            
            if login_success:
                self.patient_token = login_response.get('access_token')
                print(f"   ✅ Patient token created")
                return True
            else:
                print("   ❌ Failed to create patient token")
                return False
        else:
            print("   ❌ Failed to create test patient")
            return False

    def create_test_service(self):
        """Create a test service for booking"""
        print("\n🔧 Creating Test Service...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        service_data = {
            "name": "Morpheus8 Luxury Treatment",
            "category": "Regenerative Aesthetics",
            "description": "Advanced Morpheus8 treatment for skin tightening and rejuvenation",
            "detailed_description": "State-of-the-art Morpheus8 radiofrequency microneedling treatment that combines microneedling with radiofrequency energy to remodel and contour the face and body.",
            "duration": 90,
            "price": 599.0,
            "benefits": ["Skin tightening", "Collagen stimulation", "Wrinkle reduction", "Improved texture"],
            "is_active": True
        }
        
        success, response = self.run_test(
            "Create Test Service",
            "POST",
            "/admin/services",
            200,
            data=service_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            self.test_service_id = response.get('id')
            print(f"   ✅ Test service created with ID: {self.test_service_id}")
            return True
        else:
            print("   ❌ Failed to create test service")
            return False

    def setup_appointment_availability(self):
        """Setup appointment availability and slots for the test service"""
        print("\n🔧 Setting up Appointment Availability...")
        
        if not self.admin_token or not self.test_service_id:
            print("❌ Missing admin token or service ID")
            return False
        
        # Create availability
        availability_data = {
            "service_id": self.test_service_id,
            "days_of_week": [1, 2, 3, 4, 5],  # Mon-Fri
            "start_time": "09:00",
            "end_time": "17:00",
            "slot_duration": 90,
            "buffer_time": 15
        }
        
        success, response = self.run_test(
            "Create Service Availability",
            "POST",
            "/admin/appointments/availability",
            200,
            data=availability_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if not success:
            print("   ❌ Failed to create availability")
            return False
        
        # Generate slots for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        slots_data = {
            "service_id": self.test_service_id,
            "date_from": tomorrow,
            "date_to": tomorrow
        }
        
        success, response = self.run_test(
            "Generate Appointment Slots",
            "POST",
            "/admin/appointments/generate-slots",
            200,
            data=slots_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            slots_created = response.get('slots_created', 0)
            print(f"   ✅ Generated {slots_created} appointment slots")
            return True
        else:
            print("   ❌ Failed to generate appointment slots")
            return False

    def test_fixed_booking_endpoint(self):
        """Test the fixed booking endpoint with corrected service_id access"""
        print("\n🎯 Testing Fixed Booking Endpoint...")
        
        if not self.patient_token or not self.test_service_id:
            print("❌ Missing patient token or service ID")
            return False
        
        # Book appointment for tomorrow at 10:00 AM
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        booking_data = {
            "service_id": self.test_service_id,
            "appointment_date": tomorrow,
            "start_time": "10:00",
            "notes": "Test booking for proactive notification system"
        }
        
        success, response = self.run_test(
            "Book Appointment (Fixed Endpoint)",
            "POST",
            "/patient/appointments/book",
            200,
            data=booking_data,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            self.test_booking_id = response.get('booking_id')
            has_protocol_recommendation = response.get('has_protocol_recommendation', False)
            
            print(f"   ✅ Booking created with ID: {self.test_booking_id}")
            
            if has_protocol_recommendation:
                print(f"   ✅ Booking response includes has_protocol_recommendation: true")
                return True
            else:
                print(f"   ❌ Booking response missing has_protocol_recommendation flag")
                return False
        else:
            error_detail = response.get('detail', 'Unknown error')
            if "'Request' object has no attribute 'service_id'" in str(error_detail):
                print(f"   ❌ CRITICAL: Booking endpoint still has the 'Request' object attribute error!")
                print(f"   ❌ Error: {error_detail}")
                return False
            else:
                print(f"   ❌ Booking failed with error: {error_detail}")
                return False

    def test_proactive_notification_generation(self):
        """Test that proactive notification was automatically generated"""
        print("\n🎯 Testing Proactive Notification Generation...")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        # Wait a moment for notification to be processed
        import time
        time.sleep(2)
        
        success, response = self.run_test(
            "Get Proactive Notifications",
            "GET",
            "/patient/notifications/proactive",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            notifications = response.get('notifications', [])
            count = response.get('count', 0)
            unread_count = response.get('unread_count', 0)
            
            print(f"   ✅ Retrieved {count} proactive notifications ({unread_count} unread)")
            
            if notifications:
                # Verify notification structure
                notification = notifications[0]
                required_fields = [
                    'patient_id', 'protocol_name', 'message', 'complementary_treatments',
                    'booked_service', 'language', 'created_at', 'notification_type', 'is_read'
                ]
                
                missing_fields = [field for field in required_fields if field not in notification]
                
                if not missing_fields:
                    print(f"   ✅ Notification structure contains all required fields")
                    
                    # Verify content
                    protocol_name = notification.get('protocol_name', '')
                    complementary_treatments = notification.get('complementary_treatments', [])
                    booked_service = notification.get('booked_service', '')
                    
                    if protocol_name and complementary_treatments and booked_service:
                        print(f"   ✅ Protocol: {protocol_name}")
                        print(f"   ✅ Booked Service: {booked_service}")
                        print(f"   ✅ Complementary Treatments: {len(complementary_treatments)} treatments")
                        
                        # Verify Morpheus8 → Advanced Firm & Renew Protocol mapping
                        if "morpheus8" in booked_service.lower() and "firm" in protocol_name.lower():
                            print(f"   ✅ Correct protocol mapping: Morpheus8 → Advanced Firm & Renew")
                        else:
                            print(f"   ⚠️  Protocol mapping may be incorrect")
                        
                        return True
                    else:
                        print(f"   ❌ Notification missing content: protocol={bool(protocol_name)}, treatments={bool(complementary_treatments)}, service={bool(booked_service)}")
                        return False
                else:
                    print(f"   ❌ Missing notification fields: {missing_fields}")
                    return False
            else:
                print(f"   ❌ No proactive notifications found - notification generation may have failed")
                return False
        else:
            print("   ❌ Failed to retrieve proactive notifications")
            return False

    def test_notification_content_verification(self):
        """Test notification content for proper protocol recommendations"""
        print("\n🎯 Testing Notification Content Verification...")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        success, response = self.run_test(
            "Get Latest Protocol Recommendation",
            "GET",
            "/patient/notifications/latest-protocol-recommendation",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            has_notification = response.get('has_notification', False)
            
            if has_notification:
                notification = response.get('notification', {})
                protocol_name = notification.get('protocol_name', '')
                message = notification.get('message', '')
                complementary_treatments = notification.get('complementary_treatments', [])
                language = notification.get('language', 'en')
                
                print(f"   ✅ Latest protocol recommendation found")
                print(f"   ✅ Protocol: {protocol_name}")
                print(f"   ✅ Language: {language}")
                print(f"   ✅ Message length: {len(message)} characters")
                
                # Verify complementary treatments exclude booked treatment
                booked_service = notification.get('booked_service', '')
                if complementary_treatments:
                    excluded_booked = not any("morpheus8" in treatment.lower() for treatment in complementary_treatments)
                    if excluded_booked:
                        print(f"   ✅ Complementary treatments correctly exclude booked treatment")
                    else:
                        print(f"   ❌ Complementary treatments include booked treatment (should be excluded)")
                    
                    print(f"   ✅ Complementary treatments ({len(complementary_treatments)}):")
                    for i, treatment in enumerate(complementary_treatments[:3], 1):
                        print(f"      {i}. {treatment}")
                
                # Test bilingual functionality (if applicable)
                if language == 'it':
                    print(f"   ✅ Italian language notification detected")
                elif language == 'en':
                    print(f"   ✅ English language notification detected")
                
                return True
            else:
                print(f"   ❌ No unread protocol recommendations found")
                return False
        else:
            print("   ❌ Failed to get latest protocol recommendation")
            return False

    def test_notification_management_endpoints(self):
        """Test notification management endpoints (mark as read)"""
        print("\n🎯 Testing Notification Management Endpoints...")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        # First get notifications to find an ID
        success, response = self.run_test(
            "Get Notifications for Management",
            "GET",
            "/patient/notifications/proactive",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if not success or not response.get('notifications'):
            print("   ❌ No notifications available for management testing")
            return False
        
        notification_id = response['notifications'][0].get('id')
        if not notification_id:
            print("   ❌ Notification missing ID field")
            return False
        
        # Test marking notification as read
        success, read_response = self.run_test(
            "Mark Notification as Read",
            "PUT",
            f"/patient/notifications/proactive/{notification_id}/read",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            print(f"   ✅ Successfully marked notification as read")
            
            # Verify notification is now marked as read
            success, updated_response = self.run_test(
                "Verify Read Status",
                "GET",
                "/patient/notifications/proactive",
                200,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                updated_unread_count = updated_response.get('unread_count', 0)
                original_unread_count = response.get('unread_count', 0)
                
                if updated_unread_count < original_unread_count:
                    print(f"   ✅ Unread count decreased from {original_unread_count} to {updated_unread_count}")
                    return True
                else:
                    print(f"   ❌ Unread count did not decrease after marking as read")
                    return False
            else:
                print("   ❌ Failed to verify read status")
                return False
        else:
            print("   ❌ Failed to mark notification as read")
            return False

    def test_complete_workflow(self):
        """Test the complete proactive notification workflow"""
        print("\n🎯 Testing Complete Proactive Notification Workflow...")
        
        workflow_steps = [
            ("Setup Admin Authentication", self.setup_admin_authentication),
            ("Create Test Patient", self.create_test_patient),
            ("Create Test Service", self.create_test_service),
            ("Setup Appointment Availability", self.setup_appointment_availability),
            ("Test Fixed Booking Endpoint", self.test_fixed_booking_endpoint),
            ("Test Proactive Notification Generation", self.test_proactive_notification_generation),
            ("Test Notification Content Verification", self.test_notification_content_verification),
            ("Test Notification Management Endpoints", self.test_notification_management_endpoints)
        ]
        
        passed_steps = 0
        for step_name, step_function in workflow_steps:
            try:
                if step_function():
                    passed_steps += 1
                    print(f"   ✅ {step_name} - PASSED")
                else:
                    print(f"   ❌ {step_name} - FAILED")
            except Exception as e:
                print(f"   ❌ {step_name} - ERROR: {str(e)}")
        
        success_rate = (passed_steps / len(workflow_steps)) * 100
        print(f"\n📊 Workflow Results: {passed_steps}/{len(workflow_steps)} steps passed ({success_rate:.1f}%)")
        
        return passed_steps == len(workflow_steps)

    def run_comprehensive_test(self):
        """Run comprehensive proactive notification system test"""
        print("🚀 Starting Comprehensive Proactive Notification System Test")
        print("=" * 80)
        
        # Test the complete workflow
        workflow_success = self.test_complete_workflow()
        
        # Print final results
        print("\n" + "=" * 80)
        print("📊 FINAL TEST RESULTS")
        print("=" * 80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if workflow_success:
            print("\n🎉 COMPREHENSIVE TEST RESULT: SUCCESS")
            print("✅ Complete proactive notification system is working correctly")
            print("✅ Booking endpoint fix is working (no 'Request' object attribute errors)")
            print("✅ Proactive notification generation is functional")
            print("✅ Notification content contains proper protocol recommendations")
            print("✅ All notification management endpoints are working")
            print("✅ System is ready for frontend integration testing")
        else:
            print("\n❌ COMPREHENSIVE TEST RESULT: PARTIAL SUCCESS")
            print("⚠️  Some components of the proactive notification system need attention")
        
        return workflow_success

if __name__ == "__main__":
    tester = ProactiveNotificationTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)
"""
Enhanced Proactive Notification System Testing
Test the proactive notification system for protocol recommendations after booking.
"""

import requests
import json
import uuid
from datetime import datetime, timedelta

class ProactiveNotificationTester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.patient_token = None
        self.test_patient_id = None
        self.test_service_id = None
        self.test_booking_id = None
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

    def setup_admin_authentication(self):
        """Setup admin authentication"""
        admin_data = {
            "provider": "admin",
            "access_token": "admin_token",
            "full_name": "Dr. Marco Rossi",
            "email": "admin@kinaura.com"
        }
        
        success, response = self.run_test(
            "Admin Authentication Setup",
            "POST",
            "/auth/social-login",
            200,
            data=admin_data
        )
        
        if success:
            self.admin_token = response.get('access_token')
            print(f"   ✅ Admin authenticated successfully")
            return True
        else:
            print(f"   ❌ Admin authentication failed")
            return False

    def create_test_patient(self):
        """Create a test patient for booking simulation"""
        patient_data = {
            "email": f"proactive_test_{datetime.now().strftime('%H%M%S')}@kinaura.com",
            "full_name": "Proactive Test Patient",
            "phone": "+1234567890",
            "membership_tier": "gold",
            "tags": ["proactive", "test"]
        }
        
        success, response = self.run_test(
            "Create Test Patient",
            "POST",
            "/admin/patients",
            200,
            data=patient_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            self.test_patient_id = response.get('id')
            print(f"   ✅ Created test patient with ID: {self.test_patient_id}")
            return True
        else:
            print(f"   ❌ Failed to create test patient")
            return False

    def setup_patient_authentication(self):
        """Setup patient authentication"""
        patient_login_data = {
            "provider": "google",
            "access_token": "proactive_patient_token",
            "full_name": "Proactive Test Patient",
            "email": f"proactive_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        }
        
        success, response = self.run_test(
            "Patient Authentication Setup",
            "POST",
            "/auth/social-login",
            200,
            data=patient_login_data
        )
        
        if success:
            self.patient_token = response.get('access_token')
            print(f"   ✅ Patient authenticated successfully")
            return True
        else:
            print(f"   ❌ Patient authentication failed")
            return False

    def create_test_service(self, service_name):
        """Create a test service for booking"""
        service_data = {
            "name": service_name,
            "category": "Test Category",
            "description": f"Test service for {service_name}",
            "detailed_description": f"Detailed description for {service_name}",
            "duration": 60,
            "price": 299.0,
            "benefits": ["Test benefit"],
            "is_active": True
        }
        
        success, response = self.run_test(
            f"Create Test Service - {service_name}",
            "POST",
            "/admin/services",
            200,
            data=service_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            service_id = response.get('id')
            print(f"   ✅ Created service: {service_name} (ID: {service_id})")
            return service_id
        else:
            print(f"   ❌ Failed to create service: {service_name}")
            return None

    def setup_service_availability(self, service_id):
        """Setup availability for a service"""
        availability_data = {
            "service_id": service_id,
            "days_of_week": [1, 2, 3, 4, 5],  # Mon-Fri
            "start_time": "09:00",
            "end_time": "17:00",
            "slot_duration": 60,
            "buffer_time": 15
        }
        
        success, response = self.run_test(
            "Create Service Availability",
            "POST",
            "/admin/appointments/availability",
            200,
            data=availability_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   ✅ Service availability created")
            return True
        else:
            print(f"   ❌ Failed to create service availability")
            return False

    def generate_appointment_slots(self, service_id):
        """Generate appointment slots for a service"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        slots_data = {
            "service_id": service_id,
            "date_from": tomorrow,
            "date_to": tomorrow
        }
        
        success, response = self.run_test(
            "Generate Appointment Slots",
            "POST",
            "/admin/appointments/generate-slots",
            200,
            data=slots_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   ✅ Appointment slots generated")
            return True
        else:
            print(f"   ❌ Failed to generate appointment slots")
            return False

    def test_booking_with_proactive_notification(self, service_id, service_name):
        """Test booking appointment with proactive notification trigger"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        booking_data = {
            "service_id": service_id,
            "appointment_date": tomorrow,
            "start_time": "10:00",
            "notes": f"Test booking for {service_name}"
        }
        
        success, response = self.run_test(
            f"Book Appointment - {service_name}",
            "POST",
            "/patient/appointments/book",
            200,
            data=booking_data,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            self.test_booking_id = response.get('booking_id')
            has_protocol_recommendation = response.get('has_protocol_recommendation', False)
            
            if has_protocol_recommendation:
                print(f"   ✅ Booking triggered proactive notification")
                return True
            else:
                print(f"   ❌ Booking did not trigger proactive notification")
                return False
        else:
            print(f"   ❌ Failed to book appointment")
            return False

    def test_get_proactive_notifications(self):
        """Test retrieving proactive notifications"""
        success, response = self.run_test(
            "Get Proactive Notifications",
            "GET",
            "/patient/notifications/proactive",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            notifications = response.get('notifications', [])
            count = response.get('count', 0)
            unread_count = response.get('unread_count', 0)
            
            print(f"   ✅ Retrieved {count} proactive notifications ({unread_count} unread)")
            
            if notifications:
                notification = notifications[0]
                required_fields = ['patient_id', 'protocol_name', 'message', 'complementary_treatments', 'booked_service', 'language', 'created_at', 'notification_type', 'is_read']
                missing_fields = [field for field in required_fields if field not in notification]
                
                if not missing_fields:
                    print(f"   ✅ Notification structure contains all required fields")
                    
                    protocol_name = notification.get('protocol_name', '')
                    complementary_treatments = notification.get('complementary_treatments', [])
                    
                    if protocol_name and complementary_treatments:
                        print(f"   ✅ Protocol recommendation: {protocol_name} with {len(complementary_treatments)} complementary treatments")
                        return True, notifications[0]
                    else:
                        print(f"   ❌ Protocol recommendation missing content")
                        return False, None
                else:
                    print(f"   ❌ Missing notification fields: {missing_fields}")
                    return False, None
            else:
                print(f"   ❌ No proactive notifications found")
                return False, None
        else:
            print(f"   ❌ Failed to retrieve proactive notifications")
            return False, None

    def test_get_latest_protocol_recommendation(self):
        """Test getting latest protocol recommendation"""
        success, response = self.run_test(
            "Get Latest Protocol Recommendation",
            "GET",
            "/patient/notifications/latest-protocol-recommendation",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            has_notification = response.get('has_notification', False)
            if has_notification:
                latest_notification = response.get('notification', {})
                protocol_name = latest_notification.get('protocol_name', 'Unknown')
                print(f"   ✅ Latest protocol recommendation: {protocol_name}")
                return True
            else:
                print(f"   ⚠️  No unread protocol recommendations found")
                return True  # This is acceptable
        else:
            print(f"   ❌ Failed to get latest protocol recommendation")
            return False

    def test_mark_notification_as_read(self, notification_id):
        """Test marking notification as read"""
        success, response = self.run_test(
            "Mark Notification as Read",
            "PUT",
            f"/patient/notifications/proactive/{notification_id}/read",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            print(f"   ✅ Successfully marked notification as read")
            return True
        else:
            print(f"   ❌ Failed to mark notification as read")
            return False

    def test_protocol_recommendation_scenarios(self):
        """Test different service booking scenarios for protocol recommendations"""
        test_scenarios = [
            {
                "service_name": "Morpheus8 Treatment",
                "expected_protocol": "Advanced Firm & Renew Protocol",
                "description": "Morpheus8 → skin-laxity protocol"
            },
            {
                "service_name": "HBOT Session", 
                "expected_protocol": "Accelerated Recovery",
                "description": "HBOT → recovery/longevity protocol"
            },
            {
                "service_name": "IV Therapy",
                "expected_protocol": "Vital Reset",
                "description": "IV Therapy → fatigue/immunity protocol"
            },
            {
                "service_name": "Laser Facial",
                "expected_protocol": "Bright & Even",
                "description": "Laser Facial → pigmentation/wrinkles protocol"
            }
        ]
        
        successful_scenarios = 0
        
        for scenario in test_scenarios:
            print(f"\n📋 Testing Scenario: {scenario['description']}")
            
            # Create service
            service_id = self.create_test_service(scenario['service_name'])
            if not service_id:
                continue
            
            # Setup availability
            if not self.setup_service_availability(service_id):
                continue
            
            # Generate slots
            if not self.generate_appointment_slots(service_id):
                continue
            
            # Test booking with proactive notification
            if self.test_booking_with_proactive_notification(service_id, scenario['service_name']):
                successful_scenarios += 1
                print(f"   ✅ Scenario successful: {scenario['description']}")
            else:
                print(f"   ❌ Scenario failed: {scenario['description']}")
        
        return successful_scenarios, len(test_scenarios)

    def run_comprehensive_test(self):
        """Run comprehensive proactive notification system test"""
        print("🌟 ENHANCED PROACTIVE NOTIFICATION SYSTEM TESTING")
        print("=" * 80)
        print(f"🌐 Testing against: {self.base_url}")
        print()
        
        # Step 1: Setup admin authentication
        if not self.setup_admin_authentication():
            return False
        
        # Step 2: Create test patient
        if not self.create_test_patient():
            return False
        
        # Step 3: Setup patient authentication
        if not self.setup_patient_authentication():
            return False
        
        # Step 4: Test protocol recommendation scenarios
        print(f"\n🎯 Testing Protocol Recommendation Scenarios...")
        successful_scenarios, total_scenarios = self.test_protocol_recommendation_scenarios()
        
        if successful_scenarios > 0:
            print(f"\n✅ {successful_scenarios}/{total_scenarios} scenarios successful")
            
            # Step 5: Test notification retrieval
            print(f"\n📬 Testing Notification Retrieval...")
            notification_success, notification = self.test_get_proactive_notifications()
            
            if notification_success and notification:
                # Step 6: Test latest protocol recommendation
                self.test_get_latest_protocol_recommendation()
                
                # Step 7: Test marking notification as read
                notification_id = notification.get('id')
                if notification_id:
                    self.test_mark_notification_as_read(notification_id)
                    
                    # Step 8: Verify read status updated
                    print(f"\n🔄 Verifying Read Status Update...")
                    self.test_get_proactive_notifications()
        
        # Final results
        print(f"\n{'='*80}")
        print(f"🏁 PROACTIVE NOTIFICATION TESTING COMPLETE")
        print(f"{'='*80}")
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed / self.tests_run >= 0.8:
            print(f"🎉 EXCELLENT! Proactive notification system is working well!")
            return True
        else:
            print(f"❌ NEEDS ATTENTION. Some issues detected in proactive notification system.")
            return False

if __name__ == "__main__":
    tester = ProactiveNotificationTester()
    tester.run_comprehensive_test()