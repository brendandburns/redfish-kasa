# Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ cURL/REST    │  │ example_     │  │ Custom Applications  │  │
│  │ Client       │  │ client.py    │  │ (using requests)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST
                              │
┌─────────────────────────────▼─────────────────────────────────────┐
│                    Redfish API Server                             │
│                    (redfish_server.py)                            │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Flask Web Server (Port 5000)                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  Redfish Endpoints                          │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │ • GET  /redfish/v1/                   (Service Root)        │ │
│  │ • GET  /redfish/v1/Chassis            (Collection)          │ │
│  │ • GET  /redfish/v1/Chassis/PowerStrip (Power Strip Info)   │ │
│  │ • GET  /redfish/v1/.../Outlets        (Outlets Collection)  │ │
│  │ • GET  /redfish/v1/.../Outlets/{id}   (Outlet Info)        │ │
│  │ • POST /redfish/v1/.../PowerControl   (Power On/Off)       │ │
│  │ • GET  /redfish/v1/Systems            (Systems Collection)  │ │
│  │ • GET  /redfish/v1/Managers/BMC       (Manager Info)       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Device Communication Layer                      │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │ • discover_device() - Auto-discover or connect to IP       │ │
│  │ • init_device()     - Initialize connection                │ │
│  │ • get_device_info() - Query device status (async)          │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
                              │
                              │ python-kasa (async)
                              │
┌─────────────────────────────▼─────────────────────────────────────┐
│                      Network Layer                                │
│                      (Local Network)                              │
└───────────────────────────────────────────────────────────────────┘
                              │
                              │
┌─────────────────────────────▼─────────────────────────────────────┐
│                  TP-Link HS300 Power Strip                        │
├───────────────────────────────────────────────────────────────────┤
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │
│  │Out 0 │ │Out 1 │ │Out 2 │ │Out 3 │ │Out 4 │ │Out 5 │          │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘          │
└───────────────────────────────────────────────────────────────────┘
```

## Request Flow

### Example: Turn On Outlet 0

```
1. Client Request:
   POST /redfish/v1/Chassis/PowerStrip/Outlets/0/Actions/Outlet.PowerControl
   Body: {"PowerState": "On"}
   
   ↓

2. Flask Router:
   Matches route to outlet_power_control(outlet_id=0)
   
   ↓

3. Request Validation:
   - Check outlet_id is valid (0-5)
   - Check PowerState is "On" or "Off"
   - Validate device is connected
   
   ↓

4. Device Communication (async):
   - Get device reference (SmartStrip)
   - Get outlet/plug reference (children[0])
   - Call plug.turn_on() via python-kasa
   
   ↓

5. TP-Link Protocol:
   - python-kasa sends encrypted command to HS300
   - HS300 processes command and responds
   
   ↓

6. Response:
   - Return {"status": "success"} with HTTP 200
   - Or error message with appropriate status code
```

## Component Responsibilities

### redfish_server.py
- **Role**: Main API server and orchestrator
- **Responsibilities**:
  - HTTP request handling
  - Redfish protocol compliance
  - Device management
  - Error handling and logging
- **Technology**: Flask + python-kasa

### example_client.py
- **Role**: Reference client implementation
- **Responsibilities**:
  - Demonstrate API usage
  - Provide CLI for manual testing
  - Show best practices
- **Technology**: Python + requests

### validate_structure.py
- **Role**: Code quality assurance
- **Responsibilities**:
  - Validate implementation completeness
  - Check Redfish compliance
  - Verify required components
- **Technology**: Python AST

### test_api.py
- **Role**: API testing
- **Responsibilities**:
  - Test endpoint functionality
  - Validate JSON responses
  - Verify error handling
- **Technology**: Flask test client

## Data Flow

### State Management
```
Device State (HS300)
       ↓
  python-kasa
       ↓
Async Update (get_device_info)
       ↓
Flask Endpoint Handler
       ↓
JSON Response (Redfish format)
       ↓
Client
```

### Command Flow
```
Client Command
       ↓
HTTP POST Request
       ↓
Flask Endpoint Handler
       ↓
Input Validation
       ↓
python-kasa API Call
       ↓
Network Command to HS300
       ↓
Device Action
       ↓
Success Response
       ↓
Client
```

## Scalability Considerations

### Current Implementation
- Single device support
- Synchronous request handling (Flask default)
- In-memory device reference

### Future Enhancements
- Multiple device support (device registry)
- Async request handling (async Flask or FastAPI)
- Device state caching
- Persistent configuration
- Authentication/authorization
- Rate limiting
- Metrics and monitoring

## Security Architecture

### Current Security Measures
1. **Input Validation**: All inputs validated before processing
2. **Error Handling**: No stack trace exposure to clients
3. **Dependency Security**: Patched Flask version (>=2.3.2)
4. **Logging**: Detailed server-side logging for auditing

### Recommended Additions
1. **HTTPS/TLS**: Encrypt API traffic
2. **Authentication**: API keys or OAuth
3. **Authorization**: Role-based access control
4. **Rate Limiting**: Prevent abuse
5. **Network Isolation**: Separate management network
