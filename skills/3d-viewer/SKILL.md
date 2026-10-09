---
name: 3d-viewer
description: "Provides comprehensive information about the ctrlX 3D Viewer App, its model and kinematics workflow, permissions, installation, and ctrlX Data Layer endpoints. Always use before installing, configuring, troubleshooting, or verifying the 3D Viewer on ctrlX OS. Use the motion skill first for axis, kinematics, or movement configuration."
license: Proprietary. LICENSE.txt has complete terms
---

# 3D Viewer

## Core Concepts

### Application
The ctrlX 3D Viewer is a browser-based application for visualizing machine and
robot kinematics on ctrlX OS. The model contains the axis relationships and the
3D geometry, typically STL files, required for the visualization.

The package identity for the 4.6.1 application is:

| Item | Value |
|---|---|
| Package title | `3D Viewer` |
| Snap name | `rexroth-3dviewer` |
| Package-manager ID | `snap_rexroth-3dviewer` |
| Application route | `/3dviewer` |
| Model Library | `/3dviewer/Dashboard` |
| My Model | `/3dviewer/MachineView` |

The 3D Viewer consumes motion data; it does not replace the Motion skill or the
Motion Kernel. Use the `motion` skill before creating or changing axes,
kinematics, axis profiles, or commands that can generate movement.

## Data Layer First

Prefer ctrlX Data Layer operations whenever the requested behavior is exposed
by a Data Layer node. This is the primary routing rule for this skill:

1. `BROWSE` the relevant subtree.
2. Read `METADATA` for the exact node and operation schema.
3. Use `READ` or `SUBSCRIBE` for observation and visualization.
4. Use `WRITE`, `CREATE`, or `DELETE` only when metadata allows the operation,
   the request explicitly requires a persistent change, and the matching
   specialist skill authorizes the operation.
5. Use the 3D Viewer REST API only for app-owned model storage, active-solution
   callbacks, or another function that has no suitable Data Layer node.

Do not replace a Data Layer operation with an undocumented HTTP endpoint. The
REST facade below is itself the external transport for Data Layer access; the
node path and operation semantics remain the source of truth.

### Model
A model maps Data Layer axis values to a kinematic structure and its geometry.
Keep the model's axis names aligned with the configured Motion axes. Browse the
Data Layer first rather than guessing an axis or kinematic path.

For every XML axis with `type="rotation"`, provide finite `rzx`, `rzy`, and
`rzz` attributes. The 4.6.1 viewer constructs an internal rollover vector from
these values even when rollover is disabled. Omitting them produces
`THREE.BufferGeometry` `NaN` errors and a blank 3D viewport while the command
panels still render.

When importing a model from a ROS URDF, use the URDF joint `origin` (XYZ/RPY)
as the preceding XML transform and the URDF joint `axis` as the 3D Viewer axis
vector. ROS STL meshes are commonly expressed in meters; add a single
root-scale transform of `1000` when the viewer model and Motion positions use
millimeters.

### Data Layer
The web application uses the ctrlX REST facade for the Data Layer. Its client
uses the following base paths:

```text
/automation/api/v2
/automation/api/v2/nodes
/automation/api/v2/events
```

For a remote device, the complete endpoint is:

```text
https://<device>/automation/api/v2/nodes/<node-path>
```

Authentication is required. Load the `authentication` skill before using the
endpoint. Never store or print credentials or bearer tokens.

## Data Layer Endpoint Contract

### Browse and metadata

Always browse and read metadata before selecting a node or changing a model:

```text
GET /automation/api/v2/nodes/motion?type=browse
GET /automation/api/v2/nodes/motion/axs/<axis>?type=browse
GET /automation/api/v2/nodes/<node-path>?type=metadata
GET /automation/api/v2/nodes/<node-path>
```

The response contains the Data Layer type and, for reads, the `value` field.
Do not infer the type or operation from a model file alone.

### Motion values used by the 3D Viewer

The application source for 4.6.1 uses these paths:

| Purpose | Data Layer path | Operation |
|---|---|---|
| Axis setpoint position | `motion/axs/<axis>/state/values/ipo/pos` | READ |
| Realtime axis setpoint position, when available | `motion/axs/<axis>/realtime-data/input/data/state/values/ipo/pos` | READ/SUBSCRIBE |
| Kinematic joint poses | `motion/kin/<kinematic>/state/values/joint-poses` | READ |
| Kinematic coordinate transform | `motion/kin/<kinematic>/state/values/coord-transform` | READ |
| Motion operation state | `motion/state/opstate` | READ |

