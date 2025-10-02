# redfish-kasa

A Python implementation of the Redfish BMC API for managing TP-Link HS300 smart power strips. This project provides a RESTful Redfish-compliant interface to control individual outlets on the HS300 power strip.

## Features

- **Redfish API Compliance**: Implements standard Redfish endpoints for hardware management
- **Power Strip Management**: Control individual outlets on TP-Link HS300 power strips
- **Auto-Discovery**: Automatically discover HS300 devices on your network
- **RESTful Interface**: Standard HTTP REST API for easy integration

## Requirements

- Python 3.7 or higher
- TP-Link HS300 smart power strip on the same network
- Network connectivity between the server and the power strip

## Installation

1. Clone this repository:
```bash
git clone https://github.com/brendandburns/redfish-kasa.git
cd redfish-kasa
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Server

With auto-discovery (will find HS300 on your network):
```bash
python redfish_server.py
```

With a specific device IP:
```bash
python redfish_server.py --device-ip 192.168.1.100
```

With custom host and port:
```bash
python redfish_server.py --device-ip 192.168.1.100 --host 0.0.0.0 --port 8080
```

### Command-line Options

- `--device-ip IP`: IP address of the HS300 power strip (optional, will auto-discover if not specified)
- `--host HOST`: Host to bind to (default: 0.0.0.0)
- `--port PORT`: Port to listen on (default: 5000)

## API Endpoints

### Service Root
```
GET /redfish/v1/
```
Returns the Redfish service root with links to available resources.

### Chassis Collection
```
GET /redfish/v1/Chassis
```
Returns the collection of chassis (power strips).

### Power Strip Information
```
GET /redfish/v1/Chassis/PowerStrip
```
Returns detailed information about the power strip including model, status, and links to outlets.

### Outlets Collection
```
GET /redfish/v1/Chassis/PowerStrip/Outlets
```
Returns the collection of all available outlets.

### Individual Outlet
```
GET /redfish/v1/Chassis/PowerStrip/Outlets/{outlet_id}
```
Returns information about a specific outlet (outlet_id: 0-5 for HS300).

### Power Control
```
POST /redfish/v1/Chassis/PowerStrip/Outlets/{outlet_id}/Actions/Outlet.PowerControl
Content-Type: application/json

{
  "PowerState": "On"  // or "Off"
}
```
Controls the power state of a specific outlet.

## Examples

### Get Service Root
```bash
curl http://localhost:5000/redfish/v1/
```

### List All Outlets
```bash
curl http://localhost:5000/redfish/v1/Chassis/PowerStrip/Outlets
```

### Get Outlet Status
```bash
curl http://localhost:5000/redfish/v1/Chassis/PowerStrip/Outlets/0
```

### Turn On Outlet 0
```bash
curl -X POST http://localhost:5000/redfish/v1/Chassis/PowerStrip/Outlets/0/Actions/Outlet.PowerControl \
  -H "Content-Type: application/json" \
  -d '{"PowerState": "On"}'
```

### Turn Off Outlet 0
```bash
curl -X POST http://localhost:5000/redfish/v1/Chassis/PowerStrip/Outlets/0/Actions/Outlet.PowerControl \
  -H "Content-Type: application/json" \
  -d '{"PowerState": "Off"}'
```

## Architecture

The implementation uses:
- **Flask**: Lightweight web framework for the REST API
- **python-kasa**: Library for communicating with TP-Link Kasa smart devices
- **asyncio**: For asynchronous device communication

The server maps Redfish concepts to power strip functionality:
- **Chassis**: Represents the power strip itself
- **Outlets**: Individual controllable outlets on the power strip
- **Manager**: The software BMC managing the power strip

## Redfish Specification

This implementation follows the DMTF Redfish specification v1.6.0:
- Chassis schema for physical hardware representation
- Outlet schema for power distribution control
- Standard HTTP methods (GET, POST) for resource management

## Troubleshooting

### Device Not Found
- Ensure the HS300 is powered on and connected to the network
- Verify network connectivity between the server and the device
- Try specifying the device IP explicitly with `--device-ip`

### Connection Errors
- Check firewall settings
- Ensure the device isn't being controlled by another application
- Verify the device is a TP-Link HS300 model

### API Errors
- Check the server logs for detailed error messages
- Ensure proper JSON formatting in POST requests
- Verify outlet IDs are valid (0-5 for HS300)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.