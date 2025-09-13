import requests
import sys
import json
import uuid
from datetime import datetime, timedelta

class KinAuraProtocolTester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
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

    def test_admin_social_login(self):
        """Test admin social login with role assignment"""
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
            # Store admin token for further tests
            self.admin_token = response.get('access_token')
            user_data = response.get('user', {})
            print(f"   ✅ Admin user created with ID: {user_data.get('id')}")
            
            # Check if admin role is properly assigned
            if user_data.get('role') == 'admin':
                print(f"   ✅ Admin role properly assigned")
            else:
                print(f"   ❌ Admin role not assigned, got: {user_data.get('role')}")
                
            # Check membership tier for admin
            if user_data.get('membership_tier') == 'elite':
                print(f"   ✅ Admin membership tier set to elite")
            else:
                print(f"   ⚠️  Admin membership tier: {user_data.get('membership_tier')}")
        
        return success

    def test_protocol_knowledge_base_population(self):
        """Test Protocol Knowledge Base Population"""
        print("\n🔍 Testing Protocol Knowledge Base Population...")
        
        if not hasattr(self, 'admin_token') or not self.admin_token:
            print("❌ No admin token available for protocol knowledge base test")
            return False
        
        # Test populating protocol knowledge base
        success, response = self.run_test(
            "Populate Protocol Knowledge Base",
            "POST",
            "/admin/knowledge-base/populate-protocols",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            protocols_added = response.get('protocols_added', 0)
            items_created = response.get('items_created', 0)
            print(f"   ✅ Populated knowledge base with {protocols_added} protocols")
            print(f"   ✅ Created {items_created} knowledge base items")
            
            # Verify expected count (12 protocols × 2 languages = 24 items)
            if items_created == 24:
                print(f"   ✅ Correct number of bilingual protocol items created")
            else:
                print(f"   ⚠️  Expected 24 items, got {items_created}")
        else:
            print("   ❌ Failed to populate protocol knowledge base")
            return False
        
        # Test getting knowledge base items to verify population
        success, kb_response = self.run_test(
            "Verify Knowledge Base Items",
            "GET",
            "/admin/knowledge-base/items?category=protocols",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and isinstance(kb_response, list):
            protocol_items = [item for item in kb_response if 'protocol' in item.get('tags', [])]
            print(f"   ✅ Found {len(protocol_items)} protocol items in knowledge base")
            
            # Verify bilingual content
            english_items = [item for item in protocol_items if 'en' in item.get('tags', [])]
            italian_items = [item for item in protocol_items if 'it' in item.get('tags', [])]
            
            print(f"   ✅ English protocol items: {len(english_items)}")
            print(f"   ✅ Italian protocol items: {len(italian_items)}")
            
            if len(english_items) == len(italian_items) == 12:
                print(f"   ✅ Bilingual protocol coverage complete")
            else:
                print(f"   ⚠️  Expected 12 items per language")
        else:
            print("   ❌ Failed to verify knowledge base items")
            return False
        
        return True

    def test_protocol_detection_and_recommendation(self):
        """Test Protocol Detection and Recommendation"""
        print("\n🔍 Testing Protocol Detection and Recommendation...")
        
        # Test concern-based queries in English
        concern_queries_en = [
            "What can I do for cellulite?",
            "I have wrinkles and fine lines",
            "Help with pigmentation and dark spots",
            "I'm dealing with acne scars"
        ]
        
        for query in concern_queries_en:
            success, response = self.run_test(
                f"Concern Query EN: '{query[:30]}...'",
                "POST",
                "/chat",
                200,
                data={"message": query, "user_id": "test_user_en"}
            )
            
            if success:
                chat_response = response.get('message', '')
                protocol_recommendations = response.get('protocol_recommendations', [])
                
                if protocol_recommendations:
                    print(f"   ✅ Protocol recommendations found: {len(protocol_recommendations)}")
                    for protocol in protocol_recommendations:
                        protocol_name = protocol.get('protocol_name', 'Unknown')
                        print(f"      → {protocol_name}")
                else:
                    print(f"   ⚠️  No protocol recommendations for: {query[:30]}...")
            else:
                print(f"   ❌ Failed concern query: {query[:30]}...")
                return False
        
        # Test concern-based queries in Italian
        concern_queries_it = [
            "Cosa posso fare per la cellulite?",
            "Ho rughe e linee sottili",
            "Aiuto con pigmentazione e macchie",
            "Sto affrontando cicatrici da acne"
        ]
        
        for query in concern_queries_it:
            success, response = self.run_test(
                f"Concern Query IT: '{query[:30]}...'",
                "POST",
                "/chat",
                200,
                data={"message": query, "user_id": "test_user_it"}
            )
            
            if success:
                chat_response = response.get('message', '')
                protocol_recommendations = response.get('protocol_recommendations', [])
                
                # Check if response is in Italian
                italian_indicators = ['protocollo', 'trattamento', 'terapia', 'kinaura']
                has_italian = any(indicator in chat_response.lower() for indicator in italian_indicators)
                
                if has_italian:
                    print(f"   ✅ Italian response detected")
                
                if protocol_recommendations:
                    print(f"   ✅ Protocol recommendations found: {len(protocol_recommendations)}")
                else:
                    print(f"   ⚠️  No protocol recommendations for: {query[:30]}...")
            else:
                print(f"   ❌ Failed Italian concern query: {query[:30]}...")
                return False
        
        # Test treatment booking queries
        booking_queries = [
            "I want to book Morpheus8",
            "Vorrei prenotare HBOT",
            "Can I schedule IV therapy?",
            "Posso prenotare Red Light Therapy?"
        ]
        
        for query in booking_queries:
            success, response = self.run_test(
                f"Booking Query: '{query[:30]}...'",
                "POST",
                "/chat",
                200,
                data={"message": query, "user_id": "test_booking_user"}
            )
            
            if success:
                chat_response = response.get('message', '')
                booking_intent = response.get('booking_intent_detected', False)
                protocol_recommendations = response.get('protocol_recommendations', [])
                
                if booking_intent:
                    print(f"   ✅ Booking intent detected")
                
                if protocol_recommendations:
                    print(f"   ✅ Related protocol recommendations: {len(protocol_recommendations)}")
                
                # Check for booking guidance in response
                booking_keywords = ['book', 'appointment', 'schedule', 'prenotare', 'appuntamento']
                has_booking_guidance = any(keyword in chat_response.lower() for keyword in booking_keywords)
                
                if has_booking_guidance:
                    print(f"   ✅ Booking guidance provided")
            else:
                print(f"   ❌ Failed booking query: {query[:30]}...")
                return False
        
        return True

    def test_chat_endpoint_enhancement(self):
        """Test Chat Endpoint Enhancement with Protocol Integration"""
        print("\n🔍 Testing Chat Endpoint Enhancement...")
        
        # Test various query types with protocol integration
        test_scenarios = [
            {
                "query": "What's the best treatment for anti-aging?",
                "user_id": "antiaging_user",
                "expected_protocols": ["longevity", "wrinkles"],
                "language": "en"
            },
            {
                "query": "Qual è il miglior trattamento per l'anti-invecchiamento?",
                "user_id": "antiaging_user_it",
                "expected_protocols": ["longevity", "wrinkles"],
                "language": "it"
            },
            {
                "query": "I'm interested in comprehensive skin rejuvenation",
                "user_id": "skin_user",
                "expected_protocols": ["skin-laxity", "wrinkles", "pigmentation"],
                "language": "en"
            },
            {
                "query": "Help me with fatigue and low energy",
                "user_id": "energy_user",
                "expected_protocols": ["fatigue"],
                "language": "en"
            },
            {
                "query": "Aiutami con stanchezza e poca energia",
                "user_id": "energy_user_it",
                "expected_protocols": ["fatigue"],
                "language": "it"
            }
        ]
        
        for scenario in test_scenarios:
            success, response = self.run_test(
                f"Enhanced Chat: '{scenario['query'][:40]}...'",
                "POST",
                "/chat",
                200,
                data={"message": scenario['query'], "user_id": scenario['user_id']}
            )
            
            if success:
                chat_response = response.get('message', '')
                protocol_recommendations = response.get('protocol_recommendations', [])
                suggestions = response.get('suggestions', [])
                
                # Verify protocol recommendations
                if protocol_recommendations:
                    print(f"   ✅ Protocol recommendations: {len(protocol_recommendations)}")
                    
                    # Check if expected protocols are included
                    recommended_keys = [p.get('protocol_key', '') for p in protocol_recommendations]
                    found_expected = any(expected in recommended_keys for expected in scenario['expected_protocols'])
                    
                    if found_expected:
                        print(f"   ✅ Expected protocol types found")
                    else:
                        print(f"   ⚠️  Expected protocols not found: {scenario['expected_protocols']}")
                
                # Verify language detection
                if scenario['language'] == 'it':
                    italian_indicators = ['protocollo', 'trattamento', 'kinaura', 'terapia']
                    has_italian = any(indicator in chat_response.lower() for indicator in italian_indicators)
                    if has_italian:
                        print(f"   ✅ Italian language response detected")
                    else:
                        print(f"   ⚠️  Italian response not detected")
                
                # Verify suggestions provided
                if suggestions:
                    print(f"   ✅ Follow-up suggestions: {len(suggestions)}")
                
                # Verify KinAura exclusivity messaging
                exclusivity_keywords = ['kinaura', 'exclusive', 'only', 'milan', 'esclusivo', 'solo']
                has_exclusivity = any(keyword in chat_response.lower() for keyword in exclusivity_keywords)
                
                if has_exclusivity:
                    print(f"   ✅ KinAura exclusivity messaging present")
                else:
                    print(f"   ⚠️  KinAura exclusivity messaging not detected")
            else:
                print(f"   ❌ Failed enhanced chat test: {scenario['query'][:40]}...")
                return False
        
        return True

    def test_knowledge_base_integration(self):
        """Test Knowledge Base Integration with Protocol Data"""
        print("\n🔍 Testing Knowledge Base Integration...")
        
        if not hasattr(self, 'admin_token') or not self.admin_token:
            print("❌ No admin token available for knowledge base integration test")
            return False
        
        # Test 1: Verify protocol tags and categorization
        success, response = self.run_test(
            "Get Protocol Knowledge Base Items",
            "GET",
            "/admin/knowledge-base/items?category=protocols",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and isinstance(response, list):
            protocol_items = response
            print(f"   ✅ Retrieved {len(protocol_items)} protocol knowledge base items")
            
            # Verify tag structure
            expected_tags = ['protocol', 'concern:', 'morpheus8', 'pbm', 'hbot', 'iv', 'exosomes']
            found_tags = set()
            
            for item in protocol_items:
                item_tags = item.get('tags', [])
                found_tags.update(item_tags)
            
            matching_tags = [tag for tag in expected_tags if any(tag in found_tag for found_tag in found_tags)]
            print(f"   ✅ Found expected tag types: {len(matching_tags)}/{len(expected_tags)}")
            
            # Verify bilingual content structure
            english_items = [item for item in protocol_items if any('en' in tag for tag in item.get('tags', []))]
            italian_items = [item for item in protocol_items if any('it' in tag for tag in item.get('tags', []))]
            
            if len(english_items) > 0 and len(italian_items) > 0:
                print(f"   ✅ Bilingual protocol content verified")
                print(f"      English items: {len(english_items)}")
                print(f"      Italian items: {len(italian_items)}")
            else:
                print(f"   ❌ Bilingual content not found")
                return False
        else:
            print("   ❌ Failed to retrieve protocol knowledge base items")
            return False
        
        # Test 2: Search and retrieval functionality
        search_terms = ['morpheus8', 'cellulite', 'anti-aging', 'fatigue']
        
        for term in search_terms:
            success, search_response = self.run_test(
                f"Search Knowledge Base: '{term}'",
                "GET",
                f"/admin/knowledge-base/search?query={term}",
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success and isinstance(search_response, list):
                results_count = len(search_response)
                print(f"   ✅ Search '{term}': {results_count} results")
                
                # Verify search results contain relevant protocol information
                if results_count > 0:
                    first_result = search_response[0]
                    if 'protocol' in first_result.get('tags', []):
                        print(f"      → Protocol-related result found")
            else:
                print(f"   ❌ Failed to search for: {term}")
                return False
        
        # Test 3: Protocol context integration in chat
        context_test_query = "Tell me about treatments for skin laxity"
        success, chat_response = self.run_test(
            "Protocol Context Integration Test",
            "POST",
            "/chat",
            200,
            data={"message": context_test_query, "user_id": "context_test_user"}
        )
        
        if success:
            response_message = chat_response.get('message', '')
            protocol_recommendations = chat_response.get('protocol_recommendations', [])
            
            # Verify protocol information is integrated into response
            protocol_keywords = ['morpheus8', 'red light', 'hbot', 'exosomes']
            found_keywords = [kw for kw in protocol_keywords if kw.lower() in response_message.lower()]
            
            if found_keywords:
                print(f"   ✅ Protocol context integrated: {found_keywords}")
            else:
                print(f"   ⚠️  Protocol context not clearly integrated")
            
            if protocol_recommendations:
                print(f"   ✅ Protocol recommendations provided: {len(protocol_recommendations)}")
        else:
            print("   ❌ Failed protocol context integration test")
            return False
        
        return True

    def test_luxury_positioning_and_exclusivity(self):
        """Test KinAura Luxury Positioning and Exclusivity Messaging"""
        print("\n🔍 Testing KinAura Luxury Positioning and Exclusivity...")
        
        # Test queries that should trigger luxury positioning
        luxury_test_queries = [
            "What makes KinAura different?",
            "Why should I choose KinAura?",
            "Cosa rende KinAura diverso?",
            "Tell me about your exclusive treatments",
            "What advanced technology do you have?"
        ]
        
        for query in luxury_test_queries:
            success, response = self.run_test(
                f"Luxury Positioning: '{query[:35]}...'",
                "POST",
                "/chat",
                200,
                data={"message": query, "user_id": "luxury_test_user"}
            )
            
            if success:
                chat_response = response.get('message', '')
                
                # Check for luxury positioning keywords
                luxury_keywords = [
                    'exclusive', 'esclusivo', 'only', 'solo', 'milan', 'milano',
                    'advanced', 'latest', 'newest', 'hospital-grade', 'sterile',
                    'harvard', 'luxury', 'premium', 'elite', 'regenerative'
                ]
                
                found_luxury_keywords = [kw for kw in luxury_keywords if kw.lower() in chat_response.lower()]
                
                if found_luxury_keywords:
                    print(f"   ✅ Luxury positioning detected: {found_luxury_keywords[:3]}")
                else:
                    print(f"   ⚠️  Luxury positioning not clearly present")
                
                # Check for KinAura exclusivity claims
                exclusivity_phrases = [
                    'only kinaura', 'solo kinaura', 'exclusive to kinaura',
                    'first in milan', 'primo a milano', 'unique combination'
                ]
                
                found_exclusivity = any(phrase in chat_response.lower() for phrase in exclusivity_phrases)
                
                if found_exclusivity:
                    print(f"   ✅ KinAura exclusivity messaging present")
                else:
                    print(f"   ⚠️  KinAura exclusivity messaging not detected")
            else:
                print(f"   ❌ Failed luxury positioning test: {query[:35]}...")
                return False
        
        return True

    def run_protocol_tests(self):
        """Run all protocol-based recommendation system tests"""
        print("\n" + "="*80)
        print("🧪 KINAURA PROTOCOL-BASED RECOMMENDATION SYSTEM TESTING")
        print("="*80)
        
        # First ensure we have admin authentication
        if not hasattr(self, 'admin_token') or not self.admin_token:
            print("Setting up admin authentication...")
            admin_success = self.test_admin_social_login()
            if not admin_success:
                print("❌ Failed to authenticate admin user")
                return False
        
        protocol_tests = [
            ("Protocol Knowledge Base Population", self.test_protocol_knowledge_base_population),
            ("Protocol Detection and Recommendation", self.test_protocol_detection_and_recommendation),
            ("Chat Endpoint Enhancement", self.test_chat_endpoint_enhancement),
            ("Knowledge Base Integration", self.test_knowledge_base_integration),
            ("Luxury Positioning and Exclusivity", self.test_luxury_positioning_and_exclusivity)
        ]
        
        passed_tests = 0
        total_tests = len(protocol_tests)
        
        for test_name, test_func in protocol_tests:
            print(f"\n{'='*60}")
            print(f"🔬 {test_name}")
            print(f"{'='*60}")
            
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name} - PASSED")
                else:
                    print(f"❌ {test_name} - FAILED")
            except Exception as e:
                print(f"❌ {test_name} - ERROR: {str(e)}")
        
        # Final results
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n{'='*80}")
        print(f"📊 PROTOCOL TESTING RESULTS")
        print(f"{'='*80}")
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"Tests Run: {self.tests_run}")
        print(f"Overall Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if success_rate >= 80:
            print("🎉 PROTOCOL SYSTEM TESTING COMPLETED SUCCESSFULLY!")
            return True
        else:
            print("⚠️  PROTOCOL SYSTEM TESTING COMPLETED WITH ISSUES")
            return False


if __name__ == "__main__":
    tester = KinAuraProtocolTester()
    
    print("🚀 Starting KinAura Protocol-Based Recommendation System Testing...")
    print("=" * 80)
    
    # Run protocol-specific tests
    success = tester.run_protocol_tests()
    
    if success:
        print("\n🎉 ALL PROTOCOL TESTS COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n❌ SOME PROTOCOL TESTS FAILED")
        sys.exit(1)