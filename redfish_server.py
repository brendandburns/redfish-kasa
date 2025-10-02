#!/usr/bin/env python3
"""
Redfish BMC API implementation for TP-Link HS300 smart power strip.

This module provides a Redfish-compliant REST API that allows management
of a TP-Link HS300 smart power strip through standard Redfish endpoints.
"""

import asyncio
import json
from typing import Optional
from flask import Flask, jsonify, request, Response
from kasa import SmartStrip, Discover
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global device instance
device: Optional[SmartStrip] = None
device_ip: Optional[str] = None


async def discover_device(target_ip: Optional[str] = None) -> Optional[SmartStrip]:
    """
    Discover and connect to HS300 power strip.
    
    Args:
        target_ip: Optional specific IP address to connect to
        
    Returns:
        SmartStrip instance if found, None otherwise
    """
    try:
        if target_ip:
            logger.info(f"Connecting to device at {target_ip}")
            dev = SmartStrip(target_ip)
            await dev.update()
            return dev
        else:
            logger.info("Discovering devices on network...")
            devices = await Discover.discover()
            for ip, dev in devices.items():
                if isinstance(dev, SmartStrip):
                    logger.info(f"Found SmartStrip at {ip}")
                    await dev.update()
                    return dev
        logger.warning("No SmartStrip found")
        return None
    except Exception as e:
        logger.error(f"Error discovering device: {e}")
        return None


def init_device(ip: Optional[str] = None):
    """Initialize connection to the power strip."""
    global device, device_ip
    device_ip = ip
    device = asyncio.run(discover_device(ip))
    if device:
        logger.info(f"Successfully connected to {device.alias}")
    else:
        logger.error("Failed to connect to device")


async def get_device_info():
    """Get current device information."""
    if device:
        await device.update()
        return device
    return None


@app.route('/redfish/v1/', methods=['GET'])
def service_root():
    """Redfish service root endpoint."""
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#ServiceRoot.ServiceRoot",
        "@odata.id": "/redfish/v1/",
        "@odata.type": "#ServiceRoot.v1_5_0.ServiceRoot",
        "Id": "RootService",
        "Name": "Root Service",
        "RedfishVersion": "1.6.0",
        "UUID": "92384634-2938-2342-8820-489239905423",
        "Chassis": {
            "@odata.id": "/redfish/v1/Chassis"
        },
        "Systems": {
            "@odata.id": "/redfish/v1/Systems"
        }
    })


@app.route('/redfish/v1/Chassis', methods=['GET'])
def chassis_collection():
    """Get the chassis collection."""
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#ChassisCollection.ChassisCollection",
        "@odata.id": "/redfish/v1/Chassis",
        "@odata.type": "#ChassisCollection.ChassisCollection",
        "Name": "Chassis Collection",
        "Members@odata.count": 1,
        "Members": [
            {"@odata.id": "/redfish/v1/Chassis/PowerStrip"}
        ]
    })


@app.route('/redfish/v1/Chassis/PowerStrip', methods=['GET'])
def chassis_power_strip():
    """Get the power strip chassis information."""
    dev = asyncio.run(get_device_info())
    
    if not dev:
        return jsonify({"error": "Device not connected"}), 503
    
    # Get outlet information
    outlets = []
    for i, plug in enumerate(dev.children):
        outlets.append({
            "@odata.id": f"/redfish/v1/Chassis/PowerStrip/Outlets/{i}"
        })
    
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#Chassis.Chassis",
        "@odata.id": "/redfish/v1/Chassis/PowerStrip",
        "@odata.type": "#Chassis.v1_10_0.Chassis",
        "Id": "PowerStrip",
        "Name": dev.alias,
        "ChassisType": "PowerStrip",
        "Manufacturer": "TP-Link",
        "Model": dev.model,
        "SerialNumber": dev.device_id if hasattr(dev, 'device_id') else "Unknown",
        "Status": {
            "State": "Enabled",
            "Health": "OK"
        },
        "PowerState": "On",
        "Links": {
            "ManagedBy": [
                {"@odata.id": "/redfish/v1/Managers/BMC"}
            ]
        },
        "Outlets": {
            "@odata.id": "/redfish/v1/Chassis/PowerStrip/Outlets"
        }
    })


@app.route('/redfish/v1/Chassis/PowerStrip/Outlets', methods=['GET'])
def outlets_collection():
    """Get the collection of all outlets."""
    dev = asyncio.run(get_device_info())
    
    if not dev:
        return jsonify({"error": "Device not connected"}), 503
    
    members = []
    for i in range(len(dev.children)):
        members.append({
            "@odata.id": f"/redfish/v1/Chassis/PowerStrip/Outlets/{i}"
        })
    
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#OutletCollection.OutletCollection",
        "@odata.id": "/redfish/v1/Chassis/PowerStrip/Outlets",
        "@odata.type": "#OutletCollection.OutletCollection",
        "Name": "Outlet Collection",
        "Members@odata.count": len(members),
        "Members": members
    })


