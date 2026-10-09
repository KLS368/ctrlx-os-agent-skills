---
name: opcua-client
description: "Use when inspecting, configuring, troubleshooting, or verifying the ctrlX OPC UA Client App and its Data Layer nodes. Covers ctrlX OS 4.6.2 client sessions, endpoints, security, identities, timeouts, reconnect, redundancy, subscriptions, certificates, memory, traces, persistence, permissions, and safe read/write handling."
license: Proprietary. LICENSE.txt has complete terms
---

# ctrlX OPC UA Client

Use this skill for the ctrlX OPC UA Client App, especially when the user asks where a client setting is located, how to create a session, which Data Layer paths exist, or how the WebUI configuration relates to the Data Layer. Use the `authentication` skill before accessing a device and never print or persist credentials, OPC UA passwords, or bearer tokens.

The OPC UA Client Release Notes are a change log, not a complete Data Layer reference. Always browse and read metadata on the target device before making assumptions. The target-specific Data Layer metadata is authoritative for available paths, data types, and operations.

## Discovery and permissions

The OPC UA Client Data Layer root is:

```text
opcuaclient
```

Browse and inspect nodes with:

```text
GET /automation/api/v2/nodes/opcuaclient?type=browse
GET /automation/api/v2/nodes/opcuaclient/<path>?type=browse
GET /automation/api/v2/nodes/opcuaclient/<path>?type=metadata
GET /automation/api/v2/nodes/opcuaclient/<path>
```

The static folders are:

```text
admin
certificate-configuration
general-configuration
ipc-configuration
licenses
memory-diagnostics
trace-configuration
```

Client sessions are dynamic resources below:

```text
opcuaclient/<clientSession>/...
```

Do not assume that a missing dynamic session is an error. Read `opcuaclient/general-configuration/number-of-clients`; if it is zero, no client session currently exists and no session-specific subtree can be inspected.

## Release-note context

For OPC UA Client App 4.6.2:

- Version 4.6.2 documents third-party security fixes, legacy enumerations described only by `EnumStrings`, correct selection of unsecure endpoints, cleanup of MonitoredItems after reconnect, and handling of invalid server operation limits. These are behavior fixes, not global writable settings.
- Version 4.6.1 documents the current subscription-license model and the `UA_ReadList`/`UA_Writelist` bulk-request change in the CXA_OpcUaClient library.
- Version 4.6.0 documents WebUI memory status/configuration, server `MaxMonitoredItemsPerCall` handling, and batching of MonitoredItem add/remove requests.
- Version 4.4.1 documents ctrlX OS 4.x/core24, the current OPC UA stack, floating licenses, cold-failover redundancy, and ECC-nistP256/ECC-nistP384 support.

Do not invent a Data Layer setting for behavior fixes such as enum decoding, invalid operation-limit handling, or session cleanup.

## Creating a client session

The root is a Data Layer collection with this create type:

```text
opcuaclient
→ types/opcuaclient/client-configuration
```

Create a session only when the user explicitly requests it:

```text
POST /automation/api/v2/nodes/opcuaclient
```

The required fields are:

```text
name
endpointUrl
```

The supported configuration fields are:

```text
persistent
autoReconnect
sessionConfiguration
timeoutConfiguration
redundancyConfiguration
subscriptionConfiguration
```

`persistent=true` persists the client data and loads it when the app or controller starts. A persistent session corresponds to the Release Notes workflow that uses **App data management → Save as archive**.

### Session security and identity

`sessionConfiguration` supports:

```text
userToken
messageSecurityMode
securityPolicy
localeIds
```

Message security modes:

```text
BESTAVAILABLE
NONE
SIGN
SIGNENCRYPT
```

Security policies:

```text
BESTAVAILABLE
NONE
BASIC128RSA15
BASIC256
BASIC256SHA256
AES128_SHA256_RSAOAEP
AES256_SHA256_RSAPSS
NISTP256
NISTP384
```

User identity token types:

```text
NONE
TokenAnonymous
TokenUserPassword
TokenCert
```

For an explicitly unsecure connection, select both `messageSecurityMode=NONE` and `securityPolicy=NONE`. The 4.6.2 fix ensures that the requested unsecure endpoint is selected regardless of the order in the server's `GetEndpoints` response.

Never put a real username or password in documentation, logs, or an example command. Use placeholders and obtain credentials securely at execution time.

On the ctrlX OPC UA Server, an Anonymous token may be advertised for discovery while Anonymous `ActivateSession` is rejected with `BadIdentityTokenInvalid` / `DL_PERMISSION_DENIED`. For a real client session over Security None, use:

```text
userIdentityToken_type = TokenUserPassword
messageSecurityMode    = NONE
securityPolicy         = NONE
```

Do not switch to the `NONE` user-identity variant as a workaround unless the target client schema explicitly documents it; on the tested ctrlX Client 3.6.3 schema it is not a valid replacement for `TokenUserPassword`.

### Session timeout, reconnect, and redundancy

`timeoutConfiguration` supports these millisecond values:

```text
browseCallTimeout
discoveryTimeout
publishTimeout
readCallTimeout
sessionTimeout
watchdogTimeout
writeCallTimeout
callCallTimeout
reconnectDelay
```

`autoReconnect=true` reconnects a disconnected session using `reconnectDelay`.

`redundancyConfiguration` supports:

```text
support: None | Cold | Warm | Hot | Transparent | HotAndMirrored
samplingInterval: milliseconds
```

`support=Cold` corresponds to the cold-failover functionality described in the Release Notes. A server must provide the corresponding redundancy information; selecting the mode alone does not create redundancy.

### Subscription batching

`subscriptionConfiguration.addRemoveMonitoredItemDelay` is an integer in milliseconds:

```text
0    = execute every Add/Remove request immediately
100  = collect requests for 100 ms before sending a combined request
```

The Release Notes show the persisted archive key:

```text
settings/opcuaclient/clients_configuration.conf
clients/0/add_remove_monitered_item_delay = 100
```

The spelling `monitered` is the spelling in that file/documentation. The Data Layer create schema uses the correctly camel-cased field `addRemoveMonitoredItemDelay`.

The client reads and honors the OPC UA server's `MaxMonitoredItemsPerCall`; that operation limit is not a separate client write setting.

### Security None connection checklist

For a deliberate diagnostic/test connection to a ctrlX OPC UA Server:

```text
1. Delete the existing client session.
2. Configure server policy 0 / modeNone and a Username token with policy 0.
3. Restart the server app in SERVICE state and restore the prior scheduler state.
4. Create/update the client session with TokenUserPassword + NONE/NONE.
5. Call the no-argument connect method.
6. Require CONNECTED, server currentSessionCount >= 1, zero security rejects, and a successful browse.
```

The Package Manager restart task is:

```json
{
  "action": "restart",
  "parameters": {
    "service": "rexroth-opcua-server",
    "reload": "true"
  }
}
```

Security None sends credentials and data unencrypted. Keep this workflow limited to an isolated test network and never leave it enabled for a production connection without explicit authorization.

### Using a scope-restricted server user

When the server controller uses a user-defined Data Layer scope, configure the client session with the dedicated restricted user's credentials, not the administrator credentials. The scope must be granted on the server controller; the client controller only carries the OPC UA identity token.

After changing the user's scopes or password:

```text
1. Obtain a fresh Identity Manager token / reconnect the OPC UA session.
2. Read an allowed server node.
3. Read a deliberately denied node and require DL_SEC_UNAUTHORIZED.
4. Browse the server address space and confirm that only the intended subtree is usable.
```

Do not add `rexroth-device.all.rwx` or `rexroth-automation.datalayer.rw` to the restricted user, because those scopes override the intended restriction.

## Connecting to another ctrlX OPC UA Server

Use this workflow when the OPC UA Client on one controller must connect to an OPC UA Server on another controller. Do not assume both controllers run the same app version; read the installed package versions and the target `types/opcuaclient/client-configuration` schema first. Older clients may not support newer fields such as redundancy or subscription batching.

### Preflight

On the server controller, read:

```text
opcuaserver/server-status/state
opcuaserver/endpoint-configuration/url
opcuaserver/endpoint-configuration/sec-configs
opcuaserver/endpoint-configuration/user-token-configs
```

Select a combination that is present on both sides. For example, a server configuration with policy ID `3`, `modeSignAndEncrypt=true`, and username token `{type: 1, policyId: 3}` is compatible with:

```text
securityPolicy      = BASIC256SHA256
messageSecurityMode = SIGNENCRYPT
userIdentityToken   = TokenUserPassword
```

Do not weaken a secure server to `None` as a shortcut. Verify TCP reachability to the server endpoint from the client network before creating the session.

### Create and connect

The Data Layer REST create body must use the generic `Data` envelope. Sending the client configuration without `type` and `value` fails with `DL_TYPE_MISMATCH` / `Field type not found`:

```json
{
  "type": "object",
  "value": {
    "name": "client-session-name",
    "endpointUrl": "opc.tcp://<server-address>:4840",
    "persistent": true,
    "autoReconnect": true,
    "sessionConfiguration": {
      "userToken": {
        "userIdentityToken_type": "TokenUserPassword",
        "userIdentityToken": {
          "username": "<username>",
          "password": "<password>"
        }
      },
      "messageSecurityMode": {
        "messageSecurityMode": "SIGNENCRYPT"
      },
      "securityPolicy": {
        "securityPolicy": "BASIC256SHA256"
      }
    }
  }
}
```

