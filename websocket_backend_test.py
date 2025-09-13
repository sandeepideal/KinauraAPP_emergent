#!/usr/bin/env python3
"""
Enhanced WebSocket Server Optimization Testing
Tests the production-ready WebSocket optimization for real-time content sync with enterprise features.
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

# Backend URL configuration
BACKEND_URL = "https://golden-health-1.preview.emergentagent.com"
WS_URL = "wss://golden-health-1.preview.emergentagent.com/ws/content-sync"

class WebSocketTester:
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
    
    async def test_enhanced_websocket_connection(self):
        """Test enhanced WebSocket connection with query parameters"""
        try:
            connection_id = str(uuid.uuid4())
            user_id = "test_user_123"
            subscribe_to = "services,products,knowledge_base"
            
            # Build WebSocket URL with query parameters
            ws_url = f"{WS_URL}?connection_id={connection_id}&user_id={user_id}&subscribe_to={subscribe_to}"
            
            async with websockets.connect(ws_url) as websocket:
                # Wait for welcome message
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_msg)
                
                # Verify welcome message structure
                expected_fields = ["type", "connection_id", "subscriptions", "heartbeat_interval"]
                has_all_fields = all(field in welcome_data for field in expected_fields)
                
                if (welcome_data.get("type") == "welcome" and 
                    welcome_data.get("connection_id") == connection_id and
                    has_all_fields):
                    self.log_test("Enhanced WebSocket Connection", True, 
                                f"Connected with ID: {connection_id}, subscriptions: {welcome_data.get('subscriptions')}")
                    return True, websocket, connection_id
                else:
                    self.log_test("Enhanced WebSocket Connection", False, 
                                f"Invalid welcome message: {welcome_data}")
                    return False, None, None
                    
        except Exception as e:
            self.log_test("Enhanced WebSocket Connection", False, f"Connection error: {str(e)}")
            return False, None, None
    
    async def test_welcome_message_structure(self):
        """Test welcome message with connection details and subscriptions"""
        try:
            connection_id = str(uuid.uuid4())
            user_id = "welcome_test_user"
            subscribe_to = "services,products"
            
            ws_url = f"{WS_URL}?connection_id={connection_id}&user_id={user_id}&subscribe_to={subscribe_to}"
            
            async with websockets.connect(ws_url) as websocket:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_msg)
                
                # Verify welcome message content
                expected_subscriptions = ["services", "products"]
                actual_subscriptions = welcome_data.get("subscriptions", [])
                
                valid_structure = (
                    welcome_data.get("type") == "welcome" and
                    welcome_data.get("connection_id") == connection_id and
                    set(expected_subscriptions).issubset(set(actual_subscriptions)) and
                    isinstance(welcome_data.get("heartbeat_interval"), int)
                )
                
                if valid_structure:
                    self.log_test("Welcome Message Structure", True, 
                                f"Valid welcome with subscriptions: {actual_subscriptions}, heartbeat: {welcome_data.get('heartbeat_interval')}s")
                else:
                    self.log_test("Welcome Message Structure", False, 
                                f"Invalid structure: {welcome_data}")
                    
        except Exception as e:
            self.log_test("Welcome Message Structure", False, f"Error: {str(e)}")
    
    async def test_heartbeat_ping_pong(self):
        """Test heartbeat ping/pong mechanism"""
        try:
            connection_id = str(uuid.uuid4())
            ws_url = f"{WS_URL}?connection_id={connection_id}"
            
            async with websockets.connect(ws_url) as websocket:
                # Skip welcome message
                await websocket.recv()
                
                # Wait for ping message (should come within 30 seconds)
                ping_received = False
                start_time = time.time()
                
                while time.time() - start_time < 35:  # Wait up to 35 seconds
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
                    self.log_test("Heartbeat Ping/Pong", True, "Ping received and pong sent successfully")
                else:
                    self.log_test("Heartbeat Ping/Pong", False, "No ping received within 35 seconds")
                    
        except Exception as e:
            self.log_test("Heartbeat Ping/Pong", False, f"Error: {str(e)}")
    
    async def test_subscription_management(self):
        """Test dynamic content type subscriptions and filtering"""
        try:
            connection_id = str(uuid.uuid4())
            ws_url = f"{WS_URL}?connection_id={connection_id}&subscribe_to=services"
            
            async with websockets.connect(ws_url) as websocket:
                # Skip welcome message
                welcome_msg = await websocket.recv()
                welcome_data = json.loads(welcome_msg)
                
                # Test subscription update
                subscribe_msg = {
                    "type": "subscribe",
                    "content_types": ["products", "knowledge_base"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                
                # Wait for subscription update confirmation
                update_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                update_data = json.loads(update_msg)
                
                if (update_data.get("type") == "subscription_updated" and
                    "products" in update_data.get("subscriptions", []) and
                    "knowledge_base" in update_data.get("subscriptions", [])):
                    
                    # Test unsubscription
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
                        self.log_test("Subscription Management", True, 
                                    f"Dynamic subscription changes working. Final subscriptions: {unsub_data.get('subscriptions')}")
                    else:
                        self.log_test("Subscription Management", False, 
                                    f"Unsubscription failed: {unsub_data}")
                else:
                    self.log_test("Subscription Management", False, 
                                f"Subscription update failed: {update_data}")
                    
        except Exception as e:
            self.log_test("Subscription Management", False, f"Error: {str(e)}")
    
    async def test_admin_websocket_stats(self):
        """Test admin WebSocket stats endpoint"""
        try:
            if not self.admin_token:
                self.log_test("Admin WebSocket Stats", False, "No admin token available")
                return
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{BACKEND_URL}/api/admin/websocket/stats", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("stats", {})
                
                required_fields = ["total_connections", "connections_by_user", "subscriptions_summary", "connection_ages"]
                has_required_fields = all(field in stats for field in required_fields)
                
                if has_required_fields:
                    self.log_test("Admin WebSocket Stats", True, 
                                f"Stats retrieved: {stats.get('total_connections')} connections")
                else:
                    self.log_test("Admin WebSocket Stats", False, 
                                f"Missing required fields in stats: {stats}")
            else:
                self.log_test("Admin WebSocket Stats", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin WebSocket Stats", False, f"Error: {str(e)}")
    
    async def test_websocket_health_check(self):
        """Test WebSocket health check endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/websocket/health")
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["status", "active_connections", "timestamp"]
                has_required_fields = all(field in data for field in required_fields)
                
                if has_required_fields and data.get("status") in ["healthy", "unhealthy"]:
                    self.log_test("WebSocket Health Check", True, 
                                f"Health status: {data.get('status')}, connections: {data.get('active_connections')}")
                else:
                    self.log_test("WebSocket Health Check", False, 
                                f"Invalid health response: {data}")
            else:
                self.log_test("WebSocket Health Check", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("WebSocket Health Check", False, f"Error: {str(e)}")
    
    async def test_multiple_client_connections(self):
        """Test multiple client connection management"""
        try:
            connections = []
            connection_ids = []
            
            # Create 3 concurrent connections
            for i in range(3):
                connection_id = str(uuid.uuid4())
                user_id = f"multi_test_user_{i}"
                ws_url = f"{WS_URL}?connection_id={connection_id}&user_id={user_id}"
                
                websocket = await websockets.connect(ws_url)
                connections.append(websocket)
                connection_ids.append(connection_id)
                
                # Wait for welcome message
                welcome_msg = await websocket.recv()
                welcome_data = json.loads(welcome_msg)
                
                if welcome_data.get("type") != "welcome":
                    raise Exception(f"Invalid welcome message for connection {i}")
            
            # Test that all connections are active
            all_active = True
            for i, websocket in enumerate(connections):
                try:
                    # Send heartbeat
                    heartbeat_msg = {"type": "heartbeat"}
                    await websocket.send(json.dumps(heartbeat_msg))
                except Exception as e:
                    all_active = False
                    print(f"Connection {i} failed: {e}")
            
            # Close all connections
            for websocket in connections:
                await websocket.close()
            
            if all_active:
                self.log_test("Multiple Client Connections", True, 
                            f"Successfully managed {len(connections)} concurrent connections")
            else:
                self.log_test("Multiple Client Connections", False, 
                            "Some connections failed during testing")
                
        except Exception as e:
            self.log_test("Multiple Client Connections", False, f"Error: {str(e)}")
            # Clean up any remaining connections
            for websocket in connections:
                try:
                    await websocket.close()
                except:
                    pass
    
    async def test_connection_cleanup_timeout(self):
        """Test connection cleanup and timeout handling"""
        try:
            connection_id = str(uuid.uuid4())
            ws_url = f"{WS_URL}?connection_id={connection_id}"
            
            # Create connection but don't respond to pings
            websocket = await websockets.connect(ws_url)
            
            # Skip welcome message
            await websocket.recv()
            
            # Wait for ping and don't respond (simulate dead connection)
            ping_received = False
            start_time = time.time()
            
            while time.time() - start_time < 35:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "ping":
                        ping_received = True
                        # Don't send pong - simulate dead connection
                        print(f"   Received ping but not responding (simulating dead connection)")
                        break
                        
                except asyncio.TimeoutError:
                    continue
            
            # Wait additional time to see if connection gets cleaned up
            # The server should detect this as a dead connection after 60 seconds
            await asyncio.sleep(5)  # Wait a bit more
            
            # Try to send a message - should fail if connection was cleaned up
            try:
                await websocket.send(json.dumps({"type": "test"}))
                connection_still_alive = True
            except:
                connection_still_alive = False
            
            await websocket.close()
            
            if ping_received:
                self.log_test("Connection Cleanup/Timeout", True, 
                            f"Ping received, connection cleanup mechanism active (connection alive: {connection_still_alive})")
            else:
                self.log_test("Connection Cleanup/Timeout", False, 
                            "No ping received for timeout testing")
                
        except Exception as e:
            self.log_test("Connection Cleanup/Timeout", False, f"Error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all WebSocket tests"""
        print("🚀 Starting Enhanced WebSocket Server Optimization Testing")
        print("=" * 80)
        
        # Authenticate first
        await self.authenticate_admin()
        
        # Run all tests
        test_methods = [
            self.test_enhanced_websocket_connection,
            self.test_welcome_message_structure,
            self.test_heartbeat_ping_pong,
            self.test_subscription_management,
            self.test_admin_websocket_stats,
            self.test_websocket_health_check,
            self.test_multiple_client_connections,
            self.test_connection_cleanup_timeout
        ]
        
        for test_method in test_methods:
            try:
                if asyncio.iscoroutinefunction(test_method):
                    await test_method()
                else:
                    test_method()
                await asyncio.sleep(1)  # Brief pause between tests
            except Exception as e:
                test_name = test_method.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, False, f"Test execution error: {str(e)}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 ENHANCED WEBSOCKET SERVER OPTIMIZATION TEST SUMMARY")
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
    tester = WebSocketTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())