The exact axes and kinematics are device-specific. On the validated virtual
target, `motion/state/axs-list` returned `Axis_1` through `Axis_5`; this is a
runtime observation, not a fixed requirement.

### Realtime updates

The application uses the Automation Core event API for change notifications:

```text
POST /automation/api/v2/events
GET  /automation/api/v2/events?nodes=<node-paths>&publishIntervalMs=<ms>
```

Use the Data Layer subscription workflow for the request body and lifecycle.
Do not poll rapidly when a supported realtime node or event subscription is
available. Check metadata and the realtime node list before using the
`realtime-data` path.

### Operations that can change device state

The 3D Viewer should normally use read-only Data Layer operations. If a user
requests a change, inspect the node metadata first and route the operation to
the matching specialist skill:

| Requested change | Data Layer route | Required skill |
|---|---|---|
| Change an axis, kinematic, axis profile, or Motion configuration | `motion/...` writable nodes | `motion` |
| Command power or movement | `motion/.../cmd` create nodes | `motion`, explicit movement consent |
| Restrict Data Layer access | `datalayer/security/scopes/...` | `datalayer-scopes` |
| Save or load the 3D Viewer model configuration | No equivalent public 3D Viewer Data Layer node | 3D Viewer app API / active solution |

Never use the 3D Viewer skill to issue Motion commands merely to test a model.
Use a read or subscription instead. Movement commands require the `motion`
skill and explicit consent.

## Permissions and Package Assets

The package manifest declares these 3D Viewer permissions:

| Scope | Purpose |
|---|---|
| `3dviewer.models.r` | View the model library |
| `3dviewer.models.rw` | Upload and delete models |
| `3dviewer.axis.rw` | Browse and configure model axis mappings |

`3dviewer.axis.rw` requires `rexroth-automation.datalayer.r`. Assign only the
minimum scopes needed by the user or application.

The package depends on:

- `rexroth-automationcore`
- `rexroth-deviceadmin`
- `rexroth-solutions`

The package manifest also declares the Basic, Advanced add-on, and legacy
3D Viewer license identifiers. Installation success does not prove that a
required license is available; verify the license state in the device UI when
the app reports a licensing problem.

## Installation and Verification

Use the `app-management` skill and the `authentication` skill first. For a
local `.app` package on ctrlX OS 4.6:

1. Confirm the package file and target device.
2. Read the installed package list, scheduler state, and Package Manager
   settings.
3. Save the original scheduler state.
4. Switch the scheduler to `SERVICE` with:

   ```text
   PUT /automation/api/v1/scheduler/admin/state?format=json
   {"state":"SERVICE"}
   ```

5. Upload one package at a time:

   ```text
   POST /package-manager/api/v1/packages
   multipart/form-data: file=<3D Viewer .app>, update=true
   ```

6. Require HTTP `202` and poll the `Location` task with:

   ```text
   GET /package-manager/api/v1/tasks/<task-id>
   ```

   Stop on `state=failed`; continue only after `state=done`.
7. Restore the saved scheduler state. On a normally operating 4.6 target this
   is `OPERATING`:

   ```text
   PUT /automation/api/v1/scheduler/admin/state?format=json
   {"state":"OPERATING"}
   ```

8. Verify the package ID, title, source version, scheduler state, and UI route.
   A successful installation should make `https://<device>/3dviewer` return
   the 3D Viewer HTML.
9. Verify Data Layer access by browsing `motion` and reading at least one
   selected axis or kinematic node.
10. Perform a real browser check of `/3dviewer/<project-name>/commands`.
    Confirm that a visible WebGL canvas contains geometry and inspect browser
    console errors. HTTP 200 from the route and project API is not sufficient.
11. Read `system/state/motion.core`, `system/state/scheduler`,
    `motion/state/opstate`, and `diagnosis/get/actual/list` before reporting
    the setup as fully operational.

The 4.6.1 package contains amd64 and arm64 payloads; Package Manager selects the
matching architecture. The Package Manager health field may report `unknown`
for this app even when the package is installed and the `/3dviewer` route is
healthy, so use both package and route checks.

### Selecting a project after REST upload

`POST /3dviewer/api/v2/projects` stores the project on the device but does not
set the browser's local or session storage for the currently selected project.
Opening `/3dviewer/MachineView` directly can therefore show the command panels
without a model.

After an API upload, select the project from:

```text
https://<device>/3dviewer/Dashboard
```

or open its project route directly:

```text
https://<device>/3dviewer/<project-name>
```

