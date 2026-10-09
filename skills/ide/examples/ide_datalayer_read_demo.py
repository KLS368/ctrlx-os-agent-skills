# IDE Data Layer demo in the IDE-supported Python/Blockly syntax.

def on_main():
    title = DatalayerLib.read("/system/apps/installed/rexroth-ide/title")
    console.log("IDE-DL-DEMO PASS")
    console.logValue("IDE title", title)


loops.main(on_main)