@app.route('/redfish/v1/Chassis/PowerStrip/Outlets/<int:outlet_id>', methods=['GET'])
def get_outlet(outlet_id: int):
    """Get information about a specific outlet."""
    dev = asyncio.run(get_device_info())
    
    if not dev:
        return jsonify({"error": "Device not connected"}), 503
    
    if outlet_id >= len(dev.children):
        return jsonify({"error": "Outlet not found"}), 404
    
    plug = dev.children[outlet_id]
    
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#Outlet.Outlet",
        "@odata.id": f"/redfish/v1/Chassis/PowerStrip/Outlets/{outlet_id}",
        "@odata.type": "#Outlet.v1_1_0.Outlet",
        "Id": str(outlet_id),
        "Name": plug.alias,
        "Status": {
            "State": "Enabled",
            "Health": "OK"
        },
        "PowerState": "On" if plug.is_on else "Off",
        "PowerEnabled": plug.is_on,
        "PowerCycleDelaySeconds": 0,
        "Voltage": {
            "Reading": 120,
            "DataSourceUri": f"/redfish/v1/Chassis/PowerStrip/Outlets/{outlet_id}/Metrics"
        },
        "Actions": {
            "#Outlet.PowerControl": {
                "target": f"/redfish/v1/Chassis/PowerStrip/Outlets/{outlet_id}/Actions/Outlet.PowerControl"
            },
            "#Outlet.ResetMetrics": {
                "target": f"/redfish/v1/Chassis/PowerStrip/Outlets/{outlet_id}/Actions/Outlet.ResetMetrics"
            }
        }
    })


@app.route('/redfish/v1/Chassis/PowerStrip/Outlets/<int:outlet_id>/Actions/Outlet.PowerControl', methods=['POST'])
def outlet_power_control(outlet_id: int):
    """Control power state of an outlet."""
    dev = asyncio.run(get_device_info())
    
    if not dev:
        return jsonify({"error": "Device not connected"}), 503
    
    if outlet_id >= len(dev.children):
        return jsonify({"error": "Outlet not found"}), 404
    
    data = request.get_json()
    if not data or 'PowerState' not in data:
        return jsonify({"error": "PowerState required"}), 400
    
    power_state = data['PowerState']
    plug = dev.children[outlet_id]
    
    try:
        if power_state == "On":
            asyncio.run(plug.turn_on())
            logger.info(f"Turned on outlet {outlet_id}")
        elif power_state == "Off":
            asyncio.run(plug.turn_off())
            logger.info(f"Turned off outlet {outlet_id}")
        else:
            return jsonify({"error": f"Invalid PowerState: {power_state}"}), 400
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error controlling outlet {outlet_id}: {e}")
        return jsonify({"error": "Failed to control outlet power state"}), 500


@app.route('/redfish/v1/Systems', methods=['GET'])
def systems_collection():
    """Get the systems collection."""
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#ComputerSystemCollection.ComputerSystemCollection",
        "@odata.id": "/redfish/v1/Systems",
        "@odata.type": "#ComputerSystemCollection.ComputerSystemCollection",
        "Name": "Computer System Collection",
        "Members@odata.count": 0,
        "Members": []
    })


@app.route('/redfish/v1/Managers/BMC', methods=['GET'])
def manager():
    """Get manager information."""
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#Manager.Manager",
        "@odata.id": "/redfish/v1/Managers/BMC",
        "@odata.type": "#Manager.v1_5_0.Manager",
        "Id": "BMC",
        "Name": "Redfish Kasa Manager",
        "ManagerType": "BMC",
        "Status": {
            "State": "Enabled",
            "Health": "OK"
        },
        "Links": {
            "ManagerForChassis": [
                {"@odata.id": "/redfish/v1/Chassis/PowerStrip"}
            ]
        }
    })


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Redfish BMC API server for TP-Link HS300 power strip'
    )
    parser.add_argument(
        '--device-ip',
        help='IP address of the HS300 power strip (will auto-discover if not specified)',
        default=None
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to listen on (default: 5000)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    args = parser.parse_args()
    
    # Initialize device connection
    logger.info("Initializing device connection...")
    init_device(args.device_ip)
    
    if not device:
        logger.error("Could not connect to device. Please check the device IP and network connectivity.")
        return 1
    
    # Start Flask server
    logger.info(f"Starting Redfish API server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
    
    return 0


if __name__ == '__main__':
    exit(main())
