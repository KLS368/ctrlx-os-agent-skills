# IDE motion test for Axis_1.
# Preconditions:
# - Axis_1 is enabled and in STANDSTILL.
# - Motion is in RUNNING/OPERATION.
# - The test area is clear.

def on_main():
    motion.Axis_1.move(MoveType.ABSOLUTE, 30, 30, 100, 0)
    loops.pause(3000)

    motion.Axis_1.move(MoveType.ABSOLUTE, -30, 30, 100, 0)
    loops.pause(3000)

    console.log("AXIS-BIDIRECTIONAL-TEST PASS")


loops.main(on_main)
