---
name: motion
description: "Provides comprehensive information about ctrlX MOTION system including axes, kinematics, drives, and EtherCAT fieldbus. Always use before do any motion configuration via datalayer, commanding movements, querying states, creating/configuring axes and kinematics, working with axis profiles (SoE/CoE), checking licenses, monitoring PLCopen states, and DataLayer operations. Handles both real and virtual (simulated) motion components. Always retrieve this information before doing motion related tasks"
license: Proprietary. LICENSE.txt has complete terms
---

# Motion Control

## Core Concepts

### Axis
Logical object representing a drive or encoder (abbreviated `axs` in DataLayer). Can be real or **virtual** (simulated - copies setpoints as actual values).

### Drive
Fieldbus device that receives setpoints, delivers actual values, and moves machine parts.

### Encoder
Input delivering only actual values to Motion Kernel. Can be used as master axis in couplings.

### Axis Profile
Converts generic Motion Kernel setpoints to drive-specific encoding. Required for real drives at `motion/axs/<name>/cfg/axisprofile`. Supported profiles:
- **SoE** (Sercos over EtherCAT)
- **CoE** (CANopen over EtherCAT)

Virtual axes have no assigned profile.

### Kinematics
Group of axes (abbreviated `kin` in the datalayer) typically representing a robot. Used for path control. Configured axes are assigned via `motion/axs/<name>/cmd/add-to-kin` or `motion/kin/<name>/cfg/kin-axs` command. Includes axis transformation converting axis positions (ACS) to machine coordinates (MCS) for Cartesian commanding.

### Configuration
Static settings of the motion kernel can be found under `motion/cfg` node.
Configuration of individual logical objects can be found under `motion/<axs|kin|`.

### Commanding
General motion commands like state switching can be found in `motion/cmd` datalayer folder.
Movement generation for axis or kinematics in `motion/<axs|kin>/<name>/cmd`.

### States
Motion Kernel values under DataLayer `motion/state` node:
- **Interpolated values** (`ipo`) - calculated setpoints
- **Actual values** (`actual`) - drive-reported values

## System Status Overview

Query these paths to assess motion system health:

### Motion State

The following nodes provide the current operational state of the motion system, including initialization status and lists of configured motion elements.

| Operation | Path | Node Description | Advanced description |
|-----------|------|-------------|----------------|
| READ | `motion/state/opstate` | Operation state of motion system | Returns the current operational state #ToDo (e.g., RUNNING, STOPPED, ERROR) |
| READ | `axisprofile/system/opstate/actual` | Actual value of the axisprofile state machine | Current state of the axis profile system (initialization, configuration, operational) |
| READ | `motion/state/axs-list` | List of all axes | Array of all configured axis names in the system |
| READ | `motion/state/kin-list` | List of all kinematics | Array of all configured kinematic group names |
| READ | `axisprofile/profiles` | Name of profile | Returns the list of all configured axis profile names |
| READ | `motion/state/init-finished` | Is the motion initialization finished? | Boolean value indicating whether motion system initialization is complete |
| READ | `motion/cfg/functions/sync-motion/point-table/tables` | Configuration of all point tables | List of configured point tables for synchronized motion operations |

### Motion Licensing

The following nodes give information about the capabilities available based on the installed licenses. The Basic license is required. The other nodes give information about how many elements a user can create based on the installed license.

| Operation | Path | Node Description | Adhanced description |
|-----------|------|-------------|----------------|
| READ | `motion/state/capabilities/basic-license` | Is the motion basic license installed? |
| READ | `motion/state/capabilities/max-axes` | max. number of axes allowed |
| READ | `motion/state/capabilities/max-kinematics` | max. number of kinematics allowed |
| READ | `motion/state/capabilities/max-axisprofiles` | max. number of max axisprofiles allowed |
| READ | `motion/state/capabilities/max-axes-coordinated` | max. number of axes in coordinated motion allowed |

### System State

System-level state information for various ctrlX OS components are required for motion functionality.

| Operation | Path | Node Description | Advanced description |
|-----------|------|-------------|----------------|
| READ | `system/state/axis.profile` | Axis profile app state | State information for the axis profile app component |
| READ | `system/state/fieldbuses-ethercat-master-instances-ethercatmaster` | EtherCAT master state |  State information of the EtherCAT master interface |
| READ | `system/state/motion.core` | Motion core app state |  State information for the motion.core app |
| READ | `system/state/scheduler` | Scheduler app state |  State information of the real-time scheduler |

### Boot and recovery checks

Before requesting `Booting`, verify all of the following:

```text
system/state/scheduler           -> OPERATING
system/state/motion.core         -> not SETUP
motion/state/opstate             -> Configuration
motion/state/init-finished       -> true
motion/axs/<name>/state/opstate/plcopen
diagnosis/get/actual/list
```

