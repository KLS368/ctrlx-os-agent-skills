---
name: ide
description: "Provides comprehensive information about the ctrlX IDE App including Visual Coding, Textual Coding, Python, JavaScript, project files, debugging, and Data Layer integration. Always use before working with the IDE App on ctrlX CORE."
license: Proprietary. LICENSE.txt has complete terms
---

# ctrlX IDE App

## Core Concepts

### IDE App

The `rexroth-ide` app is a browser-based development environment for ctrlX
CORE. It contains separate editor and IDE services and is accessed through the
ctrlX CORE Web UI.

Verified package facts for IDE App 4.6.0:

- Snap: `rexroth-ide`
- Base: `core24`
- Architectures: `amd64`, `arm64`
- Confinement: `strict`
- Local target: `localhost` (`ctrlx`)
- Active solution workspace:
  `$SNAP_COMMON/solutions/activeConfiguration`

### Visual Coding

Visual Coding provides a programming framework with visual elements, project
management, configuration, editing, and debugging.

### Textual Coding

Textual Coding provides a web-based development environment with:

- code editor
- console
- debugging
- Python scripting
- JavaScript scripting
- native connectivity to the local ctrlX CORE
- editing files in the active solution

### Python/Blockly Runtime Dependency

Python- or Blockly-based projects require the separate `rexroth-python` app
(`snap_rexroth-python`). Installing `rexroth-ide` alone is not sufficient for
these projects. Check the installed-app inventory before running a Python or
Blockly program and install/verify the Python Runtime through the
`app-management` skill when it is missing.

The IDE Python environment is a restricted, IDE-provided language runtime. Use
the namespaces documented by the device-local reference; do not paste a
standard CPython test harness into the IDE editor.

### Active Solution

The IDE is configured to work with the active solution. Changes to files in
the active solution can change the behavior of the target device. Inspect the
solution and target before editing or executing code.

### IDE versus PLC Engineering

The IDE is not the PLC runtime and is not a replacement for ctrlX PLC
Engineering:

- Use this skill for IDE projects, Visual Coding, Python, JavaScript, and IDE
  project files.
- Use `plc` for PLC runtime state, PLC applications, PLC symbols, and realtime
  variables.
- Use the PLC Engineering workflow only for PLC project build, download, start,
  and Engineering-specific automation.

## Data Layer First

The IDE is a Data Layer client/integration surface. The package exposes Data
Layer access, but no stable public `ide/...` Data Layer namespace was found in
the available ctrlX documentation. Do not invent IDE-specific node paths.

For runtime data, device state, commands, and app-to-app communication, use
the `datalayer` skill and Data Layer tools first. Use the IDE Web UI for
project and code editing. Do not replace a Data Layer operation with an
undocumented REST call.

### Verified IDE app nodes

The installed-app inventory exposes the IDE through the standard system
namespace. This was verified on a ctrlX CORE with `rexroth-ide` 4.6.0:

| Operation | Path | Node Description |
|-----------|------|------------------|
| BROWSE | `system/apps/installed` | List installed app IDs |
| BROWSE | `system/apps/installed/rexroth-ide` | List IDE app properties |
| READ | `system/apps/installed/rexroth-ide` | Read the complete `types/apps/installedApp` object |
| READ | `system/apps/installed/rexroth-ide/id` | Snap package ID |
| READ | `system/apps/installed/rexroth-ide/name` | Snap name (`rexroth-ide`) |
| READ | `system/apps/installed/rexroth-ide/title` | App title (`IDE`) |
| READ | `system/apps/installed/rexroth-ide/description` | App capabilities and coding modes |
| READ | `system/apps/installed/rexroth-ide/summary` | Short app description |
| READ | `system/apps/installed/rexroth-ide/vendor` | App vendor |
| READ | `system/apps/installed/rexroth-ide/installed` | Installation state |
| READ | `system/apps/installed/rexroth-ide/enabled` | Enablement state |
| READ | `system/apps/installed/rexroth-ide/release` | Installed release information |
| READ | `system/apps/installed/rexroth-ide/appType` | App type |
| READ | `system/apps/installed/rexroth-ide/required` | Whether the app is system-required |
| READ | `system/apps/installed/rexroth-ide/impactsRealtime` | Realtime impact flag |
| READ | `system/apps/installed/rexroth-ide/updateBehavior` | Package update behavior |

