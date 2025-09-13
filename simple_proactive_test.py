#!/usr/bin/env python3
"""
Simplified Proactive Notification System Testing
Focus on testing the proactive notification endpoints and functionality.
"""

import requests
import json
import uuid
from datetime import datetime, timedelta

class SimpleProactiveNotificationTester:
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
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)

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
                        if response_data and len(response_data) > 0:
                            print(f"   First item: {response_data[0]}")
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
            return True
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
            return True
        return False

    def test_proactive_notification_endpoints(self):
        """Test the proactive notification endpoints directly"""
        print(f"\n📬 Testing Proactive Notification Endpoints...")
        
        # Test 1: Get proactive notifications (should be empty initially)
        success, response = self.run_test(
            "Get Proactive Notifications (Empty)",
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
        
        # Test 2: Get latest protocol recommendation (should be empty initially)
        success, response = self.run_test(
            "Get Latest Protocol Recommendation (Empty)",
            "GET",
            "/patient/notifications/latest-protocol-recommendation",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            has_notification = response.get('has_notification', False)
            print(f"   ✅ Has notification: {has_notification}")
        
        return True

    def test_existing_services(self):
        """Test with existing services to see if we can trigger notifications"""
        print(f"\n🔍 Testing with Existing Services...")
        
        # Get existing services
        success, response = self.run_test(
            "Get Existing Services",
            "GET",
            "/services",
            200
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            print(f"   ✅ Found {len(response)} existing services")
            
            # Look for services that might trigger protocol recommendations
            morpheus_services = [s for s in response if 'morpheus' in s.get('name', '').lower()]
            iv_services = [s for s in response if 'iv' in s.get('name', '').lower()]
            hbot_services = [s for s in response if 'hbot' in s.get('name', '').lower() or 'hyperbaric' in s.get('name', '').lower()]
            laser_services = [s for s in response if 'laser' in s.get('name', '').lower()]
            
            print(f"   📊 Service breakdown:")
            print(f"      - Morpheus8 services: {len(morpheus_services)}")
            print(f"      - IV services: {len(iv_services)}")
            print(f"      - HBOT services: {len(hbot_services)}")
            print(f"      - Laser services: {len(laser_services)}")
            
            # Try to get available slots for a service
            if response:
                test_service = response[0]
                service_id = test_service.get('id')
                service_name = test_service.get('name')
                
                print(f"   🎯 Testing availability for: {service_name}")
                
                # Get availability for this service
                tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
                
                success, availability_response = self.run_test(
                    f"Get Service Availability - {service_name}",
                    "GET",
                    f"/patient/appointments/availability/{service_id}?date_from={tomorrow}&date_to={next_week}",
                    200,
                    headers={'Authorization': f'Bearer {self.patient_token}'}
                )
                
                if success:
                    calendar_data = availability_response.get('calendar', {})
                    total_slots = sum(len(slots) for slots in calendar_data.values())
                    print(f"   ✅ Found {total_slots} available slots")
                    
                    # If we have available slots, try to book one
                    if total_slots > 0:
                        for date, slots in calendar_data.items():
                            if slots and len(slots) > 0:
                                slot = slots[0]
                                if slot.get('available_spots', 0) > 0:
                                    print(f"   🎯 Attempting to book slot on {date} at {slot.get('start_time')}")
                                    
                                    booking_data = {
                                        "service_id": service_id,
                                        "appointment_date": date,
                                        "start_time": slot.get('start_time'),
                                        "notes": f"Test booking for proactive notification - {service_name}"
                                    }
                                    
                                    success, booking_response = self.run_test(
                                        f"Book Appointment - {service_name}",
                                        "POST",
                                        "/patient/appointments/book",
                                        200,
                                        data=booking_data,
                                        headers={'Authorization': f'Bearer {self.patient_token}'}
                                    )
                                    
                                    if success:
                                        has_protocol_recommendation = booking_response.get('has_protocol_recommendation', False)
                                        booking_id = booking_response.get('booking_id')
                                        
                                        print(f"   ✅ Booking successful: {booking_id}")
                                        print(f"   🌟 Has protocol recommendation: {has_protocol_recommendation}")
                                        
                                        if has_protocol_recommendation:
                                            # Now test the notification endpoints
                                            return self.test_notification_retrieval_after_booking()
                                    break
                            break
        
        return True

    def test_notification_retrieval_after_booking(self):
        """Test notification retrieval after a successful booking"""
        print(f"\n📬 Testing Notification Retrieval After Booking...")
        
        # Test 1: Get proactive notifications (should have notifications now)
        success, response = self.run_test(
            "Get Proactive Notifications (After Booking)",
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
            
            if notifications and len(notifications) > 0:
                notification = notifications[0]
                
                # Verify notification structure
                required_fields = ['patient_id', 'protocol_name', 'message', 'complementary_treatments', 'booked_service', 'language', 'created_at', 'notification_type', 'is_read']
                missing_fields = [field for field in required_fields if field not in notification]
                
                if not missing_fields:
                    print(f"   ✅ Notification structure contains all required fields")
                    
                    protocol_name = notification.get('protocol_name', '')
                    complementary_treatments = notification.get('complementary_treatments', [])
                    booked_service = notification.get('booked_service', '')
                    language = notification.get('language', '')
                    
                    print(f"   📋 Protocol: {protocol_name}")
                    print(f"   🎯 Booked Service: {booked_service}")
                    print(f"   🌐 Language: {language}")
                    print(f"   💊 Complementary Treatments: {len(complementary_treatments)}")
                    
                    if complementary_treatments:
                        for i, treatment in enumerate(complementary_treatments[:3]):  # Show first 3
                            print(f"      {i+1}. {treatment.get('name', 'Unknown')} - {treatment.get('description', 'No description')}")
                    
                    # Test 2: Get latest protocol recommendation
                    success, latest_response = self.run_test(
                        "Get Latest Protocol Recommendation (After Booking)",
                        "GET",
                        "/patient/notifications/latest-protocol-recommendation",
                        200,
                        headers={'Authorization': f'Bearer {self.patient_token}'}
                    )
                    
                    if success:
                        has_notification = latest_response.get('has_notification', False)
                        if has_notification:
                            latest_notification = latest_response.get('notification', {})
                            latest_protocol = latest_notification.get('protocol_name', 'Unknown')
                            print(f"   ✅ Latest protocol recommendation: {latest_protocol}")
                        
                        # Test 3: Mark notification as read
                        notification_id = notification.get('id')
                        if notification_id:
                            success, read_response = self.run_test(
                                "Mark Notification as Read",
                                "PUT",
                                f"/patient/notifications/proactive/{notification_id}/read",
                                200,
                                headers={'Authorization': f'Bearer {self.patient_token}'}
                            )
                            
                            if success:
                                print(f"   ✅ Successfully marked notification as read")
                                
                                # Test 4: Verify read status updated
                                success, updated_response = self.run_test(
                                    "Verify Read Status Updated",
                                    "GET",
                                    "/patient/notifications/proactive",
                                    200,
                                    headers={'Authorization': f'Bearer {self.patient_token}'}
                                )
                                
                                if success:
                                    updated_unread_count = updated_response.get('unread_count', 0)
                                    print(f"   ✅ Updated unread count: {updated_unread_count}")
                                    
                                    if updated_unread_count < unread_count:
                                        print(f"   ✅ Read status successfully updated")
                                    else:
                                        print(f"   ⚠️  Read status may not have updated properly")
                    
                    return True
                else:
                    print(f"   ❌ Missing notification fields: {missing_fields}")
                    return False
            else:
                print(f"   ❌ No proactive notifications found after booking")
                return False
        else:
            print(f"   ❌ Failed to retrieve proactive notifications after booking")
            return False

    def test_bilingual_functionality(self):
        """Test bilingual notification functionality"""
        print(f"\n🌐 Testing Bilingual Functionality...")
        
        # Create Italian patient
        italian_patient_data = {
            "provider": "google",
            "access_token": "italian_patient_token",
            "full_name": "Paziente Italiano",
            "email": f"italian_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        }
        
        success, response = self.run_test(
            "Create Italian Patient",
            "POST",
            "/auth/social-login",
            200,
            data=italian_patient_data
        )
        
        if success:
            italian_token = response.get('access_token')
            print(f"   ✅ Italian patient created successfully")
            
            # Test Italian notifications (would need actual booking to test fully)
            success, italian_notifications = self.run_test(
                "Get Italian Patient Notifications",
                "GET",
                "/patient/notifications/proactive",
                200,
                headers={'Authorization': f'Bearer {italian_token}'}
            )
            
            if success:
                print(f"   ✅ Italian patient can access notification endpoints")
                return True
        
        return False

    def run_comprehensive_test(self):
        """Run comprehensive proactive notification system test"""
        print("🌟 SIMPLIFIED PROACTIVE NOTIFICATION SYSTEM TESTING")
        print("=" * 80)
        print(f"🌐 Testing against: {self.base_url}")
        print()
        
        # Step 1: Setup authentication
        if not self.setup_admin_authentication():
            print("❌ Admin authentication failed")
            return False
        
        if not self.setup_patient_authentication():
            print("❌ Patient authentication failed")
            return False
        
        # Step 2: Test proactive notification endpoints
        self.test_proactive_notification_endpoints()
        
        # Step 3: Test with existing services
        self.test_existing_services()
        
        # Step 4: Test bilingual functionality
        self.test_bilingual_functionality()
        
        # Final results
        print(f"\n{'='*80}")
        print(f"🏁 PROACTIVE NOTIFICATION TESTING COMPLETE")
        print(f"{'='*80}")
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed / self.tests_run >= 0.7:
            print(f"🎉 GOOD! Proactive notification system endpoints are accessible!")
            return True
        else:
            print(f"❌ NEEDS ATTENTION. Issues detected in proactive notification system.")
            return False

if __name__ == "__main__":
    tester = SimpleProactiveNotificationTester()
    tester.run_comprehensive_test()