#!/usr/bin/env python3
"""
Example client for interacting with the Redfish BMC API.

This script demonstrates how to use the Redfish API to control
outlets on the TP-Link HS300 power strip.
"""

import requests
import json
import sys


class RedfishClient:
    """Simple Redfish API client."""
    
    def __init__(self, base_url="http://localhost:5000"):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the Redfish API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_service_root(self):
        """Get the service root."""
        response = self.session.get(f"{self.base_url}/redfish/v1/")
        response.raise_for_status()
        return response.json()
    
    def get_chassis_collection(self):
        """Get the chassis collection."""
        response = self.session.get(f"{self.base_url}/redfish/v1/Chassis")
        response.raise_for_status()
        return response.json()
    
    def get_power_strip(self):
        """Get power strip information."""
        response = self.session.get(f"{self.base_url}/redfish/v1/Chassis/PowerStrip")
        response.raise_for_status()
        return response.json()
    
    def get_outlets(self):
        """Get all outlets."""
        response = self.session.get(f"{self.base_url}/redfish/v1/Chassis/PowerStrip/Outlets")
        response.raise_for_status()
        return response.json()
    
    def get_outlet(self, outlet_id):
        """
        Get information about a specific outlet.
        
        Args:
            outlet_id: ID of the outlet (0-5 for HS300)
        """
        response = self.session.get(
            f"{self.base_url}/redfish/v1/Chassis/PowerStrip/Outlets/{outlet_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def set_outlet_power(self, outlet_id, power_state):
        """
        Set the power state of an outlet.
        
        Args:
            outlet_id: ID of the outlet (0-5 for HS300)
            power_state: "On" or "Off"
        """
        response = self.session.post(
            f"{self.base_url}/redfish/v1/Chassis/PowerStrip/Outlets/{outlet_id}/Actions/Outlet.PowerControl",
            json={"PowerState": power_state}
        )
        response.raise_for_status()
        return response.json()
    
    def turn_on(self, outlet_id):
        """Turn on an outlet."""
        return self.set_outlet_power(outlet_id, "On")
    
    def turn_off(self, outlet_id):
        """Turn off an outlet."""
        return self.set_outlet_power(outlet_id, "Off")


def print_json(data):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2))


def main():
    """Main example function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Example Redfish API client'
    )
    parser.add_argument(
        '--server',
        default='http://localhost:5000',
        help='Redfish API server URL (default: http://localhost:5000)'
    )
    parser.add_argument(
        '--outlet',
        type=int,
        help='Outlet ID to control (0-5)'
    )
    parser.add_argument(
        '--action',
        choices=['on', 'off', 'status', 'list'],
        default='list',
        help='Action to perform (default: list)'
    )
    
    args = parser.parse_args()
    
    # Create client
    client = RedfishClient(args.server)
    
    try:
        if args.action == 'list':
            print("=== Power Strip Information ===")
            strip = client.get_power_strip()
            print(f"Name: {strip.get('Name')}")
            print(f"Model: {strip.get('Model')}")
            print(f"Status: {strip.get('Status', {}).get('State')}")
            print()
            
            print("=== Outlets ===")
            outlets = client.get_outlets()
            for member in outlets.get('Members', []):
                outlet_id = member['@odata.id'].split('/')[-1]
                outlet = client.get_outlet(outlet_id)
                print(f"Outlet {outlet_id}: {outlet.get('Name')} - {outlet.get('PowerState')}")
        
        elif args.action == 'status':
            if args.outlet is None:
                print("Error: --outlet required for status action")
                return 1
            
            outlet = client.get_outlet(args.outlet)
            print(f"=== Outlet {args.outlet} Status ===")
            print_json(outlet)
        
        elif args.action == 'on':
            if args.outlet is None:
                print("Error: --outlet required for on action")
                return 1
            
            result = client.turn_on(args.outlet)
            print(f"Turned on outlet {args.outlet}")
            print_json(result)
        
        elif args.action == 'off':
            if args.outlet is None:
                print("Error: --outlet required for off action")
                return 1
            
            result = client.turn_off(args.outlet)
            print(f"Turned off outlet {args.outlet}")
            print_json(result)
        
        return 0
        
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {args.server}")
        print("Make sure the Redfish server is running.")
        return 1
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP {e.response.status_code}")
        print(e.response.text)
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