The project route must use the exact name returned by
`GET /3dviewer/api/v2/projects`. For example, a project named
`BCN3D_Moveo` is opened at `/3dviewer/BCN3D_Moveo`; its command panel is at
`/3dviewer/BCN3D_Moveo/commands`.

The app also probes legacy internal Motion browse routes such as
`/automation/api/v1.0/motion/axs` and `/automation/api/v1.0/motion/kin`.
Use the documented v2 Data Layer node API for new integrations; do not infer
that a v1.0 probe is the preferred external interface.

## Configuration Workflow

1. Use the `motion` skill to confirm the Motion axes and kinematics exist and
   are in a suitable state.
2. In the 3D Viewer, open the Model Library or My Model route.
3. Select or upload a model only when the required model scopes are assigned.
4. Browse the Data Layer and map each model axis to an existing Motion axis.
5. Read the selected node metadata and confirm units and read permissions.
6. Prefer a Data Layer `WRITE` only if the selected node is explicitly
   writable and the requested model operation is actually represented there.
   Otherwise save the model through the 3D Viewer UI/active-solution workflow.
7. Verify the model with live axis values or a Data Layer subscription. Do not
   command movement from this skill; movement commands require the `motion`
   skill and explicit consent.

The package registers the active-solution load callback at:

```text
POST /3dviewer/api/v2/load
```

Do not use a GET request to infer its payload; the endpoint is a configuration
callback, not the Data Layer endpoint.

## Troubleshooting

### App installs but the page is unavailable

Check, in order:

1. Package Manager shows `rexroth-3dviewer` installed.
2. Scheduler is back in its saved operating state.
3. `/3dviewer` returns HTTP 200.
4. Required dependencies and licensing are present.
5. The active solution contains the expected model configuration.

### Model has no motion

Check:

1. The mapped axis names exist in `motion/state/axs-list`.
2. The selected node is readable and has the expected metadata.
3. The axis position path is `state/values/ipo/pos`, not an unrelated actual
   value or configuration node.
4. The Motion Kernel and relevant axes are initialized.
5. The model's units and axis directions match the Motion configuration.

### Command panels are visible but the viewport is blank

Check the browser console for `THREE.BufferGeometry` or `NaN` errors. In
viewer 4.6.1, missing `rzx`, `rzy`, or `rzz` values on a rotation axis creates
an invalid rollover vector and produces this exact symptom. Also verify that
every `geo` filename in the XML exists in the uploaded project archive.

### Geometry is visible but links are disconnected

Do not assemble print-part STL files with guessed translations. Prefer a
canonical URDF or assembly model: use each link mesh as one XML geometry,
convert each URDF joint `origin` (XYZ/RPY) to the preceding XML transform, and
use the URDF joint axis as the XML axis vector. If the URDF meshes are in
meters, apply one root scale of `1000` for the viewer's millimeter model.

An HTTP 404 for an optional project thumbnail does not prevent the 3D model
from rendering; validate the project archive and WebGL canvas separately.

### Viewer renders but the device is only partially operating

Separate visualization health from Motion health. Read:

```text
system/state/motion.core
system/state/scheduler
motion/state/opstate
diagnosis/get/actual/list
```

Do not repeatedly issue `Booting` when axes are `OUTDATED` and diagnosis
reports `Can't reset axis ... Abort BOOTING`. Hand the recovery to the
`motion` skill; a virtual target may require a saved-configuration reload or
an explicitly approved restart.

### Data Layer access is denied

Verify the user's `rexroth-automation.datalayer.r` permission and the
3D Viewer scope assignment. Use the `datalayer-scopes` skill before changing
scopes. Do not bypass authorization with a broader scope as a workaround.

## Safety

Inspection and read-only verification are safe. Treat app installation,
model uploads, configuration writes, scheduler changes, and Motion commands as
persistent changes. On a real device, obtain confirmation before executing
them. A virtual test target may be changed when the user explicitly requests
the operation, but restore the scheduler and verify the final state.

## Sources

- Bosch Rexroth ctrlX OS 3D Viewer: `https://www.boschrexroth.com/en/ca/c/ctrlx-os-3d-viewer/`
- ctrlX Automation SDK Data Layer: `https://boschrexroth.github.io/ctrlx-automation-sdk/4.6.0/datalayer.html`
- ctrlX REST API description: `https://boschrexroth.github.io/rest-api-description/`
- BCN3D Moveo URDF reference: `https://github.com/jesseweisberg/moveo_ros`
- Installed 3D Viewer 4.6.1 package metadata and live endpoint verification
