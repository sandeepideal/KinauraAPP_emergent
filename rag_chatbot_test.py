#!/usr/bin/env python3
"""
Comprehensive RAG-Powered Chatbot System Testing for KinAura
Tests the complete production-ready RAG chatbot transformation from demo to enterprise-grade system.

Test Scope:
1. Enhanced Chat API - Test the new /api/chat endpoint with RAG functionality
2. Vector Embeddings - Verify knowledge base items are processed for vector search
3. RAG Response Quality - Test knowledge retrieval and response generation with citations
4. Multilingual Support - Test English and Italian language detection and responses
5. Admin Analytics - Test new admin endpoints for monitoring and unresolved queries
6. Session Management - Verify enhanced session tracking with analytics
7. Medical Compliance - Test medical disclaimers and consultation recommendations
8. Knowledge Gaps - Test unresolved query logging and knowledge gap analysis
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://golden-health-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@kinaura.com"

class RAGChatbotTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.test_results = []
        self.test_session_ids = []
        
    async def setup(self):
        """Initialize test session and authenticate admin"""
        self.session = aiohttp.ClientSession()
        
        # Admin authentication for testing admin endpoints
        try:
            admin_login_data = {
                "provider": "google",
                "access_token": "admin_test_token",
                "full_name": "Dr. Marco Rossi",
                "email": ADMIN_EMAIL
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/social-login", json=admin_login_data) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    self.admin_token = auth_data.get("access_token")
                    print("✅ Admin authentication successful")
                else:
                    print(f"⚠️ Admin authentication failed: {response.status}")
        except Exception as e:
            print(f"⚠️ Admin authentication error: {e}")
    
    async def cleanup(self):
        """Clean up test session"""
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def test_enhanced_chat_api_basic(self):
        """Test 1: Enhanced Chat API - Basic RAG functionality"""
        test_name = "Enhanced Chat API - Basic RAG Functionality"
        
        try:
            # Test basic chat request with treatment query
            chat_request = {
                "message": "What can you tell me about Morpheus8 treatment?",
                "language": "en"
            }
            
            async with self.session.post(f"{BACKEND_URL}/chat", json=chat_request) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify RAG response structure
                    required_fields = ["message", "session_id", "sources", "confidence", "response_time", "language"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing fields: {missing_fields}")
                        return
                    
                    # Verify response quality
                    response_text = data.get("message", "")
                    has_morpheus8_info = "morpheus8" in response_text.lower()
                    has_medical_disclaimer = "medical consultation" in response_text.lower() or "clinicians" in response_text.lower()
                    
                    # Store session ID for later tests
                    self.test_session_ids.append(data.get("session_id"))
                    
                    success = (
                        len(response_text) > 100 and  # Substantial response
                        has_morpheus8_info and  # Contains relevant info
                        has_medical_disclaimer and  # Medical compliance
                        data.get("confidence", 0) > 0.3  # Reasonable confidence
                    )
                    
                    details = f"Response length: {len(response_text)}, Confidence: {data.get('confidence')}, Sources: {len(data.get('sources', []))}"
                    self.log_test_result(test_name, success, details, data)
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
    
    async def test_vector_embeddings_and_citations(self):
        """Test 2: Vector Embeddings - Knowledge retrieval with citations"""
        test_name = "Vector Embeddings - Knowledge Retrieval with Citations"
        
        try:
            # Test query that should retrieve specific knowledge base content
            chat_request = {
                "message": "Tell me about NAD+ IV therapy benefits and protocols",
                "language": "en"
            }
            
            async with self.session.post(f"{BACKEND_URL}/chat", json=chat_request) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    response_text = data.get("message", "")
                    sources = data.get("sources", [])
                    confidence = data.get("confidence", 0)
                    
                    # Check for citations in response
                    has_citations = "[KB-" in response_text or "(" in response_text
                    has_nad_info = "nad" in response_text.lower() or "iv" in response_text.lower()
                    has_sources = len(sources) > 0
                    
                    # Verify source structure if sources exist
                    source_quality = True
                    if sources:
                        for source in sources:
                            if not all(key in source for key in ["id", "title", "similarity"]):
                                source_quality = False
                                break
                    
                    success = (
                        has_nad_info and
                        confidence > 0.5 and
                        (has_sources or has_citations) and
                        source_quality
                    )
                    
                    details = f"Sources found: {len(sources)}, Has citations: {has_citations}, Confidence: {confidence}"
                    self.log_test_result(test_name, success, details, {"sources_count": len(sources), "confidence": confidence})
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
    
    async def test_multilingual_support(self):
        """Test 3: Multilingual Support - English and Italian responses"""
        test_name = "Multilingual Support - English and Italian"
        
        try:
            # Test Italian query
            italian_request = {
                "message": "Cosa posso fare per la cellulite? Quali trattamenti offrite?",
                "language": "it"
            }
            
            async with self.session.post(f"{BACKEND_URL}/chat", json=italian_request) as response:
                if response.status == 200:
                    italian_data = await response.json()
                    italian_response = italian_data.get("message", "")
                    
                    # Check for Italian language indicators
                    italian_indicators = ["trattamento", "protocollo", "terapia", "kinaura", "consulenza"]
                    has_italian = any(indicator in italian_response.lower() for indicator in italian_indicators)
                    
                    # Test English query
                    english_request = {
                        "message": "What treatments do you offer for cellulite?",
                        "language": "en"
                    }
                    
                    async with self.session.post(f"{BACKEND_URL}/chat", json=english_request) as response2:
                        if response2.status == 200:
                            english_data = await response2.json()
                            english_response = english_data.get("message", "")
                            
                            # Check for English language indicators
                            english_indicators = ["treatment", "protocol", "therapy", "consultation"]
                            has_english = any(indicator in english_response.lower() for indicator in english_indicators)
                            
                            # Verify language detection worked
                            italian_lang_detected = italian_data.get("language") == "it"
                            english_lang_detected = english_data.get("language") == "en"
                            
                            success = (
                                has_italian and has_english and
                                len(italian_response) > 100 and len(english_response) > 100 and
                                italian_lang_detected and english_lang_detected
                            )
                            
                            details = f"Italian response: {len(italian_response)} chars, English response: {len(english_response)} chars"
                            self.log_test_result(test_name, success, details)
                        else:
                            self.log_test_result(test_name, False, f"English request failed: HTTP {response2.status}")
                else:
                    self.log_test_result(test_name, False, f"Italian request failed: HTTP {response.status}")
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
    
    async def test_session_management_and_analytics(self):
        """Test 4: Session Management - Enhanced session tracking"""
        test_name = "Session Management - Enhanced Session Tracking"
        
        try:
            # Create multiple chat messages in same session
            session_id = f"test_session_{int(time.time())}"
            
            messages = [
                "Hello, I'm interested in anti-aging treatments",
                "What about HBOT therapy?",
                "Can you tell me about pricing?"
            ]
            
            session_data = []
            for message in messages:
                chat_request = {
                    "message": message,
                    "session_id": session_id,
                    "language": "en"
                }
                
                async with self.session.post(f"{BACKEND_URL}/chat", json=chat_request) as response:
                    if response.status == 200:
                        data = await response.json()
                        session_data.append(data)
                    else:
                        self.log_test_result(test_name, False, f"Message failed: HTTP {response.status}")
                        return
            
            # Test session retrieval
            async with self.session.get(f"{BACKEND_URL}/chat/sessions") as response:
                if response.status == 200:
                    sessions = await response.json()
                    
                    # Find our test session
                    test_session = None
                    for session in sessions:
                        if session.get("id") == session_id:
                            test_session = session
                            break
                    
                    # Test message retrieval
                    async with self.session.get(f"{BACKEND_URL}/chat/sessions/{session_id}/messages") as msg_response:
                        if msg_response.status == 200:
                            messages_data = await msg_response.json()
                            
                            success = (
                                test_session is not None and
                                len(messages_data) >= 6 and  # 3 user + 3 assistant messages
                                all(data.get("session_id") == session_id for data in session_data)
                            )
                            
                            details = f"Session found: {test_session is not None}, Messages: {len(messages_data)}"
                            self.log_test_result(test_name, success, details)
                        else:
                            self.log_test_result(test_name, False, f"Messages retrieval failed: HTTP {msg_response.status}")
                else:
                    self.log_test_result(test_name, False, f"Sessions retrieval failed: HTTP {response.status}")
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
    
    async def test_medical_compliance(self):
        """Test 5: Medical Compliance - Disclaimers and consultation recommendations"""
        test_name = "Medical Compliance - Disclaimers and Consultation"
        
        try:
            # Test medical query that should trigger compliance features
            medical_queries = [
                "I have severe acne, what treatment do you recommend?",
                "Can Morpheus8 help with my skin condition?",
                "What are the side effects of NAD+ therapy?"
            ]
            
            compliance_results = []
            
            for query in medical_queries:
                chat_request = {
                    "message": query,
                    "language": "en"
                }
                
                async with self.session.post(f"{BACKEND_URL}/chat", json=chat_request) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get("message", "")
                        
                        # Check for medical compliance elements
                        has_disclaimer = any(phrase in response_text.lower() for phrase in [
                            "medical consultation", "clinicians", "does not replace", 
                            "consult", "professional advice"
                        ])
                        
                        requires_consultation = data.get("requires_consultation", False)
                        has_medical_disclaimer = data.get("medical_disclaimer", "") != ""
                        
                        compliance_results.append({
                            "query": query,
                            "has_disclaimer": has_disclaimer,
                            "requires_consultation": requires_consultation,
                            "has_medical_disclaimer": has_medical_disclaimer
                        })
                    else:
                        self.log_test_result(test_name, False, f"Query failed: HTTP {response.status}")
                        return
            
            # Evaluate compliance
            total_queries = len(compliance_results)
            compliant_queries = sum(1 for result in compliance_results if result["has_disclaimer"])
            
            success = compliant_queries >= total_queries * 0.8  # At least 80% should have disclaimers
            
            details = f"Compliant responses: {compliant_queries}/{total_queries}"
            self.log_test_result(test_name, success, details, compliance_results)
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
    
    async def test_admin_analytics_endpoints(self):
        """Test 6: Admin Analytics - Monitoring and unresolved queries"""
        test_name = "Admin Analytics - Monitoring and Unresolved Queries"
        
        if not self.admin_token:
            self.log_test_result(test_name, False, "Admin token not available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test chat analytics endpoint
            async with self.session.get(f"{BACKEND_URL}/admin/chat/analytics", headers=headers) as response:
                if response.status == 200:
                    analytics_data = await response.json()
                    
                    # Verify analytics structure
                    expected_fields = ["total_sessions", "total_messages", "avg_confidence", "knowledge_coverage"]
                    has_analytics = any(field in analytics_data for field in expected_fields)
                    
                    # Test unresolved queries endpoint
                    async with self.session.get(f"{BACKEND_URL}/admin/chat/unresolved-queries", headers=headers) as unresolved_response:
                        if unresolved_response.status == 200:
                            unresolved_data = await unresolved_response.json()
                            
                            # Test knowledge gaps analysis
                            async with self.session.get(f"{BACKEND_URL}/admin/chat/knowledge-gaps", headers=headers) as gaps_response:
                                if gaps_response.status == 200:
                                    gaps_data = await gaps_response.json()
                                    
                                    has_gaps_analysis = "knowledge_gaps" in gaps_data
                                    has_recommendations = "recommendations" in gaps_data
                                    
                                    success = has_analytics and has_gaps_analysis and has_recommendations
                                    
                                    details = f"Analytics: {has_analytics}, Gaps analysis: {has_gaps_analysis}, Recommendations: {has_recommendations}"
                                    self.log_test_result(test_name, success, details)
                                else:
                                    self.log_test_result(test_name, False, f"Knowledge gaps failed: HTTP {gaps_response.status}")
                        else:
                            self.log_test_result(test_name, False, f"Unresolved queries failed: HTTP {unresolved_response.status}")
                else:
                    self.log_test_result(test_name, False, f"Analytics failed: HTTP {response.status}")
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
    
    async def test_rag_test_endpoint(self):
        """Test 7: RAG Test Endpoint - Admin validation"""
        test_name = "RAG Test Endpoint - Admin Validation"
        
        if not self.admin_token:
            self.log_test_result(test_name, False, "Admin token not available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test RAG system with admin endpoint
            test_queries = [
                "What is HBOT therapy?",
                "Explain Morpheus8 treatment protocol",
                "Tell me about NAD+ IV benefits"
            ]
            
            rag_test_results = []
            
            for query in test_queries:
                params = {
                    "test_query": query,
                    "language": "en"
                }
                
                async with self.session.post(f"{BACKEND_URL}/admin/chat/test-rag", params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Verify RAG test response structure
                        required_fields = ["test_query", "response", "sources_found", "confidence", "response_time"]
                        has_all_fields = all(field in data for field in required_fields)
                        
                        rag_test_results.append({
                            "query": query,
                            "success": has_all_fields,
                            "confidence": data.get("confidence", 0),
                            "sources_found": data.get("sources_found", 0),
                            "response_time": data.get("response_time", 0)
                        })
                    else:
                        rag_test_results.append({
                            "query": query,
                            "success": False,
                            "error": f"HTTP {response.status}"
                        })
            
            # Evaluate RAG test results
            successful_tests = sum(1 for result in rag_test_results if result.get("success", False))
            success = successful_tests >= len(test_queries) * 0.8  # At least 80% success
            
            details = f"Successful RAG tests: {successful_tests}/{len(test_queries)}"
            self.log_test_result(test_name, success, details, rag_test_results)
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
    
    async def test_knowledge_gap_logging(self):
        """Test 8: Knowledge Gaps - Unresolved query logging"""
        test_name = "Knowledge Gaps - Unresolved Query Logging"
        
        try:
            # Send queries that might not have good knowledge base coverage
            gap_queries = [
                "What is the cost of a full body scan?",
                "Do you offer payment plans for treatments?",
                "What are your clinic hours on weekends?",
                "Can I bring my pet to the clinic?"  # Intentionally odd query
            ]
            
            low_confidence_responses = 0
            
            for query in gap_queries:
                chat_request = {
                    "message": query,
                    "language": "en"
                }
                
                async with self.session.post(f"{BACKEND_URL}/chat", json=chat_request) as response:
                    if response.status == 200:
                        data = await response.json()
                        confidence = data.get("confidence", 1.0)
                        
                        # Count low confidence responses (likely to be logged as unresolved)
                        if confidence < 0.6:
                            low_confidence_responses += 1
                    else:
                        self.log_test_result(test_name, False, f"Query failed: HTTP {response.status}")
                        return
            
            # Wait a moment for logging to process
            await asyncio.sleep(2)
            
            # Check if unresolved queries were logged (if admin token available)
            if self.admin_token:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                
                async with self.session.get(f"{BACKEND_URL}/admin/chat/unresolved-queries?limit=10", headers=headers) as response:
                    if response.status == 200:
                        unresolved_data = await response.json()
                        unresolved_queries = unresolved_data.get("unresolved_queries", [])
                        
                        # Check if some of our test queries appear in unresolved list
                        recent_unresolved = [q for q in unresolved_queries if any(gap_query.lower() in q.get("query", "").lower() for gap_query in gap_queries)]
                        
                        success = low_confidence_responses > 0 or len(recent_unresolved) > 0
                        details = f"Low confidence responses: {low_confidence_responses}, Recent unresolved: {len(recent_unresolved)}"
                        self.log_test_result(test_name, success, details)
                    else:
                        # Fallback: just check that we got low confidence responses
                        success = low_confidence_responses > 0
                        details = f"Low confidence responses detected: {low_confidence_responses}"
                        self.log_test_result(test_name, success, details)
            else:
                # Without admin access, just verify low confidence detection
                success = low_confidence_responses > 0
                details = f"Low confidence responses detected: {low_confidence_responses}"
                self.log_test_result(test_name, success, details)
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {e}")
    
    async def run_all_tests(self):
        """Run all RAG chatbot tests"""
        print("🚀 Starting Comprehensive RAG-Powered Chatbot System Testing")
        print("=" * 80)
        
        await self.setup()
        
        # Run all tests
        test_methods = [
            self.test_enhanced_chat_api_basic,
            self.test_vector_embeddings_and_citations,
            self.test_multilingual_support,
            self.test_session_management_and_analytics,
            self.test_medical_compliance,
            self.test_admin_analytics_endpoints,
            self.test_rag_test_endpoint,
            self.test_knowledge_gap_logging
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                await asyncio.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"❌ Test method {test_method.__name__} failed with exception: {e}")
        
        await self.cleanup()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE RAG CHATBOT SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"    {result['details']}")
        
        print("\n🎯 RAG SYSTEM ASSESSMENT:")
        
        # Categorize results
        core_functionality = ["Enhanced Chat API", "Vector Embeddings", "Multilingual Support"]
        enterprise_features = ["Session Management", "Medical Compliance", "Admin Analytics", "RAG Test Endpoint", "Knowledge Gaps"]
        
        core_passed = sum(1 for result in self.test_results if any(core in result["test"] for core in core_functionality) and result["success"])
        enterprise_passed = sum(1 for result in self.test_results if any(ent in result["test"] for ent in enterprise_features) and result["success"])
        
        print(f"Core RAG Functionality: {core_passed}/{len(core_functionality)} tests passed")
        print(f"Enterprise Features: {enterprise_passed}/{len(enterprise_features)} tests passed")
        
        if success_rate >= 85:
            print("\n🎉 EXCELLENT: RAG chatbot system is production-ready with outstanding functionality!")
        elif success_rate >= 70:
            print("\n✅ GOOD: RAG chatbot system is functional with minor issues to address.")
        elif success_rate >= 50:
            print("\n⚠️ MODERATE: RAG chatbot system has core functionality but needs improvements.")
        else:
            print("\n❌ CRITICAL: RAG chatbot system has significant issues requiring attention.")
        
        print("\n🔍 KEY FINDINGS:")
        
        # Analyze specific findings
        findings = []
        
        for result in self.test_results:
            if "Enhanced Chat API" in result["test"] and result["success"]:
                findings.append("✅ Basic RAG chat functionality is working correctly")
            elif "Vector Embeddings" in result["test"] and result["success"]:
                findings.append("✅ Knowledge base vector search and citations are functional")
            elif "Multilingual Support" in result["test"] and result["success"]:
                findings.append("✅ English/Italian language detection and responses working")
            elif "Medical Compliance" in result["test"] and result["success"]:
                findings.append("✅ Medical disclaimers and consultation recommendations implemented")
            elif "Admin Analytics" in result["test"] and result["success"]:
                findings.append("✅ Admin monitoring and analytics endpoints operational")
            elif "Knowledge Gaps" in result["test"] and result["success"]:
                findings.append("✅ Unresolved query logging and knowledge gap analysis working")
        
        for finding in findings:
            print(finding)
        
        # Recommendations
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n🔧 RECOMMENDATIONS:")
            for failed_test in failed_tests:
                print(f"• Fix: {failed_test['test']} - {failed_test['details']}")
        
        print("\n" + "=" * 80)
        print("Testing completed. RAG chatbot system evaluation complete.")

async def main():
    """Main test execution"""
    tester = RAGChatbotTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())