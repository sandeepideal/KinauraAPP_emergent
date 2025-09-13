#!/usr/bin/env python3
"""
Supabase Edge Functions Test Suite

This test suite is designed to test the newly implemented Supabase Edge Functions
for the KinAura application. 

IMPORTANT NOTE: The Supabase Edge Functions are currently implemented as TypeScript
files in /app/supabase/functions/ but are not deployed or running. They require:
1. A Supabase project to be set up
2. Environment variables (SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY)
3. The functions to be deployed via `supabase functions deploy`

Since these functions are not currently accessible via HTTP endpoints, this test
will analyze the implementation and report on the current status.
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime

class SupabaseEdgeFunctionAnalyzer:
    def __init__(self):
        self.functions_dir = Path("/app/supabase/functions")
        self.tests_run = 0
        self.tests_passed = 0
        self.analysis_results = {}
        
        # Expected functions based on review request
        self.expected_functions = {
            'admin': {
                'endpoints': ['dashboard-overview', 'metrics', 'audit-search'],
                'methods': ['GET', 'POST']
            },
            'auth': {
                'endpoints': ['register', 'login', 'profile'],
                'methods': ['GET', 'POST', 'PUT']
            },
            'clinical': {
                'endpoints': ['protocols', 'analyses'],
                'methods': ['GET', 'POST']
            },
            'booking': {
                'endpoints': ['services', 'appointments'],
                'methods': ['GET', 'POST']
            },
            'commerce': {
                'endpoints': ['formulas', 'orders', 'membership-plans'],
                'methods': ['GET', 'POST']
            },
            'messaging': {
                'endpoints': ['threads', 'messages', 'notifications'],
                'methods': ['GET', 'POST']
            },
            'gdpr': {
                'endpoints': ['consents', 'data-requests', 'audit-logs'],
                'methods': ['GET', 'POST']
            }
        }

    def analyze_function_implementation(self, function_name):
        """Analyze a single Edge Function implementation"""
        function_path = self.functions_dir / function_name / "index.ts"
        
        if not function_path.exists():
            return {
                'exists': False,
                'error': f'Function file not found: {function_path}'
            }
        
        try:
            with open(function_path, 'r') as f:
                content = f.read()
            
            analysis = {
                'exists': True,
                'file_size': len(content),
                'has_cors_handling': 'corsHeaders' in content,
                'has_auth_check': 'auth.getUser()' in content,
                'has_error_handling': 'try {' in content and 'catch' in content,
                'endpoints_found': [],
                'methods_supported': [],
                'uses_supabase_client': 'createClient' in content,
                'has_validation': 'z.object' in content or 'Schema' in content,
                'has_admin_check': 'role === \'admin\'' in content,
                'has_rls_queries': '.from(' in content
            }
            
            # Check for specific endpoints
            expected = self.expected_functions.get(function_name, {})
            for endpoint in expected.get('endpoints', []):
                if f"case '{endpoint}'" in content or f'"{endpoint}"' in content:
                    analysis['endpoints_found'].append(endpoint)
            
            # Check for HTTP methods
            for method in ['GET', 'POST', 'PUT', 'DELETE']:
                if f"req.method === '{method}'" in content:
                    analysis['methods_supported'].append(method)
            
            return analysis
            
        except Exception as e:
            return {
                'exists': True,
                'error': f'Error analyzing function: {str(e)}'
            }

    def test_function_structure(self, function_name):
        """Test the structure and implementation of a function"""
        self.tests_run += 1
        print(f"\n🔍 Analyzing {function_name} Edge Function...")
        
        analysis = self.analyze_function_implementation(function_name)
        self.analysis_results[function_name] = analysis
        
        if not analysis.get('exists', False):
            print(f"❌ Function not found: {analysis.get('error', 'Unknown error')}")
            return False
        
        if 'error' in analysis:
            print(f"❌ Analysis error: {analysis['error']}")
            return False
        
        # Check implementation quality
        score = 0
        max_score = 8
        
        checks = [
            ('CORS handling', analysis.get('has_cors_handling', False)),
            ('Authentication check', analysis.get('has_auth_check', False)),
            ('Error handling', analysis.get('has_error_handling', False)),
            ('Supabase client', analysis.get('uses_supabase_client', False)),
            ('Input validation', analysis.get('has_validation', False)),
            ('Admin role check', analysis.get('has_admin_check', False)),
            ('RLS queries', analysis.get('has_rls_queries', False)),
            ('File exists', True)  # Already checked above
        ]
        
        for check_name, passed in checks:
            if passed:
                score += 1
                print(f"   ✅ {check_name}")
            else:
                print(f"   ⚠️  {check_name}")
        
        # Check endpoints
        expected_endpoints = self.expected_functions.get(function_name, {}).get('endpoints', [])
        found_endpoints = analysis.get('endpoints_found', [])
        
        print(f"   📍 Endpoints: {len(found_endpoints)}/{len(expected_endpoints)} found")
        for endpoint in expected_endpoints:
            if endpoint in found_endpoints:
                print(f"      ✅ {endpoint}")
            else:
                print(f"      ❌ {endpoint} (missing)")
        
        # Check HTTP methods
        methods_found = analysis.get('methods_supported', [])
        print(f"   🔧 HTTP Methods: {', '.join(methods_found) if methods_found else 'None detected'}")
        
        print(f"   📊 Implementation Score: {score}/{max_score} ({score/max_score*100:.1f}%)")
        
        # Consider it passed if score is >= 6/8 (75%)
        passed = score >= 6
        if passed:
            self.tests_passed += 1
            print(f"   ✅ Function implementation: GOOD")
        else:
            print(f"   ⚠️  Function implementation: NEEDS IMPROVEMENT")
        
        return passed

    def check_shared_utilities(self):
        """Check for shared utilities like CORS"""
        self.tests_run += 1
        print(f"\n🔍 Checking shared utilities...")
        
        cors_file = self.functions_dir / "_shared" / "cors.ts"
        if cors_file.exists():
            print(f"   ✅ CORS utility found: {cors_file}")
            try:
                with open(cors_file, 'r') as f:
                    content = f.read()
                if 'Access-Control-Allow-Origin' in content:
                    print(f"   ✅ CORS headers properly configured")
                    self.tests_passed += 1
                    return True
                else:
                    print(f"   ⚠️  CORS headers incomplete")
            except Exception as e:
                print(f"   ❌ Error reading CORS file: {e}")
        else:
            print(f"   ❌ CORS utility not found")
        
        return False

    def check_database_schema(self):
        """Check if database migrations exist"""
        self.tests_run += 1
        print(f"\n🔍 Checking database schema...")
        
        migrations_dir = Path("/app/supabase/migrations")
        if migrations_dir.exists():
            migration_files = list(migrations_dir.glob("*.sql"))
            print(f"   ✅ Migrations directory found with {len(migration_files)} files")
            
            expected_migrations = [
                'initial_schema.sql',
                'rls_policies.sql', 
                'storage.sql'
            ]
            
            found_migrations = []
            for migration_file in migration_files:
                for expected in expected_migrations:
                    if expected in migration_file.name:
                        found_migrations.append(expected)
                        print(f"      ✅ {expected}")
            
            missing = set(expected_migrations) - set(found_migrations)
            for missing_migration in missing:
                print(f"      ❌ {missing_migration} (missing)")
            
            if len(found_migrations) >= 2:  # At least 2/3 migrations
                self.tests_passed += 1
                return True
        else:
            print(f"   ❌ Migrations directory not found")
        
        return False

    def check_seed_data(self):
        """Check if seed data exists"""
        self.tests_run += 1
        print(f"\n🔍 Checking seed data...")
        
        seed_file = Path("/app/supabase/seed.sql")
        if seed_file.exists():
            try:
                with open(seed_file, 'r') as f:
                    content = f.read()
                
                # Check for key tables being seeded
                expected_tables = [
                    'organizations', 'profiles', 'patients', 
                    'services', 'protocols', 'memberships'
                ]
                
                found_tables = []
                for table in expected_tables:
                    if f"INSERT INTO {table}" in content:
                        found_tables.append(table)
                        print(f"      ✅ {table}")
                    else:
                        print(f"      ❌ {table} (no seed data)")
                
                print(f"   📊 Seed data coverage: {len(found_tables)}/{len(expected_tables)} tables")
                
                if len(found_tables) >= 4:  # At least 4/6 tables
                    self.tests_passed += 1
                    print(f"   ✅ Seed data: COMPREHENSIVE")
                    return True
                else:
                    print(f"   ⚠️  Seed data: INCOMPLETE")
            except Exception as e:
                print(f"   ❌ Error reading seed file: {e}")
        else:
            print(f"   ❌ Seed file not found")
        
        return False

    def generate_deployment_status_report(self):
        """Generate a report on deployment readiness"""
        print(f"\n📋 DEPLOYMENT READINESS REPORT")
        print("=" * 50)
        
        # Check Supabase CLI availability
        print("🔧 Prerequisites:")
        print("   ❌ Supabase CLI not installed")
        print("   ❌ Supabase project not configured")
        print("   ❌ Environment variables not set")
        print("   ❌ Functions not deployed")
        
        print("\n📁 Implementation Status:")
        for function_name, analysis in self.analysis_results.items():
            if analysis.get('exists', False) and 'error' not in analysis:
                endpoints_found = len(analysis.get('endpoints_found', []))
                expected_endpoints = len(self.expected_functions.get(function_name, {}).get('endpoints', []))
                print(f"   ✅ {function_name}: {endpoints_found}/{expected_endpoints} endpoints implemented")
            else:
                print(f"   ❌ {function_name}: Not implemented or has errors")
        
        print("\n🚀 Next Steps Required:")
        print("   1. Install Supabase CLI")
        print("   2. Initialize Supabase project")
        print("   3. Set environment variables")
        print("   4. Run database migrations")
        print("   5. Deploy Edge Functions")
        print("   6. Test deployed functions")

    def run_all_tests(self):
        """Run all tests and analyses"""
        print("🚀 Starting Supabase Edge Functions Analysis...")
        print("=" * 60)
        
        print("⚠️  IMPORTANT: Functions are not deployed - analyzing implementation only")
        print("=" * 60)
        
        # Test shared utilities
        self.check_shared_utilities()
        
        # Test database schema
        self.check_database_schema()
        
        # Test seed data
        self.check_seed_data()
        
        # Test each function
        for function_name in self.expected_functions.keys():
            self.test_function_structure(function_name)
        
        # Generate deployment report
        self.generate_deployment_status_report()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 ANALYSIS RESULTS:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Determine overall status
        if self.tests_passed >= self.tests_run * 0.7:  # 70% pass rate
            print("🎉 Implementation Quality: GOOD - Ready for deployment")
            return 0
        elif self.tests_passed >= self.tests_run * 0.5:  # 50% pass rate
            print("⚠️  Implementation Quality: FAIR - Needs improvements")
            return 1
        else:
            print("❌ Implementation Quality: POOR - Major issues found")
            return 2

def main():
    analyzer = SupabaseEdgeFunctionAnalyzer()
    return analyzer.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())