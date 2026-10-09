---
name: drive-connect
description: "Use when inspecting, connecting, troubleshooting, or verifying the ctrlX DRIVE Connect App (DCA) through Data Layer nodes, MCP, or the documented REST fallback. Covers drive discovery, subdevices, SERCOS IDNs, DCA files, parameter export/import, firmware download, and Drive Overview diagnostics."
license: Proprietary. LICENSE.txt has complete terms
---

# ctrlX DRIVE connect

Use this skill for the ctrlX DRIVE Connect App (DCA) when drives must be
discovered, drive and subdevice paths must be inspected, SERCOS parameters
must be read or written, DCA files must be managed, or parameter sets and
firmware must be transferred.

Prefer the configured ctrlX MCP/Data Layer connection for all device
interactions. Use the documented REST/Data Layer route only as an emergency
fallback when the MCP workflow cannot perform the requested operation. The
fallback may be used for reads and, after explicit confirmation, for writes.
Never use an undocumented app-specific REST endpoint. Never print or persist
usernames, passwords, bearer tokens, or parameter files containing
machine-specific data. The target Data Layer metadata is authoritative for
available paths, operations, data types, limits, and task schemas.

## Data Layer access contract

Use semantic Data Layer operations through MCP whenever they are available:

| Operation | Meaning |
|---|---|
| `BROWSE` | List children or available resources |
| `READ` | Read a node value |
| `METADATA` | Read type, attributes, limits, and supported operations |
| `WRITE` | Write a variable value after inspecting metadata |
| `CREATE` or `CALL` | Invoke a method or create a resource using its declared input type |
| `DELETE` | Remove a resource or file after explicit confirmation |
| `SUBSCRIBE` | Monitor a supported realtime node when the MCP server provides it |

The exact MCP tool names are implementation details. Pass the Data Layer
address and semantic operation through the configured MCP/Data Layer
interface. If MCP cannot perform an operation, use the documented REST
fallback route shown in this skill. Report which transport was used.

For every access, select the exact target, browse when the path is not known,
read metadata before writes or calls, use the target-reported type and value
shape, and report the returned value and diagnosis. If neither MCP nor the
documented fallback can perform the operation, stop and report the capability
gap.

## Safety and change handling

Reading nodes, browsing the drive topology, and inspecting metadata are safe
without confirmation.

The following operations change the target or its stored data:

- connecting EtherCAT-scanned drives to DCA;
- writing a SERCOS IDN;
- creating, replacing, or deleting a DCA file;
- exporting a parameter set to the target;
- importing a parameter set to a target axis;
- downloading firmware;
- invoking a drive command such as `Clear error`.

For a real device, inspect first, present the exact operation and expected
effect, obtain explicit confirmation immediately before the change, apply it,
and verify the result. A parameter write or import can affect drive behavior
and machine motion. Follow the site's commissioning and machine-safety
procedure.

Never guess a drive, subdevice, parameter file, parameter type, or import
index. Use the actual resources returned by the target. An export or import is
scoped to one `subdevice-*`, which represents one axis of a multi-axis device.

## Data Layer root and discovery

The canonical interface is the ctrlX Data Layer. The following route root is
for the documented REST fallback only:

```text
/automation/api/v2/nodes
```

Browse the DCA configuration and drive collection before using a path. Prefer
the semantic operations above; the route examples are REST fallback examples:

```text
GET /automation/api/v2/nodes/drive?type=browse
GET /automation/api/v2/nodes/devices/drives?type=browse
GET /automation/api/v2/nodes/devices/drives
```

The drive collection normally returns the available drive names. After
selecting an actual drive, browse its children:

```text
GET /automation/api/v2/nodes/devices/drives/<DRIVE_NAME>?type=browse
GET /automation/api/v2/nodes/devices/drives/<DRIVE_NAME>/subdevices?type=browse
```

Use the exact drive name returned by the target. Do not select the first item
implicitly when more than one drive is available.

For DCA discovery, browse the actual network interfaces and invoke the
documented no-input browse method through MCP or the REST fallback:

