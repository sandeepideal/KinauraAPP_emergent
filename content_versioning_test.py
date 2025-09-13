#!/usr/bin/env python3
"""
KinAura Content Versioning System Testing
Tests the new native app content versioning functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "https://golden-health-1.preview.emergentagent.com/api"

class ContentVersioningTester:
    def __init__(self):
        self.admin_token = None
        self.test_service_id = None
        self.initial_version = None
        self.results = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if data:
            result["data"] = data
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and data:
            print(f"    Data: {json.dumps(data, indent=2, default=str)}")
        print()

    def authenticate_admin(self) -> bool:
        """Authenticate as admin user"""
        try:
            # Try admin login
            login_data = {
                "email": "admin@kinaura.com",
                "password": "admin123"
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_result("Admin Authentication", True, f"Admin authenticated successfully")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Authentication error: {str(e)}")
            return False

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if not self.admin_token:
            return {}
        return {"Authorization": f"Bearer {self.admin_token}"}

    def test_content_version_endpoint(self) -> bool:
        """Test GET /api/content/version endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/content/version")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["global_version", "last_updated", "content_types"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Content Version Endpoint - Structure", False, 
                                  f"Missing required fields: {missing_fields}", data)
                    return False
                
                # Validate content_types structure
                content_types = data.get("content_types", {})
                expected_types = ["services", "products", "service_groups"]
                
                found_types = []
                for content_type in expected_types:
                    if content_type in content_types:
                        found_types.append(content_type)
                        type_data = content_types[content_type]
                        
                        # Validate each content type structure
                        required_type_fields = ["content_type", "last_modified", "content_version", "content_hash"]
                        missing_type_fields = [field for field in required_type_fields if field not in type_data]
                        
                        if missing_type_fields:
                            self.log_result("Content Version Endpoint - Content Type Structure", False,
                                          f"Missing fields in {content_type}: {missing_type_fields}", type_data)
                            return False
                
                # Store initial version for later comparison
                self.initial_version = data.get("global_version")
                
                self.log_result("Content Version Endpoint", True, 
                              f"Found content types: {found_types}, Global version: {self.initial_version[:8]}...")
                return True
            else:
                self.log_result("Content Version Endpoint", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Content Version Endpoint", False, f"Request error: {str(e)}")
            return False

    def test_content_changes_no_params(self) -> bool:
        """Test GET /api/content/changes without parameters"""
        try:
            response = requests.get(f"{BACKEND_URL}/content/changes")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["has_changes", "global_version", "changed_content"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Content Changes (No Params) - Structure", False,
                                  f"Missing required fields: {missing_fields}", data)
                    return False
                
                # Should have changes when no params provided
                if not data.get("has_changes"):
                    self.log_result("Content Changes (No Params) - Logic", False,
                                  "Should have changes when no previous version provided", data)
                    return False
                
                # Should have changed_content
                if not data.get("changed_content"):
                    self.log_result("Content Changes (No Params) - Content", False,
                                  "Should have changed_content when no previous version", data)
                    return False
                
                self.log_result("Content Changes (No Params)", True,
                              f"Has changes: {data['has_changes']}, Content types: {list(data['changed_content'].keys())}")
                return True
            else:
                self.log_result("Content Changes (No Params)", False,
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Content Changes (No Params)", False, f"Request error: {str(e)}")
            return False

    def test_content_changes_with_current_version(self) -> bool:
        """Test GET /api/content/changes with current version (should show no changes)"""
        if not self.initial_version:
            self.log_result("Content Changes (Current Version)", False, "No initial version available")
            return False
            
        try:
            params = {"since_version": self.initial_version}
            response = requests.get(f"{BACKEND_URL}/content/changes", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if the global version has changed (which would be expected if content was modified)
                current_global_version = data.get("global_version")
                if current_global_version != self.initial_version:
                    # Version has changed, so we should have changes
                    if not data.get("has_changes"):
                        self.log_result("Content Changes (Current Version) - Logic", False,
                                      "Should have changes when global version has changed", data)
                        return False
                    
                    self.log_result("Content Changes (Current Version)", True,
                                  f"Correctly shows changes when version changed: {self.initial_version[:8]}... -> {current_global_version[:8]}...")
                    return True
                else:
                    # Version hasn't changed, should have no changes
                    if data.get("has_changes"):
                        self.log_result("Content Changes (Current Version) - Logic", False,
                                      "Should have no changes when providing current version", data)
                        return False
                    
                    # changed_content should be empty
                    if data.get("changed_content"):
                        self.log_result("Content Changes (Current Version) - Content", False,
                                      "Should have empty changed_content when no changes", data)
                        return False
                    
                    self.log_result("Content Changes (Current Version)", True,
                                  f"Correctly shows no changes for current version")
                    return True
            else:
                self.log_result("Content Changes (Current Version)", False,
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Content Changes (Current Version)", False, f"Request error: {str(e)}")
            return False

    def test_content_changes_with_timestamp(self) -> bool:
        """Test GET /api/content/changes with timestamp parameter"""
        try:
            # Use timestamp from 1 hour ago
            since_timestamp = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            params = {"since_timestamp": since_timestamp}
            response = requests.get(f"{BACKEND_URL}/content/changes", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["has_changes", "global_version", "changed_content"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Content Changes (Timestamp) - Structure", False,
                                  f"Missing required fields: {missing_fields}", data)
                    return False
                
                self.log_result("Content Changes (Timestamp)", True,
                              f"Has changes: {data['has_changes']}, Changed content types: {list(data['changed_content'].keys())}")
                return True
            else:
                self.log_result("Content Changes (Timestamp)", False,
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Content Changes (Timestamp)", False, f"Request error: {str(e)}")
            return False

    def test_services_sync_endpoint(self) -> bool:
        """Test GET /api/services/sync endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/services/sync")
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["services", "count", "last_updated", "content_hash", "cache_ttl"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Services Sync Endpoint - Structure", False,
                                  f"Missing required fields: {missing_fields}", data)
                    return False
                
                # Validate services array
                services = data.get("services", [])
                if not isinstance(services, list):
                    self.log_result("Services Sync Endpoint - Services Type", False,
                                  "Services should be an array", data)
                    return False
                
                # Validate count matches services length
                if data.get("count") != len(services):
                    self.log_result("Services Sync Endpoint - Count Mismatch", False,
                                  f"Count {data.get('count')} doesn't match services length {len(services)}", data)
                    return False
                
                # Check if services have versioning fields
                if services:
                    first_service = services[0]
                    versioning_fields = ["updated_at", "content_version"]
                    missing_versioning = [field for field in versioning_fields if field not in first_service]
                    
                    if missing_versioning:
                        self.log_result("Services Sync Endpoint - Versioning Fields", False,
                                      f"Services missing versioning fields: {missing_versioning}")
                    else:
                        self.log_result("Services Sync Endpoint - Versioning Fields", True,
                                      "Services contain required versioning fields")
                
                # Store a service ID for update testing
                if services:
                    self.test_service_id = services[0].get("id")
                
                self.log_result("Services Sync Endpoint", True,
                              f"Found {len(services)} services with sync metadata")
                return True
            elif response.status_code == 404:
                # If sync endpoint doesn't exist, try regular services endpoint to get service ID
                services_response = requests.get(f"{BACKEND_URL}/services")
                if services_response.status_code == 200:
                    services_data = services_response.json()
                    if services_data:
                        self.test_service_id = services_data[0].get("id")
                        self.log_result("Services Sync Endpoint", False,
                                      f"Sync endpoint not found, but got service ID from regular endpoint")
                        return False
                else:
                    self.log_result("Services Sync Endpoint", False,
                                  f"HTTP {response.status_code}: {response.text}")
                    return False
            else:
                self.log_result("Services Sync Endpoint", False,
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Services Sync Endpoint", False, f"Request error: {str(e)}")
            return False

    def test_services_sync_with_timestamp(self) -> bool:
        """Test GET /api/services/sync with if_modified_since parameter"""
        try:
            # Use timestamp from 1 hour ago
            since_timestamp = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            params = {"if_modified_since": since_timestamp}
            response = requests.get(f"{BACKEND_URL}/services/sync", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should still have the required structure
                required_fields = ["services", "count", "last_updated", "content_hash", "cache_ttl"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Services Sync (Timestamp) - Structure", False,
                                  f"Missing required fields: {missing_fields}", data)
                    return False
                
                self.log_result("Services Sync (Timestamp)", True,
                              f"Found {data.get('count', 0)} services modified since timestamp")
                return True
            else:
                self.log_result("Services Sync (Timestamp)", False,
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Services Sync (Timestamp)", False, f"Request error: {str(e)}")
            return False

    def test_admin_service_update_versioning(self) -> bool:
        """Test PUT /api/admin/services/{service_id} updates versioning fields"""
        if not self.admin_token:
            self.log_result("Admin Service Update", False, "No admin authentication")
            return False
            
        # Get a service ID if we don't have one
        if not self.test_service_id:
            try:
                services_response = requests.get(f"{BACKEND_URL}/services")
                if services_response.status_code == 200:
                    services_data = services_response.json()
                    if services_data:
                        self.test_service_id = services_data[0].get("id")
                    else:
                        self.log_result("Admin Service Update", False, "No services available for testing")
                        return False
                else:
                    self.log_result("Admin Service Update", False, "Could not get services list")
                    return False
            except Exception as e:
                self.log_result("Admin Service Update", False, f"Error getting services: {str(e)}")
                return False
            
        try:
            # Get current service data first
            response = requests.get(f"{BACKEND_URL}/services")
            if response.status_code != 200:
                self.log_result("Admin Service Update - Get Services", False,
                              f"Could not get services: {response.status_code}")
                return False
            
            services = response.json()
            original_service = None
            for service in services:
                if service.get("id") == self.test_service_id:
                    original_service = service
                    break
            
            if not original_service:
                self.log_result("Admin Service Update - Find Service", False,
                              f"Could not find service with ID: {self.test_service_id}")
                return False
            
            original_version = original_service.get("content_version")
            original_hash = original_service.get("content_hash")
            original_updated_at = original_service.get("updated_at")
            
            # Update service with minor change
            update_data = {
                "description": f"Updated description for versioning test - {datetime.now().isoformat()}"
            }
            
            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"
            
            response = requests.put(
                f"{BACKEND_URL}/admin/services/{self.test_service_id}",
                json=update_data,
                headers=headers
            )
            
            if response.status_code == 200:
                updated_service = response.json()
                
                # Check if versioning fields were updated
                new_version = updated_service.get("content_version")
                new_hash = updated_service.get("content_hash")
                new_updated_at = updated_service.get("updated_at")
                
                version_updated = new_version != original_version
                hash_updated = new_hash != original_hash
                timestamp_updated = new_updated_at != original_updated_at
                
                if not version_updated:
                    self.log_result("Admin Service Update - Version", False,
                                  f"content_version not updated: {original_version} -> {new_version}")
                    return False
                
                if not timestamp_updated:
                    self.log_result("Admin Service Update - Timestamp", False,
                                  f"updated_at not updated: {original_updated_at} -> {new_updated_at}")
                    return False
                
                # Hash might be None initially, so we check if it's generated
                if new_hash is None:
                    self.log_result("Admin Service Update - Hash", False,
                                  f"content_hash not generated: {new_hash}")
                    return False
                
                self.log_result("Admin Service Update", True,
                              f"Versioning fields updated correctly")
                return True
            else:
                self.log_result("Admin Service Update", False,
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Admin Service Update", False, f"Request error: {str(e)}")
            return False

    def test_version_change_after_update(self) -> bool:
        """Test that global content version changes after service update"""
        try:
            # Get new global version
            response = requests.get(f"{BACKEND_URL}/content/version")
            
            if response.status_code == 200:
                data = response.json()
                new_global_version = data.get("global_version")
                
                if new_global_version == self.initial_version:
                    self.log_result("Version Change After Update", False,
                                  f"Global version unchanged after service update: {new_global_version}")
                    return False
                
                self.log_result("Version Change After Update", True,
                              f"Global version changed: {self.initial_version[:8]}... -> {new_global_version[:8]}...")
                return True
            else:
                self.log_result("Version Change After Update", False,
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Version Change After Update", False, f"Request error: {str(e)}")
            return False

    def test_content_hash_generation(self) -> bool:
        """Test that content hashes are properly generated"""
        try:
            response = requests.get(f"{BACKEND_URL}/content/version")
            
            if response.status_code == 200:
                data = response.json()
                content_types = data.get("content_types", {})
                
                hash_tests = []
                for content_type, type_data in content_types.items():
                    content_hash = type_data.get("content_hash")
                    if content_hash and len(content_hash) == 32:  # MD5 hash length
                        hash_tests.append(f"{content_type}: {content_hash[:8]}...")
                    else:
                        self.log_result("Content Hash Generation", False,
                                      f"Invalid hash for {content_type}: {content_hash}")
                        return False
                
                self.log_result("Content Hash Generation", True,
                              f"Valid hashes generated for: {', '.join(hash_tests)}")
                return True
            else:
                self.log_result("Content Hash Generation", False,
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Content Hash Generation", False, f"Request error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all content versioning tests"""
        print("🚀 Starting KinAura Content Versioning System Tests")
        print("=" * 60)
        
        # Authentication
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return
        
        # Test sequence
        tests = [
            self.test_content_version_endpoint,
            self.test_content_changes_no_params,
            self.test_content_changes_with_current_version,
            self.test_content_changes_with_timestamp,
            self.test_services_sync_endpoint,
            self.test_services_sync_with_timestamp,
            self.test_admin_service_update_versioning,
            self.test_version_change_after_update,
            self.test_content_hash_generation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        # Summary
        print("=" * 60)
        print(f"📊 CONTENT VERSIONING SYSTEM TEST RESULTS")
        print(f"✅ Passed: {passed}/{total} ({(passed/total)*100:.1f}%)")
        print(f"❌ Failed: {total-passed}/{total}")
        
        if passed == total:
            print("🎉 ALL CONTENT VERSIONING TESTS PASSED!")
            print("✅ Native app content versioning system is working correctly")
            print("✅ Content version tracking functional")
            print("✅ Change detection working properly")
            print("✅ Services sync with metadata operational")
            print("✅ Admin service updates trigger versioning")
            print("✅ Content hashes generated correctly")
        else:
            print("⚠️  Some content versioning tests failed")
            print("🔍 Check the detailed results above for issues")
        
        return passed == total

if __name__ == "__main__":
    tester = ContentVersioningTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)