If all axes become `OUTDATED` and boot reports
`Can't reset axis (Result 0xf014000e); Abort BOOTING`, stop retrying and
inspect the active diagnosis, axis profiles, virtual-kernel state, and saved
configuration. A `motion/cmd/reset-all` CREATE request uses an object payload:

```text
{"type":"object","value":{}}
```

Reset-all is a recovery attempt, not proof that the Motion system is
operational. Verify `system/state/motion.core` and `motion/state/opstate` after
it. Do not reboot or restart a target without explicit approval.

### Fieldbus/EtherCAT

EtherCAT fieldbus communication parameters and slave device information. These nodes are essential when working with EtherCAT-connected drives.

| Operation | Path | Node Description | Advanced description |
|-----------|------|-------------|----------------|
| BROWSE | `fieldbuses/ethercat/master/instances` | Browse EtherCAT master instances | Returns list of configured EtherCAT master instance names |
| READ | `fieldbuses/ethercat/master/instances/ethercatmaster/device_access/slave_address_mapping` | EtherCAT slave address mapping | Array mapping physical EtherCAT slave addresses to logical device identifiers |

### Axis Operations

| Operation | Path | Description |
|-----------|------|-------------|
| WRITE | `motion/axs/<name>` | Change axis name |
| READ | `motion/axs/<name>/cfg/lim` | Get axis limits |
| READ | `motion/axs/<name>/cfg/axisprofile` | Get axis profile (empty for virtual) |
| WRITE | `motion/axs/<name>/cfg/axisprofile` | Assign axis profile |
| READ | `motion/axs/<name>/cfg/properties/category` | Get axis category (ENCODERAXS for encoders) |
| WRITE | `motion/axs/<name>/cfg/properties/type` | Set LINEAR or ROTATIONAL |
| READ | `motion/axs/<name>/state/opstate/plcopen` | Get PLCopen state (DISABLED/STANDSTILL/ERRORSTOP) |
| READ | `motion/axs/<name>/state/values/ipo` | Get interpolated values (setpoints) |
| READ | `motion/axs/<name>/state/values/actual` | Get actual values from drive |

### Kinematics Operations

| Operation | Path | Description |
|-----------|------|-------------|
| BROWSE | `motion/state/jnt-trafo` | List available joint transformation names |
| READ | `motion/state/jnt-trafo/<name>` | Read configuration of a specific joint transformation |
| READ | `motion/state/jnt-trafo` | Read all joint transformations — ⚠️ **avoid**: returns large payload and wastes tokens; prefer BROWSE + targeted READ |
| BROWSE | `motion/kin` | List configured kinematics |
| CREATE | `motion/kin` | Create new kinematic (default Cartesian) |
| CREATE | `motion/kin/<name>/cfg/save` | Save kinematic to persistent storage |
| READ | `motion/kin/<name>/cfg` | Read kinematic configuration |
| WRITE | `motion/kin/<name>/cfg` | Change kinematic configuration |
| READ | `motion/kin/<name>/cfg/kin-axs` | Get axis mapping to kinematic |
| CREATE | `motion/kin/<name>/cfg/kin-axs` | Link axis to kinematic |
| READ | `motion/kin/<name>/state/opstate/plcopen` | Get PLCopen state (DISABLED/STANDBY/ERRORSTOP) |
| READ | `motion/kin/<name>/state/kin-axs-actual-list` | Get currently grouped axes |

## Configuration Management

Configuration found under DataLayer `cfg` node with three levels:
- motion: `motion/cfg`
- Per-axis: `motion/axs/<name>/cfg`
- Per-kinematic: `motion/kin/<name>/cfg`

### Configuration Rules

**Allowed anytime:**
- Modify most configuration values via WRITE

**Not allowed during OPERATION:**
- Creating/deleting/renaming axes, kinematics, axis profiles
- Changing `motion/axs/<name>/cfg/properties` nodes
- Changing `motion/kin/<name>/cfg/kin-axs` assignments

### Logical objects

Logical objects that can be created in the motion kernel

| Object | Path | Operations |
|--------|------|------------|
| Axes | `motion/axs` | CREATE (name as string), DELETE, WRITE (rename) |
| Kinematics | `motion/kin` | CREATE, DELETE, WRITE |
| Axis profiles | `axisprofile/profiles` | CREATE, DELETE, WRITE |
| MCS-PCS transforms | `motion/cfg/coord-systems/pcs/sets` | CREATE, DELETE |
| Tool data | `motion/cfg/functions/tool-data/sets` | CREATE, DELETE |
| Safe zones | `motion/cfg/safe-areas` | CREATE, DELETE |
| Teach points | `motion/kin/<name>/cfg/points` | CREATE, DELETE |

### Units Handling

