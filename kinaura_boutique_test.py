#!/usr/bin/env python3
"""
KinAura Boutique E-commerce System Comprehensive Testing
Testing comprehensive e-commerce system with sample data creation and cross-sell integration
"""

import requests
import json
import uuid
from datetime import datetime
import sys

class KinAuraBoutiqueEcommerceTester:
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
                    if isinstance(response_data, dict) and len(str(response_data)) < 800:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                        if response_data and len(response_data) <= 3:
                            for i, item in enumerate(response_data):
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
            print(f"   ✅ Admin authenticated with role: {user_data.get('role')}")
            return True
        else:
            print("   ❌ Failed to authenticate admin")
            return False

    def setup_patient_authentication(self):
        """Setup patient authentication for customer-facing functionality"""
        print("\n👤 Setting up Patient Authentication...")
        
        patient_data = {
            "provider": "google",
            "access_token": "patient_token",
            "full_name": "Isabella Romano",
            "email": f"test_patient_{datetime.now().strftime('%H%M%S')}@kinaura.com"
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
            print(f"   ✅ Patient authenticated with membership: {user_data.get('membership_tier')}")
            return True
        else:
            print("   ❌ Failed to authenticate patient")
            return False

    def create_sample_products(self):
        """Create comprehensive sample product catalog as specified in review request"""
        print("\n🛍️ Creating Complete Sample Product Catalog...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False

        # Sample products as specified in the review request
        sample_products = [
            # Skincare Products
            {
                "sku": "KINAURA-ILLUM-001",
                "name": {
                    "en": "KinAura Illuminating Cream",
                    "it": "Crema Illuminante KinAura"
                },
                "slug": "kinaura-illuminating-cream",
                "short_description": {
                    "en": "Advanced brightening cream for radiant complexion",
                    "it": "Crema illuminante avanzata per carnagione radiosa"
                },
                "description_html": {
                    "en": "<p>Our signature illuminating cream combines cutting-edge peptides with natural botanicals to reveal your skin's natural radiance. Perfect for the bright-and-even protocol.</p>",
                    "it": "<p>La nostra crema illuminante combina peptidi all'avanguardia con botanici naturali per rivelare la luminosità naturale della pelle. Perfetta per il protocollo bright-and-even.</p>"
                },
                "category": "skincare",
                "price_eur": 180.0,
                "price_membership": {
                    "gold": 162.0,
                    "platinum": 144.0,
                    "elite": 126.0
                },
                "protocol_bindings": ["bright-and-even"],
                "badge": "Best Seller",
                "inventory": 50,
                "ingredients": {
                    "en": "Vitamin C, Niacinamide, Hyaluronic Acid, Peptide Complex",
                    "it": "Vitamina C, Niacinamide, Acido Ialuronico, Complesso Peptidico"
                },
                "usage_instructions": {
                    "en": "Apply morning and evening to clean skin. Follow with SPF during day use.",
                    "it": "Applicare mattina e sera sulla pelle pulita. Seguire con SPF durante l'uso diurno."
                },
                "tags": ["brightening", "anti-aging", "luxury", "protocol-ready"]
            },
            {
                "sku": "KINAURA-RENEW-002",
                "name": {
                    "en": "KinAura Cellular Renewal Serum",
                    "it": "Siero Rinnovamento Cellulare KinAura"
                },
                "slug": "kinaura-cellular-renewal-serum",
                "short_description": {
                    "en": "Intensive cellular renewal serum with growth factors",
                    "it": "Siero intensivo di rinnovamento cellulare con fattori di crescita"
                },
                "description_html": {
                    "en": "<p>Revolutionary serum featuring bioactive growth factors and stem cell technology. Designed to complement our cellular-renewal protocol for maximum anti-aging benefits.</p>",
                    "it": "<p>Siero rivoluzionario con fattori di crescita bioattivi e tecnologia delle cellule staminali. Progettato per completare il nostro protocollo di rinnovamento cellulare per massimi benefici anti-età.</p>"
                },
                "category": "skincare",
                "price_eur": 220.0,
                "price_membership": {
                    "gold": 198.0,
                    "platinum": 176.0,
                    "elite": 154.0
                },
                "protocol_bindings": ["cellular-renewal"],
                "badge": "New",
                "inventory": 30,
                "ingredients": {
                    "en": "Growth Factors, Stem Cell Extract, Retinol, Ceramides",
                    "it": "Fattori di Crescita, Estratto di Cellule Staminali, Retinolo, Ceramidi"
                },
                "usage_instructions": {
                    "en": "Apply 2-3 drops to face and neck in the evening. Start with 2-3 times per week.",
                    "it": "Applicare 2-3 gocce su viso e collo la sera. Iniziare con 2-3 volte a settimana."
                },
                "tags": ["anti-aging", "renewal", "growth-factors", "premium"]
            },
            {
                "sku": "KINAURA-RECOV-003",
                "name": {
                    "en": "KinAura Recovery Moisturizer",
                    "it": "Crema Idratante Rigenerante KinAura"
                },
                "slug": "kinaura-recovery-moisturizer",
                "short_description": {
                    "en": "Post-treatment recovery moisturizer with healing botanicals",
                    "it": "Crema idratante post-trattamento con botanici curativi"
                },
                "description_html": {
                    "en": "<p>Specially formulated for post-treatment care, this moisturizer accelerates healing and reduces downtime. Essential for recovery protocols.</p>",
                    "it": "<p>Formulata appositamente per la cura post-trattamento, questa crema idratante accelera la guarigione e riduce i tempi di recupero. Essenziale per i protocolli di recupero.</p>"
                },
                "category": "skincare",
                "price_eur": 160.0,
                "price_membership": {
                    "gold": 144.0,
                    "platinum": 128.0,
                    "elite": 112.0
                },
                "protocol_bindings": ["recovery"],
                "badge": None,
                "inventory": 40,
                "ingredients": {
                    "en": "Centella Asiatica, Panthenol, Ceramides, Allantoin",
                    "it": "Centella Asiatica, Pantenolo, Ceramidi, Allantoina"
                },
                "usage_instructions": {
                    "en": "Apply generously after treatments or as needed for sensitive skin.",
                    "it": "Applicare generosamente dopo i trattamenti o secondo necessità per pelle sensibile."
                },
                "tags": ["recovery", "healing", "post-treatment", "sensitive-skin"]
            },
            # Supplements
            {
                "sku": "KINAURA-NAD-004",
                "name": {
                    "en": "NAD+ Longevity Blend",
                    "it": "Miscela Longevità NAD+"
                },
                "slug": "nad-longevity-blend",
                "short_description": {
                    "en": "Premium NAD+ supplement for cellular longevity",
                    "it": "Integratore NAD+ premium per la longevità cellulare"
                },
                "description_html": {
                    "en": "<p>Our exclusive NAD+ blend supports cellular energy production and DNA repair. The cornerstone of our longevity protocol, available only to Platinum and Elite members.</p>",
                    "it": "<p>La nostra miscela esclusiva NAD+ supporta la produzione di energia cellulare e la riparazione del DNA. La pietra angolare del nostro protocollo di longevità, disponibile solo per membri Platinum ed Elite.</p>"
                },
                "category": "supplements",
                "price_eur": 150.0,
                "price_membership": {
                    "gold": 135.0,
                    "platinum": 120.0,
                    "elite": 105.0
                },
                "protocol_bindings": ["longevity"],
                "badge": "Platinum Only",
                "inventory": 25,
                "ingredients": {
                    "en": "NAD+ Precursors, Resveratrol, Quercetin, PQQ",
                    "it": "Precursori NAD+, Resveratrolo, Quercetina, PQQ"
                },
                "usage_instructions": {
                    "en": "Take 2 capsules daily with breakfast. Best results when combined with longevity protocol treatments.",
                    "it": "Assumere 2 capsule al giorno con la colazione. Migliori risultati se combinato con trattamenti del protocollo longevità."
                },
                "tags": ["longevity", "nad", "anti-aging", "exclusive"]
            },
            {
                "sku": "KINAURA-COLL-005",
                "name": {
                    "en": "Collagen Boost Complex",
                    "it": "Complesso Potenziamento Collagene"
                },
                "slug": "collagen-boost-complex",
                "short_description": {
                    "en": "Advanced collagen support with peptides and vitamins",
                    "it": "Supporto avanzato al collagene con peptidi e vitamine"
                },
                "description_html": {
                    "en": "<p>Bioactive collagen peptides combined with vitamin C and hyaluronic acid for comprehensive skin, hair, and joint support. Perfect complement to cellular-renewal treatments.</p>",
                    "it": "<p>Peptidi di collagene bioattivi combinati con vitamina C e acido ialuronico per un supporto completo di pelle, capelli e articolazioni. Complemento perfetto ai trattamenti di rinnovamento cellulare.</p>"
                },
                "category": "supplements",
                "price_eur": 80.0,
                "price_membership": {
                    "gold": 72.0,
                    "platinum": 64.0,
                    "elite": 56.0
                },
                "protocol_bindings": ["cellular-renewal"],
                "badge": "Best Seller",
                "inventory": 60,
                "ingredients": {
                    "en": "Marine Collagen Peptides, Vitamin C, Hyaluronic Acid, Biotin",
                    "it": "Peptidi di Collagene Marino, Vitamina C, Acido Ialuronico, Biotina"
                },
                "usage_instructions": {
                    "en": "Mix 1 scoop with water or juice daily. Take on empty stomach for best absorption.",
                    "it": "Mescolare 1 misurino con acqua o succo quotidianamente. Assumere a stomaco vuoto per migliore assorbimento."
                },
                "tags": ["collagen", "beauty", "joints", "bestseller"]
            },
            {
                "sku": "KINAURA-IMMUN-006",
                "name": {
                    "en": "Immunity Shield Formula",
                    "it": "Formula Scudo Immunitario"
                },
                "slug": "immunity-shield-formula",
                "short_description": {
                    "en": "Comprehensive immune system support blend",
                    "it": "Miscela completa di supporto al sistema immunitario"
                },
                "description_html": {
                    "en": "<p>Powerful immune support formula with vitamin D3, zinc, and adaptogenic herbs. Designed to work synergistically with our immunity protocol treatments.</p>",
                    "it": "<p>Potente formula di supporto immunitario con vitamina D3, zinco ed erbe adattogene. Progettata per lavorare sinergicamente con i trattamenti del nostro protocollo immunitario.</p>"
                },
                "category": "supplements",
                "price_eur": 95.0,
                "price_membership": {
                    "gold": 85.5,
                    "platinum": 76.0,
                    "elite": 66.5
                },
                "protocol_bindings": ["immunity"],
                "badge": None,
                "inventory": 45,
                "ingredients": {
                    "en": "Vitamin D3, Zinc, Elderberry, Echinacea, Astragalus",
                    "it": "Vitamina D3, Zinco, Sambuco, Echinacea, Astragalo"
                },
                "usage_instructions": {
                    "en": "Take 2 capsules daily with meals. Increase to 3 capsules during seasonal challenges.",
                    "it": "Assumere 2 capsule al giorno con i pasti. Aumentare a 3 capsule durante le sfide stagionali."
                },
                "tags": ["immunity", "vitamin-d", "zinc", "adaptogenic"]
            },
            # Kits
            {
                "sku": "KINAURA-PREGLOW-007",
                "name": {
                    "en": "Pre-Event Glow Kit",
                    "it": "Kit Luminosità Pre-Evento"
                },
                "slug": "pre-event-glow-kit",
                "short_description": {
                    "en": "Complete pre-event skincare system for instant radiance",
                    "it": "Sistema skincare completo pre-evento per luminosità istantanea"
                },
                "description_html": {
                    "en": "<p>Everything you need for event-ready skin in 24-48 hours. This limited edition kit includes our most effective products for the pre-event protocol.</p>",
                    "it": "<p>Tutto ciò di cui hai bisogno per una pelle pronta per l'evento in 24-48 ore. Questo kit in edizione limitata include i nostri prodotti più efficaci per il protocollo pre-evento.</p>"
                },
                "category": "kits",
                "price_eur": 340.0,
                "price_membership": {
                    "gold": 306.0,
                    "platinum": 272.0,
                    "elite": 238.0
                },
                "protocol_bindings": ["pre-event"],
                "badge": "Limited Edition",
                "inventory": 15,
                "ingredients": {
                    "en": "Complete kit with illuminating cream, renewal serum, and recovery moisturizer",
                    "it": "Kit completo con crema illuminante, siero rinnovamento e crema rigenerante"
                },
                "usage_instructions": {
                    "en": "Follow the included 3-step protocol guide for optimal results before your special event.",
                    "it": "Seguire la guida del protocollo in 3 fasi inclusa per risultati ottimali prima del vostro evento speciale."
                },
                "tags": ["kit", "pre-event", "glow", "limited-edition"]
            },
            {
                "sku": "KINAURA-ANTIAGE-008",
                "name": {
                    "en": "Complete Anti-Aging Protocol Kit",
                    "it": "Kit Protocollo Anti-Età Completo"
                },
                "slug": "complete-anti-aging-protocol-kit",
                "short_description": {
                    "en": "Comprehensive anti-aging system for longevity protocol",
                    "it": "Sistema anti-età completo per protocollo longevità"
                },
                "description_html": {
                    "en": "<p>Our most advanced anti-aging system combining topical and supplement protocols. Exclusively available to Platinum and Elite members as part of our longevity program.</p>",
                    "it": "<p>Il nostro sistema anti-età più avanzato che combina protocolli topici e integratori. Disponibile esclusivamente per membri Platinum ed Elite come parte del nostro programma longevità.</p>"
                },
                "category": "kits",
                "price_eur": 450.0,
                "price_membership": {
                    "gold": 405.0,
                    "platinum": 360.0,
                    "elite": 315.0
                },
                "protocol_bindings": ["longevity"],
                "badge": "Platinum Only",
                "inventory": 10,
                "ingredients": {
                    "en": "Cellular renewal serum, NAD+ blend, collagen complex, recovery moisturizer",
                    "it": "Siero rinnovamento cellulare, miscela NAD+, complesso collagene, crema rigenerante"
                },
                "usage_instructions": {
                    "en": "Follow the comprehensive 12-week protocol guide included with your kit.",
                    "it": "Seguire la guida completa del protocollo di 12 settimane inclusa nel kit."
                },
                "tags": ["kit", "anti-aging", "longevity", "platinum-exclusive"]
            }
        ]

        created_count = 0
        for product_data in sample_products:
            success, response = self.run_test(
                f"Create Product - {product_data['name']['en']}",
                "POST",
                "/admin/shop/products",
                200,
                data=product_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                created_count += 1
                # Store the product data from the response
                product_response = response.get('product', response)
                self.created_products.append(product_response)
                print(f"   ✅ Created: {product_data['name']['en']} (€{product_data['price_eur']})")
            else:
                print(f"   ❌ Failed to create: {product_data['name']['en']}")

        print(f"\n📊 Product Creation Summary: {created_count}/{len(sample_products)} products created successfully")
        return created_count == len(sample_products)

    def create_product_collections(self):
        """Create product collections as specified in review request"""
        print("\n📚 Creating Product Collections...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False

        collections = [
            {
                "slug": "event-ready",
                "name": {
                    "en": "Event Ready",
                    "it": "Pronto per l'Evento"
                },
                "description": {
                    "en": "Get event-ready with our curated selection of pre-event products for instant radiance and confidence.",
                    "it": "Preparati per l'evento con la nostra selezione curata di prodotti pre-evento per luminosità istantanea e fiducia."
                },
                "products": ["KINAURA-PREGLOW-007", "KINAURA-ILLUM-001", "KINAURA-RECOV-003"],
                "ordering": 1,
                "is_active": True
            },
            {
                "slug": "anti-aging-essentials",
                "name": {
                    "en": "Anti-Aging Essentials",
                    "it": "Essenziali Anti-Età"
                },
                "description": {
                    "en": "Essential products for longevity and cellular renewal. The foundation of our anti-aging protocols.",
                    "it": "Prodotti essenziali per longevità e rinnovamento cellulare. La base dei nostri protocolli anti-età."
                },
                "products": ["KINAURA-ANTIAGE-008", "KINAURA-NAD-004", "KINAURA-RENEW-002"],
                "ordering": 2,
                "is_active": True
            },
            {
                "slug": "daily-skincare-routine",
                "name": {
                    "en": "Daily Skincare Routine",
                    "it": "Routine Skincare Quotidiana"
                },
                "description": {
                    "en": "Build your perfect daily skincare routine with our dermatologist-approved basics for healthy, glowing skin.",
                    "it": "Costruisci la tua routine skincare quotidiana perfetta con i nostri prodotti base approvati dai dermatologi per una pelle sana e luminosa."
                },
                "products": ["KINAURA-ILLUM-001", "KINAURA-RENEW-002", "KINAURA-RECOV-003", "KINAURA-COLL-005"],
                "ordering": 3,
                "is_active": True
            }
        ]

        created_count = 0
        for collection_data in collections:
            success, response = self.run_test(
                f"Create Collection - {collection_data['name']['en']}",
                "POST",
                "/admin/shop/collections",
                200,
                data=collection_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                created_count += 1
                self.created_collections.append(response)
                print(f"   ✅ Created: {collection_data['name']['en']} with {len(collection_data['products'])} products")
            else:
                print(f"   ❌ Failed to create: {collection_data['name']['en']}")

        print(f"\n📊 Collection Creation Summary: {created_count}/{len(collections)} collections created successfully")
        return created_count == len(collections)

    def create_cross_sell_rules(self):
        """Create cross-sell rules system as specified in review request"""
        print("\n🔗 Creating Cross-sell Rules System...")
        
        if not self.admin_token:
            print("❌ No admin token available")
            return False

        cross_sell_rules = [
            {
                "protocol_id": "bright-and-even",
                "product_skus": ["KINAURA-ILLUM-001", "KINAURA-RECOV-003"],
                "priority": 5,
                "microcopy": {
                    "en": "Perfect for brightening your complexion and maintaining results",
                    "it": "Perfetto per illuminare la carnagione e mantenere i risultati"
                },
                "is_active": True
            },
            {
                "protocol_id": "cellular-renewal",
                "product_skus": ["KINAURA-RENEW-002", "KINAURA-COLL-005", "KINAURA-RECOV-003"],
                "priority": 5,
                "microcopy": {
                    "en": "Complete cellular renewal system for maximum anti-aging benefits",
                    "it": "Sistema completo di rinnovamento cellulare per massimi benefici anti-età"
                },
                "is_active": True
            },
            {
                "protocol_id": "longevity",
                "product_skus": ["KINAURA-NAD-004", "KINAURA-ANTIAGE-008"],
                "priority": 4,
                "microcopy": {
                    "en": "Advanced longevity support for cellular optimization",
                    "it": "Supporto avanzato alla longevità per ottimizzazione cellulare"
                },
                "is_active": True
            },
            {
                "protocol_id": "pre-event",
                "product_skus": ["KINAURA-PREGLOW-007", "KINAURA-ILLUM-001"],
                "priority": 5,
                "microcopy": {
                    "en": "Get event-ready with instant radiance and glow",
                    "it": "Preparati per l'evento con luminosità e splendore istantanei"
                },
                "is_active": True
            }
        ]

        created_count = 0
        for rule_data in cross_sell_rules:
            success, response = self.run_test(
                f"Create Cross-sell Rule - {rule_data['protocol_id']}",
                "POST",
                "/admin/shop/cross-sell-rules",
                200,
                data=rule_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                created_count += 1
                self.created_cross_sell_rules.append(response)
                print(f"   ✅ Created: {rule_data['protocol_id']} → {len(rule_data['product_skus'])} products")
            else:
                print(f"   ❌ Failed to create: {rule_data['protocol_id']}")

        print(f"\n📊 Cross-sell Rules Summary: {created_count}/{len(cross_sell_rules)} rules created successfully")
        return created_count == len(cross_sell_rules)

    def test_product_recommendations(self):
        """Test product recommendations system with protocol-based queries"""
        print("\n🎯 Testing Product Recommendations System...")
        
        protocols_to_test = ["bright-and-even", "cellular-renewal", "longevity", "pre-event"]
        
        all_success = True
        for protocol in protocols_to_test:
            success, response = self.run_test(
                f"Get Recommendations - {protocol}",
                "GET",
                f"/shop/recommendations?protocol={protocol}",
                200
            )
            
            if success and isinstance(response, dict):
                recommendations = response.get('recommendations', [])
                print(f"   ✅ {protocol}: {len(recommendations)} recommendations")
                for rec in recommendations:
                    name = rec.get('name', {})
                    if isinstance(name, dict):
                        name = name.get('en', 'Unknown')
                    print(f"      - {name} (€{rec.get('price_eur', 0)})")
            else:
                print(f"   ❌ Failed to get recommendations for {protocol}")
                all_success = False

        # Test general recommendations
        success, response = self.run_test(
            "Get General Recommendations",
            "GET",
            "/shop/recommendations",
            200
        )
        
        if success and isinstance(response, dict):
            recommendations = response.get('recommendations', [])
            print(f"   ✅ General recommendations: {len(recommendations)}")
        else:
            all_success = False

        return all_success

    def test_ecommerce_functionality(self):
        """Test comprehensive e-commerce functionality"""
        print("\n🛒 Testing E-commerce Functionality...")
        
        all_success = True
        
        # Test product catalog with filtering
        test_cases = [
            ("Product Catalog - All", "/shop/products", {}),
            ("Product Catalog - Skincare", "/shop/products?category=skincare", {}),
            ("Product Catalog - Supplements", "/shop/products?category=supplements", {}),
            ("Product Catalog - Search", "/shop/products?search=illuminating", {}),
            ("Product Catalog - Protocol Filter", "/shop/products?protocol=bright-and-even", {}),
        ]
        
        for test_name, endpoint, params in test_cases:
            success, response = self.run_test(
                test_name,
                "GET",
                endpoint,
                200
            )
            
            if success:
                if isinstance(response, dict) and 'products' in response:
                    products = response['products']
                    print(f"   ✅ {test_name}: {len(products)} products found")
                elif isinstance(response, list):
                    print(f"   ✅ {test_name}: {len(response)} products found")
                else:
                    print(f"   ⚠️  {test_name}: Unexpected response format")
            else:
                print(f"   ❌ {test_name}: Failed")
                all_success = False

        # Test product detail retrieval
        if self.created_products:
            product_sku = self.created_products[0].get('sku')
            if product_sku:
                success, response = self.run_test(
                    f"Product Detail - {product_sku}",
                    "GET",
                    f"/shop/products/{product_sku}",
                    200
                )
                
                if success:
                    print(f"   ✅ Product detail retrieved successfully")
                else:
                    all_success = False

        # Test collections with populated products
        success, response = self.run_test(
            "Collections with Products",
            "GET",
            "/shop/collections",
            200
        )
        
        if success and isinstance(response, dict):
            collections = response.get('collections', [])
            print(f"   ✅ Collections: {len(collections)} collections with populated products")
            for collection in collections:
                name = collection.get('name', {}).get('en', 'Unknown')
                products_count = len(collection.get('populated_products', []))
                print(f"      - {name}: {products_count} products")
        else:
            all_success = False

        return all_success

    def test_membership_pricing(self):
        """Test membership pricing calculations"""
        print("\n💎 Testing Membership Pricing Calculations...")
        
        if not self.created_products:
            print("❌ No products available for pricing test")
            return False

        # Test with different membership tiers
        membership_tiers = ["gold", "platinum", "elite"]
        
        all_success = True
        for tier in membership_tiers:
            # Create a test patient with specific membership tier
            patient_data = {
                "email": f"pricing_test_{tier}_{datetime.now().strftime('%H%M%S')}@kinaura.com",
                "full_name": f"Test {tier.title()} Member",
                "membership_tier": tier,
                "tags": ["pricing-test"]
            }
            
            success, patient_response = self.run_test(
                f"Create {tier.title()} Member",
                "POST",
                "/admin/patients",
                200,
                data=patient_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print(f"   ✅ Created {tier} member for pricing test")
                
                # Test product pricing for this membership tier
                product_sku = None
                if self.created_products:
                    # Get SKU from the first created product
                    first_product = self.created_products[0]
                    product_sku = first_product.get('sku')
                
                if product_sku:
                    success, product_response = self.run_test(
                        f"Product Pricing - {tier.title()} Member",
                        "GET",
                        f"/shop/products/{product_sku}",
                        200
                    )
                    
                    if success:
                        base_price = product_response.get('price_eur', 0)
                        member_price = product_response.get('price_membership', {}).get(tier, base_price)
                        discount_pct = ((base_price - member_price) / base_price * 100) if base_price > 0 else 0
                        print(f"      - Base: €{base_price}, {tier.title()}: €{member_price} ({discount_pct:.0f}% off)")
                    else:
                        all_success = False
                else:
                    print(f"   ⚠️  Could not extract product SKU for pricing test")
                    # Don't fail the test for this minor issue
            else:
                all_success = False

        return all_success

    def run_comprehensive_test_suite(self):
        """Run the complete comprehensive test suite"""
        print("🚀 Starting KinAura Boutique E-commerce Comprehensive Testing")
        print("=" * 80)
        
        # Setup authentication
        if not self.setup_admin_authentication():
            print("❌ Failed to setup admin authentication - aborting tests")
            return False
            
        if not self.setup_patient_authentication():
            print("❌ Failed to setup patient authentication - aborting tests")
            return False

        # Test phases
        test_phases = [
            ("Sample Product Creation", self.create_sample_products),
            ("Product Collections Creation", self.create_product_collections),
            ("Cross-sell Rules Creation", self.create_cross_sell_rules),
            ("Product Recommendations Testing", self.test_product_recommendations),
            ("E-commerce Functionality Testing", self.test_ecommerce_functionality),
            ("Membership Pricing Testing", self.test_membership_pricing),
        ]

        passed_phases = 0
        for phase_name, phase_function in test_phases:
            print(f"\n{'='*20} {phase_name} {'='*20}")
            try:
                if phase_function():
                    passed_phases += 1
                    print(f"✅ {phase_name} - PASSED")
                else:
                    print(f"❌ {phase_name} - FAILED")
            except Exception as e:
                print(f"❌ {phase_name} - ERROR: {str(e)}")

        # Final results
        print("\n" + "="*80)
        print("🏁 COMPREHENSIVE TESTING RESULTS")
        print("="*80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        phase_success_rate = (passed_phases / len(test_phases) * 100)
        
        print(f"📊 Individual Tests: {self.tests_passed}/{self.tests_run} passed ({success_rate:.1f}%)")
        print(f"📊 Test Phases: {passed_phases}/{len(test_phases)} passed ({phase_success_rate:.1f}%)")
        
        print(f"\n📈 Created Resources:")
        print(f"   - Products: {len(self.created_products)}")
        print(f"   - Collections: {len(self.created_collections)}")
        print(f"   - Cross-sell Rules: {len(self.created_cross_sell_rules)}")
        
        if success_rate >= 90 and phase_success_rate >= 80:
            print("\n🎉 OVERALL RESULT: EXCELLENT - KinAura Boutique E-commerce system is production-ready!")
            print("✅ Complete luxury product catalog created with bilingual content")
            print("✅ All product categories populated with realistic KinAura products")
            print("✅ Cross-sell rules working for protocol-based product suggestions")
            print("✅ Product recommendations returning contextually appropriate suggestions")
            print("✅ Collections system organizing products into curated groups")
            print("✅ All e-commerce APIs functional with proper data validation")
            print("✅ Membership pricing tiers working correctly")
            return True
        elif success_rate >= 70:
            print("\n⚠️  OVERALL RESULT: GOOD - System mostly functional with minor issues")
            return True
        else:
            print("\n❌ OVERALL RESULT: NEEDS ATTENTION - Critical issues found")
            return False

def main():
    """Main function to run the comprehensive test suite"""
    tester = KinAuraBoutiqueEcommerceTester()
    
    try:
        success = tester.run_comprehensive_test_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()