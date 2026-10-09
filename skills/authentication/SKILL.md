---
name: authentication
description: "Provides reliable authentication instructions for ctrlX OS devices through the web UI and REST API, including Windows PowerShell curl handling."
license: Proprietary. LICENSE.txt has complete terms
---

# ctrlX Authentication

Use this skill before accessing a ctrlX OS web interface, REST API, or Data Layer endpoint that requires authentication.

## REST API Authentication

Create a token with:

```text
POST https://<device>/identity-manager/api/v2/auth/token?dryrun=false
```

Send JSON with the `name` and `password` fields. The API expects `name`; do not use `username`.

The `dryrun` query parameter controls whether a session is created:

- `dryrun=true`: validates credentials only and returns HTTP `204` on success.
- `dryrun=false`: creates a session and returns HTTP `201` with an `access_token`.

## Windows PowerShell

When calling the native `curl.exe` from PowerShell, do not pass inline JSON as a quoted `--data-raw` argument. PowerShell and Windows native argument parsing can strip the embedded JSON quotation marks, causing ctrlX to report the malformed request as `Invalid credentials`.

Build the JSON and pipe it through standard input instead:

```powershell
$payload = @{
    name = $username
    password = $password
} | ConvertTo-Json -Compress

$response = $payload | curl.exe -k -sS --noproxy '*' `
    -X POST "https://$device/identity-manager/api/v2/auth/token?dryrun=false" `
    -H "accept: application/json" `
    -H "Content-Type: application/json" `
    --data-binary '@-'
```

Use `-k` only when the device uses a certificate that is not trusted by the client. Add `--noproxy "*"` when a directly connected local device must bypass an environment proxy.

## Web UI Fallback

If the REST request reports `Invalid credentials` but the same credentials work in the browser, inspect the actual request body before changing credentials. Open `https://<device>/`, complete the login form, and confirm that ctrlX redirects to its device dashboard.

Never store credentials or access tokens in this skill, source files, command history, or diagnostic output.
