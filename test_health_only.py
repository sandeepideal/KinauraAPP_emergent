#!/usr/bin/env python3

import sys
import os
sys.path.append('/app')

from backend_test import KinAuraAPITester

def main():
    print("🚀 Testing Health Data Integration System Only...")
    print("=" * 50)
    
    tester = KinAuraAPITester()
    
    # First do basic authentication setup
    try:
        # Setup admin authentication
        tester.test_admin_social_login()
        
        # Test health data integration system
        result = tester.test_health_data_integration_system()
        
        if result:
            print("\n✅ Health Data Integration System test PASSED!")
            return 0
        else:
            print("\n❌ Health Data Integration System test FAILED!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())