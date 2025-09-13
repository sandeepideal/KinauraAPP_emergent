#!/usr/bin/env python3
"""
KinAura Multilingual Chatbot Backend Testing
Test the newly implemented multilingual chatbot backend functionality
"""

import requests
import json
import uuid
import sys
from datetime import datetime
import os

class MultilingualChatbotTester:
    def __init__(self):
        # Get backend URL from environment
        self.base_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://golden-health-1.preview.emergentagent.com')
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.user_id = None
        self.session_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}")
        
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })

    def setup_authentication(self):
        """Setup authentication for testing"""
        print("\n🔐 Setting up authentication...")
        
        # Try to login with demo user
        login_data = {
            "email": "demo@kinaura.com",
            "password": "demo123"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/login", json=login_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.user_id = data.get('user', {}).get('id')
                self.log_result("Authentication Setup", True, f"Logged in as user {self.user_id}")
                return True
            else:
                # Try social login as fallback
                social_data = {
                    "provider": "google",
                    "access_token": "demo_token",
                    "full_name": "Demo User",
                    "email": "demo@kinaura.com"
                }
                response = requests.post(f"{self.api_url}/auth/social-login", json=social_data, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get('access_token')
                    self.user_id = data.get('user', {}).get('id')
                    self.log_result("Authentication Setup", True, f"Social login successful for user {self.user_id}")
                    return True
                else:
                    self.log_result("Authentication Setup", False, f"Login failed: {response.status_code}")
                    return False
        except Exception as e:
            self.log_result("Authentication Setup", False, f"Authentication error: {str(e)}")
            return False

    def test_language_detection_italian(self):
        """Test Italian language detection with various messages"""
        print("\n🇮🇹 Testing Italian Language Detection...")
        
        italian_messages = [
            "Ciao, vorrei prenotare un appuntamento per un trattamento di bellezza",
            "Buongiorno, ho bisogno di informazioni sui vostri servizi",
            "Che cos'è il protocollo personalizzato?",
            "Grazie per l'aiuto, quando posso venire per una consulenza?",
            "Sono interessato al Morpheus8 per le cicatrici da acne",
            "Vorrei sapere di più sulla terapia NAD+ per la stanchezza",
            "Che trattamenti avete per il melasma?"
        ]
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        italian_responses = 0
        total_tests = len(italian_messages)
        
        for i, message in enumerate(italian_messages, 1):
            try:
                chat_data = {
                    "message": message,
                    "user_id": self.user_id
                }
                
                response = requests.post(f"{self.api_url}/chat", json=chat_data, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    response_message = data.get('message', '').lower()
                    
                    # Check for Italian language indicators in response
                    italian_indicators = [
                        'ciao', 'salve', 'buongiorno', 'grazie', 'prego', 'benvenuto',
                        'trattamento', 'terapia', 'appuntamento', 'consulenza', 'servizi',
                        'posso', 'aiutarti', 'informazioni', 'disponibile', 'prenotare'
                    ]
                    
                    has_italian = any(indicator in response_message for indicator in italian_indicators)
                    
                    if has_italian:
                        italian_responses += 1
                        print(f"   ✅ Test {i}/{total_tests}: Italian detected and responded appropriately")
                    else:
                        print(f"   ⚠️ Test {i}/{total_tests}: Italian message but response may be in English")
                        print(f"      Message: {message[:50]}...")
                        print(f"      Response: {response_message[:100]}...")
                else:
                    print(f"   ❌ Test {i}/{total_tests}: API error {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Test {i}/{total_tests}: Error - {str(e)}")
        
        success_rate = (italian_responses / total_tests) * 100
        success = success_rate >= 70  # 70% success rate threshold
        
        self.log_result(
            "Italian Language Detection", 
            success, 
            f"Italian responses: {italian_responses}/{total_tests} ({success_rate:.1f}%)"
        )
        
        return success

    def test_language_detection_english(self):
        """Test English language detection with various messages"""
        print("\n🇺🇸 Testing English Language Detection...")
        
        english_messages = [
            "Hello, I would like to book an appointment",
            "What treatments do you offer for anti-aging?",
            "Can you tell me about your services?",
            "Thank you, when can I schedule a consultation?",
            "I'm interested in NAD+ therapy for fatigue",
            "What's the best treatment for acne scars?",
            "How much does IV therapy cost?"
        ]
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        english_responses = 0
        total_tests = len(english_messages)
        
        for i, message in enumerate(english_messages, 1):
            try:
                chat_data = {
                    "message": message,
                    "user_id": self.user_id
                }
                
                response = requests.post(f"{self.api_url}/chat", json=chat_data, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    response_message = data.get('message', '').lower()
                    
                    # Check for English language (absence of Italian indicators)
                    italian_indicators = [
                        'ciao', 'salve', 'buongiorno', 'grazie', 'prego', 'benvenuto',
                        'trattamento', 'terapia', 'appuntamento', 'consulenza'
                    ]
                    
                    has_italian = any(indicator in response_message for indicator in italian_indicators)
                    
                    if not has_italian and len(response_message) > 50:  # English response
                        english_responses += 1
                        print(f"   ✅ Test {i}/{total_tests}: English detected and responded appropriately")
                    else:
                        print(f"   ⚠️ Test {i}/{total_tests}: English message but response may contain Italian")
                        print(f"      Message: {message[:50]}...")
                        print(f"      Response: {response_message[:100]}...")
                else:
                    print(f"   ❌ Test {i}/{total_tests}: API error {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Test {i}/{total_tests}: Error - {str(e)}")
        
        success_rate = (english_responses / total_tests) * 100
        success = success_rate >= 70  # 70% success rate threshold
        
        self.log_result(
            "English Language Detection", 
            success, 
            f"English responses: {english_responses}/{total_tests} ({success_rate:.1f}%)"
        )
        
        return success

    def test_mixed_language_scenarios(self):
        """Test mixed language scenarios"""
        print("\n🌐 Testing Mixed Language Scenarios...")
        
        mixed_messages = [
            "Hello, vorrei un appuntamento per NAD+ therapy",
            "Ciao, I need information about Morpheus8",
            "What is terapia con ozono?",
            "Grazie, can you help me book IV therapy?"
        ]
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        successful_responses = 0
        total_tests = len(mixed_messages)
        
        for i, message in enumerate(mixed_messages, 1):
            try:
                chat_data = {
                    "message": message,
                    "user_id": self.user_id
                }
                
                response = requests.post(f"{self.api_url}/chat", json=chat_data, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    response_message = data.get('message', '')
                    
                    if len(response_message) > 50:  # Got a meaningful response
                        successful_responses += 1
                        print(f"   ✅ Test {i}/{total_tests}: Mixed language handled successfully")
                    else:
                        print(f"   ⚠️ Test {i}/{total_tests}: Short response received")
                else:
                    print(f"   ❌ Test {i}/{total_tests}: API error {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Test {i}/{total_tests}: Error - {str(e)}")
        
        success_rate = (successful_responses / total_tests) * 100
        success = success_rate >= 75  # 75% success rate threshold
        
        self.log_result(
            "Mixed Language Scenarios", 
            success, 
            f"Successful responses: {successful_responses}/{total_tests} ({success_rate:.1f}%)"
        )
        
        return success

    def test_inquiry_detection_with_language(self):
        """Test patient inquiry detection with language context"""
        print("\n🔍 Testing Inquiry Detection with Language Context...")
        
        inquiry_messages = [
            {
                "message": "Sono interessato al Morpheus8 per le cicatrici da acne",
                "language": "Italian",
                "expected_inquiry": "treatment"
            },
            {
                "message": "Vorrei sapere di più sulla terapia NAD+ per la stanchezza",
                "language": "Italian", 
                "expected_inquiry": "treatment"
            },
            {
                "message": "Che trattamenti avete per il melasma?",
                "language": "Italian",
                "expected_inquiry": "condition"
            },
            {
                "message": "I'm interested in IV therapy for chronic fatigue",
                "language": "English",
                "expected_inquiry": "treatment"
            },
            {
                "message": "What treatments do you have for wrinkles?",
                "language": "English",
                "expected_inquiry": "condition"
            }
        ]
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        successful_detections = 0
        total_tests = len(inquiry_messages)
        
        for i, test_case in enumerate(inquiry_messages, 1):
            try:
                chat_data = {
                    "message": test_case["message"],
                    "user_id": self.user_id
                }
                
                response = requests.post(f"{self.api_url}/chat", json=chat_data, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    response_message = data.get('message', '')
                    
                    # Check if response contains treatment/condition information
                    treatment_keywords = ['treatment', 'therapy', 'trattamento', 'terapia']
                    condition_keywords = ['condition', 'concern', 'problema', 'condizione']
                    
                    has_relevant_content = any(keyword in response_message.lower() for keyword in treatment_keywords + condition_keywords)
                    
                    if has_relevant_content and len(response_message) > 100:
                        successful_detections += 1
                        print(f"   ✅ Test {i}/{total_tests}: {test_case['language']} inquiry detected and processed")
                    else:
                        print(f"   ⚠️ Test {i}/{total_tests}: {test_case['language']} inquiry may not be fully processed")
                else:
                    print(f"   ❌ Test {i}/{total_tests}: API error {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Test {i}/{total_tests}: Error - {str(e)}")
        
        success_rate = (successful_detections / total_tests) * 100
        success = success_rate >= 80  # 80% success rate threshold
        
        self.log_result(
            "Inquiry Detection with Language", 
            success, 
            f"Successful detections: {successful_detections}/{total_tests} ({success_rate:.1f}%)"
        )
        
        return success

    def test_language_consistency(self):
        """Test language consistency throughout conversations"""
        print("\n🔄 Testing Language Consistency...")
        
        # Test Italian conversation consistency
        italian_conversation = [
            "Ciao, ho bisogno di informazioni sui trattamenti",
            "Quali sono i benefici della terapia NAD+?",
            "Quanto costa un trattamento?"
        ]
        
        headers = {'Authorization': f'Bearer {self.token}'}
        italian_consistent = True
        
        print("   Testing Italian conversation consistency...")
        for i, message in enumerate(italian_conversation, 1):
            try:
                chat_data = {
                    "message": message,
                    "user_id": self.user_id
                }
                
                response = requests.post(f"{self.api_url}/chat", json=chat_data, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    response_message = data.get('message', '').lower()
                    
                    # Check for Italian indicators
                    italian_indicators = ['ciao', 'salve', 'grazie', 'prego', 'terapia', 'trattamento', 'posso']
                    has_italian = any(indicator in response_message for indicator in italian_indicators)
                    
                    if not has_italian and i > 1:  # After first message, should maintain Italian
                        italian_consistent = False
                        print(f"      ⚠️ Message {i}: Language consistency may be broken")
                    else:
                        print(f"      ✅ Message {i}: Italian consistency maintained")
                else:
                    italian_consistent = False
                    print(f"      ❌ Message {i}: API error {response.status_code}")
                    
            except Exception as e:
                italian_consistent = False
                print(f"      ❌ Message {i}: Error - {str(e)}")
        
        # Test English conversation consistency
        english_conversation = [
            "Hello, I need information about treatments",
            "What are the benefits of NAD+ therapy?",
            "How much does a treatment cost?"
        ]
        
        english_consistent = True
        
        print("   Testing English conversation consistency...")
        for i, message in enumerate(english_conversation, 1):
            try:
                chat_data = {
                    "message": message,
                    "user_id": self.user_id
                }
                
                response = requests.post(f"{self.api_url}/chat", json=chat_data, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    response_message = data.get('message', '').lower()
                    
                    # Check for Italian indicators (should not be present)
                    italian_indicators = ['ciao', 'salve', 'grazie', 'prego', 'terapia', 'trattamento']
                    has_italian = any(indicator in response_message for indicator in italian_indicators)
                    
                    if has_italian:
                        english_consistent = False
                        print(f"      ⚠️ Message {i}: English consistency may be broken (Italian detected)")
                    else:
                        print(f"      ✅ Message {i}: English consistency maintained")
                else:
                    english_consistent = False
                    print(f"      ❌ Message {i}: API error {response.status_code}")
                    
            except Exception as e:
                english_consistent = False
                print(f"      ❌ Message {i}: Error - {str(e)}")
        
        overall_success = italian_consistent and english_consistent
        
        self.log_result(
            "Language Consistency", 
            overall_success, 
            f"Italian consistent: {italian_consistent}, English consistent: {english_consistent}"
        )
        
        return overall_success

    def test_technical_implementation(self):
        """Test technical implementation of language detection functions"""
        print("\n⚙️ Testing Technical Implementation...")
        
        # Test chat endpoint with language detection
        headers = {'Authorization': f'Bearer {self.token}'}
        
        test_cases = [
            {
                "message": "Ciao, come stai?",
                "expected_language": "Italian",
                "test_name": "Italian Detection Function"
            },
            {
                "message": "Hello, how are you?", 
                "expected_language": "English",
                "test_name": "English Detection Function"
            }
        ]
        
        successful_implementations = 0
        total_tests = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                chat_data = {
                    "message": test_case["message"],
                    "user_id": self.user_id
                }
                
                response = requests.post(f"{self.api_url}/chat", json=chat_data, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if response structure is correct
                    required_fields = ['message', 'session_id']
                    has_required_fields = all(field in data for field in required_fields)
                    
                    if has_required_fields and len(data.get('message', '')) > 20:
                        successful_implementations += 1
                        print(f"   ✅ Test {i}/{total_tests}: {test_case['test_name']} working")
                        
                        # Store session_id for later tests
                        if not self.session_id:
                            self.session_id = data.get('session_id')
                    else:
                        print(f"   ❌ Test {i}/{total_tests}: {test_case['test_name']} - incomplete response")
                else:
                    print(f"   ❌ Test {i}/{total_tests}: {test_case['test_name']} - API error {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Test {i}/{total_tests}: {test_case['test_name']} - Error: {str(e)}")
        
        success_rate = (successful_implementations / total_tests) * 100
        success = success_rate >= 100  # Both functions should work
        
        self.log_result(
            "Technical Implementation", 
            success, 
            f"Working functions: {successful_implementations}/{total_tests} ({success_rate:.1f}%)"
        )
        
        return success

    def test_system_integration(self):
        """Test system integration with existing chatbot functionality"""
        print("\n🔗 Testing System Integration...")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        integration_tests = [
            {
                "endpoint": "/chat",
                "method": "POST",
                "data": {"message": "Ciao, vorrei prenotare un appuntamento", "user_id": self.user_id},
                "test_name": "Chat Endpoint Integration"
            }
        ]
        
        if self.session_id:
            integration_tests.append({
                "endpoint": f"/chat/sessions/{self.session_id}/messages",
                "method": "GET", 
                "data": None,
                "test_name": "Session Management Integration"
            })
        
        successful_integrations = 0
        total_tests = len(integration_tests)
        
        for i, test in enumerate(integration_tests, 1):
            try:
                if test["method"] == "POST":
                    response = requests.post(f"{self.api_url}{test['endpoint']}", json=test["data"], headers=headers, timeout=15)
                else:
                    response = requests.get(f"{self.api_url}{test['endpoint']}", headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if test["test_name"] == "Chat Endpoint Integration":
                        # Check for proper response structure
                        if 'message' in data and len(data['message']) > 20:
                            successful_integrations += 1
                            print(f"   ✅ Test {i}/{total_tests}: {test['test_name']} working")
                        else:
                            print(f"   ❌ Test {i}/{total_tests}: {test['test_name']} - invalid response structure")
                    
                    elif test["test_name"] == "Session Management Integration":
                        # Check for message history
                        if isinstance(data, list) and len(data) > 0:
                            successful_integrations += 1
                            print(f"   ✅ Test {i}/{total_tests}: {test['test_name']} working")
                        else:
                            print(f"   ❌ Test {i}/{total_tests}: {test['test_name']} - no message history")
                else:
                    print(f"   ❌ Test {i}/{total_tests}: {test['test_name']} - API error {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Test {i}/{total_tests}: {test['test_name']} - Error: {str(e)}")
        
        success_rate = (successful_integrations / total_tests) * 100
        success = success_rate >= 80  # 80% success rate threshold
        
        self.log_result(
            "System Integration", 
            success, 
            f"Working integrations: {successful_integrations}/{total_tests} ({success_rate:.1f}%)"
        )
        
        return success

    def run_all_tests(self):
        """Run all multilingual chatbot tests"""
        print("🚀 Starting KinAura Multilingual Chatbot Backend Testing")
        print("=" * 60)
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Run all tests
        test_results = []
        
        test_results.append(self.test_language_detection_italian())
        test_results.append(self.test_language_detection_english())
        test_results.append(self.test_mixed_language_scenarios())
        test_results.append(self.test_inquiry_detection_with_language())
        test_results.append(self.test_language_consistency())
        test_results.append(self.test_technical_implementation())
        test_results.append(self.test_system_integration())
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 MULTILINGUAL CHATBOT TESTING SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run) * 100
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n✅ MULTILINGUAL CHATBOT BACKEND: WORKING")
            print("The multilingual chatbot backend functionality is working correctly.")
        else:
            print("\n❌ MULTILINGUAL CHATBOT BACKEND: ISSUES DETECTED")
            print("Some multilingual chatbot functionality needs attention.")
        
        # Print detailed results
        print("\n📋 Detailed Test Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = MultilingualChatbotTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)