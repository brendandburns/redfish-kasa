#!/usr/bin/env python3
"""
Simple test script to verify Redfish API endpoints.

This script validates the structure and responses of the Redfish API
without requiring an actual HS300 device. It checks that all endpoints
are properly defined and return expected JSON structures.
"""

import json
import sys


def test_redfish_structure():
    """Test that the Redfish server has correct structure."""
    import redfish_server
    
    # Get Flask app
    app = redfish_server.app
    
    # Test that routes are defined
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    
    expected_routes = [
        '/redfish/v1/',
        '/redfish/v1/Chassis',
        '/redfish/v1/Chassis/PowerStrip',
        '/redfish/v1/Chassis/PowerStrip/Outlets',
        '/redfish/v1/Chassis/PowerStrip/Outlets/<int:outlet_id>',
        '/redfish/v1/Chassis/PowerStrip/Outlets/<int:outlet_id>/Actions/Outlet.PowerControl',
        '/redfish/v1/Systems',
        '/redfish/v1/Managers/BMC'
    ]
    
    print("Testing Redfish API structure...")
    print(f"Total routes defined: {len([r for r in routes if '/redfish' in r])}")
    
    for expected in expected_routes:
        if expected in routes:
            print(f"✓ Route found: {expected}")
        else:
            print(f"✗ Route missing: {expected}")
            return False
    
    print("\n✓ All expected routes are defined!")
    return True


def test_service_endpoints():
    """Test service endpoints that don't require device."""
    import redfish_server
    
    app = redfish_server.app
    client = app.test_client()
    
    print("\nTesting service endpoints...")
    
    # Test service root
    response = client.get('/redfish/v1/')
    if response.status_code == 200:
        data = json.loads(response.data)
        if '@odata.type' in data and 'ServiceRoot' in data['@odata.type']:
            print("✓ Service root endpoint works")
        else:
            print("✗ Service root missing required fields")
            return False
    else:
        print(f"✗ Service root returned {response.status_code}")
        return False
    
    # Test chassis collection
    response = client.get('/redfish/v1/Chassis')
    if response.status_code == 200:
        data = json.loads(response.data)
        if 'Members' in data:
            print("✓ Chassis collection endpoint works")
        else:
            print("✗ Chassis collection missing Members field")
            return False
    else:
        print(f"✗ Chassis collection returned {response.status_code}")
        return False
    
    # Test systems collection
    response = client.get('/redfish/v1/Systems')
    if response.status_code == 200:
        data = json.loads(response.data)
        if 'Members' in data:
            print("✓ Systems collection endpoint works")
        else:
            print("✗ Systems collection missing Members field")
            return False
    else:
        print(f"✗ Systems collection returned {response.status_code}")
        return False
    
    # Test manager endpoint
    response = client.get('/redfish/v1/Managers/BMC')
    if response.status_code == 200:
        data = json.loads(response.data)
        if 'ManagerType' in data:
            print("✓ Manager endpoint works")
        else:
            print("✗ Manager missing ManagerType field")
            return False
    else:
        print(f"✗ Manager returned {response.status_code}")
        return False
    
    print("\n✓ All service endpoints work correctly!")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Redfish API Test Suite")
    print("=" * 60)
    
    try:
        if not test_redfish_structure():
            print("\n✗ Structure test failed!")
            return 1
        
        if not test_service_endpoints():
            print("\n✗ Endpoint test failed!")
            return 1
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        print("\nNote: Device-specific endpoints (outlets, power control)")
        print("require an actual HS300 device to test.")
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