```text
BROWSE drive/network-interfaces
CALL drive/network-interfaces/<INTERFACE_NAME>/browse
CALL drive/network-interfaces/browse-all
```

The result contains discovered MAC and IP information and is not yet a drive
resource. Inspect `drive/config/connections` before combining connections.
Read metadata for each browse method before invoking it. On the verified
target, the interface browse methods are Data Layer `WRITE` methods with an
optional `uint32` timeout input; the target reported a default of 1000 ms and
a maximum of 2000 ms. Use the target-reported input type and limits rather
than assuming a timeout or a no-input call.

### Recover an empty drive collection

If `devices/drives` returns an empty list, use this sequence instead of
assuming that no drive is present:

1. Browse `drive/network-interfaces` and read the metadata of the available
   interface browse methods.
2. Invoke `browse-all`, or the exact interface browse method when only one
   interface is relevant. Record the exact MAC and IP returned by the target.
3. Browse `drive/config/connections` and compare the discovered connection
   with the returned address. A connection entry is only a discovered or
   stored connection; it does not prove that a DCA drive resource exists.
4. If the connection is present but `devices/drives` is still empty, explain
   the effect and obtain explicit confirmation before invoking
   `drive/config/connections-to-drives`.
5. Browse `devices/drives` again and report the exact drive names returned.
6. If the collection remains empty, inspect the EtherCAT scan and physical
   topology in Drive Engineering or IO Engineering. Do not change the
   EtherCAT master state as a generic recovery step.

After a ctrlX CORE restart, DCA restart, firmware update, or connection
expiration, repeat this discovery and connection sequence. A previously
stored address such as `172.31.254.1` may exist below
`drive/config/connections` while `devices/drives` remains empty.

## Connect scanned drives to DCA

After discovery or an EtherCAT scan, DCA may need an explicit connection to
the discovered drives. Use the semantic
`CALL drive/config/connections-to-drives` operation first. The documented REST
fallback has no request body:

```text
PUT /automation/api/v2/nodes/drive/config/connections-to-drives
```

Treat this as a target configuration change. Before executing it, explain
that it connects the currently discovered drives to DCA and obtain explicit
confirmation, including when the REST fallback is used. Afterwards, browse
and read `devices/drives` again and report the actual drive names.

If the drive collection remains empty, inspect the EtherCAT scan and physical
connection in Drive Engineering or IO Engineering. An error containing
`no such file or directory` and a path ending in
`DRIVEConnect/connections` normally means that no scan or DCA connection has
been created yet.

## Drive and subdevice paths

The relevant DCA structure is:

```text
devices/drives/<DRIVE_NAME>/
  export-parameter
  firmware-download
  import-parameter
  subdevices/
    subdevice-0/
      export-parameter
      identify
      import-parameter
      sercos-idns/
        S-0-0040.0.0
        S-0-0100.0.0
        S-0-0101.0.0
```

Use one `subdevice-*` per axis. For a multi-axis device, discover and verify
the available subdevices instead of assuming that `subdevice-0` is the
requested axis.

For a selected drive and subdevice, construct:

```text
/automation/api/v2/nodes/devices/drives/<DRIVE_NAME>/subdevices/<SUBDEVICE>/sercos-idns
```

The documented SIP form can include the IP address between the subdevice and
the resource:

```text
devices/drives/<DRIVE_NAME>/subdevices/<SUBDEVICE>/<IP_ADDRESS>/...
```

Use the exact path returned by target browsing. A local EtherCAT resource may
expose the shorter form.

## Firmware download

This workflow updates the firmware of the selected drive. It does not update
ctrlX OS or the ctrlX CORE firmware. A firmware update can interrupt drive
communication, reset the drive, and affect machine operation. Verify the
machine-safe state and obtain explicit confirmation immediately before the
download.

Before starting:

1. Browse `devices/drives` and select the exact drive.
2. Browse its `subdevices` and verify the affected axis when the target
   exposes more than one.
