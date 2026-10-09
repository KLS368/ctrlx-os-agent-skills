---
name: plc
description: "Provides information about the PLC runtime on the system."
license: Proprietary. LICENSE.txt has complete terms
---

# PLC

## General PLC status

The status of the PLC is composed of different values that can be read from datalayer and are important to get an aggregated PLC status. Read the following paths from datalayer and create a summary.

## PLC Runtime State

The following nodes provide the current operational state of the PLC system, including initialization status and lists of applications.

| Operation | Path | Node Description | Advanced description |
|-----------|------|-------------|----------------|
| BROWSE | `plc/admin/properties` | Operation state of PLC system | The sub nodes provide information about the PLC runtime and its state |
| BROWSE | `plc/app` | Collection of available applications | If available, you can find plc applications and their state in the sub nodes  |

## PLC Application State

| Operation | Path | Node Description | Operation description |
|-----------|------|-------------|----------------|
| WRITE | `plc/app/<name>/admin/cmd/start` | Start application | Write to start the application if stopped |
| WRITE | `plc/app/<name>/admin/cmd/stop` | Stop application | Write to stop the application if stopped |
| READ | `plc/app/<name>/admin/state/operation` | State of application | Get state of application |

## PLC Application Logic

| Operation | Path | Node Description | Operation description |
|-----------|------|-------------|----------------|
| BROWSE | `plc/app/<name>/sym/` | Symbolic variables | All symbolic variables of the user application can be found below this sub node |
| BROWSE | `plc/app/<name>/realtime_data` | Realtime variables | All realtime variables of the user application can be found below this sub node |

The realtime variables are usually updated each cycle and interesting to be used for data layer subscriptions.
Symbolic variables show the state of the user PLC application and usually can be used to interact with the PLC application. The variables are often mapped to HMI.
