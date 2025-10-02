# Redfish API Compliance

This document details how the implementation aligns with the DMTF Redfish specification and standard patterns.

## Redfish Specification Version

This implementation follows **Redfish Specification v1.6.0** as defined by DMTF.

## Standard Endpoints

### Required Service Endpoints

| Endpoint | Status | Description |
|----------|--------|-------------|
| `/redfish` | ✅ Implemented | Version discovery endpoint |
| `/redfish/v1/` | ✅ Implemented | Service root |
| `/redfish/v1/$metadata` | ✅ Implemented | OData metadata document |

### Service Root Properties

The ServiceRoot includes all required properties:
- `@odata.context`, `@odata.id`, `@odata.type` - OData annotations
- `Id`, `Name` - Resource identification
- `RedfishVersion` - "1.6.0"
- `UUID` - Unique service identifier
- `Chassis`, `Systems`, `Managers` - Collection links
- `Links` with SessionService reference

### Resource Collections

| Collection | Endpoint | Members |
|------------|----------|---------|
| Chassis | `/redfish/v1/Chassis` | PowerStrip |
| Systems | `/redfish/v1/Systems` | None (PDU only) |
| Managers | `/redfish/v1/Managers` | BMC |
| Sessions | `/redfish/v1/SessionService/Sessions` | None (future auth) |

## Chassis Implementation

### Chassis Resource
**Endpoint**: `/redfish/v1/Chassis/PowerStrip`

**Schema**: `Chassis.v1_10_0.Chassis`

**Properties**:
- Standard identification (Id, Name, ChassisType)
- Manufacturer and model information
- Status with State and Health
- PowerState for overall power status
- Links to Manager (ManagedBy)
- **Power** resource link (legacy power metrics)
- **PowerSubsystem** link (modern power distribution)

This follows the Redfish pattern where:
- Chassis represents physical enclosures
- ChassisType "RackMount" is appropriate for PDUs
- Both Power and PowerSubsystem provide compatibility with different Redfish clients

## Power Distribution

### Power Resource (Legacy Pattern)
**Endpoint**: `/redfish/v1/Chassis/PowerStrip/Power`

**Schema**: `Power.v1_7_0.Power`

Provides `PowerControl` array with per-outlet metrics:
- Power consumption (watts)
- Power capacity
- Status per outlet

This follows the traditional Redfish pattern used by many vendors.

### PowerSubsystem (Modern Pattern)
**Endpoint**: `/redfish/v1/Chassis/PowerStrip/PowerSubsystem`

**Schema**: `PowerSubsystem.v1_1_0.PowerSubsystem`

Modern hierarchical structure:
```
PowerSubsystem
├── PowerSupplies (collection)
│   └── PowerSupply/0 (AC input)
└── OutletGroups (collection)
    └── OutletGroup/All
        └── Links to Outlets
```

This follows the newer Redfish PowerDistribution model from DSP2050.

## Outlets Implementation

### Outlet Collection
**Endpoint**: `/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets`

**Schema**: `OutletCollection.OutletCollection`

Standard collection with:
- `Members@odata.count` - Number of outlets
- `Members` array - Links to individual outlets

### Individual Outlet
**Endpoint**: `/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/{id}`

**Schema**: `Outlet.v1_4_0.Outlet`

Complete outlet properties per Redfish schema:

#### Identification
- `Id`, `Name` - Outlet identification
- `Status` - State and Health

#### Electrical Properties
- `PhaseWiringType` - "OnePhase3Wire"
- `VoltageType` - "AC"
- `OutletType` - "NEMA_5_15R" (standard US outlet)
- `RatedCurrentAmps` - 15A rating
- `NominalVoltage` - "AC120V"
- `Voltage.Reading` - Current voltage

#### Power Control
- `PowerEnabled` - Current on/off state
- `PowerState` - "On" or "Off"
- `PowerCycleDelaySeconds` - Delay for power cycling
- `PowerOnDelaySeconds` - Delay before turning on
- `PowerOffDelaySeconds` - Delay before turning off
- `PowerRestoreDelaySeconds` - Delay after power restore
- `PowerRestorePolicy` - "LastState"

#### Actions
```json
"Actions": {
  "#Outlet.PowerControl": {
    "target": "...Actions/Outlet.PowerControl",
    "PowerState@Redfish.AllowableValues": ["On", "Off"]
  },
  "#Outlet.ResetMetrics": {
    "target": "...Actions/Outlet.ResetMetrics"
  }
}
```

#### Links
- `BranchCircuit` - Link to PowerSupply (circuit source)

## Power Supply

