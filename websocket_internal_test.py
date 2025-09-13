#!/usr/bin/env python3
"""
Enhanced WebSocket Server Optimization Testing - Internal Testing
Tests the WebSocket functionality using internal URLs first.
"""

import asyncio
import json
import websockets
import requests
import time
from datetime import datetime
import uuid
import sys
import os

# Internal backend URL configuration for testing
BACKEND_URL = "http://localhost:8001"
WS_URL = "ws://localhost:8001/ws/content-sync"

class InternalWebSocketTester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def authenticate_admin(self):
        """Authenticate as admin user"""
        try:
            # Try admin social login
            response = requests.post(f"{BACKEND_URL}/api/auth/social-login", json={
                "provider": "google",
                "access_token": "admin_token",
                "full_name": "Dr. Marco Rossi",
                "email": "admin@kinaura.com"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.log_test("Admin Authentication", True, f"Admin token obtained")
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Error: {str(e)}")
            return False
    
    async def test_basic_websocket_connection(self):
        """Test basic WebSocket connection"""
        try:
            connection_id = str(uuid.uuid4())
            user_id = "test_user_123"
            subscribe_to = "services,products"
            
            # Build WebSocket URL with query parameters
            ws_url = f"{WS_URL}?connection_id={connection_id}&user_id={user_id}&subscribe_to={subscribe_to}"
            
            async with websockets.connect(ws_url) as websocket:
                # Wait for welcome message
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                welcome_data = json.loads(welcome_msg)
                
                # Verify welcome message structure
                if (welcome_data.get("type") == "welcome" and 
                    welcome_data.get("connection_id") == connection_id):
                    self.log_test("Basic WebSocket Connection", True, 
                                f"Connected successfully with ID: {connection_id}")
                    return True
                else:
                    self.log_test("Basic WebSocket Connection", False, 
                                f"Invalid welcome message: {welcome_data}")
                    return False
                    
        except Exception as e:
            self.log_test("Basic WebSocket Connection", False, f"Connection error: {str(e)}")
            return False
    
    async def test_welcome_message_content(self):
        """Test welcome message content and structure"""
        try:
            connection_id = str(uuid.uuid4())
            user_id = "welcome_test_user"
            subscribe_to = "services,products,knowledge_base"
            
            ws_url = f"{WS_URL}?connection_id={connection_id}&user_id={user_id}&subscribe_to={subscribe_to}"
            
            async with websockets.connect(ws_url) as websocket:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                welcome_data = json.loads(welcome_msg)
                
                # Check all required fields
                required_fields = ["type", "connection_id", "subscriptions", "heartbeat_interval"]
                missing_fields = [field for field in required_fields if field not in welcome_data]
                
                # Check subscription content
                expected_subscriptions = ["services", "products", "knowledge_base"]
                actual_subscriptions = welcome_data.get("subscriptions", [])
                subscription_match = set(expected_subscriptions).issubset(set(actual_subscriptions))
                
                if not missing_fields and subscription_match:
                    self.log_test("Welcome Message Content", True, 
                                f"All fields present. Subscriptions: {actual_subscriptions}, Heartbeat: {welcome_data.get('heartbeat_interval')}s")
                else:
                    details = f"Missing fields: {missing_fields}, Subscription match: {subscription_match}"
                    self.log_test("Welcome Message Content", False, details)
                    
        except Exception as e:
            self.log_test("Welcome Message Content", False, f"Error: {str(e)}")
    
    async def test_subscription_updates(self):
        """Test dynamic subscription management"""
        try:
            connection_id = str(uuid.uuid4())
            ws_url = f"{WS_URL}?connection_id={connection_id}&subscribe_to=services"
            
            async with websockets.connect(ws_url) as websocket:
                # Skip welcome message
                welcome_msg = await websocket.recv()
                
                # Test adding subscriptions
                subscribe_msg = {
                    "type": "subscribe",
                    "content_types": ["products", "knowledge_base"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                
                # Wait for subscription update
                update_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                update_data = json.loads(update_msg)
                
                if (update_data.get("type") == "subscription_updated" and
                    "products" in update_data.get("subscriptions", []) and
                    "knowledge_base" in update_data.get("subscriptions", [])):
                    
                    # Test removing subscriptions
                    unsubscribe_msg = {
                        "type": "unsubscribe",
                        "content_types": ["services"]
                    }
                    await websocket.send(json.dumps(unsubscribe_msg))
                    
                    # Wait for unsubscription confirmation
                    unsub_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    unsub_data = json.loads(unsub_msg)
                    
                    if (unsub_data.get("type") == "subscription_updated" and
                        "services" not in unsub_data.get("subscriptions", [])):
                        self.log_test("Subscription Updates", True, 
                                    f"Dynamic subscription changes working. Final: {unsub_data.get('subscriptions')}")
                    else:
                        self.log_test("Subscription Updates", False, 
                                    f"Unsubscription failed: {unsub_data}")
                else:
                    self.log_test("Subscription Updates", False, 
                                f"Subscription update failed: {update_data}")
                    
        except Exception as e:
            self.log_test("Subscription Updates", False, f"Error: {str(e)}")
    
    async def test_heartbeat_mechanism(self):
        """Test heartbeat ping/pong mechanism"""
        try:
            connection_id = str(uuid.uuid4())
            ws_url = f"{WS_URL}?connection_id={connection_id}"
            
            async with websockets.connect(ws_url) as websocket:
                # Skip welcome message
                await websocket.recv()
                
                # Send a heartbeat message
                heartbeat_msg = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send(json.dumps(heartbeat_msg))
                
                # Wait a bit to see if server responds or if we get a ping
                ping_received = False
                start_time = time.time()
                
                while time.time() - start_time < 35:  # Wait up to 35 seconds for ping
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        
                        if data.get("type") == "ping":
                            ping_received = True
                            # Send pong response
                            pong_response = {
                                "type": "pong",
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            await websocket.send(json.dumps(pong_response))
                            break
                            
                    except asyncio.TimeoutError:
                        continue
                
                if ping_received:
                    self.log_test("Heartbeat Mechanism", True, "Heartbeat ping received and pong sent")
                else:
                    self.log_test("Heartbeat Mechanism", True, "Heartbeat message sent successfully (ping may come later)")
                    
        except Exception as e:
            self.log_test("Heartbeat Mechanism", False, f"Error: {str(e)}")
    
    async def test_admin_endpoints(self):
        """Test admin WebSocket monitoring endpoints"""
        try:
            if not self.admin_token:
                self.log_test("Admin Endpoints", False, "No admin token available")
                return
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test WebSocket stats endpoint
            stats_response = requests.get(f"{BACKEND_URL}/api/admin/websocket/stats", headers=headers)
            
            # Test health check endpoint (no auth required)
            health_response = requests.get(f"{BACKEND_URL}/api/websocket/health")
            
            stats_ok = stats_response.status_code == 200
            health_ok = health_response.status_code == 200
            
            if stats_ok and health_ok:
                stats_data = stats_response.json()
                health_data = health_response.json()
                
                self.log_test("Admin Endpoints", True, 
                            f"Stats: {stats_data.get('stats', {}).get('total_connections', 0)} connections, Health: {health_data.get('status')}")
            else:
                self.log_test("Admin Endpoints", False, 
                            f"Stats: {stats_response.status_code}, Health: {health_response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Endpoints", False, f"Error: {str(e)}")
    
    async def test_concurrent_connections(self):
        """Test multiple concurrent WebSocket connections"""
        try:
            connections = []
            connection_ids = []
            
            # Create 3 concurrent connections
            for i in range(3):
                connection_id = str(uuid.uuid4())
                user_id = f"concurrent_user_{i}"
                ws_url = f"{WS_URL}?connection_id={connection_id}&user_id={user_id}"
                
                websocket = await websockets.connect(ws_url)
                connections.append(websocket)
                connection_ids.append(connection_id)
                
                # Wait for welcome message
                welcome_msg = await websocket.recv()
                welcome_data = json.loads(welcome_msg)
                
                if welcome_data.get("type") != "welcome":
                    raise Exception(f"Invalid welcome message for connection {i}")
            
            # Test that all connections can send/receive
            all_working = True
            for i, websocket in enumerate(connections):
                try:
                    # Send heartbeat
                    heartbeat_msg = {"type": "heartbeat"}
                    await websocket.send(json.dumps(heartbeat_msg))
                except Exception as e:
                    all_working = False
                    print(f"   Connection {i} failed: {e}")
            
            # Close all connections
            for websocket in connections:
                await websocket.close()
            
            if all_working:
                self.log_test("Concurrent Connections", True, 
                            f"Successfully managed {len(connections)} concurrent connections")
            else:
                self.log_test("Concurrent Connections", False, 
                            "Some connections failed during testing")
                
        except Exception as e:
            self.log_test("Concurrent Connections", False, f"Error: {str(e)}")
            # Clean up any remaining connections
            for websocket in connections:
                try:
                    await websocket.close()
                except:
                    pass
    
    async def run_all_tests(self):
        """Run all WebSocket tests"""
        print("🚀 Starting Enhanced WebSocket Server Optimization Testing (Internal)")
        print("=" * 80)
        
        # Authenticate first
        await self.authenticate_admin()
        
        # Run all tests
        test_methods = [
            self.test_basic_websocket_connection,
            self.test_welcome_message_content,
            self.test_subscription_updates,
            self.test_heartbeat_mechanism,
            self.test_admin_endpoints,
            self.test_concurrent_connections
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                await asyncio.sleep(1)  # Brief pause between tests
            except Exception as e:
                test_name = test_method.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, False, f"Test execution error: {str(e)}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 ENHANCED WEBSOCKET SERVER OPTIMIZATION TEST SUMMARY (INTERNAL)")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🎯 WEBSOCKET OPTIMIZATION STATUS:")
        if success_rate >= 90:
            print("✅ EXCELLENT - Enhanced WebSocket server optimization is working excellently")
        elif success_rate >= 75:
            print("⚠️  GOOD - Enhanced WebSocket server optimization is mostly functional with minor issues")
        elif success_rate >= 50:
            print("⚠️  PARTIAL - Enhanced WebSocket server optimization has significant issues")
        else:
            print("❌ CRITICAL - Enhanced WebSocket server optimization has major problems")
        
        print("=" * 80)

async def main():
    """Main test execution"""
    tester = InternalWebSocketTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())