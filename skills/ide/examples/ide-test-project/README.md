# IDE Data Layer Test Project

## Purpose

This project contains a read-only smoke test for the ctrlX IDE App and a
separate local harness test for the current Blockly/Python `main.py`. It
verifies the path to the local ctrlX Data Layer using the IDE-supported
namespaces.

`test_main.py` is a local test harness. Do **not** paste it into the IDE
editor. The project source itself uses only the IDE-supported syntax and
namespaces.

**Scenario ID:** `IDE-PROJECT-001`

## Preconditions

- `rexroth-ide` is installed and enabled.
- The project runs inside the ctrlX CORE IDE runtime.
- The `ctrlxdatalayer` Python module is available.
- The target is a test or virtual ctrlX CORE.

## Project setup

1. Open the IDE App in the ctrlX CORE Web UI.
2. Select **Textual Coding**.
3. Create or open a project in the active solution.
4. Copy `main.py` into the project, for example:
   `scripts/ide_test_project.py`.
5. Do not add credentials. The source uses the IDE Data Layer namespace.

## Test procedure

Run the Data Layer test:

```text
python3 scripts/ide_test_project.py
```

The source performs only this Data Layer operation:

1. READ `/system/apps/installed/rexroth-ide/title`

No Data Layer `WRITE`, `CREATE`, `DELETE`, or subscription operation is used.

## Expected output

```text
IDE-PROJECT-001 PASS
  IDE title: IDE
```

The process must exit with code `0`.

Run the local callback harness outside the IDE runtime:

```text
python3 scripts/test_main.py
```

Expected result:

```text
IDE-PROJECT-002 PASS
  loops.main registrations: 1
  on_main callback: callable and executed
  Data Layer reads: 1
```

## Supported IDE source

The current project source uses the documented IDE namespaces:

```python-ignore
def on_main():
    title = DatalayerLib.read("/system/apps/installed/rexroth-ide/title")
    console.log("IDE-PROJECT-001 PASS")
    console.logValue("IDE title", title)

loops.main(on_main)
```

The corresponding supported blocks/namespaces are `loops.main`,
`DatalayerLib.read`, `console.log`, and `console.logValue`. The expected
Data Layer value is `IDE`.

## Acceptance criteria

| ID | Check | Expected result |
|---|---|---|
| T01 | Read app title | `IDE` |
| T02 | Device mutation check | No write/create/delete operation |
| T03 | Error handling | Any failed read exits nonzero and reports the node |
| T07 | Blockly callback registration | `loops.main` is called exactly once |
| T08 | Blockly callback execution | `on_main()` runs without an exception |
| T09 | Data Layer read | Exactly one read of the IDE title node |
| T10 | Console output | The title `IDE` is logged |

## Cleanup

Delete the copied test script from the active solution after verification
unless the user explicitly wants to keep the test project. Do not remove
unrelated files.