For values with units (e.g., `motion/axs/<name>/cfg/lim/vel-neg`):
- User unit (e.g., `mm/min`) provided in node metadata
- Sub-nodes for other units: `motion/axs/<name>/cfg/lim/vel-neg/in-per-min`
- Automatic conversion on read/write

Supported units at `motion/state/units`:
- `unitObjType`: `linear`, `rotational`, or `linear+rotational`
- `unitValueType`: length, velocity, force, time, etc.
- `abbreviation`: filesystem storage
- `abbreviationURI`: sub-node names

### Persistence

Changes affect memory only until saved. It is recommend to save the modifications at the end.

| Operation | Motion | Axis Profile |
|-----------|--------|--------------|
| Save all | CREATE `motion/admin/cfg/save` | CREATE `axisprofile/admin/cfg/save` |
| Load all | CREATE `motion/admin/cfg/load` | CREATE `axisprofile/admin/cfg/load` |
| Save single | CREATE `motion/admin/cfg/make-persistent` | CREATE `axisprofile/admin/cfg/make-persistent/<name>` |

> Single object saves are significantly faster for large configurations.

The `CREATE` to a save node, requires the following json object where:

- configurationPath: always empty
- id: client side generated id for traceability
- phase: always `save`

a complete datalayer request looks like the following:

```
{"type": "object", "value": {"configurationPath": "", "id": "save_all@delete_axes", "phase": "save"}}
```

## Common Workflows

### Switch Motion State

**Prerequisites:**
To switch from `Configuration` to `running` the scheduler must be switched to `operating` before:
```
CREATE scheduler/admin/state with value `{state: "OPERATING"}`
```

Switch between `Configuration` (for modifications) and `Running`:

**To Configuration:**
```
CREATE motion/cmd/opstate with value "Configuration"
```

**To Running:**
```
CREATE motion/cmd/opstate with value "Booting"
```

### Create and Configure an Axis

**Prerequisites:**
- System in `SETUP` state

**Instruction**

If you miss information. Request it from the user.

**Steps:**
1. CREATE axis: `motion/axs` with axis name as string
2. Set category: WRITE `motion/axs/<name>/cfg/properties/category` to `ENCODERAXS` (for encoders only)
3. Set type: WRITE `motion/axs/<name>/cfg/properties/type` to `LINEAR` or `ROTATIONAL`
4. Configure units: WRITE `motion/axs/<name>/cfg/units`
5. For modulo axes:
   - WRITE `motion/axs/<name>/cfg/properties/modulo` = `true`
   - WRITE `motion/axs/<name>/cfg/properties/modulo-value`
6. Configure limits: WRITE `motion/axs/<name>/cfg/lim`
7. Assign profile: WRITE `motion/axs/<name>/cfg/axisprofile`
8. Configure functions as needed:
   - Encoder: `motion/axs/<name>/cfg/functions/encoder`
   - Gantry: `motion/axs/<name>/cfg/functions/coupling/gantry/member` = `true`
   - Open-loop: `motion/axs/<name>/cfg/functions/open-loop` = `true`
   - Probe: `motion/axs/<name>/cfg/functions/probe`
   - SLS: `motion/axs/<name>/cfg/functions/safe-motion/drive-safe-limited-speed`

### Create and Configure a Kinematic

**Prerequisites:**
- System in `SETUP` state

**Steps:**
1. CREATE kinematic: `motion/kin` with name as string
2. Configure units: WRITE `motion/kin/<name>/cfg/units`
3. Assign axes: CREATE `motion/kin/<name>/cfg/kin-axs` with:
   - `axsName`: axis name
   - `axsDir`: `+` or `-`
   - `acsIndex`: 0-15 (position in kinematic)
   - `axsMeaning`: leave empty (deprecated)
4. Create MCS set: CREATE `motion/kin/<name>/cfg/coord-systems/mcs`
5. Configure MCS set at `motion/kin/<name>/cfg/coord-systems/mcs/<setName>`:
   - BROWSE `motion/state/jnt-trafo` to list available transformation names, then READ `motion/state/jnt-trafo/<name>` for the specific transformation details
   - WRITE `jnt-trafo`: transformation name selected from the browse result
   - Configure `param/axis-assignment`:
     - `indexACS`: from step 3
     - `axisName`: from transformation `reqAxes`
     - Axis types must match
6. Configure limits: WRITE `motion/kin/<name>/cfg/lim`
7. Optional: orientation limits, teach points, safe zones

### Link Axis to Kinematic (Grouping)

**Three axis types in kinematics:**
- Main axes: required by transformation
- Belt axes: sync to existing belts
- Free axes: various scenarios

**Prerequisites:**
- Axis configured in `motion/kin/<name>/cfg/kin-axs`
- System in `OPERATION` state
- Axis in `STANDSTILL` state