**Endpoint**: `/redfish/v1/Chassis/PowerStrip/PowerSubsystem/PowerSupplies/0`

**Schema**: `PowerSupply.v1_5_0.PowerSupply`

Represents the AC input:
- `PowerSupplyType` - "AC"
- `LineInputVoltage` - 120V
- `Status` - State and Health
- Manufacturer and Model

## Outlet Groups

**Endpoint**: `/redfish/v1/Chassis/PowerStrip/PowerSubsystem/OutletGroups/All`

**Schema**: `OutletGroup.v1_1_0.OutletGroup`

Logical grouping of outlets:
- `CreatedBy` - "System"
- `PowerEnabled`, `PowerState` - Group control status
- `Links.Outlets` - Array of outlet references

## Manager Implementation

### Manager Collection
**Endpoint**: `/redfish/v1/Managers`

Standard collection listing the BMC.

### BMC Manager
**Endpoint**: `/redfish/v1/Managers/BMC`

**Schema**: `Manager.v1_5_0.Manager`

Properties:
- `Id`, `Name` - Manager identification
- `ManagerType` - "BMC"
- `UUID` - Unique identifier
- `Model`, `FirmwareVersion` - BMC information
- `Status` - State and Health
- `Links.ManagerForChassis` - Chassis under management

## Session Service

**Endpoint**: `/redfish/v1/SessionService`

**Schema**: `SessionService.v1_1_7.SessionService`

Provides authentication framework:
- `ServiceEnabled` - True
- `SessionTimeout` - 3600 seconds
- `Sessions` - Link to sessions collection

Currently no active sessions (authentication not enforced), but structure is in place for future implementation.

## Actions

All actions follow the Redfish action pattern:

```
POST /redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/{id}/Actions/Outlet.PowerControl
Content-Type: application/json

{
  "PowerState": "On"  // or "Off"
}
```

Response:
```json
{
  "status": "success"
}
```

Actions include:
- `#Outlet.PowerControl` - Control outlet power state
- `#Outlet.ResetMetrics` - Reset outlet metrics

## OData Annotations

All resources include proper OData v4 annotations:

- `@odata.context` - Metadata context path
- `@odata.id` - Unique resource identifier (URI)
- `@odata.type` - Schema type with version
- `@odata.count` - Count annotation for collections

Example:
```json
{
  "@odata.context": "/redfish/v1/$metadata#Outlet.Outlet",
  "@odata.id": "/redfish/v1/Chassis/PowerStrip/PowerSubsystem/Outlets/0",
  "@odata.type": "#Outlet.v1_4_0.Outlet"
}
```

## Status Objects

All resources with operational status include Status object:

```json
"Status": {
  "State": "Enabled",    // Enabled, Disabled, StandbyOffline, etc.
  "Health": "OK"         // OK, Warning, Critical
}
```

## Links Objects

Resources include Links objects for relationships:

```json
"Links": {
  "ManagedBy": [
    {"@odata.id": "/redfish/v1/Managers/BMC"}
  ]
}
```

## Compatibility

This implementation is compatible with:

### Redfish Clients
- Standard Redfish client libraries (Python, Go, etc.)
- DMTF Redfish tools
- iLO/iDRAC style management tools (through Power resource)
- Modern PDU management tools (through PowerSubsystem)

### Redfish Validators
The structure follows patterns that pass DMTF Redfish Service Validator checks:
- Proper schema versions
- Required properties present
- Correct HTTP methods
- Valid OData annotations

## Differences from Full Redfish BMC

This implementation focuses on power distribution:

**Not Implemented** (not applicable for power strips):
- Computer Systems (no servers attached)
- Thermal management (no sensors)
- Firmware updates (TP-Link has own update mechanism)
- BIOS/UEFI settings
- Network interface management
- Storage management
- Event subscription (planned for future)

**Future Enhancements**:
- Authentication and Sessions (framework in place)
- Power metrics (if available from device)
- Event subscription for power events
- Task service for long-running operations

## References

- [DMTF Redfish Specification](https://www.dmtf.org/standards/redfish)
- [Redfish Schema Index](https://redfish.dmtf.org/redfish/schema_index)
- [OpenBMC Redfish Cheatsheet](https://github.com/openbmc/docs/blob/master/REDFISH-cheatsheet.md)
- [Redfish Mockups](https://redfish.dmtf.org/redfish/mockups/v1)
- [DSP2050 - Power Equipment](https://www.dmtf.org/dsp/DSP2050)
- [DSP0266 - Redfish Specification](https://www.dmtf.org/dsp/DSP0266)
