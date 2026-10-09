---
name: datalayer
description: "Extended information about using the ctrlX Data Layer. E.g. for subscribing to realtime values."
license: Proprietary. LICENSE.txt has complete terms
---

# Data Layer

## Logical paths versus transport

Data Layer paths are logical node addresses, not REST URLs. For example, the
IDE app inventory node is:

```text
system/apps/installed/rexroth-ide
```

IDE Blockly/Python uses the documented namespace functions and normally writes
the node path with a leading slash:

```python
DatalayerLib.read("/system/apps/installed/rexroth-ide/title")
```

When a REST gateway is used only as a transport fallback, the URL is formed
from `/automation/api/v2/nodes/` plus the logical path. Do not invent an
`ide/...` Data Layer root just because the app is named IDE.

Always BROWSE and read metadata before using an unfamiliar path. Use the
dedicated IDE reference for allowed Blockly/Python functions.

## Subscription

The tool `datalayer_subscribe` can be used to subscribe (sample) data.

### Lossless Subscription

Certain realtime data layer nodes can be sampled lossless. Lossless sampling cabability is signaled in metadata of the data layer when the extension attribute `qos.lossless` is set to `true`.

Lossless sampling can be activated by setting the `samplingInterval` argument of `datalayer_subscribe` to `0`.

All nodes which are part of realtime data layer can be sampled lossless.

To get a list of all realtime data layer nodes, READ th node  `datalayer/nodesrt`.

For each realtime data node the following sub nodes exist:

| Operation | Path | Node Description | Advanced description |
|-----------|------|-------------|----------------|
| READ | `<realtime data layer node>/map` | json object which describes the process data byte array | |
| READ | `<realtime data layer node>/data` | Complete realtime data byte array | |
| BROWSE | `<realtime data layer node>/data` | The decoded variables of the byte array as individual variables | Automatically decoded based on the map. These variables can be subscribed lossless |

## System Scheduler State

Read the current system scheduler state before any operation that changes the device state:

```text
GET /automation/api/v2/nodes/scheduler/admin/state
```

For ctrlX OS 4.6 package-management workflows, switch the scheduler with the dedicated scheduler endpoint rather than a generic v2 Data Layer `POST`:

```text
PUT /automation/api/v1/scheduler/admin/state?format=json
Content-Type: application/json

{"state":"SERVICE"}
```

Verify the transition by reading `scheduler/admin/state` again. Restore the state that was active before the operation in a `finally`/cleanup path. On ctrlX OS 4.6, restoring `OPERATING` uses the same endpoint with `{"state":"OPERATING"}`; do not send an older `action`/`parameters` payload to this state node unless the target API explicitly supports it.

## OPC UA Server

Use the dedicated `opcua-server` skill for the OPC UA Server App. Its Data Layer root is `opcuaserver`; browse it and read node metadata before assuming a path or write operation:

```text
GET /automation/api/v2/nodes/opcuaserver?type=browse
GET /automation/api/v2/nodes/opcuaserver/<path>?type=metadata
```

The OPC UA skill documents endpoint/security, certificate, memory, session, subscription, redundancy, diagnostics, and companion-model paths, including their read-only versus writable operations and required data types.

## OPC UA Client

Use the dedicated `opcua-client` skill for the OPC UA Client App. Its static Data Layer root is `opcuaclient`; client sessions are dynamic resources created below `opcuaclient/<clientSession>`:

```text
GET /automation/api/v2/nodes/opcuaclient?type=browse
GET /automation/api/v2/nodes/opcuaclient/<path>?type=metadata
```

The client skill documents session creation, endpoint/security selection, user tokens, timeouts, reconnect, redundancy, subscription batching, certificates, IPC, traces, persistence, and read-only status paths.
