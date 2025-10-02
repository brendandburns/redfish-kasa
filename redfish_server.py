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


@app.route('/redfish', methods=['GET'])
def redfish_version():
    """Redfish version endpoint."""
    return jsonify({
        "v1": "/redfish/v1/"
    })


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
        },
        "Managers": {
            "@odata.id": "/redfish/v1/Managers"
        },
        "Links": {
            "Sessions": {
                "@odata.id": "/redfish/v1/SessionService/Sessions"
            }
        }
    })


@app.route('/redfish/v1/$metadata', methods=['GET'])
def metadata():
    """Redfish metadata endpoint."""
    # Return minimal metadata document
    metadata_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
    <edmx:Reference Uri="http://redfish.dmtf.org/schemas/v1/ServiceRoot_v1.xml">
        <edmx:Include Namespace="ServiceRoot"/>
        <edmx:Include Namespace="ServiceRoot.v1_5_0"/>
    </edmx:Reference>
    <edmx:Reference Uri="http://redfish.dmtf.org/schemas/v1/Chassis_v1.xml">
        <edmx:Include Namespace="Chassis"/>
        <edmx:Include Namespace="Chassis.v1_10_0"/>
    </edmx:Reference>
    <edmx:DataServices>
        <Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="Service">
            <EntityContainer Name="Service" Extends="ServiceRoot.v1_5_0.ServiceContainer"/>
        </Schema>
    </edmx:DataServices>
