---
name: datalayer-scopes
description: "Use to restrict, grant, verify or troubleshoot user access to ctrlX Data Layer nodes. Covers user-defined Data Layer scopes (datalayer/security/scopes): creating, reading, changing, deleting and persisting scopes, wildcard rules, which permission list (R/RW/X/RWX) an operation needs, checking effective permissions with datalayer/security/check-operations, and interpreting DL_SEC_UNAUTHORIZED / 403 'Need one scope of ...' errors. Always use before creating or changing a scope."
license: Proprietary. LICENSE.txt has complete terms
---

# Data Layer Scopes

## Core Concepts

### Scope
A scope is a named permission that is granted to a user or group in the Identity Manager. All scopes of a user are placed in the `scope` claim of the user's JWT token. The Data Layer broker checks every request that carries a token against the scopes in that token.

There are two kinds of scopes:

- **App scopes** (static): declared by an app package. They cannot be changed at runtime. Examples: `rexroth-device.all.rwx` (full access to everything), `rexroth-automation.datalayer.r` / `.rw` / `.x` (read / read+write / create+delete on the complete Data Layer), `datalayer.view` / `datalayer.manage` (Data Layer settings page in the web UI), `motion.view` / `motion.operate` / `motion.manage` (Motion app).
- **Data Layer scopes** (user-defined, dynamic): created at runtime in the Data Layer under `datalayer/security/scopes`. They restrict access to individual addresses or address trees. Their identifier must start with `datalayer.`. This skill is about these scopes.

### Access decision
Access is granted if **at least one** scope in the token allows the requested operation on the requested address. Scopes are combined as a union, never as an intersection. A user who holds `rexroth-device.all.rwx` or `rexroth-automation.datalayer.rw` is therefore never restricted by an additional Data Layer scope. To restrict a user, the user must hold **only** Data Layer scopes (plus the app scopes needed for the web UI pages the user should see).

The check is applied to TCP connections (web UI, REST, OPC UA server, Node-RED, external clients). Apps that connect on the device via IPC without a token are not restricted. Responses of providers are always allowed.

### Required permission per operation

| Data Layer operation | Required permission on the address |
|----------------------|------------------------------------|
| READ, subscribe | read |
| WRITE | write |
| CREATE, DELETE | execute |
| BROWSE, metadata | browse (any list that contains the address) |
| provider register / unregister | execute |

## Nodes

| Operation | Path | Node Description | Advanced description |
|-----------|------|------------------|----------------------|
| READ | `datalayer/security/scopes` | List of all user-defined scopes | Type `types/datalayer/scopes`. Returns `{"scopes": [...]}` |
| BROWSE | `datalayer/security/scopes` | Identifiers of all user-defined scopes | One sub node per scope |
| CREATE | `datalayer/security/scopes` | Create a new scope | Payload type `types/datalayer/scope`. Fails with `DL_ALREADY_EXISTS` if the identifier exists |
| READ | `datalayer/security/scopes/<identifier>` | Read one scope definition | Type `types/datalayer/scope` |
| WRITE | `datalayer/security/scopes/<identifier>` | Replace one scope definition | Write the complete definition. Effective immediately, also for tokens that already exist |
| DELETE | `datalayer/security/scopes/<identifier>` | Delete one scope | Effective immediately |
| READ (with input) | `datalayer/security/check-operations` | Allowed operations for a token/address combination | Input `types/datalayer/check-operations`, output `types/datalayer/allowed-operations` |
| CREATE | `datalayer/admin/cfg/save` | Persist the Data Layer configuration including all scopes | Payload type `types/datalayer/persistence_param` |
| CREATE | `datalayer/admin/cfg/load` | Reload the persisted Data Layer configuration | Discards unsaved scope changes |

## Scope Definition

A scope is a JSON object of type `types/datalayer/scope`:

```json
{
  "identifier": "datalayer.motion-readonly",
  "name": "Motion read-only",
  "description": "Read and browse all motion nodes, nothing else",
  "permissionsR": ["motion/**"],
  "permissionsRW": [],
  "permissionsX": [],
  "permissionsRWX": []
}
```

| Field | Meaning |
|-------|---------|
| `identifier` | Unique key of the scope. **Must start with `datalayer.`**, otherwise `DL_INVALID_VALUE` ("user defined scope has to start with \"datalayer.\""). This string appears in the token and in the Identity Manager |
| `name` | Display name shown in the permission settings of the web UI |
| `description` | Description shown in the permission settings |
| `permissionsR` | Addresses that may be read, browsed and whose metadata may be read (includes subscriptions) |
| `permissionsRW` | Addresses that may be read, written, browsed and whose metadata may be read |
| `permissionsX` | Addresses on which nodes may be created and deleted, plus browse and metadata |
| `permissionsRWX` | Addresses with all operations: create, delete, read, write, browse, metadata |

