---
name: diagnosis-definitions
description: "Use when creating and publishing custom ctrlX OS diagnosis messages, warnings, or errors for an application. Triggers on diagnosis definition, diagnostic number, rexroth_diag, mainDiagnostics, detailedDiagnostics, set-active, reset-active, and custom Logbook alarms."
license: MIT
---

# ctrlX Diagnosis Definitions

Use this skill only for creating, registering, publishing, resetting, and
validating custom application diagnoses. Use the `diagnosis` skill for reading
existing alarms, Logbook analysis, and troubleshooting.

## Mandatory proposal gate

Before writing a catalog, registering definitions, or publishing a diagnosis,
always show a readable proposal and wait for explicit user confirmation.
Changing a number, name, severity, text, priority, entity, or lifecycle
requires a new confirmation.

For several definitions, show one block per diagnosis. Start with the
human-readable name, then show:

- main and detailed diagnostic numbers
- severity and its plain-language meaning
- priority and possible system reaction
- main and detailed text
- entity
- activation and reset conditions
- Data Layer lifecycle
- runtime information to include

Use these severity explanations:

- **MESSAGE:** Informational notice. Priority 0 is Logbook-only; priority 6
  also creates a deletable alarm entry.
- **WARNING:** A condition requiring attention, but not yet a blocking error.
  It causes no automatic machine reaction and remains active until reset.
- **ERROR:** A deviation requiring a corrective response. The priority
  determines the system reaction; priority 0 is non-fatal and causes no
  automatic axis or system reaction.

Example:

```text
Tank voll
  Main number:     0E0F0101
  Detailed number: 00000001
  Severity:        ERROR - corrective response required
  Priority:        0 - non-fatal, no automatic system reaction
  Main text:       Tank voll
  Detail text:     Tank level reached the maximum limit
  Entity:          plc/app/tank
  Active when:     tank level >= maximum limit
  Reset when:      tank level is below the reset threshold
  Lifecycle:       set-active -> reset-active -> confirm/error
  Context:         current tank level and configured limit
```

## Diagnostic numbers

The main diagnostic number is a 32-bit identifier:

| Bits | Meaning |
|---|---|
| 31-30 | Reserved |
| 29-24 | Source type; `0x0E` OEM machine-specific, `0x0F` OEM machine-HMI |
| 23-21 | Reserved |
| 20 | Reset state; managed by the diagnosis interface |
| 19-16 | Class: `0xA` message, `0xE` warning, `0xF` error |
| 15-12 | Priority |
| 11-0 | Application-specific status number |

Rules:

- Main numbers must be globally unique and must not be reused for another
  condition.
- Detailed numbers must be stable and unique under their related main number.
  The same detail number may be used under another main number.
- Set the reset bit to `0` in diagnosis requests; the interface manages it.
- Warning priority bits are reserved and must be `0`.
- Message priority `0` is Logbook-only; priority `6` is a deletable alarm
  entry.
- Error priority `0` is non-fatal. Higher priorities can stop axes, stop all
  axes, restart an application, or shut down the system. Require safety-owner
  approval before using them.
- Reserve the number range with the owning product team before implementation.

## JSON catalog

Create one catalog per supported language. Keep numbers and structure equal
across language files. Detailed definitions are nested below their main
diagnostic:

```json
{
  "product": "my-application",
  "mainDiagnostics": {
    "0E0F0101": {
      "text": "Tank voll",
      "version": 1,
      "detailedDiagnostics": {
        "00000001": {
          "text": "Tank level reached the maximum limit",
          "version": 1
        }
      }
    }
  }
}
```

Catalog rules:

- `product` identifies the owning application or product family.
- Keep operator texts short, actionable, and suitable for Logbook and System
  Overview.
- Keep volatile values, limits, object names, and measured values in runtime
  additional information, not in new diagnostic numbers.
- Use `version` when supported and increment it when the meaning changes.
- Validate the JSON against the official diagnosis schema before packaging.
- A catalog only registers text and numbers; it does not activate a diagnosis.

## Data Layer contract

