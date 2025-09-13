import requests
import sys
import json
import uuid
from datetime import datetime, timedelta

class KinAuraBoutiqueAPITester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.patient_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_products = []
        self.created_collections = []
        self.created_cross_sell_rules = []

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
                    if isinstance(response_data, dict) and len(str(response_data)) < 1000:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                        if response_data and len(response_data) <= 3:
                            for i, item in enumerate(response_data[:3]):
                                if isinstance(item, dict):
                                    print(f"   Item {i+1}: {item.get('name', item.get('sku', item.get('id', 'Unknown')))}")
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

    def setup_admin_authentication(self):
        """Setup admin authentication for testing"""
        print("\n🔐 Setting up Admin Authentication...")
        
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
            self.admin_token = response.get('access_token')
            user_data = response.get('user', {})
            print(f"   ✅ Admin authenticated with ID: {user_data.get('id')}")
            print(f"   ✅ Admin role: {user_data.get('role')}")
            return True
        else:
            print("   ❌ Failed to authenticate admin")
            return False

    def setup_patient_authentication(self):
        """Setup patient authentication for testing"""
        print("\n🔐 Setting up Patient Authentication...")
        
        patient_data = {
            "provider": "google",
            "access_token": "patient_token",
            "full_name": "Test Patient",
            "email": f"patient_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        }
        
        success, response = self.run_test(
            "Patient Social Login",
            "POST",
            "/auth/social-login",
            200,
            data=patient_data
        )
        
        if success:
            self.patient_token = response.get('access_token')
            user_data = response.get('user', {})
            print(f"   ✅ Patient authenticated with ID: {user_data.get('id')}")
            print(f"   ✅ Patient membership tier: {user_data.get('membership_tier')}")
            return True
        else:
            print("   ❌ Failed to authenticate patient")
            return False

    def test_boutique_product_catalog_api(self):
        """Test GET /api/shop/products - Boutique product catalog API endpoints"""
        print("\n🛍️ Testing Boutique Product Catalog API...")
        
        # Test 1: Get all products
        success, response = self.run_test(
            "Get All Products",
            "GET",
            "/shop/products",
            200
        )
        
        if not success:
            print("   ❌ Failed to retrieve product catalog")
            return False
        
        # Verify response structure
        if isinstance(response, dict):
            products = response.get('products', [])
            total_count = response.get('total_count', 0)
            print(f"   ✅ Product catalog structure correct - {total_count} total products")
            print(f"   ✅ Retrieved {len(products)} products in current page")
            
            # Verify product structure
            if products:
                product = products[0]
                required_fields = ['sku', 'name', 'price_eur', 'category', 'is_active']
                missing_fields = [field for field in required_fields if field not in product]
                if not missing_fields:
                    print(f"   ✅ Product structure contains all required fields")
                    print(f"   📦 Sample product: {product.get('name', {}).get('en', 'Unknown')} - €{product.get('price_eur', 0)}")
                else:
                    print(f"   ❌ Missing product fields: {missing_fields}")
            else:
                print(f"   ⚠️  No products found in catalog")
        else:
            print(f"   ❌ Invalid response structure - expected dict, got {type(response)}")
            return False
        
        # Test 2: Filter by category
        success, response = self.run_test(
            "Filter Products by Category (skincare)",
            "GET",
            "/shop/products?category=skincare",
            200
        )
        
        if success:
            if isinstance(response, dict):
                skincare_products = response.get('products', [])
                print(f"   ✅ Skincare category filter working - {len(skincare_products)} products")
            else:
                print(f"   ❌ Invalid category filter response")
        
        # Test 3: Search functionality
        success, response = self.run_test(
            "Search Products (illuminating)",
            "GET",
            "/shop/products?search=illuminating",
            200
        )
        
        if success:
            if isinstance(response, dict):
                search_results = response.get('products', [])
                print(f"   ✅ Product search working - {len(search_results)} results for 'illuminating'")
            else:
                print(f"   ❌ Invalid search response")
        
        # Test 4: Protocol-based filtering
        success, response = self.run_test(
            "Filter by Protocol (bright-and-even)",
            "GET",
            "/shop/products?protocol=bright-and-even",
            200
        )
        
        if success:
            if isinstance(response, dict):
                protocol_products = response.get('products', [])
                print(f"   ✅ Protocol filtering working - {len(protocol_products)} products for 'bright-and-even'")
            else:
                print(f"   ❌ Invalid protocol filter response")
        
        return True

    def test_product_collections_api(self):
        """Test GET /api/shop/collections - Product collections API"""
        print("\n📚 Testing Product Collections API...")
        
        # Test 1: Get all collections
        success, response = self.run_test(
            "Get All Collections",
            "GET",
            "/shop/collections",
            200
        )
        
        if not success:
            print("   ❌ Failed to retrieve collections")
            return False
        
        # Verify response structure
        if isinstance(response, dict) and 'collections' in response:
            collections = response.get('collections', [])
            print(f"   ✅ Retrieved {len(collections)} collections")
            
            if collections:
                collection = collections[0]
                required_fields = ['id', 'slug', 'name', 'description', 'products', 'is_active']
                missing_fields = [field for field in required_fields if field not in collection]
                if not missing_fields:
                    print(f"   ✅ Collection structure contains all required fields")
                    print(f"   📚 Sample collection: {collection.get('name', {}).get('en', 'Unknown')} with {len(collection.get('products', []))} products")
                    
                    # Check if collection has populated products
                    if 'populated_products' in collection:
                        populated_products = collection.get('populated_products', [])
                        print(f"   ✅ Collection has {len(populated_products)} populated products")
                    else:
                        print(f"   ⚠️  Collection products not populated")
                else:
                    print(f"   ❌ Missing collection fields: {missing_fields}")
            else:
                print(f"   ⚠️  No collections found")
        else:
            print(f"   ❌ Invalid response structure - expected dict with 'collections', got {type(response)}")
            return False
        
        return True

    def test_cross_sell_recommendations_api(self):
        """Test GET /api/shop/recommendations - Cross-sell recommendations"""
        print("\n🎯 Testing Cross-sell Recommendations API...")
        
        # Test 1: General recommendations
        success, response = self.run_test(
            "Get General Recommendations",
            "GET",
            "/shop/recommendations",
            200
        )
        
        if not success:
            print("   ❌ Failed to retrieve general recommendations")
            return False
        
        # Verify response structure
        if isinstance(response, dict) and 'recommendations' in response:
            recommendations = response.get('recommendations', [])
            print(f"   ✅ Retrieved {len(recommendations)} general recommendations")
            
            if recommendations:
                recommendation = recommendations[0]
                required_fields = ['sku', 'name', 'price_eur', 'category']
                missing_fields = [field for field in required_fields if field not in recommendation]
                if not missing_fields:
                    print(f"   ✅ Recommendation structure contains all required fields")
                    print(f"   🎯 Sample recommendation: {recommendation.get('name', {}).get('en', 'Unknown')} - €{recommendation.get('price_eur', 0)}")
                else:
                    print(f"   ❌ Missing recommendation fields: {missing_fields}")
        else:
            print(f"   ❌ Invalid response structure - expected dict with 'recommendations', got {type(response)}")
            return False
        
        # Test 2: Protocol-based recommendations
        protocols_to_test = ['bright-and-even', 'cellular-renewal', 'longevity', 'pre-event']
        
        for protocol in protocols_to_test:
            success, response = self.run_test(
                f"Get Protocol Recommendations ({protocol})",
                "GET",
                f"/shop/recommendations?protocol={protocol}",
                200
            )
            
            if success and isinstance(response, dict) and 'recommendations' in response:
                recommendations = response.get('recommendations', [])
                print(f"   ✅ {protocol} protocol recommendations: {len(recommendations)} products")
            else:
                print(f"   ❌ Failed to get {protocol} protocol recommendations")
        
        return True

    def test_admin_product_management(self):
        """Test admin product management endpoints"""
        print("\n👨‍💼 Testing Admin Product Management...")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
        
        # Test 1: Get admin products view
        success, response = self.run_test(
            "Get Admin Products",
            "GET",
            "/admin/shop/products",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            if isinstance(response, dict) and 'products' in response:
                products = response.get('products', [])
                print(f"   ✅ Admin can view {len(products)} products")
            else:
                print(f"   ❌ Invalid admin products response")
        
        # Test 2: Create a new product
        product_data = {
            "sku": f"TEST-PRODUCT-{datetime.now().strftime('%H%M%S')}",
            "name": {
                "en": "Test KinAura Product",
                "it": "Prodotto Test KinAura"
            },
            "slug": f"test-product-{datetime.now().strftime('%H%M%S')}",
            "short_description": {
                "en": "A test product for API testing",
                "it": "Un prodotto di test per i test API"
            },
            "description_html": {
                "en": "<p>This is a test product created for API testing purposes.</p>",
                "it": "<p>Questo è un prodotto di test creato per scopi di test API.</p>"
            },
            "category": "skincare",
            "price_eur": 199.99,
            "price_membership": {
                "gold": 179.99,
                "platinum": 159.99,
                "elite": 139.99
            },
            "tags": ["test", "api", "skincare"],
            "protocol_bindings": ["bright-and-even", "cellular-renewal"],
            "inventory": 100,
            "is_active": True,
            "badge": "New",
            "ingredients": {
                "en": "Test ingredients list",
                "it": "Lista ingredienti di test"
            },
            "usage_instructions": {
                "en": "Apply as directed for testing",
                "it": "Applicare come indicato per il test"
            }
        }
        
        success, response = self.run_test(
            "Create New Product",
            "POST",
            "/admin/shop/products",
            200,
            data=product_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            created_sku = response.get('sku') or response.get('product', {}).get('sku')
            if created_sku:
                self.created_products.append(created_sku)
                print(f"   ✅ Product created successfully with SKU: {created_sku}")
            else:
                print(f"   ⚠️  Product created but SKU not returned in response")
                # Use the SKU from our request data as fallback
                self.created_products.append(product_data['sku'])
            
            # Verify bilingual content
            product_name = response.get('name') or response.get('product', {}).get('name', {})
            if product_name.get('en') == product_data['name']['en']:
                print(f"   ✅ Bilingual content stored correctly")
            
            # Verify membership pricing
            pricing = response.get('price_membership') or response.get('product', {}).get('price_membership', {})
            if pricing.get('gold') == product_data['price_membership']['gold']:
                print(f"   ✅ Membership pricing stored correctly")
        else:
            print(f"   ❌ Failed to create product")
            return False
        
        return True

    def test_admin_collections_management(self):
        """Test admin collections management endpoints"""
        print("\n📚 Testing Admin Collections Management...")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
        
        # Test 1: Get admin collections view
        success, response = self.run_test(
            "Get Admin Collections",
            "GET",
            "/admin/shop/collections",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            if isinstance(response, dict) and 'collections' in response:
                collections = response.get('collections', [])
                print(f"   ✅ Admin can view {len(collections)} collections")
            else:
                print(f"   ❌ Invalid admin collections response")
        
        # Test 2: Create a new collection
        collection_data = {
            "slug": f"test-collection-{datetime.now().strftime('%H%M%S')}",
            "name": {
                "en": "Test Collection",
                "it": "Collezione Test"
            },
            "description": {
                "en": "A test collection for API testing",
                "it": "Una collezione di test per i test API"
            },
            "products": self.created_products[:2] if self.created_products else [],
            "ordering": 1,
            "is_active": True
        }
        
        success, response = self.run_test(
            "Create New Collection",
            "POST",
            "/admin/shop/collections",
            200,
            data=collection_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            created_id = response.get('id')
            self.created_collections.append(created_id)
            print(f"   ✅ Collection created successfully with ID: {created_id}")
            
            # Verify bilingual content
            if response.get('name', {}).get('en') == collection_data['name']['en']:
                print(f"   ✅ Collection bilingual content stored correctly")
        else:
            print(f"   ❌ Failed to create collection")
            return False
        
        return True

    def test_admin_cross_sell_rules(self):
        """Test admin cross-sell rules management"""
        print("\n🎯 Testing Admin Cross-sell Rules Management...")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
        
        # Test 1: Get existing cross-sell rules
        success, response = self.run_test(
            "Get Cross-sell Rules",
            "GET",
            "/admin/shop/cross-sell-rules",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            if isinstance(response, dict) and 'rules' in response:
                rules = response.get('rules', [])
                print(f"   ✅ Retrieved {len(rules)} cross-sell rules")
            else:
                print(f"   ❌ Invalid cross-sell rules response")
        
        # Test 2: Create a new cross-sell rule
        if self.created_products:
            rule_data = {
                "protocol_id": "bright-and-even",
                "product_skus": self.created_products[:2] if len(self.created_products) >= 2 else self.created_products,
                "priority": 3,
                "microcopy": {
                    "en": "Perfect for brightening your complexion",
                    "it": "Perfetto per illuminare la tua carnagione"
                },
                "is_active": True
            }
            
            success, response = self.run_test(
                "Create Cross-sell Rule",
                "POST",
                "/admin/shop/cross-sell-rules",
                200,
                data=rule_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                created_id = response.get('id')
                self.created_cross_sell_rules.append(created_id)
                print(f"   ✅ Cross-sell rule created successfully with ID: {created_id}")
                
                # Verify bilingual microcopy
                if response.get('microcopy', {}).get('en') == rule_data['microcopy']['en']:
                    print(f"   ✅ Cross-sell rule bilingual microcopy stored correctly")
            else:
                print(f"   ❌ Failed to create cross-sell rule")
                return False
        else:
            print(f"   ⚠️  No products available to create cross-sell rule")
        
        return True

    def test_membership_pricing_tiers(self):
        """Test membership pricing functionality"""
        print("\n💎 Testing Membership Pricing Tiers...")
        
        # Create test patients with different membership tiers
        membership_tiers = ['gold', 'platinum', 'elite']
        patient_tokens = {}
        
        for tier in membership_tiers:
            # Create patient with specific membership tier
            patient_data = {
                "email": f"{tier}_member_{datetime.now().strftime('%H%M%S')}@kinaura.com",
                "full_name": f"{tier.title()} Member Test",
                "phone": "+1234567890",
                "membership_tier": tier,
                "tags": [tier, "test"]
            }
            
            success, response = self.run_test(
                f"Create {tier.title()} Member",
                "POST",
                "/admin/patients",
                200,
                data=patient_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                # Login as this patient
                login_data = {
                    "provider": "google",
                    "access_token": f"{tier}_token",
                    "full_name": patient_data['full_name'],
                    "email": patient_data['email']
                }
                
                login_success, login_response = self.run_test(
                    f"Login {tier.title()} Member",
                    "POST",
                    "/auth/social-login",
                    200,
                    data=login_data
                )
                
                if login_success:
                    patient_tokens[tier] = login_response.get('access_token')
                    print(f"   ✅ {tier.title()} member authenticated successfully")
        
        # Test pricing for each membership tier
        for tier, token in patient_tokens.items():
            success, response = self.run_test(
                f"Get Products as {tier.title()} Member",
                "GET",
                "/shop/products",
                200,
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if success and isinstance(response, dict):
                products = response.get('products', [])
                if products:
                    product = products[0]
                    base_price = product.get('price_eur', 0)
                    membership_pricing = product.get('price_membership', {})
                    tier_price = membership_pricing.get(tier, base_price)
                    
                    if tier_price < base_price:
                        discount_percent = ((base_price - tier_price) / base_price) * 100
                        print(f"   ✅ {tier.title()} member gets {discount_percent:.1f}% discount (€{base_price} → €{tier_price})")
                    else:
                        print(f"   ⚠️  {tier.title()} member pricing not applied correctly")
        
        return True

    def test_boutique_data_integrity(self):
        """Test data integrity and relationships"""
        print("\n🔍 Testing Boutique Data Integrity...")
        
        # Test 1: Verify product-collection relationships
        success, collections_response = self.run_test(
            "Verify Product-Collection Relationships",
            "GET",
            "/shop/collections",
            200
        )
        
        if success and isinstance(collections_response, dict):
            collections = collections_response.get('collections', [])
            for collection in collections:
                product_skus = collection.get('products', [])
                if product_skus:
                    # Check if products exist
                    success, products_response = self.run_test(
                        f"Verify Products in Collection {collection.get('name', {}).get('en', 'Unknown')}",
                        "GET",
                        "/shop/products",
                        200
                    )
                    
                    if success and isinstance(products_response, dict):
                        all_products = products_response.get('products', [])
                        existing_skus = [p.get('sku') for p in all_products]
                        missing_products = [sku for sku in product_skus if sku not in existing_skus]
                        
                        if not missing_products:
                            print(f"   ✅ All products in collection exist")
                        else:
                            print(f"   ❌ Missing products in collection: {missing_products}")
        
        # Test 2: Verify cross-sell rule product references
        success, rules_response = self.run_test(
            "Verify Cross-sell Rule Product References",
            "GET",
            "/admin/shop/cross-sell-rules",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and isinstance(rules_response, dict):
            rules = rules_response.get('rules', [])
            for rule in rules:
                product_skus = rule.get('product_skus', [])
                if product_skus:
                    # Check if referenced products exist
                    success, products_response = self.run_test(
                        f"Verify Products in Cross-sell Rule",
                        "GET",
                        "/shop/products",
                        200
                    )
                    
                    if success and isinstance(products_response, dict):
                        all_products = products_response.get('products', [])
                        existing_skus = [p.get('sku') for p in all_products]
                        missing_products = [sku for sku in product_skus if sku not in existing_skus]
                        
                        if not missing_products:
                            print(f"   ✅ All products in cross-sell rule exist")
                        else:
                            print(f"   ❌ Missing products in cross-sell rule: {missing_products}")
        
        return True

    def run_comprehensive_boutique_tests(self):
        """Run all Boutique backend tests"""
        print("🛍️ Starting Comprehensive KinAura Boutique Backend Testing...")
        print("=" * 80)
        
        # Setup authentication
        if not self.setup_admin_authentication():
            print("❌ Failed to setup admin authentication - aborting tests")
            return False
        
        if not self.setup_patient_authentication():
            print("❌ Failed to setup patient authentication - aborting tests")
            return False
        
        # Run all tests
        test_methods = [
            self.test_boutique_product_catalog_api,
            self.test_product_collections_api,
            self.test_cross_sell_recommendations_api,
            self.test_admin_product_management,
            self.test_admin_collections_management,
            self.test_admin_cross_sell_rules,
            self.test_membership_pricing_tiers,
            self.test_boutique_data_integrity
        ]
        
        passed_tests = 0
        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
                    print(f"✅ {test_method.__name__} PASSED")
                else:
                    print(f"❌ {test_method.__name__} FAILED")
            except Exception as e:
                print(f"❌ {test_method.__name__} FAILED with exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("🛍️ BOUTIQUE BACKEND TESTING SUMMARY")
        print("=" * 80)
        print(f"Total API Tests Run: {self.tests_run}")
        print(f"Total API Tests Passed: {self.tests_passed}")
        print(f"API Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"Total Test Methods: {len(test_methods)}")
        print(f"Test Methods Passed: {passed_tests}")
        print(f"Test Method Success Rate: {(passed_tests/len(test_methods))*100:.1f}%")
        
        if passed_tests == len(test_methods):
            print("🎉 ALL BOUTIQUE BACKEND TESTS PASSED!")
            return True
        else:
            print(f"⚠️  {len(test_methods) - passed_tests} test methods failed")
            return False

def main():
    """Main function to run the tests"""
    tester = KinAuraBoutiqueAPITester()
    
    try:
        success = tester.run_comprehensive_boutique_tests()
        if success:
            print("\n✅ Boutique backend functionality is working correctly!")
            sys.exit(0)
        else:
            print("\n❌ Some Boutique backend tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()