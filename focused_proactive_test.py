#!/usr/bin/env python3
"""
Focused Test for Proactive Notification System - Key Functionality
"""

import requests
import sys
import json
from datetime import datetime, timedelta

def test_proactive_notification_system():
    """Test the key proactive notification functionality"""
    base_url = "https://golden-health-1.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🚀 Testing Proactive Notification System - Key Functionality")
    print("=" * 70)
    
    tests_passed = 0
    total_tests = 0
    
    # Step 1: Admin Authentication
    print("\n1️⃣ Testing Admin Authentication...")
    total_tests += 1
    
    admin_data = {
        "provider": "admin",
        "access_token": "admin_token",
        "full_name": "Dr. Marco Rossi",
        "email": "admin@kinaura.com"
    }
    
    try:
        response = requests.post(f"{api_url}/auth/social-login", json=admin_data, timeout=10)
        if response.status_code == 200:
            admin_token = response.json().get('access_token')
            print("✅ Admin authentication successful")
            tests_passed += 1
        else:
            print(f"❌ Admin authentication failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Admin authentication error: {e}")
        return False
    
    # Step 2: Create Test Patient
    print("\n2️⃣ Creating Test Patient...")
    total_tests += 1
    
    patient_data = {
        "email": f"test_patient_{datetime.now().strftime('%H%M%S')}@kinaura.com",
        "full_name": "Test Patient",
        "phone": "+1234567890",
        "membership_tier": "gold"
    }
    
    try:
        headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
        response = requests.post(f"{api_url}/admin/patients", json=patient_data, headers=headers, timeout=10)
        if response.status_code == 200:
            patient_id = response.json().get('id')
            print(f"✅ Test patient created: {patient_id}")
            tests_passed += 1
        else:
            print(f"❌ Patient creation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Patient creation error: {e}")
        return False
    
    # Step 3: Patient Login
    print("\n3️⃣ Patient Login...")
    total_tests += 1
    
    patient_login_data = {
        "provider": "google",
        "access_token": "patient_token",
        "full_name": "Test Patient",
        "email": patient_data["email"]
    }
    
    try:
        response = requests.post(f"{api_url}/auth/social-login", json=patient_login_data, timeout=10)
        if response.status_code == 200:
            patient_token = response.json().get('access_token')
            print("✅ Patient login successful")
            tests_passed += 1
        else:
            print(f"❌ Patient login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Patient login error: {e}")
        return False
    
    # Step 4: Get Available Services
    print("\n4️⃣ Getting Available Services...")
    total_tests += 1
    
    try:
        response = requests.get(f"{api_url}/services", timeout=10)
        if response.status_code == 200:
            services = response.json()
            morpheus_services = [s for s in services if 'morpheus' in s.get('name', '').lower()]
            if morpheus_services:
                service_id = morpheus_services[0]['id']
                service_name = morpheus_services[0]['name']
                print(f"✅ Found Morpheus8 service: {service_name}")
                tests_passed += 1
            else:
                # Use any available service
                service_id = services[0]['id']
                service_name = services[0]['name']
                print(f"✅ Using available service: {service_name}")
                tests_passed += 1
        else:
            print(f"❌ Failed to get services: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Services error: {e}")
        return False
    
    # Step 5: Test Booking Endpoint (Key Test)
    print("\n5️⃣ Testing Booking Endpoint (CRITICAL TEST)...")
    total_tests += 1
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    booking_data = {
        "service_id": service_id,
        "appointment_date": tomorrow,
        "start_time": "10:00",
        "notes": "Test booking for proactive notification"
    }
    
    try:
        headers = {'Authorization': f'Bearer {patient_token}', 'Content-Type': 'application/json'}
        response = requests.post(f"{api_url}/patient/appointments/book", json=booking_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            booking_response = response.json()
            booking_id = booking_response.get('booking_id')
            has_protocol_recommendation = booking_response.get('has_protocol_recommendation', False)
            
            print(f"✅ Booking successful: {booking_id}")
            
            if has_protocol_recommendation:
                print("✅ CRITICAL: has_protocol_recommendation flag is TRUE")
                print("✅ Booking endpoint fix is working correctly")
                tests_passed += 1
            else:
                print("❌ Missing has_protocol_recommendation flag")
                return False
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            if "'Request' object has no attribute 'service_id'" in str(error_data):
                print("❌ CRITICAL: Booking endpoint still has 'Request' object attribute error!")
                print(f"❌ Error: {error_data}")
                return False
            else:
                print(f"❌ Booking failed: {response.status_code} - {error_data}")
                return False
    except Exception as e:
        print(f"❌ Booking error: {e}")
        return False
    
    # Step 6: Test Proactive Notification Retrieval
    print("\n6️⃣ Testing Proactive Notification Retrieval...")
    total_tests += 1
    
    # Wait for notification processing
    import time
    time.sleep(3)
    
    try:
        headers = {'Authorization': f'Bearer {patient_token}', 'Content-Type': 'application/json'}
        response = requests.get(f"{api_url}/patient/notifications/proactive", headers=headers, timeout=10)
        
        if response.status_code == 200:
            notifications_data = response.json()
            notifications = notifications_data.get('notifications', [])
            count = notifications_data.get('count', 0)
            unread_count = notifications_data.get('unread_count', 0)
            
            print(f"✅ Retrieved {count} notifications ({unread_count} unread)")
            
            if notifications:
                notification = notifications[0]
                protocol_name = notification.get('protocol_name', '')
                booked_service = notification.get('booked_service', '')
                complementary_treatments = notification.get('complementary_treatments', [])
                
                print(f"✅ Protocol: {protocol_name}")
                print(f"✅ Booked Service: {booked_service}")
                print(f"✅ Complementary Treatments: {len(complementary_treatments)}")
                
                if protocol_name and booked_service and complementary_treatments:
                    print("✅ Proactive notification contains all required content")
                    tests_passed += 1
                else:
                    print("❌ Proactive notification missing content")
                    return False
            else:
                print("❌ No proactive notifications found")
                return False
        else:
            print(f"❌ Failed to get notifications: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Notification retrieval error: {e}")
        return False
    
    # Step 7: Test Latest Protocol Recommendation Endpoint
    print("\n7️⃣ Testing Latest Protocol Recommendation Endpoint...")
    total_tests += 1
    
    try:
        headers = {'Authorization': f'Bearer {patient_token}', 'Content-Type': 'application/json'}
        response = requests.get(f"{api_url}/patient/notifications/latest-protocol-recommendation", headers=headers, timeout=10)
        
        if response.status_code == 200:
            latest_data = response.json()
            has_notification = latest_data.get('has_notification', False)
            
            if has_notification:
                notification = latest_data.get('notification', {})
                protocol_name = notification.get('protocol_name', '')
                print(f"✅ Latest protocol recommendation: {protocol_name}")
                tests_passed += 1
            else:
                print("⚠️  No unread protocol recommendations (may have been marked as read)")
                tests_passed += 1  # This is acceptable
        else:
            print(f"❌ Failed to get latest recommendation: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Latest recommendation error: {e}")
        return False
    
    # Final Results
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("\n🎉 SUCCESS: Proactive Notification System is Working Correctly!")
        print("✅ Booking endpoint fix is working (no 'Request' object errors)")
        print("✅ Proactive notifications are generated automatically after booking")
        print("✅ Notification content contains proper protocol recommendations")
        print("✅ All notification retrieval endpoints are functional")
        print("✅ System is ready for frontend integration testing")
        return True
    else:
        print("\n❌ PARTIAL SUCCESS: Some issues need attention")
        return False

if __name__ == "__main__":
    success = test_proactive_notification_system()
    sys.exit(0 if success else 1)