| Purpose | Data Layer node | Required behavior |
|---|---|---|
| Register device-side catalog | `diagnosis/registration/register-file` | Register a JSON file stored below the device `diagnostics` directory |
| Register catalog content | `diagnosis/registration/register-file-content` | Send the catalog as binary file content before publishing |
| Publish transient event | `diagnosis/set/set-and-reset` | Use for priority 0 messages and fire-and-forget events |
| Set active diagnosis | `diagnosis/set/set-active` | Use for active warnings/errors and explicitly persistent priority 6 messages |
| Reset active diagnosis | `diagnosis/set/reset-active` | Use after the underlying condition is resolved |
| Verify identity and state | `diagnosis/get/actual/list` | Check identity, reset/active state encoding, entity, and timestamp |
| Delete reset error/message | `diagnosis/confirm/error` | Delete one reset error or priority 6 message by identity |
| Delete all eligible entries | `diagnosis/confirm/all-errors` | Delete reset errors and priority 6 messages; active errors remain |
| Unregister catalog content | `diagnosis/registration/unregister-file-content` | Unregister only after owned active diagnoses are reset |

For REST JSON, `register-file-content` and
`unregister-file-content` use an `aruint8` value containing the UTF-8 bytes of
the catalog. Do not invent a `raw` or Base64 object shape. The SDK equivalent
is a byte array.

Runtime publication uses the SDK diagnosis structure (`LogParameters`) or the
verified Data Layer type. Its identity contains:

- `mainDiagnosisCode`
- `detailedDiagnosisCode`
- optional `entity`

It may also contain `origin`, `unitName`, source location, and
`dynamicDescription`. Do not invent field names when the SDK or node metadata
provides the type.

Text lookup, when needed for verification, uses read arguments:

- `diagnosis/get/text/main`: `mainDiagnosisNumber`
- `diagnosis/get/text/detailed`: `detailedDiagnosisNumber` and
  `relatedMainDiagnosisNumber`

## Creation and publication workflow

1. Show the readable proposal and obtain explicit confirmation.
2. Reserve and verify the main number and its detailed numbers.
3. Create and schema-validate the language-specific JSON catalog.
4. Register the catalog with `register-file` or `register-file-content`.
5. Publish:
   - `MESSAGE`: normally `set-and-reset`
   - `WARNING` or `ERROR`: `set-active`
6. Read `diagnosis/get/actual/list` and verify the expected identity, state
   encoding, entity, and timestamp.
7. Read the Logbook or use the text lookup nodes and verify the expected
   message text, detail text, runtime information, and severity.
8. If the condition clears, call `reset-active`. Warnings clear automatically;
   reset errors and priority 6 messages require `confirm/error` or
   `confirm/all-errors`.
9. Before unregistering or unloading the application, reset all owned active
   warnings and errors.

`set-and-reset` behavior depends on the class: priority 0 messages are
Logbook-only, warnings are immediately cleared, and errors become reset
entries that still require deletion.

## Validation checklist

- Proposal was shown in name-first format and explicitly confirmed.
- Main number is globally unique; detail numbers are unique under that main.
- Class and priority match the intended operator behavior.
- Warning priority bits are zero.
- JSON parses, matches the schema, and is consistent across languages.
- Catalog registration succeeds before publication.
- The published entry appears with the expected identity, entity, and state.
- Logbook or text lookup verification confirms the expected texts and
  severity.
- Logbook severity matches the intended class.
- Reset and deletion behavior was tested separately.
- No credentials, customer data, or sensitive runtime data are included.

## Safety

- Do not create test errors on a productive device without explicit approval.
- Test on a virtual ctrlX CORE or isolated application first.
- Do not use diagnosis publication to hide failures or simulate a safe state.
- Surface failed registration, publication, reset, or deletion; do not silently
  treat an error as success.
- Reset active diagnoses before unregistering their definitions.

## References

- [ctrlX OS Diagnostic System: Use your own diagnostic messages](https://community.boschrexroth.com/ctrlx-automation-how-tos-qmglrz33/post/ctrlx-os-diagnostic-system-use-your-own-diagnostic-messages-JhzWtcKvrrs0ROT)
- [ctrlX Data Layer Diagnosis SDK sample](https://boschrexroth.github.io/ctrlx-automation-sdk/samples-cpp/datalayer.diagnosis/index.html)
- [Bosch Rexroth JSON schema](https://json-schema.boschrexroth.com/)
- [ctrlX OS Diagnostics reference](https://docs.automation.boschrexroth.com/pdf/document/ID1895008_303843156?filename=ctrlX%20OS%2C%20Diagnostics%2002VRS%2C%20Reference%20Book&lang=eng)
