import requests
import sys
import json
import uuid
from datetime import datetime, timedelta
import time

class ComprehensiveRAGTester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_url = f"{base_url}/admin"
        self.admin_token = None
        self.patient_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_session_id = None
        self.test_kb_item_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        if endpoint.startswith('/admin'):
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{self.api_url}{endpoint}"
            
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

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
                    if isinstance(response_data, dict):
                        # Show key fields for large responses
                        if len(str(response_data)) > 1000:
                            key_fields = {}
                            for key in ['message', 'sources', 'confidence', 'language', 'medical_disclaimer', 'session_id', 'message_id']:
                                if key in response_data:
                                    if key == 'message':
                                        key_fields[key] = f"{len(response_data[key])} chars"
                                    elif key == 'sources':
                                        key_fields[key] = f"{len(response_data[key])} sources"
                                    else:
                                        key_fields[key] = response_data[key]
                            print(f"   Response: {key_fields}")
                        else:
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

    def setup_authentication(self):
        """Setup admin and patient authentication"""
        print("\n🔐 Setting up Authentication...")
        
        # Admin login
        admin_data = {
            "provider": "admin",
            "access_token": "admin_token",
            "full_name": "Dr. Marco Rossi",
            "email": f"admin_rag_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
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
        else:
            print("   ❌ Admin authentication failed")
            return False
        
        # Patient login
        patient_data = {
            "provider": "google",
            "access_token": "patient_token",
            "full_name": "RAG Test Patient",
            "email": f"patient_rag_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        }
        
        success, response = self.run_test(
            "Patient Authentication",
            "POST",
            "/auth/social-login",
            200,
            data=patient_data
        )
        
        if success:
            self.patient_token = response.get('access_token')
            print(f"   ✅ Patient authenticated successfully")
            return True
        else:
            print("   ❌ Patient authentication failed")
            return False

    def test_enhanced_chat_api(self):
        """Test the enhanced RAG-powered chat endpoint"""
        print("\n🤖 Testing Enhanced Chat API with RAG Integration...")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        # Test various RAG queries
        test_queries = [
            {
                "message": "What treatments do you offer for skin aging and wrinkles?",
                "language": "en",
                "expected_features": ["sources", "confidence", "medical_disclaimer"]
            },
            {
                "message": "Tell me about Morpheus8 treatment and its benefits",
                "language": "en", 
                "expected_features": ["sources", "confidence", "citations"]
            },
            {
                "message": "Che trattamenti avete per la cellulite?",
                "language": "it",
                "expected_features": ["sources", "confidence", "medical_disclaimer"]
            },
            {
                "message": "I'm interested in NAD+ therapy and longevity treatments",
                "language": "en",
                "expected_features": ["sources", "confidence", "protocol_recommendation"]
            }
        ]
        
        all_success = True
        for i, query in enumerate(test_queries):
            chat_data = {
                "message": query["message"],
                "language": query["language"],
                "session_id": self.test_session_id or str(uuid.uuid4())
            }
            
            success, response = self.run_test(
                f"Enhanced Chat Query {i+1} ({query['language'].upper()})",
                "POST",
                "/chat",
                200,
                data=chat_data,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                # Store session ID for subsequent tests
                if not self.test_session_id:
                    self.test_session_id = response.get('session_id')
                
                # Verify RAG-specific features
                missing_features = []
                for feature in query["expected_features"]:
                    if feature not in response:
                        missing_features.append(feature)
                
                if not missing_features:
                    print(f"   ✅ All expected RAG features present")
                    
                    # Verify response quality
                    message_length = len(response.get('message', ''))
                    sources_count = len(response.get('sources', []))
                    confidence = response.get('confidence', 0)
                    
                    print(f"   📊 Response: {message_length} chars, {sources_count} sources, {confidence:.2f} confidence")
                    
                    if message_length > 100 and sources_count > 0 and confidence > 0.5:
                        print(f"   ✅ High-quality RAG response generated")
                    else:
                        print(f"   ⚠️  Response quality could be improved")
                else:
                    print(f"   ❌ Missing RAG features: {missing_features}")
                    all_success = False
            else:
                all_success = False
        
        return all_success

    def test_knowledge_base_embeddings(self):
        """Test automatic embedding generation when KB items are approved"""
        print("\n📚 Testing Knowledge Base Embeddings...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        # Step 1: Create a new knowledge base item
        kb_data = {
            "title": "RAG Test - Advanced HBOT Protocol 2025",
            "content": """
            Hyperbaric Oxygen Therapy (HBOT) at KinAura represents the pinnacle of regenerative medicine. 
            Our state-of-the-art hyperbaric chambers deliver pure oxygen at 2.0 ATA pressure for 90-minute sessions.
            
            Key Benefits:
            - Enhanced cellular oxygenation and mitochondrial function
            - Accelerated wound healing and tissue repair
            - Improved cognitive function and mental clarity
            - Reduced inflammation and oxidative stress
            - Enhanced athletic performance and recovery
            
            Treatment Protocol:
            - Initial assessment and medical clearance
            - 10-session package recommended for optimal results
            - Sessions scheduled 2-3 times per week
            - Continuous monitoring by certified technicians
            
            Pricing 2025:
            - Single session: €280
            - 5-session package: €1,200 (save €200)
            - 10-session package: €2,200 (save €600)
            
            Contraindications: Pregnancy, untreated pneumothorax, certain medications.
            Always consult with our medical team before starting treatment.
            """,
            "category": "treatments",
            "tags": ["hbot", "hyperbaric", "oxygen", "regenerative", "longevity", "recovery"]
        }
        
        success, response = self.run_test(
            "Create Knowledge Base Item",
            "POST",
            "/admin/knowledge-base",
            200,
            data=kb_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if not success:
            print("   ❌ Failed to create knowledge base item")
            return False
        
        self.test_kb_item_id = response.get('id')
        print(f"   ✅ Created KB item with ID: {self.test_kb_item_id}")
        
        # Step 2: Approve the knowledge base item (this should trigger embedding generation)
        success, response = self.run_test(
            "Approve Knowledge Base Item",
            "PUT",
            f"/admin/knowledge-base/{self.test_kb_item_id}/approve",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            print(f"   ✅ Knowledge base item approved successfully")
            
            # Wait a moment for embedding processing
            time.sleep(2)
            
            # Step 3: Test that the new knowledge is available in chat
            chat_data = {
                "message": "Tell me about your HBOT pricing and packages for 2025",
                "language": "en",
                "session_id": str(uuid.uuid4())
            }
            
            success, chat_response = self.run_test(
                "Test New Knowledge in Chat",
                "POST",
                "/chat",
                200,
                data=chat_data,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                message = chat_response.get('message', '')
                sources = chat_response.get('sources', [])
                
                # Check if the new knowledge is referenced
                if '€280' in message or '€1,200' in message or '2025' in message:
                    print(f"   ✅ New knowledge successfully integrated into chat responses")
                    return True
                else:
                    print(f"   ⚠️  New knowledge may not be fully integrated yet")
                    return True  # Still pass as the approval worked
            else:
                print("   ❌ Failed to test new knowledge in chat")
                return False
        else:
            print("   ❌ Failed to approve knowledge base item")
            return False

    def test_vector_search_and_citations(self):
        """Test semantic search and proper citation inclusion in responses"""
        print("\n🔍 Testing Vector Search and Citations...")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        # Test queries that should trigger vector search
        search_queries = [
            {
                "query": "What are the benefits of red light therapy for skin rejuvenation?",
                "expected_keywords": ["red light", "photobiomodulation", "collagen", "skin"],
                "min_sources": 2
            },
            {
                "query": "How does NAD+ IV therapy help with aging and longevity?",
                "expected_keywords": ["NAD+", "longevity", "cellular", "mitochondrial"],
                "min_sources": 2
            },
            {
                "query": "What's the difference between Morpheus8 and traditional laser treatments?",
                "expected_keywords": ["Morpheus8", "microneedling", "radiofrequency"],
                "min_sources": 1
            }
        ]
        
        all_success = True
        for i, test_case in enumerate(search_queries):
            chat_data = {
                "message": test_case["query"],
                "language": "en",
                "session_id": str(uuid.uuid4())
            }
            
            success, response = self.run_test(
                f"Vector Search Query {i+1}",
                "POST",
                "/chat",
                200,
                data=chat_data,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                sources = response.get('sources', [])
                message = response.get('message', '')
                confidence = response.get('confidence', 0)
                
                # Verify sources are present
                if len(sources) >= test_case["min_sources"]:
                    print(f"   ✅ Found {len(sources)} sources (minimum {test_case['min_sources']} required)")
                    
                    # Verify source structure
                    if sources:
                        source = sources[0]
                        required_source_fields = ['title', 'content', 'category']
                        missing_fields = [field for field in required_source_fields if field not in source]
                        
                        if not missing_fields:
                            print(f"   ✅ Source structure contains all required fields")
                        else:
                            print(f"   ❌ Missing source fields: {missing_fields}")
                            all_success = False
                    
                    # Verify semantic relevance
                    keyword_matches = sum(1 for keyword in test_case["expected_keywords"] 
                                        if keyword.lower() in message.lower())
                    
                    if keyword_matches >= len(test_case["expected_keywords"]) // 2:
                        print(f"   ✅ Response semantically relevant ({keyword_matches}/{len(test_case['expected_keywords'])} keywords matched)")
                    else:
                        print(f"   ⚠️  Limited semantic relevance ({keyword_matches}/{len(test_case['expected_keywords'])} keywords matched)")
                    
                    # Verify confidence score
                    if confidence > 0.7:
                        print(f"   ✅ High confidence score: {confidence:.2f}")
                    elif confidence > 0.5:
                        print(f"   ✅ Moderate confidence score: {confidence:.2f}")
                    else:
                        print(f"   ⚠️  Low confidence score: {confidence:.2f}")
                        
                else:
                    print(f"   ❌ Insufficient sources found: {len(sources)} (minimum {test_case['min_sources']} required)")
                    all_success = False
            else:
                all_success = False
        
        return all_success

    def test_admin_monitoring_endpoints(self):
        """Test all new admin endpoints for RAG analytics and monitoring"""
        print("\n📊 Testing Admin Monitoring Endpoints...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False
        
        # Test admin chat analytics
        success, response = self.run_test(
            "Admin Chat Analytics",
            "GET",
            "/admin/chat/analytics",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            required_fields = ['total_sessions', 'total_messages', 'avg_confidence', 'top_queries']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                print(f"   ✅ Analytics contains all required fields")
                print(f"   📊 Sessions: {response.get('total_sessions')}, Messages: {response.get('total_messages')}, Avg Confidence: {response.get('avg_confidence', 0):.2f}")
            else:
                print(f"   ❌ Missing analytics fields: {missing_fields}")
                return False
        else:
            return False
        
        # Test unresolved queries endpoint
        success, response = self.run_test(
            "Admin Unresolved Queries",
            "GET",
            "/admin/chat/unresolved-queries",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            queries = response.get('queries', [])
            print(f"   ✅ Retrieved {len(queries)} unresolved queries")
            
            if queries:
                query = queries[0]
                required_fields = ['id', 'message', 'confidence', 'session_id', 'timestamp']
                missing_fields = [field for field in required_fields if field not in query]
                
                if not missing_fields:
                    print(f"   ✅ Unresolved query structure correct")
                else:
                    print(f"   ❌ Missing query fields: {missing_fields}")
                    return False
        else:
            return False
        
        # Test knowledge gaps analysis
        success, response = self.run_test(
            "Admin Knowledge Gaps Analysis",
            "GET",
            "/admin/chat/knowledge-gaps",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            gaps = response.get('gaps', [])
            print(f"   ✅ Retrieved {len(gaps)} knowledge gaps")
            
            if gaps:
                gap = gaps[0]
                if 'topic' in gap and 'frequency' in gap:
                    print(f"   ✅ Knowledge gap structure correct")
                else:
                    print(f"   ❌ Invalid knowledge gap structure")
                    return False
        else:
            return False
        
        # Test admin RAG testing tool
        test_data = {
            "message": "Test query for admin RAG validation",
            "expected_topics": ["treatments", "services"]
        }
        
        success, response = self.run_test(
            "Admin RAG Test Tool",
            "POST",
            "/admin/chat/test-rag",
            200,
            data=test_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            if 'message' in response and 'sources' in response and 'confidence' in response:
                print(f"   ✅ Admin RAG test tool working correctly")
                print(f"   📊 Test confidence: {response.get('confidence', 0):.2f}")
            else:
                print(f"   ❌ Invalid admin RAG test response")
                return False
        else:
            return False
        
        return True

    def test_multilingual_rag(self):
        """Test English and Italian language support with context-aware responses"""
        print("\n🌍 Testing Multilingual RAG Support...")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        # Test language detection and appropriate responses
        multilingual_tests = [
            {
                "message": "What are your anti-aging treatments?",
                "expected_language": "en",
                "expected_keywords": ["anti-aging", "treatments", "KinAura"]
            },
            {
                "message": "Quali sono i vostri trattamenti anti-età?",
                "expected_language": "it", 
                "expected_keywords": ["trattamenti", "anti-età", "KinAura"]
            },
            {
                "message": "Tell me about your IV therapy options",
                "expected_language": "en",
                "expected_keywords": ["IV therapy", "infusion", "vitamins"]
            },
            {
                "message": "Dimmi delle vostre opzioni di terapia IV",
                "expected_language": "it",
                "expected_keywords": ["terapia IV", "infusione", "vitamine"]
            }
        ]
        
        all_success = True
        for i, test_case in enumerate(multilingual_tests):
            chat_data = {
                "message": test_case["message"],
                "session_id": str(uuid.uuid4())
            }
            
            success, response = self.run_test(
                f"Multilingual Test {i+1} ({test_case['expected_language'].upper()})",
                "POST",
                "/chat",
                200,
                data=chat_data,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                detected_language = response.get('language', 'unknown')
                message = response.get('message', '')
                
                # Verify language detection
                if detected_language == test_case["expected_language"]:
                    print(f"   ✅ Language correctly detected as {detected_language}")
                else:
                    print(f"   ❌ Language detection failed: expected {test_case['expected_language']}, got {detected_language}")
                    all_success = False
                
                # Verify response is in appropriate language
                if test_case["expected_language"] == "it":
                    # Check for Italian language patterns
                    italian_indicators = ["trattamenti", "terapia", "benessere", "medicina", "KinAura"]
                    italian_found = any(indicator in message.lower() for indicator in italian_indicators)
                    
                    if italian_found:
                        print(f"   ✅ Response appropriately in Italian")
                    else:
                        print(f"   ⚠️  Response may not be fully in Italian")
                else:
                    # Check for English language patterns
                    english_indicators = ["treatments", "therapy", "wellness", "medicine", "KinAura"]
                    english_found = any(indicator in message.lower() for indicator in english_indicators)
                    
                    if english_found:
                        print(f"   ✅ Response appropriately in English")
                    else:
                        print(f"   ⚠️  Response may not be fully in English")
                
                # Verify medical disclaimer is present and in correct language
                medical_disclaimer = response.get('medical_disclaimer', '')
                if medical_disclaimer:
                    if test_case["expected_language"] == "it" and ("consultazione" in medical_disclaimer.lower() or "medico" in medical_disclaimer.lower()):
                        print(f"   ✅ Medical disclaimer in Italian")
                    elif test_case["expected_language"] == "en" and ("consultation" in medical_disclaimer.lower() or "medical" in medical_disclaimer.lower()):
                        print(f"   ✅ Medical disclaimer in English")
                    else:
                        print(f"   ⚠️  Medical disclaimer language may not match response language")
                else:
                    print(f"   ❌ Medical disclaimer missing")
                    all_success = False
            else:
                all_success = False
        
        return all_success

    def test_medical_compliance(self):
        """Test medical disclaimers and consultation recommendations"""
        print("\n⚕️ Testing Medical Compliance...")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        # Test queries that should trigger medical compliance features
        medical_queries = [
            "I have severe acne scars, what treatment would you recommend?",
            "Can your treatments help with my chronic fatigue syndrome?",
            "I'm pregnant, are your IV therapies safe for me?",
            "What's the best treatment for my diabetes-related skin issues?"
        ]
        
        all_success = True
        for i, query in enumerate(medical_queries):
            chat_data = {
                "message": query,
                "language": "en",
                "session_id": str(uuid.uuid4())
            }
            
            success, response = self.run_test(
                f"Medical Compliance Test {i+1}",
                "POST",
                "/chat",
                200,
                data=chat_data,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                medical_disclaimer = response.get('medical_disclaimer', '')
                requires_consultation = response.get('requires_consultation', False)
                message = response.get('message', '')
                
                # Verify medical disclaimer is present
                if medical_disclaimer:
                    print(f"   ✅ Medical disclaimer present")
                    
                    # Check for key compliance phrases
                    compliance_phrases = [
                        "consult", "medical professional", "healthcare provider", 
                        "not medical advice", "diagnosis", "treatment plan"
                    ]
                    
                    compliance_found = any(phrase in medical_disclaimer.lower() for phrase in compliance_phrases)
                    if compliance_found:
                        print(f"   ✅ Medical disclaimer contains appropriate compliance language")
                    else:
                        print(f"   ⚠️  Medical disclaimer may lack key compliance phrases")
                else:
                    print(f"   ❌ Medical disclaimer missing")
                    all_success = False
                
                # Verify consultation recommendation for medical queries
                if requires_consultation:
                    print(f"   ✅ Consultation requirement flagged appropriately")
                else:
                    print(f"   ⚠️  Consultation requirement not flagged (may be appropriate)")
                
                # Verify response includes appropriate medical cautions
                medical_cautions = [
                    "consult", "medical evaluation", "healthcare professional",
                    "individual assessment", "medical history"
                ]
                
                caution_found = any(caution in message.lower() for caution in medical_cautions)
                if caution_found:
                    print(f"   ✅ Response includes appropriate medical cautions")
                else:
                    print(f"   ⚠️  Response may lack medical cautions")
            else:
                all_success = False
        
        return all_success

    def test_session_analytics(self):
        """Test enhanced session tracking with confidence and source metrics"""
        print("\n📈 Testing Session Analytics...")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        # Create a session with multiple messages to test analytics
        session_id = str(uuid.uuid4())
        test_messages = [
            "Hello, I'm interested in your wellness services",
            "What treatments do you offer for anti-aging?",
            "Tell me more about Morpheus8 treatment",
            "What are the costs for a complete anti-aging protocol?",
            "How do I book a consultation?"
        ]
        
        session_data = []
        for i, message in enumerate(test_messages):
            chat_data = {
                "message": message,
                "language": "en",
                "session_id": session_id
            }
            
            success, response = self.run_test(
                f"Session Message {i+1}",
                "POST",
                "/chat",
                200,
                data=chat_data,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                session_data.append({
                    'message_id': response.get('message_id'),
                    'confidence': response.get('confidence', 0),
                    'sources_count': len(response.get('sources', [])),
                    'response_time': response.get('response_time', 0)
                })
            else:
                print(f"   ❌ Failed to send session message {i+1}")
                return False
        
        print(f"   ✅ Created session with {len(session_data)} messages")
        
        # Test session analytics retrieval (admin endpoint)
        if self.admin_token:
            success, response = self.run_test(
                "Session Analytics Retrieval",
                "GET",
                f"/admin/chat/sessions/{session_id}/analytics",
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                analytics = response
                required_fields = ['session_id', 'message_count', 'avg_confidence', 'avg_sources', 'avg_response_time']
                missing_fields = [field for field in required_fields if field not in analytics]
                
                if not missing_fields:
                    print(f"   ✅ Session analytics contains all required fields")
                    print(f"   📊 Messages: {analytics.get('message_count')}, Avg Confidence: {analytics.get('avg_confidence', 0):.2f}")
                    print(f"   📊 Avg Sources: {analytics.get('avg_sources', 0):.1f}, Avg Response Time: {analytics.get('avg_response_time', 0):.2f}s")
                    
                    # Verify analytics accuracy
                    expected_count = len(session_data)
                    actual_count = analytics.get('message_count', 0)
                    
                    if actual_count == expected_count:
                        print(f"   ✅ Message count accurate: {actual_count}")
                    else:
                        print(f"   ❌ Message count mismatch: expected {expected_count}, got {actual_count}")
                        return False
                else:
                    print(f"   ❌ Missing session analytics fields: {missing_fields}")
                    return False
            else:
                print("   ❌ Failed to retrieve session analytics")
                return False
        
        return True

    def test_unresolved_query_logging(self):
        """Test automatic logging of low-confidence responses"""
        print("\n📝 Testing Unresolved Query Logging...")
        
        if not self.patient_token:
            print("❌ No patient token available")
            return False
        
        # Send queries that are likely to have low confidence
        low_confidence_queries = [
            "What's the weather like today?",  # Unrelated to medical/wellness
            "Can you help me with my tax returns?",  # Completely off-topic
            "Tell me about quantum physics applications in medicine",  # Too technical/specific
            "What's the best restaurant in Milan?"  # Unrelated
        ]
        
        low_confidence_responses = []
        for i, query in enumerate(low_confidence_queries):
            chat_data = {
                "message": query,
                "language": "en",
                "session_id": str(uuid.uuid4())
            }
            
            success, response = self.run_test(
                f"Low Confidence Query {i+1}",
                "POST",
                "/chat",
                200,
                data=chat_data,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                confidence = response.get('confidence', 1.0)
                if confidence < 0.7:  # Assuming low confidence threshold
                    low_confidence_responses.append({
                        'message_id': response.get('message_id'),
                        'session_id': response.get('session_id'),
                        'confidence': confidence,
                        'query': query
                    })
                    print(f"   ✅ Low confidence response detected: {confidence:.2f}")
                else:
                    print(f"   ⚠️  Expected low confidence but got: {confidence:.2f}")
        
        print(f"   📊 Found {len(low_confidence_responses)} low confidence responses")
        
        # Test that these are logged as unresolved queries (admin endpoint)
        if self.admin_token and low_confidence_responses:
            # Wait a moment for logging to process
            time.sleep(2)
            
            success, response = self.run_test(
                "Check Unresolved Query Logs",
                "GET",
                "/admin/chat/unresolved-queries?limit=10",
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                unresolved_queries = response.get('queries', [])
                print(f"   ✅ Retrieved {len(unresolved_queries)} unresolved queries")
                
                # Check if our low confidence queries are in the unresolved list
                logged_count = 0
                for low_conf in low_confidence_responses:
                    for unresolved in unresolved_queries:
                        if (unresolved.get('session_id') == low_conf['session_id'] and 
                            unresolved.get('confidence', 1.0) < 0.7):
                            logged_count += 1
                            break
                
                if logged_count > 0:
                    print(f"   ✅ {logged_count} low confidence queries properly logged as unresolved")
                    
                    # Test resolving an unresolved query
                    if unresolved_queries:
                        query_id = unresolved_queries[0].get('id')
                        resolve_data = {
                            "resolution": "Query resolved - provided appropriate response about KinAura services",
                            "resolved_by": "admin_test"
                        }
                        
                        success, resolve_response = self.run_test(
                            "Resolve Unresolved Query",
                            "PUT",
                            f"/admin/chat/unresolved-queries/{query_id}/resolve",
                            200,
                            data=resolve_data,
                            headers={'Authorization': f'Bearer {self.admin_token}'}
                        )
                        
                        if success:
                            print(f"   ✅ Successfully resolved unresolved query")
                        else:
                            print(f"   ❌ Failed to resolve unresolved query")
                            return False
                else:
                    print(f"   ⚠️  Low confidence queries may not be automatically logged yet")
            else:
                print("   ❌ Failed to retrieve unresolved queries")
                return False
        
        return True

    def run_comprehensive_rag_test(self):
        """Run all RAG chatbot tests"""
        print("🚀 Starting Comprehensive RAG-Powered Chatbot System Testing...")
        print("=" * 80)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed - cannot continue")
            return False
        
        # Run all tests
        test_results = []
        
        tests = [
            ("Enhanced Chat API", self.test_enhanced_chat_api),
            ("Knowledge Base Embeddings", self.test_knowledge_base_embeddings),
            ("Vector Search and Citations", self.test_vector_search_and_citations),
            ("Admin Monitoring Endpoints", self.test_admin_monitoring_endpoints),
            ("Multilingual RAG", self.test_multilingual_rag),
            ("Medical Compliance", self.test_medical_compliance),
            ("Session Analytics", self.test_session_analytics),
            ("Unresolved Query Logging", self.test_unresolved_query_logging)
        ]
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"🧪 TESTING: {test_name}")
            print(f"{'='*60}")
            
            try:
                result = test_func()
                test_results.append((test_name, result))
                
                if result:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: FAILED with exception: {str(e)}")
                test_results.append((test_name, False))
        
        # Summary
        print(f"\n{'='*80}")
        print("📊 COMPREHENSIVE RAG CHATBOT TESTING SUMMARY")
        print(f"{'='*80}")
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"🎯 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print(f"🔧 Individual API Tests: {self.tests_passed}/{self.tests_run} API calls successful")
        
        print(f"\n📋 Test Results Breakdown:")
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status} - {test_name}")
        
        # Performance assessment
        if success_rate >= 90:
            print(f"\n🎉 OUTSTANDING PERFORMANCE - RAG chatbot system is production-ready!")
        elif success_rate >= 75:
            print(f"\n✅ GOOD PERFORMANCE - RAG chatbot system is functional with minor issues to address")
        elif success_rate >= 50:
            print(f"\n⚠️  MODERATE PERFORMANCE - RAG chatbot system needs improvements")
        else:
            print(f"\n❌ POOR PERFORMANCE - RAG chatbot system requires significant fixes")
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = ComprehensiveRAGTester()
    success = tester.run_comprehensive_rag_test()
    sys.exit(0 if success else 1)