3. Locate the exact firmware file in the DCA file store. The DCA App 03VRS
   documentation describes the active configuration folder `DRIVEConnect`
   and the Data Layer file collection
   `driveconnect/filesystem/drivefirmware`. Use the path and file name
   returned by the target; do not assume that a `drivefirmware` subfolder is
   exposed.
4. When using the WebDAV fallback for a read-only file listing, issue
   `PROPFIND` with `Depth: 1` against:

   ```text
   https://<DEVICE>/solutions/webdav/appdata/DRIVEConnect/
   ```

   Select the actual firmware file (normally the `.fwa` file) and exclude
   `connections/`, `internal/`, and `.par` parameter files. Do not infer a
   firmware version from a parameter-file name.
   If no exact `.fwa` file is returned, stop before calling
   `firmware-download`. Upload the file to the DCA `DRIVEConnect` storage
   first, then browse again and verify its exact name, type, and size.
5. Read metadata from
   `devices/drives/<DRIVE_NAME>/firmware-download`. The verified DCA node
   exposes `CREATE`, a string `createType`, and a program-task readout type.
   Use the target metadata if it differs.
6. Read the EtherCAT master state and status before starting. On the verified
   target, the expected state was `OPERATING`, current/requested state `op`,
   and master status `0`. Use the target-reported values and do not change
   the master state blindly as a firmware workaround.

Start the update through MCP with a `CREATE` operation on the selected
`firmware-download` node:

```json
{
  "type": "string",
  "value": "<EXACT_FIRMWARE_FILE_NAME>"
}
```

The documented REST fallback is:

```text
POST /automation/api/v2/nodes/devices/drives/<DRIVE_NAME>/firmware-download
```

The response returns a task ID. Poll
`devices/drives/<DRIVE_NAME>/firmware-download/<TASK_ID>` until
`state=done` and `progress=100`. Surface the returned diagnosis if the task
fails; never report a firmware update as successful from the create response
alone. After completion, browse `devices/drives` again and verify that the
drive is still available.

If the task reaches a high progress value but finishes with `state=failed`,
the firmware update is not successful. Report the task diagnosis and verify
the drive again; do not infer success from the presence of the firmware file
or from the transfer progress alone.

### Configuration Mode fallback

If the task fails with `application not ready`, do not retry blindly. Some
SERCOS parameters are writable only in Configuration Mode (CM).

1. Read the complete `S-0-0420.0.0` node and its `/data` metadata. Continue
   only when the target identifies it as `C0400 Activate configuration mode`,
   `/data` is writable, and the machine is safe to change modes.
2. Use the value representation reported and accepted by the target. On the
   verified DCA target, the command word was accepted as an `arstring` with
   bits 0 and 1 set:

   ```json
   {
     "type": "arstring",
     "value": ["0b0000.0000.0000.0011"]
   }
   ```

   Read the value back before continuing. The same target rejected a
   `uint32` envelope with `DL_TYPE_MISMATCH`, despite advertising
   `uint32` as its write input type.
3. Reset the procedure command after it has been accepted:

   ```json
   {
     "type": "arstring",
     "value": ["0b0000.0000.0000.0000"]
   }
   ```

   Read it back and report any diagnosis. Do not reuse this bitstring or
   payload on another drive without checking that drive's node name,
   metadata, and current value.
4. Re-read the firmware-download metadata and obtain a new explicit
   confirmation before retrying the firmware update.

## Read SERCOS parameters

The complete IDN node provides metadata such as name, unit, limits, access
rights, and data type. Prefer these semantic operations:

```text
READ <DCA_SUBDEVICE_PATH>/sercos-idns/<SERCOS_IDN>
METADATA <DCA_SUBDEVICE_PATH>/sercos-idns/<SERCOS_IDN>
READ <DCA_SUBDEVICE_PATH>/sercos-idns/<SERCOS_IDN>/data
```

The documented REST fallback is:

