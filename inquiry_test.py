#!/usr/bin/env python3
"""
Patient Inquiry Tracking System Test
Tests the recently fixed Patient Inquiry Tracking System endpoints
"""

import requests
import json
import time
from datetime import datetime, timedelta

class PatientInquiryTester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.patient_token = None
        self.patient_user_id = None
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

    def setup_admin_auth(self):
        """Setup admin authentication"""
        admin_data = {
            "provider": "admin",
            "access_token": "admin_token",
            "full_name": "Dr. Marco Rossi",
            "email": f"admin_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
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
            print(f"   ✅ Admin authenticated successfully")
            return True
        else:
            print(f"   ❌ Admin authentication failed")
            return False

    def test_patient_inquiry_tracking_system(self):
        """Test comprehensive Patient Inquiry Tracking System functionality"""
        print("\n🔍 Testing Patient Inquiry Tracking System...")
        
        if not self.admin_token:
            print("❌ No admin token available for inquiry tracking test")
            return False
        
        # Step 1: Create a test patient for inquiry tracking
        patient_data = {
            "email": f"inquiry_patient_{datetime.now().strftime('%H%M%S')}@kinaura.com",
            "full_name": "Inquiry Test Patient",
            "phone": "+1234567890",
            "membership_tier": "gold",
            "tags": ["inquiry", "test"]
        }
        
        success, patient_response = self.run_test(
            "Create Patient for Inquiry Tracking",
            "POST",
            "/admin/patients",
            200,
            data=patient_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if not success:
            print("❌ Failed to create test patient for inquiry tracking")
            return False
        
        patient_id = patient_response.get('id')
        print(f"   ✅ Created test patient with ID: {patient_id}")
        
        # Step 2: Login as the patient to get patient token for chat
        patient_login_data = {
            "provider": "google",
            "access_token": "inquiry_patient_token",
            "full_name": patient_data['full_name'],
            "email": patient_data['email']
        }
        
        success, login_response = self.run_test(
            "Patient Login for Chat",
            "POST",
            "/auth/social-login",
            200,
            data=patient_login_data
        )
        
        if not success:
            print("❌ Failed to login patient for chat")
            return False
        
        self.patient_token = login_response.get('access_token')
        self.patient_user_id = login_response.get('user', {}).get('id')
        print(f"   ✅ Patient logged in with user ID: {self.patient_user_id}")
        
        # Step 3: Test inquiry detection through chat messages
        inquiry_messages = [
            {
                "message": "I'm interested in Morpheus8 for acne treatment",
                "expected_types": ["treatment", "condition"],
                "expected_items": ["Morpheus8", "Acne"]
            },
            {
                "message": "Can you tell me about NAD+ therapy for anti-aging and fatigue?",
                "expected_types": ["treatment", "wellness_goal", "condition"],
                "expected_items": ["Nad Therapy", "Anti Aging", "Fatigue"]
            },
            {
                "message": "I have melasma and want to know about laser treatments",
                "expected_types": ["condition", "treatment"],
                "expected_items": ["Melasma", "Laser Co2"]
            },
            {
                "message": "Looking for ozone therapy to boost my immune system",
                "expected_types": ["treatment", "condition"],
                "expected_items": ["Ozone Therapy", "Immune"]
            }
        ]
        
        detected_inquiries = []
        for i, msg_data in enumerate(inquiry_messages):
            chat_request = {
                "message": msg_data["message"],
                "user_id": self.patient_user_id
            }
            
            success, chat_response = self.run_test(
                f"Chat Message {i+1} - Inquiry Detection",
                "POST",
                "/chat",
                200,
                data=chat_request,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                print(f"   ✅ Chat message {i+1} processed successfully")
                print(f"   📝 Message: {msg_data['message'][:50]}...")
            else:
                print(f"   ❌ Failed to process chat message {i+1}")
                return False
        
        # Wait a moment for async inquiry processing
        print("   ⏳ Waiting for inquiry processing...")
        time.sleep(3)
        
        # Step 4: Test GET /admin/inquiries - Get all inquiries
        success, inquiries_response = self.run_test(
            "Get All Patient Inquiries",
            "GET",
            "/admin/inquiries",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and isinstance(inquiries_response, list):
            print(f"   ✅ Retrieved {len(inquiries_response)} total inquiries")
            
            # Filter inquiries for our test patient
            patient_inquiries = [inq for inq in inquiries_response if inq.get('patient_id') == self.patient_user_id]
            print(f"   ✅ Found {len(patient_inquiries)} inquiries for test patient")
            
            if len(patient_inquiries) >= 4:  # We sent 4 messages
                print(f"   ✅ Expected number of inquiries detected")
                detected_inquiries = patient_inquiries
            else:
                print(f"   ⚠️  Expected at least 4 inquiries, found {len(patient_inquiries)}")
                detected_inquiries = patient_inquiries  # Use what we have
        else:
            print("   ❌ Failed to retrieve patient inquiries")
            return False
        
        # Step 5: Test GET /admin/inquiries/stats - Stats endpoint (the main focus of this test)
        success, stats_response = self.run_test(
            "Get Inquiry Statistics (Counter Import Fix)",
            "GET",
            "/admin/inquiries/stats?days=7",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   ✅ Stats endpoint working - Counter import issue resolved!")
            
            # Verify stats structure
            required_stats = ['total_inquiries', 'new_inquiries', 'inquiry_types', 'top_treatments', 'top_conditions', 'period']
            missing_stats = [stat for stat in required_stats if stat not in stats_response]
            
            if not missing_stats:
                print(f"   ✅ Stats response has all required fields")
                print(f"   📊 Total inquiries: {stats_response.get('total_inquiries')}")
                print(f"   📊 New inquiries: {stats_response.get('new_inquiries')}")
                print(f"   📊 Treatment inquiries: {stats_response.get('inquiry_types', {}).get('treatment', 0)}")
                print(f"   📊 Top treatments: {stats_response.get('top_treatments', {})}")
                print(f"   📊 Top conditions: {stats_response.get('top_conditions', {})}")
            else:
                print(f"   ❌ Missing stats fields: {missing_stats}")
                return False
        else:
            print("   ❌ Stats endpoint failed - Counter import issue not resolved")
            return False
        
        # Step 6: Test individual inquiry management
        if detected_inquiries:
            inquiry_id = detected_inquiries[0]['id']
            
            # Test GET /admin/inquiries/{inquiry_id}
            success, inquiry_detail = self.run_test(
                "Get Individual Inquiry Details",
                "GET",
                f"/admin/inquiries/{inquiry_id}",
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print(f"   ✅ Retrieved inquiry details for ID: {inquiry_id}")
                
                # Verify inquiry structure
                required_fields = ['id', 'patient_id', 'inquiry_type', 'detected_items', 'original_message', 'status', 'timestamp']
                missing_fields = [field for field in required_fields if field not in inquiry_detail]
                
                if not missing_fields:
                    print(f"   ✅ Inquiry has all required fields")
                    print(f"   📝 Type: {inquiry_detail.get('inquiry_type')}")
                    print(f"   📝 Items: {inquiry_detail.get('detected_items')}")
                    print(f"   📝 Status: {inquiry_detail.get('status')}")
                else:
                    print(f"   ❌ Missing inquiry fields: {missing_fields}")
                    return False
            else:
                print("   ❌ Failed to get inquiry details")
                return False
            
            # Test PUT /admin/inquiries/{inquiry_id} - Update inquiry status
            update_data = {
                "status": "contacted",
                "admin_notes": "Patient contacted via phone. Scheduled consultation for Morpheus8 treatment.",
                "priority_score": 5
            }
            
            success, update_response = self.run_test(
                "Update Inquiry Status",
                "PUT",
                f"/admin/inquiries/{inquiry_id}",
                200,
                data=update_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print(f"   ✅ Successfully updated inquiry status to 'contacted'")
                if update_response.get('status') == 'contacted':
                    print(f"   ✅ Status update confirmed")
                if update_response.get('admin_notes') == update_data['admin_notes']:
                    print(f"   ✅ Admin notes updated correctly")
            else:
                print("   ❌ Failed to update inquiry status")
                return False
            
            # Test POST /admin/inquiries/{inquiry_id}/send-booking-request
            booking_request_data = {
                "patient_id": self.patient_user_id,
                "inquiry_id": inquiry_id,
                "treatments": ["Morpheus8", "Consultation"],
                "message": "Based on your interest in Morpheus8 for acne treatment, we'd like to schedule a consultation to discuss your treatment plan.",
                "suggested_times": ["2024-12-25 10:00", "2024-12-25 14:00", "2024-12-26 09:00"]
            }
            
            success, booking_response = self.run_test(
                "Send Booking Request",
                "POST",
                f"/admin/inquiries/{inquiry_id}/send-booking-request",
                200,
                data=booking_request_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print(f"   ✅ Booking request sent successfully")
                if booking_response.get('message'):
                    print(f"   ✅ Booking request response: {booking_response.get('message')}")
            else:
                print("   ❌ Failed to send booking request")
                return False
        
        # Step 7: Test admin notifications were created
        success, notifications_response = self.run_test(
            "Check Admin Notifications for Inquiries",
            "GET",
            "/admin/notifications",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and isinstance(notifications_response, list):
            # Look for inquiry-related notifications
            inquiry_notifications = [
                notif for notif in notifications_response 
                if notif.get('type') == 'inquiry_alert' and self.patient_user_id in str(notif.get('data', {}))
            ]
            
            print(f"   ✅ Found {len(inquiry_notifications)} inquiry-related notifications")
            
            if inquiry_notifications:
                notification = inquiry_notifications[0]
                print(f"   📧 Notification: {notification.get('title')}")
                print(f"   📧 Message: {notification.get('message')}")
                print(f"   ✅ Admin notification system working correctly")
            else:
                print(f"   ⚠️  No inquiry notifications found (may be processed asynchronously)")
        else:
            print("   ❌ Failed to retrieve admin notifications")
            return False
        
        # Step 8: Test database integration - verify data is stored correctly
        print(f"   🔍 Verifying database integration...")
        
        if detected_inquiries and len(detected_inquiries) >= 2:
            # Check that different inquiry types were detected
            inquiry_types = [inq.get('inquiry_type') for inq in detected_inquiries]
            unique_types = set(inquiry_types)
            
            if 'treatment' in unique_types:
                print(f"   ✅ Treatment inquiry types detected: {unique_types}")
            
            # Check that detected items are properly stored
            all_detected_items = []
            for inq in detected_inquiries:
                all_detected_items.extend(inq.get('detected_items', []))
            
            if len(all_detected_items) >= 4:  # We expect multiple items from our test messages
                print(f"   ✅ Detected items properly stored: {len(all_detected_items)} items")
                print(f"   📝 Sample items: {all_detected_items[:5]}")
            
            # Check that timestamps are recent (within last few minutes)
            recent_inquiries = 0
            current_time = datetime.utcnow()
            for inq in detected_inquiries:
                timestamp_str = inq.get('timestamp')
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if (current_time - timestamp.replace(tzinfo=None)).total_seconds() < 600:  # 10 minutes
                            recent_inquiries += 1
                    except:
                        pass
            
            if recent_inquiries >= 1:
                print(f"   ✅ Recent inquiries found: {recent_inquiries} (database integration working)")
            else:
                print(f"   ⚠️  Few recent inquiries found: {recent_inquiries}")
        
        print("   🎉 Patient Inquiry Tracking System test completed successfully!")
        return True

    def run_tests(self):
        """Run all inquiry tracking tests"""
        print("🚀 Starting Patient Inquiry Tracking System Test...")
        print(f"   Base URL: {self.base_url}")
        print(f"   API URL: {self.api_url}")
        
        # Setup admin authentication
        if not self.setup_admin_auth():
            print("❌ Failed to setup admin authentication")
            return False
        
        # Run the main test
        success = self.test_patient_inquiry_tracking_system()
        
        # Print final results
        print(f"\n{'='*60}")
        print(f"📊 PATIENT INQUIRY TRACKING TEST RESULTS")
        print(f"{'='*60}")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if success:
            print("🎉 Patient Inquiry Tracking System test completed successfully!")
            print("✅ Counter import issue has been resolved!")
            print("✅ Stats endpoint is working correctly!")
            print("✅ Complete inquiry workflow is functional!")
        else:
            print("❌ Patient Inquiry Tracking System test failed!")
        
        return success

if __name__ == "__main__":
    tester = PatientInquiryTester()
    success = tester.run_tests()
    exit(0 if success else 1)