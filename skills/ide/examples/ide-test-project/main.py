#!/usr/bin/env python3

def on_main():
    title = DatalayerLib.read("/system/apps/installed/rexroth-ide/title")
    console.log("IDE-PROJECT-001 PASS")
    console.logValue("IDE title", title)


loops.main(on_main)
