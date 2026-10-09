---
name: opcua-server
description: "Use when inspecting, configuring, troubleshooting, or verifying the ctrlX OPC UA Server App and its Data Layer nodes. Covers ctrlX OS 4.6.2 endpoint, security, certificate, memory, session, subscription, redundancy, diagnostics, companion-model paths, permissions, and safe read/write handling."
license: Proprietary. LICENSE.txt has complete terms
---

# ctrlX OPC UA Server

Use this skill for the ctrlX OPC UA Server App, especially when the user asks where a setting is located, which Data Layer paths exist, or how the WebUI and Data Layer configuration correspond. Use the `authentication` skill before accessing a device and never print or persist credentials or bearer tokens.

The OPC UA Server Release Notes are a change log, not a complete Data Layer reference. Always browse and read metadata on the target device before making assumptions. The target-specific Data Layer metadata is authoritative for available paths, data types, and operations.

## Discovery and permissions

The OPC UA Server Data Layer root is:

```text
opcuaserver
```

Browse and inspect nodes with:

```text
GET /automation/api/v2/nodes/opcuaserver?type=browse
GET /automation/api/v2/nodes/opcuaserver/<path>?type=browse
GET /automation/api/v2/nodes/opcuaserver/<path>?type=metadata
GET /automation/api/v2/nodes/opcuaserver/<path>
```

The main folders are:

```text
admin
certificate-configuration
companion-model
endpoint-configuration
ipc-configuration
licenses
memory-diagnostics
redundancy-configuration
server-diagnostics
server-status
server-status2
session-configuration
subscription-configuration
trace-configuration
```

Reading normally requires the OPC UA view scope. Configuration requires the OPC UA manage scope:

```text
opcuaserver.view
opcuaserver.manage
```

The release notes also refer to the corresponding OPC UA server and PubSub role/scope mappings (`SCOPE_OPCUA_SERVER_MANAGE` and `SCOPE_OPCUA_PUBSUB_MANAGE`). Surface an authorization error; do not bypass it by using an unscoped account.

## Release-note context

For OPC UA Server App 4.6.2:

- Version 4.6.2 primarily documents security fixes in third-party components.
- Version 4.6.1 documents the WebUI memory-size unit correction to bytes, the higher Namespace 0 reference limit, and updated subscription-license handling.
- Version 4.6.0 documents WebUI memory status/configuration and fixes for OPC UA role mapping and session shutdown behavior.
- Version 4.4.1 documents the certificate-store link, ECC-nistP256/ECC-nistP384 policies, Data Layer bulk browse, health status, cold-failover support, and the current license model.

The increased Namespace 0 reference limit is an internal behavior change; do not invent a writable Data Layer path for it.

## Writable configuration

Only write after reading the current value and metadata. A metadata response exposes `writeType` or `writeInType`; use that referenced type instead of guessing.

### Endpoint and security

Writable variables and methods:

```text
opcuaserver/endpoint-configuration/bind-port
opcuaserver/endpoint-configuration/allow-deprecated-policies
opcuaserver/endpoint-configuration/sec-configs
opcuaserver/endpoint-configuration/sec-policies
opcuaserver/endpoint-configuration/user-token-configs
opcuaserver/endpoint-configuration/user-tokens
opcuaserver/endpoint-configuration/add-sec-config
opcuaserver/endpoint-configuration/remove-sec-config
opcuaserver/endpoint-configuration/add-user-token-config
opcuaserver/endpoint-configuration/remove-user-token-config
```

The advertised endpoint is read-only:

```text
opcuaserver/endpoint-configuration/url
```

Security policy IDs are defined by `types/opcuaserver/sec-configs`:

```text
0 = None
1 = Basic128Rsa15
2 = Basic256
3 = Basic256Sha256
4 = Aes128_Sha256_RsaOaep
5 = Aes256_Sha256_RsaPss
6 = NistP256
7 = NistP384
```

User token types are defined by `types/opcuaserver/user-token-configs`:

```text
0 = Anonymous
1 = Username
2 = Certificate
3 = IssuedToken
```

`sec-configs` is an object with `secConfigArray` entries containing `policyId`, `modeNone`, `modeSign`, and `modeSignAndEncrypt`. `user-token-configs` is an object with `userTokenArray` entries containing `type` and `policyId`.

The endpoint methods use these metadata types:

```text
add-sec-config             -> types/opcuaserver/sec-configs
add-user-token-config      -> types/opcuaserver/user-token-configs
remove-sec-config          -> types/datalayer/uint32
remove-user-token-config   -> types/datalayer/uint32
```

Do not enable deprecated policies without an explicit request. Changing port, endpoint security, or token configuration can disconnect clients and can require an application restart.

### Cross-controller client connections

Before connecting an external ctrlX OPC UA Client, publish or read the endpoint and security combination from the server instead of assuming defaults:

```text
opcuaserver/server-status/state
opcuaserver/endpoint-configuration/url
opcuaserver/endpoint-configuration/sec-configs
opcuaserver/endpoint-configuration/user-token-configs
```

For a common secure username connection, policy ID `3` with `modeSignAndEncrypt=true` and user token `{type: 1, policyId: 3}` maps to:

```text
BASIC256SHA256 + SIGNENCRYPT + TokenUserPassword
```

### Security None on ctrlX OS

An unencrypted endpoint uses:

```text
policyId             = 0
modeNone             = true
security policy      = None
message security     = None
```

The ctrlX OPC UA Server documentation distinguishes discovery from session activation: Anonymous is available for FindServer/GetEndpoints discovery, but Anonymous is not accepted for an OPC-UA session on this server. Use a Username token for a session, even when the channel policy is `None`.

To configure Username/Password with `None`:

1. Keep or add a `user-token-configs` entry `{type: 1, policyId: 0}`.
2. Add the index of that entry to `endpoint-configuration/user-tokens`. This node is an index array into `user-token-configs`, not a list of policy IDs.
3. Ensure `sec-configs` contains `policyId: 0` with `modeNone: true`.
4. Restart the OPC UA Server App so the endpoint configuration is applied.

The restart task requires the system scheduler to be in `SERVICE`. Save the original scheduler state, switch to `SERVICE` with the scheduler REST endpoint, restart the app through the Package Manager, restore the original state, and verify `server-status/state=RUNNING`.

Do not treat an endpoint advertised with an Anonymous token as proof that Anonymous session activation works. A client may receive `BadIdentityTokenInvalid` or `DL_PERMISSION_DENIED` during `ActivateSession`; use Username/Password instead.

Security None transmits OPC-UA data and credentials without encryption or signing. Use it only for an isolated diagnostic/test network and restore a secure policy for production.

If a client reports `DL_COMMUNICATION_ERROR` or `An error occurred verifying security`, inspect the server's Certificate Manager application:

```text
GET /certificate-manager/api/v2/applications/rexroth-opcua-server/certificates
```

The client certificate may be present as category `rejected`. Identify it by its subject/common name and certificate ID. Move only that exact certificate to `trusted` using the asynchronous Certificate Manager task:

