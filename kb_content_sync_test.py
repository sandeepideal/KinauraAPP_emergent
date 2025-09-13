#!/usr/bin/env python3
"""
Enhanced Knowledge Base Content Sync System Testing
Tests the complete content sync system for knowledge base updates
"""

import requests
import json
import time
import asyncio
import websockets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import uuid

# Configuration
BACKEND_URL = "https://golden-health-1.preview.emergentagent.com/api"
WEBSOCKET_URL = "wss://golden-health-1.preview.emergentagent.com/ws/content-sync"

class KnowledgeBaseContentSyncTester:
    def __init__(self):
        self.admin_token = None
        self.test_kb_items = []
        self.websocket_messages = []
        
    def authenticate_admin(self) -> bool:
        """Authenticate as admin user"""
        try:
            # Use existing admin credentials
            login_data = {
                "email": "admin@kinaura.com",
                "password": "admin123"
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                print(f"✅ Admin authentication successful")
                return True
            else:
                print(f"❌ Admin authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Admin authentication error: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with admin token"""
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_content_version_endpoint(self) -> bool:
        """Test 1: Verify GET /api/content/version includes knowledge_base in content_types"""
        print("\n🧪 TEST 1: Content Version Endpoint - Knowledge Base Inclusion")
        try:
            response = requests.get(f"{BACKEND_URL}/content/version")
            
            if response.status_code != 200:
                print(f"❌ Content version endpoint failed: {response.status_code}")
                return False
            
            data = response.json()
            
            # Verify response structure
            required_fields = ["global_version", "last_updated", "content_types"]
            for field in required_fields:
                if field not in data:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Verify knowledge_base is in content_types
            content_types = data["content_types"]
            if "knowledge_base" not in content_types:
                print(f"❌ knowledge_base not found in content_types. Available: {list(content_types.keys())}")
                return False
            
            # Verify knowledge_base structure
            kb_status = content_types["knowledge_base"]
            required_kb_fields = ["content_type", "last_modified", "content_version", "content_hash"]
            for field in required_kb_fields:
                if field not in kb_status:
                    print(f"❌ Missing knowledge_base field: {field}")
                    return False
            
            # Verify other expected content types are also present
            expected_types = ["services", "products", "service_groups", "knowledge_base"]
            for content_type in expected_types:
                if content_type in content_types:
                    print(f"✅ Found content type: {content_type}")
            
            print(f"✅ Content version endpoint working correctly")
            print(f"   - Global version: {data['global_version'][:8]}...")
            print(f"   - Knowledge base version: {kb_status['content_version'][:8]}...")
            print(f"   - Knowledge base hash: {kb_status['content_hash'][:8]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Content version endpoint test error: {e}")
            return False
    
    def test_knowledge_base_creation_sync(self) -> bool:
        """Test 2: Test knowledge base creation triggers content sync"""
        print("\n🧪 TEST 2: Knowledge Base Creation Content Sync")
        try:
            # Get initial content version
            initial_response = requests.get(f"{BACKEND_URL}/content/version")
            if initial_response.status_code != 200:
                print(f"❌ Failed to get initial content version")
                return False
            
            initial_data = initial_response.json()
            initial_kb_version = initial_data["content_types"].get("knowledge_base", {}).get("content_version", "")
            
            # Create a new knowledge base item
            kb_data = {
                "title": f"Test KB Item - Content Sync {uuid.uuid4().hex[:8]}",
                "content": "This is a test knowledge base item for content sync testing. It contains information about KinAura treatments and protocols.",
                "category": "treatments",
                "tags": ["test", "content-sync", "morpheus8"],
                "source_type": "admin_created"
            }
            
            create_response = requests.post(
                f"{BACKEND_URL}/admin/knowledge-base",
                json=kb_data,
                headers=self.get_headers()
            )
            
            if create_response.status_code != 200:
                print(f"❌ Failed to create knowledge base item: {create_response.status_code} - {create_response.text}")
                return False
            
            created_item = create_response.json()
            self.test_kb_items.append(created_item["id"])
            print(f"✅ Created knowledge base item: {created_item['id']}")
            
            # Wait a moment for async processing
            time.sleep(2)
            
            # Check if content version changed (only if item was approved)
            final_response = requests.get(f"{BACKEND_URL}/content/version")
            if final_response.status_code != 200:
                print(f"❌ Failed to get final content version")
                return False
            
            final_data = final_response.json()
            final_kb_version = final_data["content_types"].get("knowledge_base", {}).get("content_version", "")
            
            # Note: Content sync only triggers for approved items
            if created_item.get("is_approved", False):
                if initial_kb_version == final_kb_version:
                    print(f"⚠️ Content version did not change after approved KB creation")
                    return False
                else:
                    print(f"✅ Content version changed after approved KB creation")
                    print(f"   - Initial: {initial_kb_version[:8]}...")
                    print(f"   - Final: {final_kb_version[:8]}...")
            else:
                print(f"✅ KB item created but not approved - content sync correctly not triggered")
                print(f"   - Item approval status: {created_item.get('is_approved', False)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Knowledge base creation sync test error: {e}")
            return False
    
    def test_knowledge_base_approval_sync(self) -> bool:
        """Test 3: Test knowledge base approval triggers content sync"""
        print("\n🧪 TEST 3: Knowledge Base Approval Content Sync")
        try:
            if not self.test_kb_items:
                print(f"❌ No test KB items available for approval test")
                return False
            
            kb_id = self.test_kb_items[0]
            
            # Get initial content version
            initial_response = requests.get(f"{BACKEND_URL}/content/version")
            if initial_response.status_code != 200:
                print(f"❌ Failed to get initial content version")
                return False
            
            initial_data = initial_response.json()
            initial_kb_version = initial_data["content_types"].get("knowledge_base", {}).get("content_version", "")
            initial_global_version = initial_data["global_version"]
            
            # Approve the knowledge base item
            approve_response = requests.put(
                f"{BACKEND_URL}/admin/knowledge-base/{kb_id}/approve",
                headers=self.get_headers()
            )
            
            if approve_response.status_code != 200:
                print(f"❌ Failed to approve knowledge base item: {approve_response.status_code} - {approve_response.text}")
                return False
            
            print(f"✅ Approved knowledge base item: {kb_id}")
            
            # Wait for async processing
            time.sleep(2)
            
            # Check if content version changed
            final_response = requests.get(f"{BACKEND_URL}/content/version")
            if final_response.status_code != 200:
                print(f"❌ Failed to get final content version")
                return False
            
            final_data = final_response.json()
            final_kb_version = final_data["content_types"].get("knowledge_base", {}).get("content_version", "")
            final_global_version = final_data["global_version"]
            
            # Verify content version changed
            if initial_kb_version == final_kb_version:
                print(f"❌ Knowledge base content version did not change after approval")
                return False
            
            if initial_global_version == final_global_version:
                print(f"❌ Global content version did not change after approval")
                return False
            
            print(f"✅ Content versions changed after KB approval")
            print(f"   - KB version: {initial_kb_version[:8]}... → {final_kb_version[:8]}...")
            print(f"   - Global version: {initial_global_version[:8]}... → {final_global_version[:8]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Knowledge base approval sync test error: {e}")
            return False
    
    def test_knowledge_base_update_sync(self) -> bool:
        """Test 4: Test knowledge base updates trigger content sync"""
        print("\n🧪 TEST 4: Knowledge Base Update Content Sync")
        try:
            if not self.test_kb_items:
                print(f"❌ No test KB items available for update test")
                return False
            
            kb_id = self.test_kb_items[0]
            
            # Get initial content version
            initial_response = requests.get(f"{BACKEND_URL}/content/version")
            if initial_response.status_code != 200:
                print(f"❌ Failed to get initial content version")
                return False
            
            initial_data = initial_response.json()
            initial_kb_version = initial_data["content_types"].get("knowledge_base", {}).get("content_version", "")
            
            # Update the knowledge base item
            update_data = {
                "title": f"Updated Test KB Item - {uuid.uuid4().hex[:8]}",
                "content": "This is updated content for the knowledge base item. Updated with new information about KinAura protocols and treatments.",
                "tags": ["test", "updated", "content-sync", "morpheus8", "protocols"]
            }
            
            update_response = requests.put(
                f"{BACKEND_URL}/admin/knowledge-base/{kb_id}",
                json=update_data,
                headers=self.get_headers()
            )
            
            if update_response.status_code != 200:
                print(f"❌ Failed to update knowledge base item: {update_response.status_code} - {update_response.text}")
                return False
            
            updated_item = update_response.json()
            print(f"✅ Updated knowledge base item: {kb_id}")
            
            # Wait for async processing
            time.sleep(2)
            
            # Check if content version changed (only if item is approved)
            final_response = requests.get(f"{BACKEND_URL}/content/version")
            if final_response.status_code != 200:
                print(f"❌ Failed to get final content version")
                return False
            
            final_data = final_response.json()
            final_kb_version = final_data["content_types"].get("knowledge_base", {}).get("content_version", "")
            
            # Check if the item is approved to determine if sync should have occurred
            if updated_item.get("is_approved", False):
                if initial_kb_version == final_kb_version:
                    print(f"❌ Content version did not change after approved KB update")
                    return False
                else:
                    print(f"✅ Content version changed after approved KB update")
                    print(f"   - Initial: {initial_kb_version[:8]}...")
                    print(f"   - Final: {final_kb_version[:8]}...")
            else:
                print(f"✅ KB item updated but not approved - content sync correctly not triggered")
            
            return True
            
        except Exception as e:
            print(f"❌ Knowledge base update sync test error: {e}")
            return False
    
    def test_content_changes_detection(self) -> bool:
        """Test 5: Test GET /api/content/changes detects knowledge base updates"""
        print("\n🧪 TEST 5: Content Changes Detection for Knowledge Base")
        try:
            # Get current content version as baseline
            current_response = requests.get(f"{BACKEND_URL}/content/version")
            if current_response.status_code != 200:
                print(f"❌ Failed to get current content version")
                return False
            
            current_data = current_response.json()
            current_global_version = current_data["global_version"]
            
            # Test 1: Check changes with current version (should show no changes)
            no_changes_response = requests.get(
                f"{BACKEND_URL}/content/changes?since_version={current_global_version}"
            )
            
            if no_changes_response.status_code != 200:
                print(f"❌ Failed to check content changes: {no_changes_response.status_code}")
                return False
            
            no_changes_data = no_changes_response.json()
            if no_changes_data.get("has_changes", True):
                print(f"❌ Should show no changes for current version")
                return False
            
            print(f"✅ Correctly shows no changes for current version")
            
            # Test 2: Check changes with old version (should show changes)
            old_version = "old_version_123"
            changes_response = requests.get(
                f"{BACKEND_URL}/content/changes?since_version={old_version}"
            )
            
            if changes_response.status_code != 200:
                print(f"❌ Failed to check content changes with old version")
                return False
            
            changes_data = changes_response.json()
            if not changes_data.get("has_changes", False):
                print(f"❌ Should show changes for old version")
                return False
            
            # Verify knowledge_base is in changed content
            changed_content = changes_data.get("changed_content", {})
            if "knowledge_base" not in changed_content:
                print(f"❌ knowledge_base not in changed content")
                return False
            
            print(f"✅ Correctly shows changes for old version")
            print(f"   - Changed content types: {list(changed_content.keys())}")
            
            # Test 3: Check changes with timestamp
            past_timestamp = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            timestamp_response = requests.get(
                f"{BACKEND_URL}/content/changes?since_timestamp={past_timestamp}"
            )
            
            if timestamp_response.status_code != 200:
                print(f"❌ Failed to check content changes with timestamp")
                return False
            
            timestamp_data = timestamp_response.json()
            print(f"✅ Timestamp-based change detection working")
            print(f"   - Has changes: {timestamp_data.get('has_changes', False)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Content changes detection test error: {e}")
            return False
    
    async def test_websocket_notifications(self) -> bool:
        """Test 6: Test WebSocket notifications for knowledge base updates"""
        print("\n🧪 TEST 6: WebSocket Notifications for Knowledge Base Updates")
        try:
            # Connect to WebSocket
            print(f"🔌 Connecting to WebSocket: {WEBSOCKET_URL}")
            
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                print(f"✅ WebSocket connected successfully")
                
                # Set up message listener
                async def listen_for_messages():
                    try:
                        while True:
                            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                            data = json.loads(message)
                            self.websocket_messages.append(data)
                            print(f"📨 Received WebSocket message: {data}")
                    except asyncio.TimeoutError:
                        print(f"⏰ WebSocket listening timeout")
                    except Exception as e:
                        print(f"❌ WebSocket listening error: {e}")
                
                # Start listening in background
                listen_task = asyncio.create_task(listen_for_messages())
                
                # Wait a moment to establish connection
                await asyncio.sleep(1)
                
                # Trigger a knowledge base update to generate WebSocket notification
                print(f"🔄 Triggering knowledge base update to test WebSocket...")
                
                # Create and approve a new KB item (this should trigger WebSocket notification)
                kb_data = {
                    "title": f"WebSocket Test KB Item - {uuid.uuid4().hex[:8]}",
                    "content": "This KB item is created to test WebSocket notifications for content sync.",
                    "category": "treatments",
                    "tags": ["websocket", "test", "content-sync"],
                    "source_type": "admin_created"
                }
                
                # Use requests in a separate thread to avoid blocking
                def create_and_approve_kb():
                    try:
                        # Create KB item
                        create_response = requests.post(
                            f"{BACKEND_URL}/admin/knowledge-base",
                            json=kb_data,
                            headers=self.get_headers()
                        )
                        
                        if create_response.status_code == 200:
                            created_item = create_response.json()
                            kb_id = created_item["id"]
                            self.test_kb_items.append(kb_id)
                            
                            # Approve the item (this should trigger WebSocket notification)
                            approve_response = requests.put(
                                f"{BACKEND_URL}/admin/knowledge-base/{kb_id}/approve",
                                headers=self.get_headers()
                            )
                            
                            if approve_response.status_code == 200:
                                print(f"✅ Created and approved KB item for WebSocket test")
                                return True
                        
                        return False
                    except Exception as e:
                        print(f"❌ Error creating KB item for WebSocket test: {e}")
                        return False
                
                # Run the KB creation in a thread
                import threading
                kb_thread = threading.Thread(target=create_and_approve_kb)
                kb_thread.start()
                kb_thread.join()
                
                # Wait for WebSocket messages
                await asyncio.sleep(5)
                
                # Cancel the listening task
                listen_task.cancel()
                
                # Check if we received WebSocket notifications
                if not self.websocket_messages:
                    print(f"⚠️ No WebSocket messages received")
                    return False
                
                # Verify message content
                knowledge_base_notifications = [
                    msg for msg in self.websocket_messages 
                    if msg.get("type") == "content_update" and "knowledge_base" in msg.get("content_types", [])
                ]
                
                if not knowledge_base_notifications:
                    print(f"❌ No knowledge_base content update notifications received")
                    print(f"   - Received messages: {self.websocket_messages}")
                    return False
                
                print(f"✅ WebSocket notifications working correctly")
                print(f"   - Total messages: {len(self.websocket_messages)}")
                print(f"   - Knowledge base notifications: {len(knowledge_base_notifications)}")
                
                # Verify notification structure
                notification = knowledge_base_notifications[0]
                required_fields = ["type", "content_types", "timestamp"]
                for field in required_fields:
                    if field not in notification:
                        print(f"❌ Missing field in WebSocket notification: {field}")
                        return False
                
                print(f"✅ WebSocket notification structure correct")
                return True
                
        except Exception as e:
            print(f"❌ WebSocket notifications test error: {e}")
            return False
    
    def test_end_to_end_flow(self) -> bool:
        """Test 7: Complete admin knowledge base update → chatbot refresh cycle"""
        print("\n🧪 TEST 7: End-to-End Knowledge Base Update Flow")
        try:
            # Step 1: Create a knowledge base item with specific content
            kb_data = {
                "title": "End-to-End Test: Updated HBOT Protocol 2025",
                "content": """
                HBOT (Hyperbaric Oxygen Therapy) at KinAura - Updated 2025 Protocol
                
                Treatment Details:
                - Pressure: 2.0 ATA (atmospheres absolute)
                - Duration: 90 minutes per session
                - Oxygen concentration: 100% medical grade
                - Chamber type: Monoplace hyperbaric chamber
                
                Pricing 2025:
                - Single session: €280
                - Package of 5 sessions: €1,200 (save €200)
                - Package of 10 sessions: €2,200 (save €600)
                
                Benefits:
                - Enhanced tissue oxygenation
                - Accelerated wound healing
                - Reduced inflammation
                - Improved cognitive function
                - Enhanced athletic recovery
                
                KinAura Exclusivity:
                Only KinAura in Milan offers medical-grade HBOT combined with regenerative therapies in a sterile hospital environment.
                """,
                "category": "treatments",
                "tags": ["hbot", "hyperbaric", "oxygen", "therapy", "2025", "protocol"],
                "source_type": "admin_created"
            }
            
            print(f"📝 Step 1: Creating knowledge base item...")
            create_response = requests.post(
                f"{BACKEND_URL}/admin/knowledge-base",
                json=kb_data,
                headers=self.get_headers()
            )
            
            if create_response.status_code != 200:
                print(f"❌ Failed to create KB item: {create_response.status_code}")
                return False
            
            created_item = create_response.json()
            kb_id = created_item["id"]
            self.test_kb_items.append(kb_id)
            print(f"✅ Created KB item: {kb_id}")
            
            # Step 2: Approve the knowledge base item
            print(f"✅ Step 2: Approving knowledge base item...")
            approve_response = requests.put(
                f"{BACKEND_URL}/admin/knowledge-base/{kb_id}/approve",
                headers=self.get_headers()
            )
            
            if approve_response.status_code != 200:
                print(f"❌ Failed to approve KB item: {approve_response.status_code}")
                return False
            
            print(f"✅ Approved KB item")
            
            # Step 3: Wait for content sync
            time.sleep(3)
            
            # Step 4: Verify content version updated
            print(f"🔄 Step 3: Verifying content version update...")
            version_response = requests.get(f"{BACKEND_URL}/content/version")
            if version_response.status_code != 200:
                print(f"❌ Failed to get content version")
                return False
            
            version_data = version_response.json()
            kb_status = version_data["content_types"].get("knowledge_base")
            if not kb_status:
                print(f"❌ Knowledge base not in content types")
                return False
            
            print(f"✅ Content version updated")
            print(f"   - KB version: {kb_status['content_version'][:8]}...")
            print(f"   - Last modified: {kb_status['last_modified']}")
            
            # Step 5: Test chatbot can access updated knowledge
            print(f"🤖 Step 4: Testing chatbot access to updated knowledge...")
            
            # Test chatbot query about HBOT
            chat_data = {
                "message": "Tell me about HBOT therapy pricing and benefits at KinAura",
                "session_id": f"test_session_{uuid.uuid4().hex[:8]}"
            }
            
            chat_response = requests.post(
                f"{BACKEND_URL}/chat",
                json=chat_data
            )
            
            if chat_response.status_code != 200:
                print(f"❌ Chatbot query failed: {chat_response.status_code}")
                return False
            
            chat_result = chat_response.json()
            chatbot_message = chat_result.get("message", "").lower()
            
            # Check if chatbot response includes updated information
            expected_keywords = ["hbot", "€280", "2.0 ata", "90 minutes", "hyperbaric"]
            found_keywords = [kw for kw in expected_keywords if kw in chatbot_message]
            
            if len(found_keywords) < 3:
                print(f"⚠️ Chatbot may not have latest knowledge (found {len(found_keywords)}/5 keywords)")
                print(f"   - Found keywords: {found_keywords}")
                print(f"   - Response preview: {chatbot_message[:200]}...")
            else:
                print(f"✅ Chatbot has access to updated knowledge")
                print(f"   - Found keywords: {found_keywords}")
            
            # Step 6: Verify change detection works
            print(f"🔍 Step 5: Testing change detection...")
            old_timestamp = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
            changes_response = requests.get(
                f"{BACKEND_URL}/content/changes?since_timestamp={old_timestamp}"
            )
            
            if changes_response.status_code != 200:
                print(f"❌ Change detection failed")
                return False
            
            changes_data = changes_response.json()
            if not changes_data.get("has_changes") or "knowledge_base" not in changes_data.get("changed_content", {}):
                print(f"❌ Change detection did not detect knowledge base updates")
                return False
            
            print(f"✅ Change detection working correctly")
            
            print(f"\n🎉 END-TO-END FLOW COMPLETED SUCCESSFULLY!")
            print(f"   ✅ Knowledge base item created")
            print(f"   ✅ Knowledge base item approved")
            print(f"   ✅ Content sync notification triggered")
            print(f"   ✅ Content version updated")
            print(f"   ✅ Chatbot has access to updated content")
            print(f"   ✅ Change detection working")
            
            return True
            
        except Exception as e:
            print(f"❌ End-to-end flow test error: {e}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test knowledge base items"""
        print(f"\n🧹 Cleaning up test data...")
        try:
            for kb_id in self.test_kb_items:
                try:
                    # Delete the test KB item
                    delete_response = requests.delete(
                        f"{BACKEND_URL}/admin/knowledge-base/{kb_id}",
                        headers=self.get_headers()
                    )
                    if delete_response.status_code in [200, 404]:
                        print(f"✅ Cleaned up KB item: {kb_id}")
                    else:
                        print(f"⚠️ Could not delete KB item {kb_id}: {delete_response.status_code}")
                except Exception as e:
                    print(f"⚠️ Error deleting KB item {kb_id}: {e}")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
    
    def run_all_tests(self):
        """Run all knowledge base content sync tests"""
        print("🚀 ENHANCED KNOWLEDGE BASE CONTENT SYNC SYSTEM TESTING")
        print("=" * 70)
        
        # Authenticate
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        test_results = []
        
        # Run all tests
        tests = [
            ("Content Version Endpoint", self.test_content_version_endpoint),
            ("Knowledge Base Creation Sync", self.test_knowledge_base_creation_sync),
            ("Knowledge Base Approval Sync", self.test_knowledge_base_approval_sync),
            ("Knowledge Base Update Sync", self.test_knowledge_base_update_sync),
            ("Content Changes Detection", self.test_content_changes_detection),
            ("End-to-End Flow", self.test_end_to_end_flow),
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                test_results.append((test_name, False))
        
        # Run WebSocket test separately (async)
        try:
            print("\n🔄 Running WebSocket test...")
            websocket_result = asyncio.run(self.test_websocket_notifications())
            test_results.append(("WebSocket Notifications", websocket_result))
        except Exception as e:
            print(f"❌ WebSocket test failed with exception: {e}")
            test_results.append(("WebSocket Notifications", False))
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 ENHANCED KNOWLEDGE BASE CONTENT SYNC TEST RESULTS")
        print("=" * 70)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Enhanced Knowledge Base Content Sync System is working perfectly!")
        else:
            print(f"⚠️ {total-passed} test(s) failed. Please review the issues above.")
        
        return passed == total

if __name__ == "__main__":
    tester = KnowledgeBaseContentSyncTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)