</edmx:Edmx>'''
    return Response(metadata_xml, mimetype='application/xml')


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
    
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#Chassis.Chassis",
        "@odata.id": "/redfish/v1/Chassis/PowerStrip",
        "@odata.type": "#Chassis.v1_10_0.Chassis",
        "Id": "PowerStrip",
        "Name": dev.alias,
        "ChassisType": "RackMount",
        "Manufacturer": "TP-Link",
        "Model": dev.model,
        "SerialNumber": dev.device_id if hasattr(dev, 'device_id') else "Unknown",
        "PartNumber": "HS300",
        "Status": {
            "State": "Enabled",
            "Health": "OK"
        },
        "PowerState": "On",
        "Power": {
            "@odata.id": "/redfish/v1/Chassis/PowerStrip/Power"
        },
        "PowerSubsystem": {
            "@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem"
        },
        "Links": {
            "ManagedBy": [
                {"@odata.id": "/redfish/v1/Managers/BMC"}
            ]
        }
    })


@app.route('/redfish/v1/Chassis/PowerStrip/Power', methods=['GET'])
def chassis_power():
    """Get the power resource for the chassis."""
    dev = asyncio.run(get_device_info())
    
    if not dev:
        return jsonify({"error": "Device not connected"}), 503
    
    # Build PowerControl array for each outlet
    power_control = []
    for i, plug in enumerate(dev.children):
        power_control.append({
            "@odata.id": f"/redfish/v1/Chassis/PowerStrip/Power#/PowerControl/{i}",
            "MemberId": str(i),
            "Name": plug.alias,
            "PowerConsumedWatts": 0,  # HS300 doesn't provide real-time wattage easily
            "PowerCapacityWatts": 1800,  # 15A * 120V typical
            "Status": {
                "State": "Enabled" if plug.is_on else "Disabled",
                "Health": "OK"
            }
        })
    
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#Power.Power",
        "@odata.id": "/redfish/v1/Chassis/PowerStrip/Power",
        "@odata.type": "#Power.v1_7_0.Power",
        "Id": "Power",
        "Name": "Power",
        "PowerControl": power_control,
        "PowerControl@odata.count": len(power_control)
    })


@app.route('/redfish/v1/Chassis/PowerStrip/PowerSubsystem', methods=['GET'])
def power_subsystem():
    """Get the power subsystem for the chassis."""
    dev = asyncio.run(get_device_info())
    
    if not dev:
        return jsonify({"error": "Device not connected"}), 503
    
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#PowerSubsystem.PowerSubsystem",
        "@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem",
        "@odata.type": "#PowerSubsystem.v1_1_0.PowerSubsystem",
        "Id": "PowerSubsystem",
        "Name": "Power Subsystem",
        "Status": {
            "State": "Enabled",
            "Health": "OK"
        },
        "PowerSupplies": {
            "@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem/PowerSupplies"
        },
        "OutletGroups": {
            "@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem/OutletGroups"
        }
    })


@app.route('/redfish/v1/Chassis/PowerStrip/PowerSubsystem/PowerSupplies', methods=['GET'])
def power_supplies_collection():
    """Get the power supplies collection."""
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#PowerSupplyCollection.PowerSupplyCollection",
        "@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem/PowerSupplies",
        "@odata.type": "#PowerSupplyCollection.PowerSupplyCollection",
        "Name": "Power Supply Collection",
        "Members@odata.count": 1,
        "Members": [
            {"@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem/PowerSupplies/0"}
        ]
    })


@app.route('/redfish/v1/Chassis/PowerStrip/PowerSubsystem/PowerSupplies/0', methods=['GET'])
def power_supply():
    """Get the main power supply (AC input)."""
    dev = asyncio.run(get_device_info())
    
    if not dev:
        return jsonify({"error": "Device not connected"}), 503
    
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#PowerSupply.PowerSupply",
        "@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem/PowerSupplies/0",
        "@odata.type": "#PowerSupply.v1_5_0.PowerSupply",
        "Id": "0",
        "Name": "AC Input",
        "Status": {
            "State": "Enabled",
            "Health": "OK"
        },
        "PowerSupplyType": "AC",
        "LineInputVoltage": 120,
        "Model": dev.model,
        "Manufacturer": "TP-Link"
    })


@app.route('/redfish/v1/Chassis/PowerStrip/PowerSubsystem/OutletGroups', methods=['GET'])
def outlet_groups_collection():
    """Get the outlet groups collection."""
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#OutletGroupCollection.OutletGroupCollection",
        "@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem/OutletGroups",
        "@odata.type": "#OutletGroupCollection.OutletGroupCollection",
        "Name": "Outlet Group Collection",
        "Members@odata.count": 1,
        "Members": [
            {"@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem/OutletGroups/All"}
        ]
    })


@app.route('/redfish/v1/Chassis/PowerStrip/PowerSubsystem/OutletGroups/All', methods=['GET'])
def outlet_group():
    """Get the outlet group containing all outlets."""
    dev = asyncio.run(get_device_info())
    
    if not dev:
        return jsonify({"error": "Device not connected"}), 503
    
    outlets = []
    for i in range(len(dev.children)):
        outlets.append({
            "@odata.id": f"/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/{i}"
        })
    
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#OutletGroup.OutletGroup",
        "@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem/OutletGroups/All",
        "@odata.type": "#OutletGroup.v1_1_0.OutletGroup",
        "Id": "All",
        "Name": "All Outlets",
        "Status": {
            "State": "Enabled",
            "Health": "OK"
        },
        "CreatedBy": "System",
        "PowerEnabled": True,
        "PowerState": "On",
        "Links": {
            "Outlets": outlets,
            "Outlets@odata.count": len(outlets)
        }
    })


@app.route('/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets', methods=['GET'])
def outlets_collection():
    """Get the collection of all outlets."""
    dev = asyncio.run(get_device_info())
    
    if not dev:
        return jsonify({"error": "Device not connected"}), 503
    
    members = []
    for i in range(len(dev.children)):
        members.append({
            "@odata.id": f"/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/{i}"
        })
    
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#OutletCollection.OutletCollection",
        "@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets",
        "@odata.type": "#OutletCollection.OutletCollection",
        "Name": "Outlet Collection",
        "Members@odata.count": len(members),
        "Members": members
    })


@app.route('/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/<int:outlet_id>', methods=['GET'])
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
        "@odata.id": f"/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/{outlet_id}",
        "@odata.type": "#Outlet.v1_4_0.Outlet",
        "Id": str(outlet_id),
        "Name": plug.alias,
        "Status": {
            "State": "Enabled",
            "Health": "OK"
        },
        "PhaseWiringType": "OnePhase3Wire",
        "VoltageType": "AC",
        "OutletType": "NEMA_5_15R",
        "RatedCurrentAmps": 15,
        "NominalVoltage": "AC120V",
        "PowerEnabled": plug.is_on,
        "PowerState": "On" if plug.is_on else "Off",
        "PowerCycleDelaySeconds": 0,
        "PowerOnDelaySeconds": 0,
        "PowerOffDelaySeconds": 0,
        "PowerRestoreDelaySeconds": 0,
        "PowerRestorePolicy": "LastState",
        "Voltage": {
            "Reading": 120,
            "DataSourceUri": f"/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/{outlet_id}/Sensors/Voltage"
        },
        "Actions": {
            "#Outlet.PowerControl": {
                "target": f"/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/{outlet_id}/Actions/Outlet.PowerControl",
                "PowerState@Redfish.AllowableValues": [
                    "On",
                    "Off"
                ]
            },
            "#Outlet.ResetMetrics": {
                "target": f"/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/{outlet_id}/Actions/Outlet.ResetMetrics"
            }
        },
        "Links": {
            "BranchCircuit": {
                "@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem/PowerSupplies/0"
            }
        }
    })


@app.route('/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/<int:outlet_id>/Actions/Outlet.PowerControl', methods=['POST'])
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


@app.route('/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/<int:outlet_id>/Actions/Outlet.ResetMetrics', methods=['POST'])
def outlet_reset_metrics(outlet_id: int):
    """Reset metrics for an outlet."""
    dev = asyncio.run(get_device_info())
    
    if not dev:
        return jsonify({"error": "Device not connected"}), 503
    
    if outlet_id >= len(dev.children):
        return jsonify({"error": "Outlet not found"}), 404
    
    # HS300 doesn't support resetting metrics, but return success for API compatibility
    logger.info(f"Reset metrics requested for outlet {outlet_id}")
    return jsonify({"status": "success"}), 200


@app.route('/redfish/v1/SessionService', methods=['GET'])
def session_service():
    """Get the session service."""
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#SessionService.SessionService",
        "@odata.id": "/redfish/v1/SessionService",
        "@odata.type": "#SessionService.v1_1_7.SessionService",
        "Id": "SessionService",
        "Name": "Session Service",
        "Description": "Session Service",
        "Status": {
            "State": "Enabled",
            "Health": "OK"
        },
        "ServiceEnabled": True,
        "SessionTimeout": 3600,
        "Sessions": {
            "@odata.id": "/redfish/v1/SessionService/Sessions"
        }
    })


@app.route('/redfish/v1/SessionService/Sessions', methods=['GET'])
def sessions_collection():
    """Get the sessions collection."""
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#SessionCollection.SessionCollection",
        "@odata.id": "/redfish/v1/SessionService/Sessions",
        "@odata.type": "#SessionCollection.SessionCollection",
        "Name": "Session Collection",
        "Description": "Session Collection",
        "Members@odata.count": 0,
        "Members": []
    })


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


@app.route('/redfish/v1/Managers', methods=['GET'])
def managers_collection():
    """Get the managers collection."""
    return jsonify({
        "@odata.context": "/redfish/v1/$metadata#ManagerCollection.ManagerCollection",
        "@odata.id": "/redfish/v1/Managers",
        "@odata.type": "#ManagerCollection.ManagerCollection",
        "Name": "Manager Collection",
        "Members@odata.count": 1,
        "Members": [
            {"@odata.id": "/redfish/v1/Managers/BMC"}
        ]
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
        "UUID": "92384634-2938-2342-8820-489239905424",
        "Model": "Redfish-Kasa BMC",
        "FirmwareVersion": "1.0.0",
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
