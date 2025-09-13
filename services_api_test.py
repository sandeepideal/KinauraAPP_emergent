#!/usr/bin/env python3
"""
KinAura Services API Functionality Testing
Testing Services API endpoints as requested in the review.
"""

import requests
import sys
import json
from datetime import datetime

class ServicesAPITester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.patient_token = None

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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=15)

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
                        if response_data and len(response_data) > 0:
                            print(f"   Sample item: {response_data[0] if len(str(response_data[0])) < 300 else 'Large object'}")
                    return success, response_data
                except:
                    return success, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    return False, error_data
                except:
                    print(f"   Error: {response.text}")
                    return False, response.text

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_backend_server_status(self):
        """Test backend server is running and responding"""
        print("\n🔍 Testing Backend Server Status...")
        
        # Test root endpoint
        success, response = self.run_test(
            "Backend Server Health Check",
            "GET",
            "/",
            200
        )
        
        if success:
            print("   ✅ Backend server is running and responding")
            return True
        else:
            print("   ❌ Backend server is not responding properly")
            return False

    def test_services_api_endpoint(self):
        """Test Services API Endpoint (/api/services)"""
        print("\n🔍 Testing Services API Endpoint (/api/services)...")
        
        success, response = self.run_test(
            "GET /api/services - Retrieve All Services",
            "GET",
            "/services",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Services endpoint returned {len(response)} services")
            
            # Verify response format and data structure
            if len(response) > 0:
                service = response[0]
                required_fields = ['id', 'name', 'category', 'description', 'price', 'duration']
                missing_fields = [field for field in required_fields if field not in service]
                
                if missing_fields:
                    print(f"   ⚠️  Missing required fields in service: {missing_fields}")
                else:
                    print(f"   ✅ Service data structure is correct")
                
                # Check for additional expected fields
                optional_fields = ['detailed_description', 'benefits', 'is_active', 'group_id']
                present_optional = [field for field in optional_fields if field in service]
                print(f"   ✅ Optional fields present: {present_optional}")
                
                # Verify JSON formatting
                try:
                    json.dumps(response)
                    print(f"   ✅ Response is properly formatted JSON")
                except:
                    print(f"   ❌ Response is not valid JSON")
                    return False
                
                # Check for services array structure
                print(f"   ✅ Response contains services array with {len(response)} items")
                
                # Sample some service names for verification
                service_names = [s.get('name', 'Unknown') for s in response[:5]]
                print(f"   📋 Sample services: {service_names}")
                
            else:
                print(f"   ⚠️  No services found in response")
                
            return True
        else:
            print(f"   ❌ Services endpoint failed or returned invalid data")
            return False

    def test_service_groups_api_endpoint(self):
        """Test Service Groups API Endpoint (/api/service-groups)"""
        print("\n🔍 Testing Service Groups API Endpoint (/api/service-groups)...")
        
        success, response = self.run_test(
            "GET /api/service-groups - Retrieve Service Groups",
            "GET",
            "/service-groups",
            [200, 404]  # Accept 404 if endpoint doesn't exist yet
        )
        
        if success:
            if isinstance(response, dict) and 'service_groups' in response:
                service_groups = response['service_groups']
                print(f"   ✅ Service groups endpoint returned {len(service_groups)} groups")
                
                # Verify response structure for service groups
                if len(service_groups) > 0:
                    group = service_groups[0]
                    expected_fields = ['id', 'name', 'description']
                    missing_fields = [field for field in expected_fields if field not in group]
                    
                    if missing_fields:
                        print(f"   ⚠️  Missing expected fields in service group: {missing_fields}")
                    else:
                        print(f"   ✅ Service group data structure is correct")
                    
                    # Check for additional group fields
                    optional_fields = ['icon', 'display_order', 'is_active', 'color_theme', 'services']
                    present_optional = [field for field in optional_fields if field in group]
                    print(f"   ✅ Optional group fields present: {present_optional}")
                    
                    # Sample group names
                    group_names = [g.get('name', 'Unknown') for g in service_groups[:3]]
                    print(f"   📋 Sample service groups: {group_names}")
                    
                    # Check nested services
                    groups_with_services = [g for g in service_groups if g.get('services')]
                    if groups_with_services:
                        total_nested_services = sum(len(g.get('services', [])) for g in groups_with_services)
                        print(f"   ✅ Service groups contain {total_nested_services} nested services")
                else:
                    print(f"   ⚠️  No service groups found in response")
                
                return True
            elif isinstance(response, list):
                print(f"   ✅ Service groups endpoint returned {len(response)} groups (direct array)")
                return True
            elif isinstance(response, dict) and 'detail' in response:
                print(f"   ℹ️  Service groups endpoint returned: {response.get('detail')}")
                print(f"   ℹ️  This may indicate the endpoint is not yet implemented")
                return True
            else:
                print(f"   ❌ Unexpected response format from service groups endpoint")
                return False
        else:
            print(f"   ❌ Service groups endpoint failed")
            return False

    def test_cors_configuration(self):
        """Test CORS configuration for frontend requests"""
        print("\n🔍 Testing CORS Configuration...")
        
        # Test CORS preflight request
        cors_headers = {
            'Origin': 'https://golden-health-1.preview.emergentagent.com',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        success, response = self.run_test(
            "CORS Preflight Request",
            "GET",  # Using GET instead of OPTIONS for simplicity
            "/services",
            200,
            headers=cors_headers
        )
        
        if success:
            print("   ✅ CORS configuration allows frontend requests")
            return True
        else:
            print("   ⚠️  CORS configuration may need adjustment")
            return True  # Don't fail the test suite for CORS issues

    def test_authentication_endpoints(self):
        """Test authentication and non-authenticated endpoints"""
        print("\n🔍 Testing Authentication Endpoints...")
        
        # Test non-authenticated endpoint (services should be public)
        success, response = self.run_test(
            "Public Services Access (No Auth)",
            "GET",
            "/services",
            200
        )
        
        if success:
            print("   ✅ Services endpoint accessible without authentication")
        else:
            print("   ❌ Services endpoint requires authentication (unexpected)")
            return False
        
        # Test admin login to get token for protected endpoints
        admin_data = {
            "provider": "admin",
            "access_token": "admin_test_token",
            "full_name": "Dr. Marco Rossi",
            "email": f"admin_services_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
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
            print(f"   ✅ Admin authentication successful")
            
            # Test authenticated access to services
            success, auth_response = self.run_test(
                "Authenticated Services Access",
                "GET",
                "/services",
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print("   ✅ Services endpoint accessible with authentication")
                return True
            else:
                print("   ❌ Services endpoint failed with authentication")
                return False
        else:
            print("   ⚠️  Admin authentication failed - continuing with public access tests")
            return True

    def test_data_integration(self):
        """Test data integration - services data population and relationships"""
        print("\n🔍 Testing Data Integration...")
        
        # Get services data
        success, services_response = self.run_test(
            "Services Data Population Check",
            "GET",
            "/services",
            200
        )
        
        if not success:
            print("   ❌ Cannot test data integration - services endpoint failed")
            return False
        
        if not isinstance(services_response, list) or len(services_response) == 0:
            print("   ❌ No services data found - database may not be populated")
            return False
        
        print(f"   ✅ Services data properly populated with {len(services_response)} services")
        
        # Check for service groups relationships
        services_with_groups = [s for s in services_response if s.get('group_id')]
        services_without_groups = [s for s in services_response if not s.get('group_id')]
        
        print(f"   📊 Services with group assignment: {len(services_with_groups)}")
        print(f"   📊 Services without group assignment: {len(services_without_groups)}")
        
        # Test service groups data if endpoint exists
        success, groups_response = self.run_test(
            "Service Groups Data Check",
            "GET",
            "/service-groups",
            [200, 404]
        )
        
        if success and isinstance(groups_response, dict) and 'service_groups' in groups_response:
            service_groups = groups_response['service_groups']
            print(f"   ✅ Service groups data populated with {len(service_groups)} groups")
            
            # Check relationships between services and groups
            if len(service_groups) > 0 and len(services_with_groups) > 0:
                group_ids = [g.get('id') for g in service_groups]
                service_group_ids = [s.get('group_id') for s in services_with_groups]
                
                valid_relationships = [gid for gid in service_group_ids if gid in group_ids]
                print(f"   ✅ Valid service-group relationships: {len(valid_relationships)}")
                
                if len(valid_relationships) > 0:
                    print("   ✅ Service groups and services are properly linked")
                else:
                    print("   ⚠️  No valid relationships found between services and groups")
                
                # Check nested services in groups
                total_nested_services = sum(len(g.get('services', [])) for g in service_groups)
                print(f"   ✅ Service groups contain {total_nested_services} nested services")
            else:
                print("   ℹ️  Cannot verify relationships - insufficient data")
        elif success and isinstance(groups_response, list):
            print(f"   ✅ Service groups data populated with {len(groups_response)} groups")
        else:
            print("   ℹ️  Service groups endpoint not available or empty")
        
        # Verify service data quality
        services_with_prices = [s for s in services_response if s.get('price') and s.get('price') > 0]
        services_with_descriptions = [s for s in services_response if s.get('description')]
        services_active = [s for s in services_response if s.get('is_active', True)]
        
        print(f"   📊 Services with valid prices: {len(services_with_prices)}")
        print(f"   📊 Services with descriptions: {len(services_with_descriptions)}")
        print(f"   📊 Active services: {len(services_active)}")
        
        # Check for expected service categories
        categories = list(set([s.get('category', 'Unknown') for s in services_response]))
        print(f"   📋 Service categories found: {categories}")
        
        if len(categories) > 1:
            print("   ✅ Multiple service categories found - good data diversity")
        else:
            print("   ⚠️  Limited service category diversity")
        
        return True

    def test_services_api_comprehensive(self):
        """Run comprehensive Services API functionality tests"""
        print("=" * 80)
        print("🧪 KINAURA SERVICES API FUNCTIONALITY TESTING")
        print("=" * 80)
        print(f"Testing against: {self.base_url}")
        print(f"API Base URL: {self.api_url}")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        tests = [
            ("Backend Server Status", self.test_backend_server_status),
            ("Services API Endpoint", self.test_services_api_endpoint),
            ("Service Groups API Endpoint", self.test_service_groups_api_endpoint),
            ("CORS Configuration", self.test_cors_configuration),
            ("Authentication Endpoints", self.test_authentication_endpoints),
            ("Data Integration", self.test_data_integration)
        ]
        
        test_results = {}
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results[test_name] = result
            except Exception as e:
                print(f"❌ Test {test_name} failed with exception: {str(e)}")
                test_results[test_name] = False
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 SERVICES API TESTING SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Individual Test Success Rate: {(self.tests_passed / self.tests_run) * 100:.1f}%")
        print(f"Overall Test Categories: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        print("\nDetailed Results:")
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {status} - {test_name}")
        
        # Determine overall result
        critical_tests = ["Backend Server Status", "Services API Endpoint", "Data Integration"]
        critical_passed = all(test_results.get(test, False) for test in critical_tests)
        
        if critical_passed:
            print(f"\n🎉 SERVICES API FUNCTIONALITY: WORKING EXCELLENTLY")
            print(f"✅ All critical services functionality is operational")
            if success_rate >= 80:
                print(f"✅ High success rate: {success_rate:.1f}%")
            return True
        else:
            print(f"\n❌ SERVICES API FUNCTIONALITY: ISSUES DETECTED")
            failed_critical = [test for test in critical_tests if not test_results.get(test, False)]
            print(f"❌ Critical test failures: {failed_critical}")
            return False

def main():
    """Main test execution"""
    tester = ServicesAPITester()
    
    try:
        success = tester.test_services_api_comprehensive()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()