---
name: app-management
description: "Use when installing, updating, uninstalling, enabling, disabling, or verifying ctrlX OS applications or packages (.app/.snap) through the Package Manager REST API. Covers SERVICE state handling, asynchronous package tasks, Windows PowerShell curl handling, and safe state restoration."
license: Proprietary. LICENSE.txt has complete terms
---

# ctrlX App Management

Use this skill for local or remote ctrlX OS app/package management. Use the `authentication` skill first and never print or persist credentials or bearer tokens.

## Preconditions

1. Confirm the target device and app files exist.
2. Read the installed package list:

   ```text
   GET /package-manager/api/v1/packages
   ```

3. Read the scheduler state and remember it for cleanup:

   ```text
   GET /automation/api/v2/nodes/scheduler/admin/state
   ```

4. Package installation requires `SERVICE`. On ctrlX OS 4.6, switch it with:

   ```text
   PUT /automation/api/v1/scheduler/admin/state?format=json
   {"state":"SERVICE"}
   ```

   Verify the state after the request. Do not use a generic v2 Data Layer `POST` for this scheduler state unless the target device exposes the required type information.

5. Read package-manager settings before changing them:

   ```text
   GET /package-manager/api/v1/settings
   ```

   If `allowUnknownApps` must be enabled for a local package, change it only for the requested operation and restore its previous value afterward.

## Upload and install

Install one app at a time with:

   ```text
   POST /package-manager/api/v1/packages
   Content-Type: multipart/form-data
   file=<app package>
   update=true
   ```

The response must be HTTP `202` and contain a `Location` header for the asynchronous task. Poll the task URL until `state` is `done`:

   ```text
   GET /package-manager/api/v1/tasks/<task-id>
   ```

Stop and surface the task result if the state is `failed`; do not continue with the next app after a failed dependency or package operation. Verify the installed package list after all requested apps complete.

For Windows PowerShell, call native `curl.exe` with explicit arguments. Avoid reusing the automatic PowerShell variables `$args` and `$Matches` for curl arguments or result collections. Do not manually override curl's multipart `Content-Type`, because curl must add the boundary:

```powershell
curl.exe -k -sS --noproxy '*' `
  -X POST "https://<device>/package-manager/api/v1/packages" `
  -H "Authorization: Bearer <token>" `
  -F "file=@C:\path\app.app" `
  -F "update=true"
```

Use `-k` only for an untrusted device certificate and `--noproxy '*'` for a directly connected local device.

## Cleanup and verification

Always restore the scheduler state saved during preconditions, even when an upload or task fails. On ctrlX OS 4.6, restore `OPERATING` with:

```text
PUT /automation/api/v1/scheduler/admin/state?format=json
{"state":"OPERATING"}
```

Read the scheduler state and `/package-manager/api/v1/packages` again after cleanup. Report package IDs, titles, and versions, not credentials or tokens.

After installing `rexroth-opcua-server`, use the dedicated `opcua-server` skill for OPC UA configuration and Data Layer verification. Installation success alone does not prove that the OPC UA server is enabled or in `RUNNING` state; verify Package Manager health and `opcuaserver/server-status/state`.

After installing `rexroth-opcua-client`, use the dedicated `opcua-client` skill. Verify Package Manager health, license state, and `opcuaclient/general-configuration/number-of-clients`; client endpoint and security settings exist only after a dynamic client session is created.
