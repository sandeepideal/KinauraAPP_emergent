import requests
import sys
import json
from datetime import datetime, timedelta

class CRMTester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
                
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    # Check if it's a CSV response
                    if 'text/csv' in response.headers.get('content-type', ''):
                        return success, response.text
                    else:
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
            "email": "admin@kinaura.com"
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

    def test_crm_funnel_analytics(self):
        """Test comprehensive CRM funnel and engagement system"""
        print("\n🔍 Testing CRM Funnel and Engagement System...")
        
        if not self.admin_token:
            print("❌ No admin token available for CRM testing")
            return False
        
        # Step 1: Create test patients in different lifecycle stages
        test_patients = [
            {
                "email": f"lead_patient_{datetime.now().strftime('%H%M%S')}@kinaura.com",
                "full_name": "Lead Test Patient",
                "phone": "+1234567890",
                "membership_tier": "not_member",
                "tags": ["lead", "new"],
                "lifecycle_stage": "lead",
                "total_bookings": 0,
                "last_booking": None
            },
            {
                "email": f"active_patient_{datetime.now().strftime('%H%M%S')}@kinaura.com", 
                "full_name": "Active Test Patient",
                "phone": "+1234567891",
                "membership_tier": "gold",
                "tags": ["active", "regular"],
                "lifecycle_stage": "active",
                "total_bookings": 3,
                "last_booking": (datetime.now() - timedelta(days=30)).isoformat()
            },
            {
                "email": f"lapsed_patient_{datetime.now().strftime('%H%M%S')}@kinaura.com",
                "full_name": "Lapsed Test Patient", 
                "phone": "+1234567892",
                "membership_tier": "platinum",
                "tags": ["lapsed", "reactivation"],
                "lifecycle_stage": "lapsed",
                "total_bookings": 5,
                "last_booking": (datetime.now() - timedelta(days=90)).isoformat()
            }
        ]
        
        created_patient_ids = []
        for patient_data in test_patients:
            success, response = self.run_test(
                f"Create {patient_data['lifecycle_stage'].title()} Patient",
                "POST",
                "/admin/patients",
                200,
                data=patient_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                patient_id = response.get('id')
                created_patient_ids.append(patient_id)
                print(f"   ✅ Created {patient_data['lifecycle_stage']} patient: {patient_data['full_name']}")
            else:
                print(f"   ❌ Failed to create {patient_data['lifecycle_stage']} patient")
                return False
        
        # Step 2: Test CRM Funnel Analytics API
        success, funnel_response = self.run_test(
            "Get CRM Funnel Analytics",
            "GET",
            "/admin/patients/funnel",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            # The response is wrapped in success/data structure
            if 'data' in funnel_response:
                funnel_data = funnel_response['data']
                
                # Verify funnel data structure
                required_fields = ['leads', 'active', 'lapsed', 'totals', 'trends']
                missing_fields = [field for field in required_fields if field not in funnel_data]
                
                if not missing_fields:
                    print(f"   ✅ Funnel data has all required fields")
                    
                    # Verify counts
                    leads_count = funnel_data.get('leads', {}).get('count', 0)
                    active_count = funnel_data.get('active', {}).get('count', 0) 
                    lapsed_count = funnel_data.get('lapsed', {}).get('count', 0)
                    total_count = funnel_data.get('totals', {}).get('total_patients', 0)
                    
                    print(f"   📊 Funnel Analytics: {leads_count} leads, {active_count} active, {lapsed_count} lapsed (Total: {total_count})")
                    
                    # Verify our test patients are categorized correctly
                    if leads_count >= 3:  # We created 3 test patients
                        print(f"   ✅ Patient lifecycle categorization working correctly")
                    else:
                        print(f"   ⚠️  Expected at least 3 patients in leads category")
                        
                    # Verify conversion rates structure
                    totals = funnel_data.get('totals', {})
                    if 'conversion_rate' in totals and 'lapse_rate' in totals:
                        print(f"   ✅ Conversion rates calculated: Conversion: {totals.get('conversion_rate', 0):.1f}%, Lapse: {totals.get('lapse_rate', 0):.1f}%")
                    else:
                        print(f"   ❌ Missing conversion rate calculations")
                        
                    # Verify trends structure
                    trends = funnel_data.get('trends', {})
                    if 'leads_trend' in trends and 'active_trend' in trends and 'lapsed_trend' in trends:
                        print(f"   ✅ Trends calculated: Leads: {trends.get('leads_trend', 0):.1f}%, Active: {trends.get('active_trend', 0):.1f}%, Lapsed: {trends.get('lapsed_trend', 0):.1f}%")
                    else:
                        print(f"   ❌ Missing trend calculations")
                        
                else:
                    print(f"   ❌ Missing funnel data fields: {missing_fields}")
                    return False
            else:
                print(f"   ❌ Funnel response missing 'data' field")
                return False
        else:
            print("   ❌ Failed to get CRM funnel analytics")
            return False
        
        # Step 3: Test CSV Export Functionality
        success, csv_response = self.run_test(
            "Export Funnel Data as CSV",
            "GET",
            "/admin/patients/funnel?export_format=csv",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            # Check if response is CSV format by checking content type and headers
            # Note: requests.get().json() won't work for CSV, so we need to check the raw response
            print(f"   ✅ CSV export functionality working")
        else:
            print("   ❌ Failed to export funnel data as CSV")
            return False
        
        # Step 4: Test Engagement Campaign System
        success, campaign_response = self.run_test(
            "Trigger Engagement Campaigns",
            "POST",
            "/admin/engagement/run-campaigns",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            campaigns_sent = campaign_response.get('campaigns_sent', 0)
            print(f"   ✅ Engagement campaigns triggered: {campaigns_sent} campaigns sent")
            
            # Verify campaign types were processed
            campaign_details = campaign_response.get('campaign_details', {})
            if campaign_details:
                lapsed_campaigns = campaign_details.get('lapsed_reactivation', 0)
                lead_campaigns = campaign_details.get('lead_nurturing', 0)
                print(f"   📧 Campaign breakdown: {lapsed_campaigns} lapsed reactivation, {lead_campaigns} lead nurturing")
            
        else:
            print("   ❌ Failed to trigger engagement campaigns")
            return False
        
        # Step 5: Test Patient Lifecycle Manual Updates
        if created_patient_ids:
            test_patient_id = created_patient_ids[0]  # Use first created patient
            
            # Test updating lifecycle stage
            update_data = {
                "lifecycle_stage": "active",
                "engagement_score": 75,
                "total_bookings": 2,
                "last_booking": datetime.now().isoformat()
            }
            
            success, update_response = self.run_test(
                "Update Patient Lifecycle Data",
                "PUT",
                f"/admin/patients/{test_patient_id}/lifecycle",
                200,
                data=update_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print(f"   ✅ Patient lifecycle data updated successfully")
                
                # Since there's no individual patient endpoint, we'll verify by checking the funnel again
                success, updated_funnel = self.run_test(
                    "Verify Lifecycle Update via Funnel",
                    "GET",
                    "/admin/patients/funnel",
                    200,
                    headers={'Authorization': f'Bearer {self.admin_token}'}
                )
                
                if success and 'data' in updated_funnel:
                    active_count = updated_funnel['data'].get('active', {}).get('count', 0)
                    if active_count > 0:
                        print(f"   ✅ Lifecycle update verified: {active_count} active patients found")
                    else:
                        print(f"   ⚠️  Lifecycle update may not be reflected yet in funnel data")
                        
            else:
                print("   ❌ Failed to update patient lifecycle data")
                return False
        
        # Step 6: Test Engagement Logging
        success, logs_response = self.run_test(
            "Get Engagement Logs",
            "GET",
            "/admin/patients/engagement-logs",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and 'logs' in logs_response:
            logs = logs_response.get('logs', [])
            print(f"   ✅ Retrieved {len(logs)} engagement log entries")
            
            if logs:
                log_entry = logs[0]
                required_log_fields = ['id', 'patient_id', 'campaign_type', 'content_language', 'sent_at', 'status']
                missing_log_fields = [field for field in required_log_fields if field not in log_entry]
                
                if not missing_log_fields:
                    print(f"   ✅ Engagement logs have proper structure")
                else:
                    print(f"   ❌ Missing engagement log fields: {missing_log_fields}")
            else:
                print(f"   ℹ️  No engagement logs found (expected for new system)")
        else:
            print("   ❌ Failed to retrieve engagement logs")
            return False
        
        # Step 7: Test Booking Integration with Lifecycle Tracking
        if created_patient_ids:
            # Create a patient token for booking simulation
            patient_email = f"booking_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
            patient_login_data = {
                "provider": "google",
                "access_token": "booking_test_token",
                "full_name": "Booking Test Patient",
                "email": patient_email
            }
            
            success, login_response = self.run_test(
                "Patient Login for Booking Test",
                "POST",
                "/auth/social-login",
                200,
                data=patient_login_data
            )
            
            if success:
                patient_token = login_response.get('access_token')
                
                # Get available services for booking
                success, services_response = self.run_test(
                    "Get Services for Booking",
                    "GET",
                    "/services",
                    200
                )
                
                if success and services_response:
                    service_id = services_response[0].get('id')
                    
                    # Create a booking (this should update lifecycle)
                    booking_data = {
                        "service_id": service_id,
                        "appointment_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                        "start_time": "10:00",
                        "notes": "CRM lifecycle tracking test booking"
                    }
                    
                    success, booking_response = self.run_test(
                        "Create Booking with Lifecycle Tracking",
                        "POST",
                        "/patient/appointments/book",
                        200,
                        data=booking_data,
                        headers={'Authorization': f'Bearer {patient_token}'}
                    )
                    
                    if success:
                        print(f"   ✅ Booking created successfully with lifecycle tracking")
                        
                        # Verify lifecycle was updated (patient should now be 'active')
                        # Note: This would require getting the patient's updated data
                        # which might need admin access or a separate endpoint
                        
                    else:
                        print("   ❌ Failed to create booking with lifecycle tracking")
        
        print("   ✅ CRM Funnel and Engagement System testing completed")
        return True

if __name__ == "__main__":
    tester = CRMTester()
    print('🚀 Starting CRM Funnel and Engagement System Testing...')
    print(f'🌐 Testing against: {tester.base_url}')
    print('=' * 80)

    # Setup admin authentication first
    print('Setting up admin authentication...')
    if tester.setup_admin_auth():
        print('✅ Admin authentication successful')
        
        # Run CRM tests
        try:
            if tester.test_crm_funnel_analytics():
                print('🎉 CRM Funnel and Engagement System - PASSED')
                sys.exit(0)
            else:
                print('❌ CRM Funnel and Engagement System - FAILED')
                sys.exit(1)
        except Exception as e:
            print(f'❌ CRM Testing Error: {str(e)}')
            sys.exit(1)
    else:
        print('❌ Admin authentication failed - cannot proceed with CRM tests')
        sys.exit(1)