Create it with:

```text
POST /automation/api/v2/nodes/opcuaclient
```

After creation, explicitly invoke:

```text
PUT /automation/api/v2/nodes/opcuaclient/<client-session>/connect
```

For this method, send no request body. Sending `{"type":"empty"}` is interpreted as an argument and can fail with `Too many arguments were provided`.

Poll:

```text
GET /automation/api/v2/nodes/opcuaclient/<client-session>/state
```

The expected state is `CONNECTED`. Keep the session if it is persistent and the user requested the connection; delete it only on explicit cleanup request.

When changing an existing session from secure mode to Security None, delete the old session first or update every session-security field together. Reconnect only after the server has applied its endpoint configuration.

### Certificate trust troubleshooting

If `connect` returns `DL_COMMUNICATION_ERROR` with `An error occurred verifying security`, inspect the Certificate Manager on the server:

```text
GET /certificate-manager/api/v2/applications
GET /certificate-manager/api/v2/applications/rexroth-opcua-server/certificates
```

Find the exact client certificate by its subject/common name and confirm that it is in category `rejected`. Never move all rejected certificates or trust a certificate based only on its filename.

Move only the verified client certificate to the server app's `trusted` category with the Certificate Manager task API:

```json
{
  "action": "move",
  "parameters": {
    "itemId": "<verified-certificate-id>",
    "itemType": "certificate",
    "srcApplicationId": "rexroth-opcua-server",
    "dstApplicationId": "rexroth-opcua-server",
    "dstCategory": "trusted"
  }
}
```

```text
POST /certificate-manager/api/v2/tasks
GET  /certificate-manager/api/v2/tasks/<task-id>
```

Accept task responses with HTTP `200` or `201`, then poll until `state=done`. Retry `connect` only after the certificate task has completed.

### End-to-end verification

Verify all of the following:

```text
opcuaclient/<client-session>/state                    = CONNECTED
opcuaserver/server-diagnostics/server-diagnostics-summary/currentSessionCount >= 1
opcuaserver/server-diagnostics/server-diagnostics-summary/securityRejectedRequests = 0
opcuaserver/server-diagnostics/server-diagnostics-summary/securityRejectedSession = 0
```

Browse a known server address-space root through the client session, for example:

```text
GET /automation/api/v2/nodes/opcuaclient/<client-session>/i=85?type=browse
```

Do not report success based only on a created session. The client state, server session counter, and an address-space browse must agree.

## Reading server data through the client

The client exposes the remote OPC UA address space below the dynamic session resource:

```text
opcuaclient/<client-session>/...
```

Use this sequence:

1. Read the session state and require `CONNECTED`.
2. Browse `i=85` (the standard Objects folder).
3. Read standard OPC UA nodes directly when known.
4. For the ctrlX Data Layer address space, browse first and follow the exact NodeIds returned by the server.

Useful standard NodeIds on a ctrlX OPC UA Server include:

```text
i=2255  NamespaceArray
i=2256  ServerStatus / BuildInfo
i=2275  ServerDiagnosticsSummary
```

Examples:

```text
GET /automation/api/v2/nodes/opcuaclient/<client-session>/i=85?type=browse
GET /automation/api/v2/nodes/opcuaclient/<client-session>/i=2255
GET /automation/api/v2/nodes/opcuaclient/<client-session>/i=2256
GET /automation/api/v2/nodes/opcuaclient/<client-session>/i=2275
```

The remote ctrlX Data Layer is normally discovered by browsing:

```text
GET /automation/api/v2/nodes/opcuaclient/<client-session>/ns=8;s=opcuaserver?type=browse
```

The result can contain child NodeIds with a different namespace index, for example:

```text
ns=2;s=opcuaserver/server-status2
```

Do not reconstruct or simplify these paths. Append the exact returned NodeId segment to the client path. For example:

```text
GET /automation/api/v2/nodes/opcuaclient/<client-session>/ns=8;s=opcuaserver/ns=2;s=opcuaserver/server-status2
GET /automation/api/v2/nodes/opcuaclient/<client-session>/ns=8;s=opcuaserver/ns=2;s=opcuaserver/server-status2?type=browse
```

Composite OPC UA objects may return `DL_FAILED` / `The attribute is not supported for the specified Node` when read directly through the Data Layer REST projection. Browse the object and read its returned leaf NodeIds instead:

```text
GET /automation/api/v2/nodes/opcuaclient/<client-session>/ns=8;s=opcuaserver/ns=2;s=opcuaserver/server-status2/ns=2;s=opcuaserver/server-status2/State
```

The response is a typed Data Layer value, for example:

```json
{
  "type": "string",
  "value": "Running"
}
```

A Data Layer browse/read through the client is an OPC UA read of the remote server; it is not a local read of the client controller's own `opcuaserver` tree.

### Read, write, and subscribe safely

Before writing a remote value, request metadata for the exact leaf and require a writable access level on the OPC UA server:

```text
GET /automation/api/v2/nodes/opcuaclient/<client-session>/<exact-node>?type=metadata
```

Only then use the declared Data Layer type in a `PUT` body. Do not write to composite objects. For subscriptions, configure the client session's subscription settings and create monitored items through the client API/library; verify the resulting server subscription counters and data flow. Inspection requests must not change remote values or client configuration.

## Global Data Layer configuration

### General configuration

Writable:

```text
opcuaclient/general-configuration/address-placeholders
```

This object contains the NodeId prefixes used below a client session:

```json
{
  "ns": "ns=",
  "string": "s=",
  "integer": "i=",
  "guid": "g=",
  "opaque": "b="
}
```

Read-only:

```text
opcuaclient/general-configuration/error-code-mapping
opcuaclient/general-configuration/max-number-of-clients
opcuaclient/general-configuration/max-number-of-subscriptions
opcuaclient/general-configuration/number-of-clients
```

`error-code-mapping` maps Data Layer results to OPC UA status codes. The max-count and current-count nodes are status/capability information, not write targets.

### IPC and memory

Writable:

```text
opcuaclient/ipc-configuration/ipc-size
opcuaclient/ipc-configuration/num-messages
opcuaclient/ipc-configuration/num-queues
opcuaclient/ipc-configuration/num-services
opcuaclient/ipc-configuration/queue-size
```

The folder metadata states that changes require an OPC UA Client App restart.

Read-only diagnostics:

```text
opcuaclient/memory-diagnostics/ipc-heap
opcuaclient/memory-diagnostics/ipc-heap/free-mem
opcuaclient/memory-diagnostics/ipc-heap/used-mem
opcuaclient/memory-diagnostics/ipc-heap/max-used-mem
opcuaclient/memory-diagnostics/ipc-heap/total-mem
opcuaclient/memory-diagnostics/object-pools
```

The IPC heap diagnostic values are in KB. The configured IPC size is a separate configuration value; use the target metadata and WebUI labels rather than guessing units.

### Certificates

Writable:

```text
opcuaclient/certificate-configuration/certificates/0/days-valid
opcuaclient/certificate-configuration/certificates/1/days-valid
opcuaclient/certificate-configuration/certificates/2/days-valid
```

Certificate metadata is read-only:

```text
algorithm
certificate
create
key
key-length
key-usage
store
valid-from
valid-to
```

Use the WebUI certificate store for certificate management rather than writing certificate or key paths directly.

### Licenses, traces, and persistence

License status is read-only:

```text
opcuaclient/licenses/active-state
opcuaclient/licenses/active-state-fb
opcuaclient/licenses/name
opcuaclient/licenses/version
```

Trace configuration is writable:

```text
opcuaclient/trace-configuration/facility-mask
opcuaclient/trace-configuration/trace-level
```

The `trace/rexroth-opcua-client` provider must also be enabled for trace messages to be emitted.

Load a saved configuration through the program:

```text
opcuaclient/admin/cfg/load
→ types/datalayer/persistence_param
```

This is a configuration-load task, not a normal setting. Use it only when the user explicitly requests an archive/configuration load.

Read client exceptions with:

```text
opcuaclient/admin/exceptions
opcuaclient/admin/exceptions/original
```

## REST write and create shapes

Read metadata before every write:

```text
GET /automation/api/v2/nodes/opcuaclient/<path>?type=metadata
```

For a primitive writable node, use its declared `writeType`:

```json
{
  "type": "uint32",
  "value": 100
}
```

For a client session, use the declared collection `createType` and read back the created dynamic session path. Do not create a client session during inspection-only requests.

The `connect` method is the exception to the usual typed write examples: it is a no-argument method and must be called with an empty request body.

## Inspection baseline

A read-only inspection of ctrlX OS 4.6.2 on `192.168.88.242` found:

```text
Package: rexroth-opcua-client 4.6.2
Package health: okay
Enabled: true
License: active
number-of-clients: 0
max-number-of-clients: 50
max-number-of-subscriptions: 50
```

The baseline is device-specific and can change. Re-read values before using them; do not treat them as defaults for another controller.