```text
GET /automation/api/v2/nodes/devices/drives/<DRIVE_NAME>/subdevices/<SUBDEVICE>/sercos-idns/S-0-0040.0.0
GET /automation/api/v2/nodes/devices/drives/<DRIVE_NAME>/subdevices/<SUBDEVICE>/sercos-idns/S-0-0040.0.0?type=metadata
GET /automation/api/v2/nodes/devices/drives/<DRIVE_NAME>/subdevices/<SUBDEVICE>/sercos-idns/S-0-0040.0.0/data
```

Direct DCA IDN paths use the `.0.0` suffix. Apply the same path convention to
`P-0-xxxx` parameters. If a read returns `DL_INVALID_ADDRESS`, verify the
drive connection, drive name, subdevice, IP-qualified path variant, IDN spelling, and suffix before
reporting the parameter as unavailable.

DCA also documents `dataAndAttribute`, `dataAsBytes`, `dataState`,
`descAsBytes`, and `everythingAsBytes`. Use those nodes when the user
requests attributes, raw bytes, state, description, or the complete raw
representation.

## Write SERCOS parameters

Before a write:

1. Read the complete IDN node and its metadata.
2. Confirm the target drive, subdevice, IDN, current value, requested value,
   and expected effect with the user.
3. Use the target-reported data type and value shape; never assume that all
   IDNs are strings or numbers.

For an IDN whose metadata reports an `arstring` value, the request shape is:

```json
{
  "type": "arstring",
  "value": ["5.0"]
}
```

Write the `data` node using the Data Layer operation documented by its
metadata, then read the same `data` node again. Report both the returned value
and any Data Layer diagnosis. A REST fallback write requires a new explicit
confirmation immediately before the request. Do not treat an empty response
as proof that the write succeeded.

## Export a parameter set

Before starting an export, verify that the fieldbus and S/IP communication
are ready. Read the EtherCAT master state and status through the available
target nodes. On the verified target, the expected values were:

```text
system state: OPERATING
master currentState: op
master requestedState: op
master status: 0
```

Use the target-reported state names and status semantics when they differ.
Read at least one known available SERCOS IDN, and read `S-0-0192.0.0` when
the target exposes it. If these reads return HTTP 500, a timeout, or
`S/IP: Timeout`, stop the export and restore EtherCAT/S/IP readiness first.
Do not treat an export failure caused by an unavailable fieldbus as a payload
or file-name problem.

Ask which scope is wanted before starting an export:

```text
All available drive parameters
Standard Backup parameter set
```

If the user only says "backup", ask whether all parameters or only the
standard backup set should be exported. Read the target metadata before
mapping either choice to a payload field.

Export from the selected drive or subdevice with the target-declared input
type. The following is only an example when the target metadata explicitly
reports these fields:

```json
{
  "type": "object",
  "value": {
    "fileName": "<EXACT_FILE_NAME>",
    "backupType": "<TARGET_DECLARED_SCOPE_VALUE>"
  }
}
```

Call the selected `export-parameter` node with the target-declared Data Layer
`CREATE`/`CALL` operation, preferably through MCP. The DCA App 03VRS manual
delegates the exact input schema to the ctrlX OS Data Layer Version 3
reference; do not assume fields such as `backupType` or `fileName` without
reading metadata. On the verified target, `ExportParFile` declared the
string enum values `"All"` and `"Backup"`; do not replace those values with
numeric codes unless the target metadata explicitly requires numbers. A REST
fallback export requires explicit confirmation.

Check whether the exact target file name already exists in the DCA file store
before creating it. DCA does not overwrite an existing file with the same
name. If a previous failed task left a zero-byte or partial file, mark it as
invalid; use a new name or obtain explicit confirmation before deleting the
old file.

The response returns an asynchronous task ID. Poll the task below the same
`export-parameter` node until `state=done` and `progress=100`.
If the task fails, report its diagnosis and do not claim that a file was
created.

If an `All` export fails with `context deadline exceeded` for one specific
SERCOS parameter:

1. Read that exact parameter separately and report the returned diagnosis.
2. Treat any file left behind by the failed task as incomplete, even if it is
   visible in the DCA file store. Do not use it as a backup and do not delete
   it without explicit confirmation.
