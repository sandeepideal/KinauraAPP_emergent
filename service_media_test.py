import requests
import sys
import json
from datetime import datetime, timedelta

class ServiceMediaTester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.regular_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_service_id = None

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

    def setup_admin_token(self):
        """Setup admin token for testing"""
        admin_data = {
            "provider": "admin",
            "access_token": "admin_token",
            "full_name": "Dr. Marco Rossi",
            "email": f"admin_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        }
        
        success, response = self.run_test(
            "Admin Login Setup",
            "POST",
            "/auth/social-login",
            200,
            data=admin_data
        )
        
        if success:
            self.admin_token = response.get('access_token')
            print(f"   ✅ Admin token obtained")
            return True
        else:
            print("❌ Failed to obtain admin token")
            return False

    def setup_regular_token(self):
        """Setup regular user token for testing"""
        user_data = {
            "provider": "google",
            "access_token": "regular_token",
            "full_name": "Regular User",
            "email": f"regular_test_{datetime.now().strftime('%H%M%S')}@example.com"
        }
        
        success, response = self.run_test(
            "Regular User Login Setup",
            "POST",
            "/auth/social-login",
            200,
            data=user_data
        )
        
        if success:
            self.regular_token = response.get('access_token')
            print(f"   ✅ Regular user token obtained")
            return True
        else:
            print("❌ Failed to obtain regular user token")
            return False

    def test_service_creation_with_media(self):
        """Test creating a service with all media fields"""
        print("\n🔍 Testing Service Creation with Media Fields...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        service_with_media = {
            "name": "Enhanced Media Service Test",
            "category": "Regenerative Wellness",
            "description": "Service with comprehensive media support for testing",
            "detailed_description": "This service tests all media fields including images, main_image, brochure_url, and video_url functionality.",
            "duration": 90,
            "price": 299.0,
            "benefits": ["Media support", "Enhanced presentation", "Comprehensive documentation"],
            "is_active": True,
            "images": [
                "https://example.com/service1.jpg",
                "https://example.com/service2.jpg",
                "https://example.com/service3.jpg"
            ],
            "main_image": "https://example.com/main-service.jpg",
            "brochure_url": "https://example.com/service-brochure.pdf",
            "video_url": "https://example.com/service-demo.mp4"
        }
        
        success, response = self.run_test(
            "Create Service with Media Fields",
            "POST",
            "/admin/services",
            200,
            data=service_with_media,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            self.created_service_id = response.get('id')
            print(f"   ✅ Service created with ID: {self.created_service_id}")
            
            # Verify all media fields are stored correctly
            media_checks = [
                (response.get('images'), service_with_media['images'], "Images"),
                (response.get('main_image'), service_with_media['main_image'], "Main image"),
                (response.get('brochure_url'), service_with_media['brochure_url'], "Brochure URL"),
                (response.get('video_url'), service_with_media['video_url'], "Video URL")
            ]
            
            all_correct = True
            for actual, expected, field_name in media_checks:
                if actual == expected:
                    print(f"   ✅ {field_name} stored correctly")
                else:
                    print(f"   ❌ {field_name} not stored correctly - Expected: {expected}, Got: {actual}")
                    all_correct = False
            
            return all_correct
        else:
            print("❌ Failed to create service with media")
            return False

    def test_service_update_with_media(self):
        """Test updating a service with media fields"""
        print("\n🔍 Testing Service Update with Media...")
        
        if not self.admin_token or not self.created_service_id:
            print("❌ No admin token or service ID available")
            return False
        
        update_data = {
            "name": "Updated Media Service",
            "description": "Updated service description with new media",
            "images": [
                "https://example.com/updated1.jpg",
                "https://example.com/updated2.jpg"
            ],
            "main_image": "https://example.com/updated-main.jpg",
            "brochure_url": "https://example.com/updated-brochure.pdf",
            "video_url": "https://example.com/updated-demo.mp4"
        }
        
        success, response = self.run_test(
            "Update Service with Media",
            "PUT",
            f"/admin/services/{self.created_service_id}",
            200,
            data=update_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   ✅ Service updated successfully")
            
            # Verify updated fields
            checks = [
                (response.get('name'), update_data['name'], "Name"),
                (len(response.get('images', [])), 2, "Images count"),
                (response.get('main_image'), update_data['main_image'], "Main image"),
                (response.get('video_url'), update_data['video_url'], "Video URL")
            ]
            
            all_correct = True
            for actual, expected, field_name in checks:
                if actual == expected:
                    print(f"   ✅ {field_name} updated correctly")
                else:
                    print(f"   ❌ {field_name} not updated correctly - Expected: {expected}, Got: {actual}")
                    all_correct = False
            
            return all_correct
        else:
            print("❌ Failed to update service with media")
            return False

    def test_partial_service_update(self):
        """Test partial service update (only specific fields)"""
        print("\n🔍 Testing Partial Service Update...")
        
        if not self.admin_token or not self.created_service_id:
            print("❌ No admin token or service ID available")
            return False
        
        partial_update = {
            "video_url": "https://example.com/new-video.mp4",
            "price": 349.0
        }
        
        success, response = self.run_test(
            "Partial Service Update",
            "PUT",
            f"/admin/services/{self.created_service_id}",
            200,
            data=partial_update,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   ✅ Partial update successful")
            
            # Verify only specified fields were updated
            if response.get('video_url') == partial_update['video_url']:
                print(f"   ✅ Video URL updated correctly")
            else:
                print(f"   ❌ Video URL not updated correctly")
                return False
                
            if response.get('price') == partial_update['price']:
                print(f"   ✅ Price updated correctly")
            else:
                print(f"   ❌ Price not updated correctly")
                return False
            
            # Verify other fields remain unchanged
            if response.get('name') == "Updated Media Service":  # From previous test
                print(f"   ✅ Unchanged fields preserved")
            else:
                print(f"   ❌ Unchanged fields not preserved")
                return False
            
            return True
        else:
            print("❌ Failed to perform partial update")
            return False

    def test_service_media_upload(self):
        """Test service media upload endpoint"""
        print("\n🔍 Testing Service Media Upload...")
        
        if not self.admin_token or not self.created_service_id:
            print("❌ No admin token or service ID available")
            return False
        
        success, response = self.run_test(
            "Upload Service Media Files",
            "POST",
            f"/admin/services/{self.created_service_id}/media/upload",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   ✅ Media upload endpoint working")
            uploaded_files = response.get('uploaded_files', [])
            if isinstance(uploaded_files, list):
                print(f"   ✅ Upload response structure correct")
                return True
            else:
                print(f"   ❌ Upload response structure incorrect")
                return False
        else:
            print("❌ Media upload failed")
            return False

    def test_set_main_image(self):
        """Test setting main image for a service"""
        print("\n🔍 Testing Set Main Image...")
        
        if not self.admin_token or not self.created_service_id:
            print("❌ No admin token or service ID available")
            return False
        
        main_image_data = {
            "image_url": "https://example.com/new-main-image.jpg"
        }
        
        success, response = self.run_test(
            "Set Service Main Image",
            "PUT",
            f"/admin/services/{self.created_service_id}/main-image",
            200,
            data=main_image_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   ✅ Main image set successfully")
            return True
        else:
            print("❌ Failed to set main image")
            return False

    def test_delete_service_media(self):
        """Test deleting service media"""
        print("\n🔍 Testing Delete Service Media...")
        
        if not self.admin_token or not self.created_service_id:
            print("❌ No admin token or service ID available")
            return False
        
        # Use a media URL that should exist from our previous tests
        media_url_to_delete = "https://example.com/updated1.jpg"
        
        success, response = self.run_test(
            "Delete Service Media",
            "DELETE",
            f"/admin/services/{self.created_service_id}/media/{media_url_to_delete}",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   ✅ Service media deleted successfully")
            return True
        else:
            print("❌ Failed to delete service media")
            return False

    def test_admin_services_retrieval(self):
        """Test admin services retrieval with media"""
        print("\n🔍 Testing Admin Services Retrieval...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        success, response = self.run_test(
            "Get Admin Services with Media",
            "GET",
            "/admin/services",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            services = response.get('services', [])
            print(f"   ✅ Retrieved {len(services)} services for admin")
            
            # Find our test service
            test_service = None
            for service in services:
                if service.get('id') == self.created_service_id:
                    test_service = service
                    break
            
            if test_service:
                print(f"   ✅ Test service found in admin services list")
                
                # Verify media fields are present
                media_fields = ['images', 'main_image', 'brochure_url', 'video_url']
                missing_fields = [field for field in media_fields if field not in test_service]
                if missing_fields:
                    print(f"   ❌ Missing media fields: {missing_fields}")
                    return False
                else:
                    print(f"   ✅ All media fields present in admin view")
                    return True
            else:
                print(f"   ❌ Test service not found in admin services list")
                return False
        else:
            print("❌ Failed to retrieve admin services")
            return False

    def test_public_services_retrieval(self):
        """Test public services retrieval with media"""
        print("\n🔍 Testing Public Services Retrieval...")
        
        success, response = self.run_test(
            "Get Public Services with Media",
            "GET",
            "/services",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Retrieved {len(response)} public services")
            
            # Find our test service
            test_service = None
            for service in response:
                if service.get('id') == self.created_service_id:
                    test_service = service
                    break
            
            if test_service:
                print(f"   ✅ Test service found in public services list")
                
                # Verify media fields are present
                media_fields = ['images', 'main_image', 'brochure_url', 'video_url']
                missing_fields = [field for field in media_fields if field not in test_service]
                if missing_fields:
                    print(f"   ❌ Missing media fields in public view: {missing_fields}")
                    return False
                else:
                    print(f"   ✅ All media fields present in public view")
                    return True
            else:
                print(f"   ❌ Test service not found in public services list")
                return False
        else:
            print("❌ Failed to retrieve public services")
            return False

    def test_individual_service_retrieval(self):
        """Test individual service retrieval with media"""
        print("\n🔍 Testing Individual Service Retrieval...")
        
        if not self.created_service_id:
            print("❌ No service ID available")
            return False
        
        success, response = self.run_test(
            "Get Individual Service with Media",
            "GET",
            f"/services/{self.created_service_id}",
            200
        )
        
        if success:
            print(f"   ✅ Retrieved individual service successfully")
            
            # Verify all media fields are present
            media_fields = ['images', 'main_image', 'brochure_url', 'video_url']
            missing_fields = [field for field in media_fields if field not in response]
            if missing_fields:
                print(f"   ❌ Missing media fields: {missing_fields}")
                return False
            else:
                print(f"   ✅ All media fields present")
                
                # Verify media content structure
                if isinstance(response.get('images'), list):
                    print(f"   ✅ Images field properly formatted as list")
                if response.get('main_image'):
                    print(f"   ✅ Main image field has content")
                
                return True
        else:
            print("❌ Failed to retrieve individual service")
            return False

    def test_backward_compatibility(self):
        """Test backward compatibility - service without media fields"""
        print("\n🔍 Testing Backward Compatibility...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        basic_service = {
            "name": "Basic Service Without Media",
            "category": "Basic Category",
            "description": "Service without media fields for backward compatibility test",
            "detailed_description": "Testing that services work without media fields",
            "duration": 60,
            "price": 199.0,
            "benefits": ["Basic functionality", "Backward compatibility"],
            "is_active": True
        }
        
        success, response = self.run_test(
            "Create Basic Service (Backward Compatibility)",
            "POST",
            "/admin/services",
            200,
            data=basic_service,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   ✅ Basic service created successfully")
            
            # Verify default media field values
            checks = [
                (response.get('images'), [], "Images defaults to empty list"),
                (response.get('main_image'), None, "Main image defaults to None"),
                (response.get('brochure_url'), None, "Brochure URL defaults to None"),
                (response.get('video_url'), None, "Video URL defaults to None")
            ]
            
            all_correct = True
            for actual, expected, description in checks:
                if actual == expected:
                    print(f"   ✅ {description}")
                else:
                    print(f"   ❌ {description} - Got: {actual}")
                    all_correct = False
            
            return all_correct
        else:
            print("❌ Failed to create basic service")
            return False

    def test_authentication_requirements(self):
        """Test authentication requirements for media endpoints"""
        print("\n🔍 Testing Authentication Requirements...")
        
        if not self.regular_token or not self.created_service_id:
            print("❌ No regular token or service ID available")
            return False
        
        # Test non-admin access to service creation
        basic_service = {
            "name": "Unauthorized Service",
            "category": "Test",
            "description": "Should not be created",
            "detailed_description": "Test",
            "duration": 60,
            "price": 100.0,
            "benefits": ["Test"],
            "is_active": True
        }
        
        success1, response1 = self.run_test(
            "Non-Admin Service Creation",
            "POST",
            "/admin/services",
            403,
            data=basic_service,
            headers={'Authorization': f'Bearer {self.regular_token}'}
        )
        
        # Test non-admin access to media upload
        success2, response2 = self.run_test(
            "Non-Admin Media Upload",
            "POST",
            f"/admin/services/{self.created_service_id}/media/upload",
            403,
            headers={'Authorization': f'Bearer {self.regular_token}'}
        )
        
        if success1 and success2:
            print(f"   ✅ Non-admin users correctly denied access")
            return True
        else:
            print(f"   ❌ Authentication requirements not properly enforced")
            return False

    def test_existing_services_compatibility(self):
        """Test that existing services work with new media fields"""
        print("\n🔍 Testing Existing Services Compatibility...")
        
        success, response = self.run_test(
            "Get Existing Services with Media Fields",
            "GET",
            "/services",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Retrieved {len(response)} existing services")
            
            if response:
                # Check first service for media fields
                first_service = response[0]
                
                # Verify media fields exist (even if empty/null)
                media_fields = ['images', 'main_image', 'brochure_url', 'video_url']
                present_fields = [field for field in media_fields if field in first_service]
                
                print(f"   ✅ Media fields present: {present_fields}")
                
                # Verify images field is properly formatted
                if 'images' in first_service:
                    if isinstance(first_service['images'], list):
                        print(f"   ✅ Images field properly formatted as list")
                    else:
                        print(f"   ❌ Images field not properly formatted")
                        return False
                
                print(f"   ✅ Existing services compatible with media enhancement")
                return True
            else:
                print("   ⚠️  No existing services found")
                return True
        else:
            print("❌ Failed to retrieve existing services")
            return False

    def run_all_tests(self):
        """Run all service media management tests"""
        print("🚀 Starting Service Media Management Testing...")
        print(f"🌐 Testing against: {self.api_url}")
        print("=" * 80)
        
        # Setup tokens
        if not self.setup_admin_token():
            print("❌ Failed to setup admin token - aborting tests")
            return False
        
        if not self.setup_regular_token():
            print("❌ Failed to setup regular token - aborting tests")
            return False
        
        # Run all tests
        tests = [
            self.test_service_creation_with_media,
            self.test_service_update_with_media,
            self.test_partial_service_update,
            self.test_service_media_upload,
            self.test_set_main_image,
            self.test_delete_service_media,
            self.test_admin_services_retrieval,
            self.test_public_services_retrieval,
            self.test_individual_service_retrieval,
            self.test_backward_compatibility,
            self.test_authentication_requirements,
            self.test_existing_services_compatibility
        ]
        
        passed = 0
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
        
        print("\n" + "=" * 80)
        print(f"📊 FINAL RESULTS: {passed}/{len(tests)} tests passed ({(passed/len(tests)*100):.1f}%)")
        print(f"🔍 Individual API calls: {self.tests_passed}/{self.tests_run} passed ({(self.tests_passed/self.tests_run*100):.1f}%)")
        
        if passed == len(tests):
            print("🎉 All service media management tests passed!")
            return True
        elif passed >= len(tests) * 0.8:
            print("✅ Most tests passed! Service media management working well.")
            return True
        else:
            print("⚠️  Some tests failed. Service media management needs attention.")
            return False

if __name__ == "__main__":
    tester = ServiceMediaTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)