The complete object uses schema `types/apps/installedApp` and contains the
installed version under `release.version`. Use this inventory for app
discovery and status checks. It does not expose IDE project files or a
documented IDE control namespace.

### Data Layer discovery and access pattern

These are generic Data Layer operations, not IDE-specific endpoints:

| Operation | Path | Purpose |
|-----------|------|---------|
| BROWSE | `datalayer/nodesrt` | List realtime Data Layer nodes |
| BROWSE | `<provider-root>` | Discover nodes exposed by a known provider |
| READ metadata | `<node>` | Verify type, schema, unit, and access |
| READ | `<node>` | Read a verified node value |
| WRITE | `<node>` | Write a verified writable node after confirmation |
| CREATE | `<node>` | Call a verified command or create operation |
| SUBSCRIBE | `<realtime-node>` | Subscribe to realtime values |

Before every read, write, create, or subscription:

1. BROWSE the relevant provider or node tree.
2. Read metadata for the exact node.
3. Confirm the operation type, payload, and access permission.
4. Use the `datalayer` skill for the operation.
5. Verify the resulting value or device state.

If no documented Data Layer node exists for the requested IDE function, state
the limitation and use the IDE Web UI rather than guessing an endpoint.

## System and App Status

Use the `app-management` skill first for package state, app health, service
lifecycle, and installation. Use the `diagnosis` skill first for active
alarms and logbook entries.

For IDE inventory and enablement, browse and read
`system/apps/installed/rexroth-ide`. Do not use a guessed
`system/state/rexroth-ide` path. Browse the available system state tree and
read the actual node exposed by the installed ctrlX OS version.

## Standard Workflows

### Open and inspect the IDE

1. Confirm the target is the intended real or virtual ctrlX CORE.
2. Confirm `rexroth-ide` is installed and healthy.
3. Open the ctrlX CORE Web UI and launch IDE.
4. Confirm the active solution and project mode.
5. Inspect existing files before editing.

### Visual Coding

1. Open the Visual Coding workspace.
2. Create or open the intended project.
3. Configure visual elements and their connections.
4. Identify every Data Layer node used by the project.
5. Verify each node with the `datalayer` skill before connecting or writing it.
6. Test on a virtual or test target before a production device.

### Textual Coding

1. Open the Textual Coding workspace.
2. Select the correct Python or JavaScript project file.
3. Confirm the active solution path and runtime dependencies.
4. Use documented Data Layer client libraries or IDE blocks only after the
   target nodes and permissions are verified.
5. Run or debug only after confirming the target and execution context.
6. Verify generated values, files, and device state.

### Debugging

1. Use `app-management` to check IDE app health.
2. Use `diagnosis` to read active alarms and logbook entries.
3. Inspect the IDE service state and Web UI route.
4. Check IDE nginx/backend logs only when more detail is required.
5. For Data Layer failures, use `datalayer` to browse, read metadata, and
   verify the connection and node permissions.

## Data Layer and Device Interaction

IDE code can read, write, subscribe to, and expose values through the Data
Layer when the selected project mechanism supports it. A variable in an IDE
project is not automatically a Data Layer node; it must be explicitly mapped
or provided.

The installed IDE reference documents these namespaces for Blockly/Python
source:

- `loops.main(function)` for the main routine
- `console.log(value)` for browser-console output
- `console.logValue(label, value)` for labelled output
- `DatalayerLib.browse(path)` for Data Layer browsing
- `DatalayerLib.read(path)` for primitive Data Layer reads
- `DatalayerLib.readJson(path)` for object reads
- `ctrlx.write(path, value[, type])` for writes
- `ctrlx.create(path, value[, type])` for creates

