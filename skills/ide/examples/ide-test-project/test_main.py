#!/usr/bin/env python3

"""IDE-PROJECT-002: test the IDE-supported main routine locally."""

from pathlib import Path


class LoopTestDouble:
    def __init__(self):
        self.callbacks = []

    def main(self, callback):
        self.callbacks.append(callback)


class DatalayerTestDouble:
    def __init__(self):
        self.reads = []

    def read(self, path):
        self.reads.append(path)
        if path != "/system/apps/installed/rexroth-ide/title":
            raise AssertionError(f"unexpected Data Layer path: {path}")
        return "IDE"


class ConsoleTestDouble:
    def __init__(self):
        self.messages = []

    def log(self, message):
        self.messages.append(str(message))

    def logValue(self, label, value):
        self.messages.append(f"{label}: {value}")


def main():
    source_path = Path(__file__).with_name("main.py")
    source = source_path.read_text(encoding="utf-8")
    loops = LoopTestDouble()
    datalayer = DatalayerTestDouble()
    console = ConsoleTestDouble()

    namespace = {
        "__name__": "ide_test_project_main",
        "__file__": str(source_path),
        "loops": loops,
        "DatalayerLib": datalayer,
        "console": console,
    }
    exec(compile(source, str(source_path), "exec"), namespace)

    if len(loops.callbacks) != 1:
        raise AssertionError(
            f"expected one loops.main registration, got {len(loops.callbacks)}"
        )

    callback = loops.callbacks[0]
    if not callable(callback):
        raise AssertionError("registered on_main callback is not callable")

    callback()

    if datalayer.reads != ["/system/apps/installed/rexroth-ide/title"]:
        raise AssertionError(f"unexpected Data Layer reads: {datalayer.reads}")
    if console.messages != ["IDE-PROJECT-001 PASS", "IDE title: IDE"]:
        raise AssertionError(f"unexpected console output: {console.messages}")

    print("IDE-PROJECT-002 PASS")
    print("  loops.main registrations: 1")
    print("  on_main callback: callable and executed")
    print("  Data Layer reads: 1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
