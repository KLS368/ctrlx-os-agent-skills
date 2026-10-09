---
name: diagnosis
description: "Provides information about how to read the diagnosis logbook and to find active alarms in order to provide a diagnosis overview. Contains additional instructions on how to perform troubleshooting in case of problems and how to find the root cause of an error."
license: Proprietary. LICENSE.txt has complete terms
---

# Diagnosis & Logbook

## Overview

### About Logbook & Alarms

The logbook is a list of multiple entries with different properties.

There are different types of entries in the logbook:

- **Diagnosis Entries** (`type=rexroth_diag`): A structured realtime alarm of an app. Contains a diagnostic number, detailed diagnostic information, plain text description and additional information. There are 3 types of diagnosis entries:
  - **Messages**: These are diagnosis entries providing information (e.g. temperature monitoring active). They do not trigger a response.
  - **Warnings**: These are entries informing on a possible upcoming error that can still be avoided (e.g. overtemperature warning). They do not trigger a response.
  - **Error**: These are entries informing on a deviation from the command state (e.g. overtemperature reached - System is paused). They trigger a response. This response depends on the error class.
- **Trace Messages** (`type=rexroth_trace`): Optional debug messages of an application. Usually disabled. Can be enabled for in depth debugging of an application.
- **System Messages** (`type=system`): Linux messages as captured by `systemd` and `journald`. Usually the `stdout` and `stderr` of an app.

### Active Alarm States

Errors and Warnings of type=rexroth_diag have a state which reflects if the error or warning state is still active. A second logbook entry is emitted by the system if the alarm or error is no longer active. Each alarm state must be confirmed by the user.

To get a list of the current active alarm states read the data layer node: `diagnosis/get/actual/list`
To get the number of active errors read the data layer node: `diagnosis/get/actual/list/amount-errors`
To get the number of active warnings read the data layer node: `diagnosis/get/actual/list/amount-warnings`

### Read Logbook

You can read the diagnosis logbook with the `logbook_list_entries` tool. Based on the parameter `types` the log tool will return Diagnosis, Trace and System messages.

## Workflows

## Get overview current diagnosis status

1. Start by reading the list of current active alarms (`diagnosis/get/actual/list`) to get an overview of all pending diagnosis.
2. Read the logbook with `logbook_list_entries` tool to get a list of all historical entries which might have led to the active alarms.
3. Create a summary of the provided information.

## In depth analysis

For more in depth analysis of a problem you may read the logbook including `Debug` and `Info` loglevels.
