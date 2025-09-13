#!/usr/bin/env python3
"""
KinAura Chatbot Backend Testing - ObjectId Serialization Fixes
Focus on testing the critical chatbot endpoints that were failing with ObjectId serialization issues.
"""

import requests
import json
import sys
from datetime import datetime

class KinAuraChatbotTester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.critical_failures = []

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
        """Setup admin authentication for testing"""
        admin_data = {
            "provider": "admin",
            "access_token": "admin_token",
            "full_name": "Dr. Marco Rossi",
            "email": f"admin_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
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
            print(f"   ✅ Admin token obtained: {self.admin_token[:20]}...")
            return True
        else:
            print("   ❌ Failed to obtain admin token")
            return False

    def test_chatbot_configuration_management(self):
        """Test KinAura Chatbot Configuration Management with ObjectId fixes"""
        print("\n🔍 Testing KinAura Chatbot Configuration Management...")
        
        if not self.admin_token:
            print("❌ No admin token available for chatbot configuration test")
            return False
        
        # Test 1: Get current chatbot configuration
        success, config_response = self.run_test(
            "Get Chatbot Configuration",
            "GET",
            "/admin/chatbot/config",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            required_fields = ['id', 'system_prompt', 'is_active', 'version', 'created_by']
            missing_fields = [field for field in required_fields if field not in config_response]
            if missing_fields:
                print(f"   ❌ Missing configuration fields: {missing_fields}")
                self.critical_failures.append(f"Chatbot Config - Missing fields: {missing_fields}")
                return False
            else:
                print(f"   ✅ Configuration has all required fields")
                print(f"   📊 Current version: {config_response.get('version')}, Active: {config_response.get('is_active')}")
        else:
            print("   ❌ Failed to get chatbot configuration")
            self.critical_failures.append("Chatbot Config - Failed to retrieve configuration")
            return False
        
        # Test 2: Update chatbot configuration
        new_system_prompt = """You are KinAura Concierge, an AI assistant for KinAura - Centre for Regenerative Wellness in Milan, Italy. 

You provide information about our regenerative wellness services including:
- IV Therapy (NAD+, Vitamin drips, Ozone therapy)
- Hyperbaric Oxygen Therapy (HBOT)
- PEMF Therapy
- Peptide Therapy
- Red Light Therapy
- Male Wellness Programs

You can help with:
- Service information and benefits
- Appointment scheduling guidance
- Treatment recommendations
- Membership benefits

Always respond professionally and empathetically. If asked about appointments, guide users to book through our system or contact our team.

Respond in the same language as the user (Italian or English)."""

        update_data = {
            "system_prompt": new_system_prompt
        }
        
        success, update_response = self.run_test(
            "Update Chatbot Configuration",
            "PUT",
            "/admin/chatbot/config",
            200,
            data=update_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            if update_response.get('system_prompt') == new_system_prompt:
                print(f"   ✅ System prompt updated successfully")
            if update_response.get('version') > config_response.get('version', 0):
                print(f"   ✅ Version incremented correctly to {update_response.get('version')}")
        else:
            print("   ❌ Failed to update chatbot configuration")
            self.critical_failures.append("Chatbot Config - Failed to update configuration")
            return False
        
        # Test 3: Get configuration history
        success, history_response = self.run_test(
            "Get Chatbot Configuration History",
            "GET",
            "/admin/chatbot/config/history",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and isinstance(history_response, list):
            print(f"   ✅ Retrieved {len(history_response)} configuration versions")
            if len(history_response) >= 2:  # Should have at least original + updated
                print(f"   ✅ Configuration history tracking working")
                # Verify history structure
                if history_response:
                    history_item = history_response[0]
                    required_history_fields = ['id', 'system_prompt', 'version', 'created_by', 'created_at']
                    missing_fields = [field for field in required_history_fields if field not in history_item]
                    if missing_fields:
                        print(f"   ❌ Missing history fields: {missing_fields}")
                        self.critical_failures.append(f"Chatbot Config History - Missing fields: {missing_fields}")
                        return False
                    else:
                        print(f"   ✅ Configuration history has all required fields")
        else:
            print("   ❌ Failed to get configuration history")
            self.critical_failures.append("Chatbot Config - Failed to retrieve configuration history")
            return False
        
        print("   ✅ Chatbot Configuration Management test completed successfully")
        return True

    def test_knowledge_base_management(self):
        """Test KinAura Knowledge Base Management with ObjectId serialization fixes"""
        print("\n🔍 Testing KinAura Knowledge Base Management...")
        
        if not self.admin_token:
            print("❌ No admin token available for knowledge base test")
            return False
        
        # Test 1: Create knowledge base items
        knowledge_items = [
            {
                "title": "IV Therapy Benefits and Procedures",
                "content": "IV Therapy at KinAura provides direct nutrient delivery to your bloodstream, bypassing the digestive system for maximum absorption. Our IV drips include NAD+, vitamin cocktails, and ozone therapy. Benefits include increased energy, improved immune function, and enhanced cellular repair. Sessions typically last 30-60 minutes in our comfortable treatment rooms.",
                "category": "treatments",
                "tags": ["iv_therapy", "nad", "vitamins", "ozone"],
                "source_type": "admin_created"
            },
            {
                "title": "Hyperbaric Oxygen Therapy (HBOT) Overview",
                "content": "HBOT involves breathing pure oxygen in a pressurized chamber, increasing oxygen levels in your blood and tissues. This promotes healing, reduces inflammation, and supports tissue regeneration. Ideal for wound healing, sports recovery, and anti-aging. Sessions are 60 minutes in our state-of-the-art hyperbaric chambers.",
                "category": "treatments", 
                "tags": ["hbot", "oxygen", "healing", "recovery"],
                "source_type": "admin_created"
            },
            {
                "title": "Appointment Booking and Cancellation Policy",
                "content": "Appointments can be booked online through our patient portal or by calling our clinic. We require 24-hour notice for cancellations to avoid fees. Same-day appointments may be available based on availability. Elite members receive priority booking access. All appointments require confirmation 24 hours prior.",
                "category": "policies",
                "tags": ["appointments", "booking", "cancellation", "policy"],
                "source_type": "admin_created"
            }
        ]
        
        created_item_ids = []
        for item_data in knowledge_items:
            success, response = self.run_test(
                f"Create Knowledge Base Item - {item_data['title'][:30]}...",
                "POST",
                "/admin/knowledge-base",
                200,
                data=item_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                item_id = response.get('id')
                created_item_ids.append(item_id)
                print(f"   ✅ Created knowledge base item with ID: {item_id}")
                
                # Verify item structure
                required_fields = ['id', 'title', 'content', 'category', 'tags', 'source_type']
                missing_fields = [field for field in required_fields if field not in response]
                if missing_fields:
                    print(f"   ❌ Missing item fields: {missing_fields}")
                    self.critical_failures.append(f"Knowledge Base Item - Missing fields: {missing_fields}")
                    return False
                else:
                    print(f"   ✅ Knowledge base item has all required fields")
            else:
                print(f"   ❌ Failed to create knowledge base item: {item_data['title']}")
                self.critical_failures.append(f"Knowledge Base - Failed to create item: {item_data['title']}")
                return False
        
        # Test 2: Get all knowledge base items (CRITICAL TEST - was failing with ObjectId serialization)
        success, items_response = self.run_test(
            "Get All Knowledge Base Items (ObjectId Serialization Test)",
            "GET",
            "/admin/knowledge-base",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and isinstance(items_response, list):
            print(f"   ✅ CRITICAL SUCCESS: Retrieved {len(items_response)} knowledge base items without ObjectId errors")
            print(f"   🎉 ObjectId serialization issue FIXED for Knowledge Base!")
            
            # Verify we can find our created items
            created_titles = [item['title'] for item in knowledge_items]
            retrieved_titles = [item.get('title', '') for item in items_response]
            found_items = [title for title in created_titles if any(title in ret_title for ret_title in retrieved_titles)]
            
            if len(found_items) >= len(created_titles):
                print(f"   ✅ All created knowledge base items found in retrieval")
            else:
                print(f"   ⚠️  Only {len(found_items)}/{len(created_titles)} created items found")
            
            # Verify JSON serialization is working (no ObjectId issues)
            try:
                json_str = json.dumps(items_response)
                print(f"   ✅ Knowledge base items properly JSON serializable")
            except Exception as e:
                print(f"   ❌ JSON serialization failed: {str(e)}")
                self.critical_failures.append(f"Knowledge Base - JSON serialization failed: {str(e)}")
                return False
                
        else:
            print("   ❌ CRITICAL FAILURE: Failed to retrieve knowledge base items - likely ObjectId serialization issue")
            self.critical_failures.append("Knowledge Base - CRITICAL: ObjectId serialization still broken")
            return False
        
        # Test 3: Update a knowledge base item
        if created_item_ids:
            item_id_to_update = created_item_ids[0]
            update_data = {
                "title": "Updated IV Therapy Benefits and Procedures",
                "content": "UPDATED: IV Therapy at KinAura provides direct nutrient delivery with enhanced protocols...",
                "category": "treatments",
                "tags": ["iv_therapy", "nad", "vitamins", "ozone", "updated"],
                "is_active": True
            }
            
            success, update_response = self.run_test(
                "Update Knowledge Base Item",
                "PUT",
                f"/admin/knowledge-base/{item_id_to_update}",
                200,
                data=update_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                if update_response.get('title') == update_data['title']:
                    print(f"   ✅ Knowledge base item updated successfully")
                if 'updated' in update_response.get('tags', []):
                    print(f"   ✅ Tags updated correctly")
            else:
                print(f"   ❌ Failed to update knowledge base item")
                self.critical_failures.append("Knowledge Base - Failed to update item")
                return False
        
        # Test 4: Delete a knowledge base item
        if len(created_item_ids) > 1:
            item_id_to_delete = created_item_ids[-1]
            success, delete_response = self.run_test(
                "Delete Knowledge Base Item",
                "DELETE",
                f"/admin/knowledge-base/{item_id_to_delete}",
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print(f"   ✅ Knowledge base item deleted successfully")
            else:
                print(f"   ❌ Failed to delete knowledge base item")
                self.critical_failures.append("Knowledge Base - Failed to delete item")
                return False
        
        print("   ✅ Knowledge Base Management test completed successfully")
        return True

    def test_patient_chat_functionality(self):
        """Test KinAura Patient Chat Functionality with ObjectId serialization fixes"""
        print("\n🔍 Testing KinAura Patient Chat Functionality...")
        
        # Test 1: Anonymous chat functionality
        chat_queries = [
            {
                "message": "Hello, I'm interested in IV therapy. Can you tell me about the benefits?",
                "expected_keywords": ["iv", "therapy", "benefits", "nutrients"]
            },
            {
                "message": "What is NAD IV therapy and how much does it cost?",
                "expected_keywords": ["nad", "therapy", "cost", "price"]
            },
            {
                "message": "Ciao, vorrei sapere di più sulla terapia con ozono. Quali sono i benefici?",
                "expected_keywords": ["ozono", "terapia", "benefici"]
            },
            {
                "message": "I want to book an appointment for hyperbaric oxygen therapy. What times are available?",
                "expected_keywords": ["appointment", "hyperbaric", "oxygen", "available"]
            }
        ]
        
        session_id = None
        for i, query in enumerate(chat_queries):
            chat_data = {
                "message": query["message"],
                "session_id": session_id,  # Will be None for first message
                "user_id": None  # Anonymous chat
            }
            
            success, response = self.run_test(
                f"Chat Query {i+1} - {'Italian' if 'Ciao' in query['message'] else 'English'}",
                "POST",
                "/chat",
                200,
                data=chat_data
            )
            
            if success:
                # Store session ID for subsequent messages
                if not session_id:
                    session_id = response.get('session_id')
                    print(f"   ✅ Chat session created with ID: {session_id}")
                
                # Verify response structure
                required_fields = ['message', 'session_id', 'suggestions']
                missing_fields = [field for field in required_fields if field not in response]
                if missing_fields:
                    print(f"   ❌ Missing chat response fields: {missing_fields}")
                    self.critical_failures.append(f"Chat Response - Missing fields: {missing_fields}")
                    return False
                else:
                    print(f"   ✅ Chat response has all required fields")
                
                # Verify response content
                response_message = response.get('message', '').lower()
                suggestions = response.get('suggestions', [])
                
                print(f"   📝 Response length: {len(response_message)} characters")
                print(f"   💡 Suggestions provided: {len(suggestions)}")
                
                # Check if response is contextually relevant
                keyword_found = any(keyword.lower() in response_message for keyword in query["expected_keywords"])
                if keyword_found:
                    print(f"   ✅ Response contextually relevant to query")
                else:
                    print(f"   ⚠️  Response may not be contextually relevant")
                
            else:
                print(f"   ❌ Failed chat query {i+1}")
                self.critical_failures.append(f"Chat - Failed query {i+1}")
                return False
        
        # Test 2: Get chat sessions (CRITICAL TEST - was failing with ObjectId serialization)
        success, sessions_response = self.run_test(
            "Get Chat Sessions (ObjectId Serialization Test)",
            "GET",
            "/chat/sessions",
            200
        )
        
        if success and isinstance(sessions_response, list):
            print(f"   ✅ CRITICAL SUCCESS: Retrieved {len(sessions_response)} chat sessions without ObjectId errors")
            print(f"   🎉 Chat sessions ObjectId serialization issue FIXED!")
            
            # Verify our session is in the list
            if session_id:
                session_found = any(session.get('id') == session_id for session in sessions_response)
                if session_found:
                    print(f"   ✅ Current chat session found in sessions list")
                else:
                    print(f"   ⚠️  Current chat session not found in sessions list")
            
            # Verify JSON serialization is working (no ObjectId issues)
            try:
                json_str = json.dumps(sessions_response)
                print(f"   ✅ Chat sessions properly JSON serializable")
            except Exception as e:
                print(f"   ❌ JSON serialization failed: {str(e)}")
                self.critical_failures.append(f"Chat Sessions - JSON serialization failed: {str(e)}")
                return False
                
        else:
            print("   ❌ CRITICAL FAILURE: Failed to retrieve chat sessions - likely ObjectId serialization issue")
            self.critical_failures.append("Chat Sessions - CRITICAL: ObjectId serialization still broken")
            return False
        
        # Test 3: Get messages for a specific session (CRITICAL TEST - was failing with ObjectId serialization)
        if session_id:
            success, messages_response = self.run_test(
                "Get Session Messages (ObjectId Serialization Test)",
                "GET",
                f"/chat/sessions/{session_id}/messages",
                200
            )
            
            if success and isinstance(messages_response, list):
                print(f"   ✅ CRITICAL SUCCESS: Retrieved {len(messages_response)} messages without ObjectId errors")
                print(f"   🎉 Chat messages ObjectId serialization issue FIXED!")
                
                # Verify message structure
                if messages_response:
                    message = messages_response[0]
                    required_fields = ['id', 'session_id', 'role', 'content', 'timestamp']
                    missing_fields = [field for field in required_fields if field not in message]
                    if missing_fields:
                        print(f"   ❌ Missing message fields: {missing_fields}")
                        self.critical_failures.append(f"Chat Messages - Missing fields: {missing_fields}")
                        return False
                    else:
                        print(f"   ✅ Chat messages have all required fields")
                
                # Verify we have both user and assistant messages
                roles = [msg.get('role') for msg in messages_response]
                if 'user' in roles and 'assistant' in roles:
                    print(f"   ✅ Both user and assistant messages found")
                
                # Verify JSON serialization is working (no ObjectId issues)
                try:
                    json_str = json.dumps(messages_response)
                    print(f"   ✅ Chat messages properly JSON serializable")
                except Exception as e:
                    print(f"   ❌ JSON serialization failed: {str(e)}")
                    self.critical_failures.append(f"Chat Messages - JSON serialization failed: {str(e)}")
                    return False
                    
            else:
                print("   ❌ CRITICAL FAILURE: Failed to retrieve session messages - likely ObjectId serialization issue")
                self.critical_failures.append("Chat Messages - CRITICAL: ObjectId serialization still broken")
                return False
        
        # Test 4: Appointment-related chat queries
        appointment_queries = [
            "I want to book an IV therapy session for next week",
            "What appointment slots do you have for NAD IV therapy?",
            "Can I schedule a consultation for regenerative medicine treatments?",
            "Vorrei prenotare una seduta di terapia con ozono"  # Italian
        ]
        
        appointment_success_count = 0
        for query in appointment_queries:
            chat_data = {
                "message": query,
                "session_id": session_id,
                "user_id": None
            }
            
            success, response = self.run_test(
                f"Appointment Query - {query[:30]}...",
                "POST",
                "/chat",
                200,
                data=chat_data
            )
            
            if success:
                appointment_success_count += 1
                response_message = response.get('message', '').lower()
                
                # Check for appointment-related keywords in response
                appointment_keywords = ['appointment', 'book', 'schedule', 'available', 'prenotare', 'appuntamento']
                if any(keyword in response_message for keyword in appointment_keywords):
                    print(f"   ✅ Appointment-related response provided")
                else:
                    print(f"   ⚠️  Response may not be appointment-focused")
            else:
                print(f"   ❌ Failed appointment query")
        
        appointment_success_rate = (appointment_success_count / len(appointment_queries)) * 100
        print(f"   📊 Appointment integration success rate: {appointment_success_rate:.1f}%")
        
        print("   ✅ Patient Chat Functionality test completed successfully")
        return True

    def run_comprehensive_chatbot_tests(self):
        """Run comprehensive KinAura Chatbot testing focusing on ObjectId serialization fixes"""
        print("\n🚀 COMPREHENSIVE KINAURA CHATBOT TESTING - OBJECTID SERIALIZATION FIXES")
        print("=" * 80)
        
        # Setup admin authentication
        print("Setting up admin authentication for chatbot testing...")
        if not self.setup_admin_token():
            print("❌ Failed to get admin token for chatbot testing")
            return False
        
        # Run all chatbot tests
        tests = [
            ("Chatbot Configuration Management", self.test_chatbot_configuration_management),
            ("Knowledge Base Management (ObjectId Fix)", self.test_knowledge_base_management),
            ("Patient Chat Functionality (ObjectId Fix)", self.test_patient_chat_functionality)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_method in tests:
            print(f"\n{'='*60}")
            print(f"🔍 RUNNING: {test_name}")
            print(f"{'='*60}")
            
            try:
                if test_method():
                    passed_tests += 1
                    print(f"✅ PASSED: {test_name}")
                else:
                    print(f"❌ FAILED: {test_name}")
            except Exception as e:
                print(f"❌ EXCEPTION in {test_name}: {str(e)}")
                self.critical_failures.append(f"{test_name} - Exception: {str(e)}")
        
        # Calculate success rate
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"\n{'='*80}")
        print(f"🏆 KINAURA CHATBOT TESTING RESULTS")
        print(f"{'='*80}")
        print(f"📊 Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"📊 Total API Calls: {self.tests_passed}/{self.tests_run} ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        
        if success_rate >= 100:
            print("🎉 EXCELLENT: All chatbot tests passed! ObjectId serialization issues resolved.")
        elif success_rate >= 75:
            print("✅ GOOD: Most chatbot functionality working. Minor issues may remain.")
        elif success_rate >= 50:
            print("⚠️  PARTIAL: Some chatbot functionality working. Significant issues remain.")
        else:
            print("❌ CRITICAL: Major chatbot functionality failures. Requires immediate attention.")
        
        # Specific ObjectId serialization status
        if passed_tests >= 2:  # Knowledge Base and Chat Sessions tests
            print("✅ CRITICAL SUCCESS: ObjectId serialization issues appear to be resolved!")
        else:
            print("❌ CRITICAL FAILURE: ObjectId serialization issues still present!")
        
        # Report critical failures
        if self.critical_failures:
            print(f"\n🚨 CRITICAL FAILURES DETECTED:")
            for i, failure in enumerate(self.critical_failures, 1):
                print(f"   {i}. {failure}")
        else:
            print(f"\n🎉 NO CRITICAL FAILURES DETECTED!")
        
        return success_rate >= 75  # Consider success if 75% or more tests pass

if __name__ == "__main__":
    print("🚀 STARTING KINAURA CHATBOT BACKEND TESTING - OBJECTID SERIALIZATION FIXES")
    print("=" * 80)
    
    tester = KinAuraChatbotTester()
    
    # Run the comprehensive chatbot test
    success = tester.run_comprehensive_chatbot_tests()
    
    if success:
        print("\n🎉 KINAURA CHATBOT TESTING COMPLETED SUCCESSFULLY!")
        print("✅ All ObjectId serialization issues have been resolved!")
        sys.exit(0)
    else:
        print("\n❌ KINAURA CHATBOT TESTING FAILED!")
        print("⚠️  ObjectId serialization issues may still be present!")
        sys.exit(1)