Use only commands listed by the installed IDE documentation. Imports of
arbitrary Python modules, filesystem access, `exec`, and standard-library test
harnesses are not valid Blockly/Python project source.

For Data Layer work:

- Use `datalayer` first for node discovery, metadata, reads, writes, calls, and
  subscriptions.
- Use `datalayer-scopes` first when the problem concerns user-defined scopes
  or authorization.
- Use `motion` first before code that configures or commands axes or
  kinematics.
- Use `plc` first for PLC symbols, realtime variables, and PLC runtime
  operations.
- Use `authentication` for credentials; never put tokens or passwords in
  project files, screenshots, or logs.

## Motion Integration

Use the `motion` skill first for every IDE program that commands an axis or
kinematic. The IDE motion reference uses:

```python
motion.Axis_1.move(MoveType.ABSOLUTE, position, velocity, acceleration, jerk)
```

The jerk argument is mandatory. The IDE program does not implicitly power the
axis. Before starting a real movement, verify:

1. Motion is `Running`.
2. The axis is `STANDSTILL`, not `DISABLED` or `ERRORSTOP`.
3. The motion area is clear and the target positions are safe.
4. The axis units and limits are read from Data Layer metadata/configuration.

For rotational modulo axes, a target such as `-30 deg` can be reported as
`330 deg` after the move. Compare positions using the configured modulo
behavior, not only literal signed values. After a test, power the axis off and
verify `DISABLED`.

## Configuration and Persistence Rules

IDE project and solution files are persistent device data:

- Inspect before editing.
- Make the smallest change required.
- Do not overwrite an active solution without an approved backup or recovery
  path.
- Do not execute Python, JavaScript, or visual code on a real device without
  explicit confirmation.
- Treat Data Layer `WRITE` and `CREATE` operations as persistent changes.
- Verify the target state after every change.

## Test Scenario: IDE Data Layer Smoke Test

Use this read-only scenario after installing or updating the IDE App.

**Scenario ID:** `IDE-DL-SMOKE-001`

**Target:** A real or virtual ctrlX CORE with `rexroth-ide` installed.

**Procedure:**

1. BROWSE `system/apps/installed`.
2. Assert that `rexroth-ide` is present.
3. BROWSE `system/apps/installed/rexroth-ide`.
4. Assert that the app properties include `installed`, `enabled`, `release`,
   `title`, `description`, `id`, and `name`.
5. READ `system/apps/installed/rexroth-ide` and verify the schema
   `types/apps/installedApp`.
6. Verify:
   - `name` is `rexroth-ide`
   - `title` is `IDE`
   - `installed` is `true`
   - `enabled` is `true`
   - `release.version` is the expected installed version
   - `impactsRealtime` and `required` are present
7. READ the individual properties needed by the caller, rather than
   repeatedly reading the complete object.

**Pass criteria:**

- All required browse and read operations succeed.
- `rexroth-ide` is installed and enabled.
- The complete object uses `types/apps/installedApp`.
- No device state, project file, or Data Layer value is changed.

**Failure handling:**

- If `rexroth-ide` is absent, use `app-management` to inspect package state.
- If the app is installed but disabled, do not enable it implicitly; report the
  state and request confirmation before changing it.
- If a node is missing, browse the installed-app tree again and do not guess a
  replacement path.

## Complete Demo Scenario

**Scenario ID:** `IDE-DL-DEMO-001`

This demo validates the complete path from the IDE Textual Coding environment
to a verified Data Layer node without changing device state.

### Preparation

1. Use the `app-management` skill to confirm that `rexroth-ide` is installed
   and enabled.
2. Run `IDE-DL-SMOKE-001`.
3. Open IDE in the ctrlX CORE Web UI and select Textual Coding.
4. Copy `examples/ide_datalayer_read_demo.py` into the active Blockly/Python
   project or recreate it with the documented blocks.
5. Do not add imports or install Python packages. The demo uses the IDE
   built-in `DatalayerLib` and `console` namespaces.

### Execution

Start the project with the IDE Run command. The program reads
`/system/apps/installed/rexroth-ide/title` through `DatalayerLib.read` and
logs the result without a Data Layer write, command, subscription, or device
configuration change.