3. Ask whether the user wants the Standard Backup parameter set instead. Do
   not switch scopes silently.
4. If the user selects Standard Backup, use `backupType: "Backup"` when the
   target schema reports that enum, choose a new file name, obtain explicit
   confirmation, poll the new task to completion, and verify the resulting
   file in the DCA file store.

If an export fails with `S/IP: Timeout`, HTTP 500 on a known IDN, or an
equivalent fieldbus communication error, do not retry blindly. Re-read the
EtherCAT master state, master status, and a representative SERCOS IDN. Retry
only after communication is ready and only with a confirmed file name that
does not already exist.

DCA stores the result on the ctrlX CORE at:

```text
/var/snap/rexroth-solutions/common/solutions/activeConfiguration/DRIVEConnect/<FILE_NAME>
```

The directory is exposed through WebDAV:

```text
https://<DEVICE>/solutions/webdav/appdata/DRIVEConnect/
```

List the directory with WebDAV `PROPFIND` and `Depth: 1`. Include regular
parameter files whether or not they have a `.par` extension. Exclude the
`connections/` and `internal/` collections.

Prefer the DCA Data Layer filesystem for MCP and REST fallback access:

```text
BROWSE driveconnect/filesystem
READ driveconnect/filesystem/<FILE_NAME>
```

## Import a parameter set

An import overwrites parameters on the selected target axis and can affect
machine behavior. Before proposing an import:

1. Browse `devices/drives` and present the actual available drives.
2. For the selected drive, browse `subdevices` and present the actual axes.
3. Browse `driveconnect/filesystem` and identify the exact parameter file.
4. Ask the user to confirm the exact drive, subdevice, file name, and
   parameter-set scope.
5. Read the import node metadata and use its declared input type and task
   schema. Do not assume an import index or parameter-set field.

If there is more than one drive, subdevice, or parameter file, stop and ask
the user to choose. Never choose the first, newest, or most recently created
item implicitly. If no regular parameter file is present, stop.

For the confirmed file and subdevice, use the target-declared input type. This
is only an example when metadata confirms the `fileName` and `setIndex` fields:

```json
{
  "type": "object",
  "value": {
    "fileName": "<EXACT_FILE_NAME>",
    "setIndex": 0
  }
}
```

Call the selected `import-parameter` node with the target-declared Data Layer
`CREATE`/`CALL` operation, preferably through MCP. A REST fallback import
requires explicit confirmation immediately before the request. Poll the
returned task until `state=done` and `progress=100`.
Report a failed diagnosis explicitly. After a successful import, read back
important parameter values and report the verification result.

If Configuration Mode was activated for the import, keep it active for the
entire asynchronous import task. Reset C0400 only after the task reports both
`state=done` and `progress=100`; a task with `state=failed` and
`progress=100` is not successful. If the task fails, aborts, or cannot be
verified, do not reset C0400 automatically. Report that Configuration Mode
remains active and wait for an explicit next action.

## Troubleshooting

- If `devices/drives` is empty or an IDN read returns `DL_INVALID_ADDRESS`,
  verify the DCA connection first, then inspect the EtherCAT scan and physical
  topology only if the collection remains empty.
- The DCA connection may not remain available after a ctrlX CORE restart or
  after the connection expires. Repeat the connection workflow only after
  confirming the current target and expected effect.
- Always use the `.0.0` suffix for direct DCA SERCOS IDN paths.
- A multi-axis device exposes one `subdevice-*` node per axis; never combine
  parameter files from different axes.
- If a firmware task fails with `application not ready`, check whether the
  affected SERCOS procedure command requires Configuration Mode before
  retrying. Do not force an EtherCAT master state transition as a generic
  workaround.
- Surface MCP, REST fallback, and Data Layer errors with the affected operation.
  Never replace an error with an empty or success-shaped fallback.
- If neither MCP nor the documented REST/Data Layer fallback can perform the
  requested operation, stop and report the missing capability.
