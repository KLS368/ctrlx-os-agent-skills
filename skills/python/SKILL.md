---
name: python
description: "Provides guidance for creating, deploying, and executing Python scripts on ctrlX OS and ctrlX CORE, including runtime checks and log messages."
license: Proprietary. LICENSE.txt has complete terms
---

# Python on ctrlX OS

Use this skill when a user wants to create, copy, execute, or monitor a Python script on ctrlX OS or ctrlX CORE.

## Target and access checks

1. Identify the target and whether it is a real CORE or a virtual CORE.
2. For a virtual CORE, check the instance status before and after the task.
3. Prefer the ctrlX MCP Server when it is installed.
4. Check the available execution path before writing files:
   - MCP file tools can read and write allowed files, but they do not provide arbitrary shell execution.
   - REST and the Logbook API do not provide a generic Python command executor or a generic log-entry create endpoint.
   - SSH requires an enabled server and a shell-capable, non-expired user.

Do not claim that a script ran because a file was uploaded. Verify execution with its exit code and output.

## Execution decision

### Existing Python runtime

Use SSH for a read-only runtime check:

```sh
command -v python3
python3 --version
command -v logger
```

If a shell-capable user is unavailable or expired, stop and report the access blocker. Do not change users or SSH configuration implicitly.

If Python is available, transfer the script to an approved writable directory, execute it through SSH, and verify:

```sh
python3 /path/to/script.py
echo $?
```

For a one-off script, stdout is returned in the SSH terminal. It is not automatically a ctrlX Logbook entry.

### No Python runtime or no shell access

Do not install packages or create an ad-hoc system service without an explicit target and confirmation.

Use one of these alternatives:

- Build and deploy a snap app that bundles its Python runtime and runs the script as a managed service.
- Use ctrlX PLC or Node-RED when the requirement is control logic rather than general-purpose Python.
- Run the script locally when device execution is not required.

## Hello World

Minimal script:

```python
print("Hello, world!")
```

The expected output is:

```text
Hello, world!
```

## Writing a log message

The Logbook REST API and `logbook_list_entries` MCP tool are read-oriented. They can verify entries, but they are not a generic append API.

If the runtime provides a `logger` command or a supported syslog endpoint, create the message through that runtime interface and then verify it in the Logbook:

```sh
logger -t python-hello "hallo Welt"
```

Use this command only after verifying that `logger` exists and that the target routes syslog messages to the ctrlX Logbook. If it is unavailable, use the logging mechanism of the deployed snap, PLC, or Node-RED service instead.

Verify with the documented Logbook API or the MCP `logbook_list_entries` tool by searching for the message text. Do not report success based only on the process exit code.

## Device safety

- Treat file uploads, app deployment, service changes, and log writes as device changes.
- On a real device, inspect first and obtain confirmation before persistent changes.
- Never use a Python script to command motion unless the user explicitly requests it and the motion safety workflow has been followed.
- Remove temporary transfer files after verification.