**Command:**
```
CREATE motion/axs/<name>/cmd/add-to-kin with kinName = "<kinematic_name>"
```

**Result:** Axis transitions to `COORDINATED_MOTION` state and moves with kinematic.

**To ungroup:**
```
CREATE motion/axs/<name>/cmd/rem-frm-kin
```

### Enable kinematic

**Prerequisites**:
- Machine and Motion state in `Operating`

**Steps:**
1. Power all related axis via `motion/axs/<name>/cmd/power`
2. Add all related axis to kinematic via `motion/axs/<name>/cmd/add-to-kin`


### Complete Configuration Workflow

1. Switch to `SETUP`
2. Create and configure axis profiles for each drive
3. Delete old axes (DELETE `motion/axs/<name>`)
4. Create new axes
5. Configure axis basic data
6. Configure axis additional data
7. Delete old kinematics (DELETE `motion/kin/<name>`)
8. Create new kinematics
9. Configure kinematic basic data
10. Configure kinematic additional data
11. Save: CREATE `motion/admin/cfg/save`

## Commanding

> ⚠️ **Warning:** Commands generate movements. Require explicit user consent before commanding.

### IDE Blockly/Python integration

The ctrlX IDE uses a separate restricted Blockly/Python runtime. Use the IDE
reference on the device (`/tiger/docs.html#doc:reference`) for the available
motion namespaces and blocks.

The documented absolute-move signature is:

```python
motion.Axis_1.move(MoveType.ABSOLUTE, position, velocity, acceleration, jerk)
```

The `jerk` argument is mandatory. An IDE program does not implicitly power an
axis; verify `Running` motion state and `STANDSTILL` axis state first. For a
rotational modulo axis, a command to `-30` can be reported as `330` after the
move. Compare with the configured modulo value.

Commands via CREATE to `cmd` nodes:
- Global: `motion/cmd`
- Axis: `motion/axs/<name>/cmd`
- Kinematic: `motion/kin/<name>/cmd`

### Global Commands

| Command | Path | Purpose |
|---------|------|---------|
| Change state | `motion/cmd/opstate` | Switch operational state |
| Reset all | `motion/cmd/reset-all` | Reset all axes/kinematics in error |

### Axis Commands

Motion Kernel must be in `RUNNING` state (global `OPERATION`).

#### Power On/Off

**Power On:**
- Prerequisite: `DISABLED` state
- Command: CREATE `motion/axs/<name>/cmd/power` with `true`
- Result: `DISABLED` → `STANDSTILL_PENDING` → `STANDSTILL`

**Power Off:**
- Prerequisite: `STANDSTILL` state
- Command: CREATE `motion/axs/<name>/cmd/power` with `false`
- Result: `STANDSTILL` → `DISABLED`

#### Movement Commands

**Absolute Position:**
- Prerequisite: `STANDSTILL` state
- Command: CREATE `motion/axs/<name>/cmd/pos-abs` with:
  - `axsPos`: target position
  - `lim`: dynamic limits
- Result: `STANDSTILL` → `DISCRETE_MOTION` → `STANDSTILL`

### Kinematic Commands

**Absolute Movement:**
- Prerequisite: `STANDBY` state
- Command: CREATE `motion/kin/<name>/cmd/move-abs` with:
  - `kinPos`: target position as array with 16 elements. One for each dimensions.
  - `lim`: dynamic limits
  - `coordSys`: Use `WCS` for World Coordinate System.
  - Use `buffered`=`true` to send all movement commands immediately into queue whithout having to wait for the individual movements to complete
- Result: `STANDBY` → `MOVING` → `STANDBY`

## PLCopen States

### Axis States

| State | Meaning |
|-------|---------|
| `DISABLED` | Ready for power on |
| `STANDSTILL` | Stopped, can be commanded |
| `STANDSTILL_PENDING` | Transitioning to standstill |
| `DISCRETE_MOTION` | Executing movement |
| `COORDINATED_MOTION` | Grouped to kinematic |
| `ERRORSTOP` | Error occurred, needs reset |

### Kinematic States

| State | Meaning |
|-------|---------|
| `DISABLED` | Not active, can be enabled |
| `STANDBY` | Stopped, can be commanded |
| `MOVING` | Executing movement |
| `ERRORSTOP` | Error occurred, needs reset |

## Axes and Kinematics Relationship

- Kinematics contains multiple axes
- Axes must be assigned in `motion/kin/<name>/cfg/kin-axs` (allocates memory)
- Index (0-15) specifies position in kinematic
- Position in ACS is 16-value array, each axis at its index
- When system is `OPERATION` and axes are `STANDSTILL`, grouping is possible
- Grouped axes move with kinematic movements
- Actual position flows from axes to kinematic