> ⚠️ The field names carry a plural **s** (`permissionsR`, not `permissionR`). The ctrlX OS manual prints them without the `s`; the broker rejects that spelling with `DL_TYPE_MISMATCH: unknown field: permissionR`.

Only `identifier` is validated. Empty `name` / `description` and permission lists are accepted. Omit the lists that are not needed.

### Address patterns

| Pattern | Meaning | Example |
|---------|---------|---------|
| exact address | one node | `datalayer/nodes` |
| `*` | any single node name, between two `/` or at the end | `motion/axs/*/state/values/actual/pos` grants the `pos` node of every axis |
| `**` | any sub tree, only at the end of an address | `motion/**` grants every node below `motion` |

Rules:

- A granted address implicitly allows BROWSE and metadata on all parent nodes. Browsing a parent returns only the children the token may access (e.g. with `motion/axs/**` browsing `motion` returns only `axs`). A few folders such as `types`, `system/state` and `datalayer/security/check-operations` are readable without any scope and therefore always appear.
- Siblings are not granted: `scheduler/tasks/*/info/duration-rt` allows `duration-rt` of every task, but not `common-data-rt` next to it.
- Patterns are **not validated**. `motion/**/pos` is accepted but `**` in the middle of an address is not supported. Keep `**` at the end.
- The permission for CREATE / DELETE is checked on the address that is created or deleted: `permissionsX: ["datalayer/security/scopes"]` allows creating scopes, but deleting `datalayer/security/scopes/<id>` needs `datalayer/security/scopes/**`.

## Common Workflows

> ⚠️ **Warning:** Creating, changing or deleting a scope changes what users are allowed to do. Require explicit user consent before writing, and never grant `**` in `permissionsRWX` without a reason. Keep at least one user with `rexroth-device.all.rwx` so administrators are never locked out.

### Create a restricted scope

**Prerequisites:**
- The current token needs execute permission on `datalayer/security/scopes` (`rexroth-device.all.rwx`, `rexroth-automation.datalayer.x` or `datalayer.manage`).

**Steps:**
1. BROWSE the target nodes first (e.g. `motion/axs`) and derive the exact addresses. Never guess addresses; they differ between ctrlX OS versions and installed apps.
2. Decide per address which list it belongs to: reading and subscribing → `permissionsR`; writing values → `permissionsRW`; CREATE/DELETE and method calls implemented as CREATE → `permissionsX`; everything → `permissionsRWX`.
3. READ `datalayer/security/scopes` and make sure the identifier is unused. Do not reuse the identifiers of app scopes (`datalayer.view`, `datalayer.manage`); the broker does not reject the collision.
4. CREATE `datalayer/security/scopes` with the complete scope object as value:
   ```json
   {"type": "object", "value": {"identifier": "datalayer.motion-readonly", "name": "Motion read-only", "description": "Read all motion nodes", "permissionsR": ["motion/**"]}}
   ```
5. READ `datalayer/security/scopes/datalayer.motion-readonly` to verify the stored definition.
6. Persist the scope (see *Persistence*).
7. Grant the scope to the user or group in the web UI: *Settings → Users & Permissions → Users* (or *Groups*) → open the user → *Individual permissions*. The Identity Manager registers the scope as a dynamic scope within a few seconds after the CREATE; it appears in the category **Data Layer Global** with its `name` (next to *View resources*, *Modify resources*, *Create resources*). Do not grant *Full access* or the *Data Layer Global* app permissions to that user, otherwise the restriction has no effect.
8. The user must log in again. Scopes are placed in the token at login; an existing token does not receive newly granted scopes.
9. Verify with `check-operations` (see below) or by reading an allowed and a denied node with the user's token.

### Change an existing scope

1. READ `datalayer/security/scopes/<identifier>`.
2. Modify the lists in the returned object. Keep `identifier`, `name` and `description`.
3. WRITE the **complete** object to `datalayer/security/scopes/<identifier>`. A write replaces the definition.
4. The change is effective immediately for all users that hold the scope, including tokens that were issued before the change. No new login is needed.
5. Persist the change (see *Persistence*).

### Delete a scope

1. Ask the user to remove the scope from all users and groups in the web UI first, otherwise those users keep an orphaned permission entry.
2. DELETE `datalayer/security/scopes/<identifier>`.
3. BROWSE `datalayer/security/scopes` to verify.
4. Persist the change (see *Persistence*).

### Check effective permissions of a token

READ `datalayer/security/check-operations` with an input value of type `types/datalayer/check-operations`:

```json
{"type": "object", "value": {"address": "motion/state/opstate", "token": "<JWT of the user to check>"}}
```

- `address`: the address to check.
- `token`: the JWT to check. If omitted, the token of the current request is checked.

The result is of type `types/datalayer/allowed-operations`:

```json
{"read": true, "write": false, "create": false, "delete": false, "browse": true}
```

Use this before and after a scope change to prove the effect without logging in as the restricted user.

### Persistence

Scope changes live in memory until the Data Layer configuration is saved. Unsaved scopes are lost at the next reboot. Save after every change:

```
CREATE datalayer/admin/cfg/save with value {"type": "object", "value": {"configurationPath": "", "id": "save-scopes-<timestamp>", "phase": "save"}}
```

- `configurationPath`: always empty (active configuration).
- `id`: client-generated id for traceability.
- `phase`: always `save`.

`datalayer/admin/cfg/load` with `"phase": "load"` reloads the saved state and discards unsaved scope changes. Saving the complete app data in the web UI (*Settings → Configurations → Save*) also triggers this save.

The scopes are stored in the active configuration as `datalayer/security/scopes.json` (app data of the Data Layer, visible via the Solutions app). Do not edit that file by hand; use the nodes above.

### Restricting a cross-controller OPC UA connection

For the setup "controller A exposes an OPC UA Server and controller B runs the OPC UA Client", create the user-defined scope on **controller A**, where the OPC UA Server validates the client token. A scope on controller B does not restrict what controller A serves.

Use a separate local user for the OPC UA connection. Do not use an administrator with `rexroth-device.all.rwx`, `rexroth-automation.datalayer.r`, or `.rw`; scopes are combined as a union and those global scopes bypass the restriction. The restricted user needs:

```text
rexroth-opcua-server.opcua.x
datalayer.<the-user-defined-scope>
```

`rexroth-opcua-server.opcua.x` grants access through the OPC UA Server protocol. The user-defined scope grants the selected Data Layer addresses. Do not grant `opcuaserver.view`/`opcuaserver.manage` or global Data Layer scopes unless the user also needs the server configuration UI; those scopes can broaden access beyond the test scope.

Example read-only scope for a server that should expose only its own status and selected Motion data:

```json
{
  "identifier": "datalayer.opcua-scope-test",
  "name": "OPC UA restricted test",
  "description": "Read-only OPC UA server status and motion data",
  "permissionsR": [
    "opcuaserver/server-status2/**",
    "motion/**"
  ]
}
```

After creating and persisting the scope:

1. Create the separate local user on controller A, set its password, and assign only `rexroth-opcua-server.opcua.x` plus the dynamic scope.
2. Obtain a fresh token by logging in as that user. Newly granted scopes are not added to an already-issued token.
3. Configure the OPC UA Client session on controller B with that username/password and reconnect.
4. Verify an allowed read, such as `opcuaserver/server-status2`, and a denied read, such as `opcuaserver/licenses` or `opcuaserver/endpoint-configuration/url`, expecting HTTP 403 / `DL_SEC_UNAUTHORIZED`.
5. Verify the OPC UA Client session is `CONNECTED`, the server has `currentSessionCount >= 1`, security-reject counters remain zero, and a browse shows only the intended accessible subtree.

The scope controls Data Layer access; it does not automatically change the OPC UA endpoint's security policy. If the endpoint uses Security None, the client still needs a valid OPC UA session identity, and credentials/data are transmitted unencrypted.

## Troubleshooting

### DL_SEC_UNAUTHORIZED (REST: HTTP 403)

A request is denied. The diagnosis carries `mainDiagnosisCode 080F0600` and a `dynamicDescription` such as:

```
Need one scope of motion.manage motion.operate motion.view rexroth-automation.datalayer.r rexroth-automation.datalayer.rw rexroth-device.all.rwx
```

The listed scopes are the **app scopes** that would grant the operation. User-defined Data Layer scopes are not listed, even if one of them would grant it. Fix: extend the correct list of the user's Data Layer scope with the address (WRITE the scope), or grant one of the listed app scopes.

### Other error patterns

| Symptom | Cause | Fix |
|---------|-------|-----|
| `DL_TYPE_MISMATCH: unknown field: permissionR` on CREATE/WRITE | field name without `s` | use `permissionsR`, `permissionsRW`, `permissionsX`, `permissionsRWX` |
| `DL_INVALID_VALUE`, "user defined scope has to start with \"datalayer.\"" | wrong identifier prefix | identifier `datalayer.<name>` |
| `DL_ALREADY_EXISTS` (409) on CREATE | identifier already exists | WRITE `datalayer/security/scopes/<identifier>` instead |
| 403 with detail "Can't read type information" on CREATE | token has no execute permission on the collection | grant `permissionsX` on `datalayer/security/scopes` or use an admin token |
| `DL_UNSUPPORTED` (501) on READ after the permission was granted | node does not support READ (e.g. realtime nodes) | use subscribe or the `/data` sub nodes; not a permission problem |
| Newly granted scope has no effect | user still uses the old token | log in again; only scope *content* changes apply to existing tokens |
| Restricted user still sees everything | user also holds `rexroth-device.all.rwx` or `rexroth-automation.datalayer.*` | remove those permissions from the user or group |
| Scope disappeared after reboot | configuration was not saved | CREATE `datalayer/admin/cfg/save` after every change |
| BROWSE of a parent returns fewer nodes than expected | browse shows only children the token may access | expected behaviour |