### Expected result

```text
IDE-DL-DEMO PASS
IDE title: IDE
```

An unavailable IDE namespace, failed Data Layer read, or unexpected title is a
failed demo and must be reported explicitly.

### Optional Visual Coding variant

If the installed IDE version provides a Data Layer read block, configure it
with the verified path
`/system/apps/installed/rexroth-ide/title`, connect its output to a display or
console block, and expect `IDE`. Use the block documentation from the active
IDE version; do not infer block names or write behavior from this skill.

### Cleanup

Remove the copied demo file from the active solution after verification unless
the user explicitly wants to keep it. Do not delete unrelated project files.

## Test Project Scenario

The complete copyable project is in
`examples/ide-test-project/`. Use it for a repeatable IDE validation:

- `README.md` contains the setup, procedure, acceptance criteria, and cleanup.
- `main.py` performs the read-only Data Layer test.
- `test_main.py` tests the current Blockly callback registration without
  starting the real loop.
- The project uses IDE-supported namespaces and does not contain credentials.
- The project does not write, create, delete, or subscribe to Data Layer nodes.

Start the project from the IDE Run command.

Expected result:

```text
IDE-PROJECT-001 PASS
IDE title: IDE
```

Run `test_main.py` only as a local host-side harness, not inside the Blockly
editor:

```text
python3 scripts/test_main.py
```

The IDE reference is available on the device at:

```text
https://<ctrlx-core>/tiger/docs.html#doc:reference
https://<ctrlx-core>/tiger/docs.html#doc:blocks
```

## Boundaries

- This skill does not replace the `plc`, `datalayer`, `diagnosis`, or `motion`
  skills.
- It does not define undocumented IDE REST endpoints.
- It does not use the PLC Engineering REST API for ordinary IDE tasks.
- It does not claim that an IDE project is a PLC application.
- It does not bypass device permissions, licenses, confinement, or Data Layer
  scopes.

## Official Documentation

- [IDE App Application Manual](https://docs.automation.boschrexroth.com/pdf/document/ID1668592_212822336?filename=IDE%20App%2C%20Integrated%20Development%20Environment%2001VRS%2C%20Application%20Manual&lang=eng)
- [Bosch Rexroth Product Information Portal](https://docs.automation.boschrexroth.com/welcome/)
- [Using IDE app in ctrlX CORE](https://community.boschrexroth.com/ctrlx-automation-how-tos-qmglrz33/post/using-ide-app-in-ctrlx-core-kYnQusnhQK8sqb0)
- [Graphical and textual Python programming with IDE App](https://community.boschrexroth.com/ctrlx-automation-how-tos-qmglrz33/post/graphical-and-textual-python-programming-for-pick-and-place-using-ide-app-POwlJDzEIUO72AR)
- [Read/create Data Layer variables with IDE Python/Blockly](https://community.boschrexroth.com/ctrlx-works-mpp856pr/post/read-create-variables-to-the-datalayer-with-ctrlx-ide-python-blockly-2qxKSh23h7gZXGo)
- [IDE and Data Layer](https://community.boschrexroth.com/ctrlx-works-mpp856pr/post/ctrlx-automation---ide-how-would-i-pull-data-from-the-data-layer-f58rg2nnpQzpHpA)
- Device-local IDE reference: `https://<ctrlx-core>/tiger/docs.html#doc:reference`
- Device-local Blockly reference: `https://<ctrlx-core>/tiger/docs.html#doc:blocks`
- [Read/create Data Layer variables with IDE Python/Blockly](https://community.boschrexroth.com/ctrlx-works-mpp856pr/post/read-create-variables-to-the-datalayer-with-ctrlx-ide-python-blockly-2qxKSh23h7gZXGo)
- [IDE and Data Layer](https://community.boschrexroth.com/ctrlx-works-mpp856pr/post/ctrlx-automation---ide-how-would-i-pull-data-from-the-data-layer-f58rg2nnpQzpHpA)
