#!/usr/bin/env python3
"""
Simple RAG Chatbot Test - Direct API Testing
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "https://golden-health-1.preview.emergentagent.com/api"

def test_basic_chat():
    """Test basic chat functionality"""
    print("🔍 Testing basic chat endpoint...")
    
    try:
        chat_request = {
            "message": "Hello, what treatments do you offer?",
            "language": "en"
        }
        
        print(f"Sending request to: {BACKEND_URL}/chat")
        print(f"Request data: {json.dumps(chat_request, indent=2)}")
        
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json=chat_request,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat endpoint working!")
            print(f"Response data: {json.dumps(data, indent=2)}")
            
            # Check for RAG fields
            rag_fields = ["message", "session_id", "sources", "confidence", "response_time", "language"]
            missing_fields = [field for field in rag_fields if field not in data]
            
            if missing_fields:
                print(f"⚠️ Missing RAG fields: {missing_fields}")
            else:
                print("✅ All RAG fields present!")
                
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_admin_auth():
    """Test admin authentication"""
    print("\n🔍 Testing admin authentication...")
    
    try:
        admin_login_data = {
            "provider": "google",
            "access_token": "admin_test_token",
            "full_name": "Dr. Marco Rossi",
            "email": "admin@kinaura.com"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/auth/social-login",
            json=admin_login_data,
            timeout=10
        )
        
        print(f"Admin auth status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Admin authentication working!")
            admin_token = data.get("access_token")
            
            # Test admin endpoint
            if admin_token:
                headers = {"Authorization": f"Bearer {admin_token}"}
                analytics_response = requests.get(
                    f"{BACKEND_URL}/admin/chat/analytics",
                    headers=headers,
                    timeout=10
                )
                print(f"Admin analytics status: {analytics_response.status_code}")
                
                if analytics_response.status_code == 200:
                    print("✅ Admin endpoints working!")
                else:
                    print(f"⚠️ Admin endpoints issue: {analytics_response.text}")
        else:
            print(f"❌ Admin auth failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Admin auth exception: {e}")

def test_health_check():
    """Test basic health check"""
    print("\n🔍 Testing health check...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        print(f"Health check status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Backend is healthy!")
        else:
            print(f"⚠️ Backend health issue: {response.text}")
            
    except Exception as e:
        print(f"❌ Health check exception: {e}")

if __name__ == "__main__":
    print("🚀 Simple RAG Chatbot Test")
    print("=" * 50)
    
    test_health_check()
    test_admin_auth()
    test_basic_chat()
    
    print("\n" + "=" * 50)
    print("Testing completed.")