```json
{
  "action": "move",
  "parameters": {
    "itemId": "<verified-client-certificate-id>",
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

Wait for `state=done` before asking the client to reconnect. Never trust all rejected certificates and never disable server security merely to bypass certificate verification.

### Scope-restricted OPC UA users

To expose only selected server data to an external OPC UA Client, use a separate local user on this server controller. The user must not hold `rexroth-device.all.rwx` or global Data Layer read/write scopes.

Grant the user:

```text
rexroth-opcua-server.opcua.x
datalayer.<restricted-scope>
```

Example read-only permissions:

```text
opcuaserver/server-status2/**
motion/**
```

The `datalayer.*` scope is created under `datalayer/security/scopes` and must be persisted with `datalayer/admin/cfg/save`. After granting it, the client must log in again or reconnect with a fresh token. Verify one allowed node and one denied node (`HTTP 403 / DL_SEC_UNAUTHORIZED`) before declaring the restriction effective. The scope belongs on the server controller because that is where the OPC UA token is evaluated.

### Memory and IPC

```text
opcuaserver/ipc-configuration/ipc-size
opcuaserver/ipc-configuration/num-messages
opcuaserver/ipc-configuration/num-queues
opcuaserver/ipc-configuration/num-services
opcuaserver/ipc-configuration/queue-size
```

The Release Notes state that the configured WebUI memory size is displayed in bytes. Runtime memory diagnostics remain status values in KB:

```text
opcuaserver/memory-diagnostics/ipc-heap/free-mem
opcuaserver/memory-diagnostics/ipc-heap/used-mem
opcuaserver/memory-diagnostics/ipc-heap/total-mem
opcuaserver/memory-diagnostics/ipc-heap/max-used-mem
opcuaserver/memory-diagnostics/object-pools
```

### Sessions

```text
opcuaserver/session-configuration/keep-spare-session
opcuaserver/session-configuration/lifetime-check-interval
opcuaserver/session-configuration/lifetime-max
opcuaserver/session-configuration/lifetime-min
opcuaserver/session-configuration/max-references-per-node
opcuaserver/session-configuration/max-session-calls
opcuaserver/session-configuration/num-sessions
```

The lifetime values are milliseconds. `max-references-per-node` limits references returned by Browse; this is related to, but distinct from, the Namespace 0 reference-limit improvement described in the release notes.

### Subscriptions

```text
opcuaserver/subscription-configuration/default-lossless-interval
opcuaserver/subscription-configuration/default-lossless-interval-tolerance
opcuaserver/subscription-configuration/default-lossless-rate-limit
opcuaserver/subscription-configuration/min-lifetime
opcuaserver/subscription-configuration/max-lifetime
opcuaserver/subscription-configuration/min-publishing-interval
opcuaserver/subscription-configuration/max-publishing-interval
opcuaserver/subscription-configuration/min-sampling-interval
opcuaserver/subscription-configuration/max-sampling-interval
opcuaserver/subscription-configuration/num-subscriptions
opcuaserver/subscription-configuration/num-subscriptions-per-session
opcuaserver/subscription-configuration/num-sessions-with-subscriptions
opcuaserver/subscription-configuration/num-monitoreditems
opcuaserver/subscription-configuration/num-monitoreditems-per-subscription
opcuaserver/subscription-configuration/num-notificationmessages-per-session
opcuaserver/subscription-configuration/num-publishrequests-per-session
opcuaserver/subscription-configuration/max-monitoreditem-queue-size
opcuaserver/subscription-configuration/max-monitoreditem-event-queue-size
opcuaserver/subscription-configuration/max-notifications-per-publish
opcuaserver/subscription-configuration/num-eventfields
opcuaserver/subscription-configuration/num-eventnotifiers
```

Sampling and publishing interval values are milliseconds. Lossless interval and tolerance are microseconds. The release notes describe a fix that keeps requested sampling intervals inside the configured min/max limits; preserve those limits when changing them.

### Certificates

```text
opcuaserver/certificate-configuration/ips
opcuaserver/certificate-configuration/certificates/0/days-valid
opcuaserver/certificate-configuration/certificates/1/days-valid
opcuaserver/certificate-configuration/certificates/2/days-valid
opcuaserver/certificate-configuration/certificates/3/days-valid
```

Certificate metadata such as `certificate`, `key`, `algorithm`, `key-length`, `valid-from`, and `valid-to` is read-only under this tree. Use the WebUI certificate-store link for certificate management rather than attempting to write certificate file paths.

### Companion model and Data Layer mappings

Create operations:

```text
opcuaserver/companion-model/mappings
opcuaserver/companion-model/mappings-dl-mirror
```

Their create types are:

```text
types/opcuaserver/companion-model/mapping
types/opcuaserver/companion-model/dl-mirror-mapping
```

Companion mappings use OPC UA NodeIds. Data Layer mirror mappings use `sourceUaNodeId` and `targetDlAddress`. Read existing mapping resources before creating another mapping; duplicate target mappings are rejected.

`opcuaserver/admin/cfg/load` is a program with create type `types/datalayer/persistence_param`. Invoke it only when the user explicitly asks to load persisted OPC UA configuration; it is not a normal setting.

### Redundancy and tracing

```text
opcuaserver/redundancy-configuration/additional-servers
opcuaserver/redundancy-configuration/server-uris
opcuaserver/redundancy-configuration/service-level
opcuaserver/redundancy-configuration/support
opcuaserver/trace-configuration/facility-mask
opcuaserver/trace-configuration/trace-level
```

The release notes describe cold-failover support. A non-empty redundancy configuration requires explicit server URIs/additional-server data; a `support` value alone does not prove that redundancy is active.

## Read-only status and diagnostics

Use these paths to verify the result of configuration changes:

```text
opcuaserver/server-status
opcuaserver/server-status2
opcuaserver/server-diagnostics/server-diagnostics-summary
opcuaserver/server-diagnostics/server-diagnostics-summary2
opcuaserver/server-diagnostics/session-diagnostics-summary
opcuaserver/licenses
opcuaserver/companion-model/namespace-array
opcuaserver/companion-model/loaded-bin-files
opcuaserver/companion-model/not-loaded-bin-files
opcuaserver/admin/exceptions
```

The installed package and Data Layer server state are separate checks: verify both the Package Manager health and `server-status/state`.

For a client connection, also verify:

```text
opcuaserver/server-diagnostics/server-diagnostics-summary/currentSessionCount
opcuaserver/server-diagnostics/server-diagnostics-summary/securityRejectedRequests
opcuaserver/server-diagnostics/server-diagnostics-summary/securityRejectedSession
```

Successful end-to-end operation requires an increased current-session count, zero new security rejects, and a client-side address-space browse.

### What an external client reads

The standard OPC UA Objects folder is `i=85`. Common server nodes exposed to a connected client include:

```text
i=2255  NamespaceArray
i=2256  ServerStatus / BuildInfo
i=2275  ServerDiagnosticsSummary
```

The ctrlX Data Layer is exposed below the server's OPC UA Data Layer root. A client should browse that root and follow the exact NodeIds returned by the browse response. Namespace indexes in returned child NodeIds can differ from the root namespace index; the client must not normalize them manually.

Composite status objects should be browsed and then read at their leaf nodes. A direct read of a composite object through the client's Data Layer projection can return `DL_FAILED` with an unsupported-attribute diagnosis even though the browse operation succeeds.

## REST write shape

For a primitive Data Layer variable, use the Data Layer `write` operation (REST `PUT`) with the declared type:

```json
{
  "type": "uint32",
  "value": 4840
}
```

For a collection, use the Data Layer `create` operation (REST `POST`) and the type named by `createType`. For a method, use the `writeInType` from metadata. Always read back the node after a successful write. Do not modify endpoint, security, memory, session, or subscription settings during an inspection-only request.

## Reference inspection baseline

A read-only inspection of ctrlX OS 4.6.2 on `192.168.88.242` found:

```text
Package health: okay
Server state: RUNNING
Endpoint: opc.tcp://ctrlX-X7-Hailo:4840
bind-port: 4840
allow-deprecated-policies: false
```

The baseline is device-specific and can change. Re-read all values before using them; do not treat it as a default for another controller.
