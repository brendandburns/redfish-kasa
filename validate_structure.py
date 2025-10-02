#!/usr/bin/env python3
"""
Validates the structure of redfish_server.py without requiring dependencies.
"""

import ast
import sys
import re


def validate_redfish_server():
    """Validate the Redfish server implementation."""
    
    print("=" * 60)
    print("Redfish Server Structure Validation")
    print("=" * 60)
    
    # Read the source code
    with open('redfish_server.py', 'r') as f:
        source = f.read()
    
    # Parse the AST
    tree = ast.parse(source, filename='redfish_server.py')
    
    # Check for required imports
    print("\n1. Checking imports...")
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend([alias.name for alias in node.names])
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)
    
    required_imports = ['flask', 'kasa', 'asyncio', 'logging']
    for req in required_imports:
        if any(req in imp for imp in imports):
            print(f"  ✓ {req} imported")
        else:
            print(f"  ✗ {req} not imported")
            return False
    
    # Check for route definitions
    print("\n2. Checking Redfish endpoints...")
    routes = re.findall(r"@app\.route\('([^']+)'", source)
    
    expected_routes = [
        '/redfish/v1/',
        '/redfish/v1/Chassis',
        '/redfish/v1/Chassis/PowerStrip',
        '/redfish/v1/Chassis/PowerStrip/Outlets',
        '/redfish/v1/Systems',
        '/redfish/v1/Managers/BMC'
    ]
    
    for route in expected_routes:
        if route in routes:
            print(f"  ✓ {route}")
        else:
            print(f"  ✗ {route} missing")
            return False
    
    # Check for outlet endpoints (with parameters)
    outlet_routes = [r for r in routes if 'Outlets/<int:outlet_id>' in r]
    if len(outlet_routes) >= 2:  # GET and POST
        print(f"  ✓ Outlet-specific endpoints (found {len(outlet_routes)})")
    else:
        print(f"  ✗ Outlet-specific endpoints missing")
        return False
    
    # Check for key functions
    print("\n3. Checking key functions...")
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    async_functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)]
    all_functions = functions + async_functions
    
    required_functions = [
        'discover_device',
        'init_device',
        'get_device_info',
        'service_root',
        'chassis_collection',
        'chassis_power_strip',
        'outlets_collection',
        'get_outlet',
        'outlet_power_control',
        'main'
    ]
    
    for func in required_functions:
        if func in all_functions:
            print(f"  ✓ {func}()")
        else:
            print(f"  ✗ {func}() missing")
            return False
    
    # Check for async operations
    print("\n4. Checking async operations...")
    async_functions = [node.name for node in ast.walk(tree) 
                      if isinstance(node, ast.AsyncFunctionDef)]
    
    if 'discover_device' in async_functions:
        print("  ✓ Async device discovery")
    else:
        print("  ✗ Async device discovery missing")
        return False
    
    if 'get_device_info' in async_functions:
        print("  ✓ Async device info retrieval")
    else:
        print("  ✗ Async device info retrieval missing")
        return False
    
    # Check for command-line argument parsing
    print("\n5. Checking CLI arguments...")
    if 'argparse' in source:
        print("  ✓ Argparse for CLI arguments")
    else:
        print("  ✗ Argparse missing")
        return False
    
    if '--device-ip' in source:
        print("  ✓ --device-ip argument")
    else:
        print("  ✗ --device-ip argument missing")
        return False
    
    if '--port' in source:
        print("  ✓ --port argument")
    else:
        print("  ✗ --port argument missing")
        return False
    
    # Check for Redfish compliance
    print("\n6. Checking Redfish compliance...")
    
    if '@odata.context' in source:
        print("  ✓ @odata.context fields")
    else:
        print("  ✗ @odata.context fields missing")
        return False
    
    if '@odata.type' in source:
        print("  ✓ @odata.type fields")
    else:
        print("  ✗ @odata.type fields missing")
        return False
    
    if 'ServiceRoot' in source:
        print("  ✓ ServiceRoot schema")
    else:
        print("  ✗ ServiceRoot schema missing")
        return False
    
    if 'Chassis' in source and 'PowerStrip' in source:
        print("  ✓ Chassis and PowerStrip schemas")
    else:
        print("  ✗ Chassis/PowerStrip schemas missing")
        return False
    
    # Check for error handling
    print("\n7. Checking error handling...")
    
    if 'try:' in source and 'except' in source:
        print("  ✓ Exception handling")
    else:
        print("  ✗ Exception handling missing")
        return False
    
    if 'logger' in source:
        print("  ✓ Logging")
    else:
        print("  ✗ Logging missing")
        return False
    
    # Check for power control
    print("\n8. Checking power control functionality...")
    
    if 'turn_on' in source:
        print("  ✓ Turn on functionality")
    else:
        print("  ✗ Turn on functionality missing")
        return False
    
    if 'turn_off' in source:
        print("  ✓ Turn off functionality")
    else:
        print("  ✗ Turn off functionality missing")
        return False
    
    if 'PowerState' in source:
        print("  ✓ PowerState field")
    else:
        print("  ✗ PowerState field missing")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All validation checks passed!")
    print("=" * 60)
    print(f"\nTotal routes: {len(routes)}")
    print(f"Total functions: {len(functions)}")
    print(f"Total async functions: {len(async_functions)}")
    
    return True


def main():
    """Main entry point."""
    try:
        if validate_redfish_server():
            print("\n✓ Structure validation successful!")
            print("\nThe Redfish server is properly structured and ready to use.")
            print("To test with an actual device, install dependencies:")
            print("  pip install -r requirements.txt")
            print("\nThen run:")
            print("  python redfish_server.py --device-ip <your-hs300-ip>")
            return 0
        else:
            print("\n✗ Validation failed!")
            return 1
    except Exception as e:
        print(f"\n✗ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
