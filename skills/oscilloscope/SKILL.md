---
name: oscilloscope
description: "Configure, start, monitor, and read ctrlX Oscilloscope instances through the ctrlX Data Layer."
license: MIT
---

# ctrlX Oscilloscope

This repository skill is the canonical Oscilloscope workflow. Use its Data
Layer guidance and the Web UI for guided commissioning tests. Do not use
device-local MCP servers or device-local skill files. REST/HTTP is an
emergency fallback only when the repository workflow cannot perform the
operation.

For motion tests, the user initiates the axis movement. The agent may
configure and start the Oscilloscope, but must never issue `cmd/power` to
enable an axis or start a movement. It may issue `cmd/power` only with
`value: false` after the capture, solely to switch the axis off. It must
never issue `cmd/pos-abs`, `cmd/pos-rel`, `cmd/velocity`, `cmd/jog-*`, or
`cmd/flexprofile`.
The agent must never call `cmd/trigger`; motion recordings always use an
automatic direction-specific trigger.

An instruction such as "test again" or "try again" does not authorize an
automatic axis movement. After arming the Oscilloscope, pause and have the
user press Start in Motion Commissioning. Only poll the resulting state.
Each new movement requires a new user action in the Commissioning UI.

## Data Layer operations

| Operation | Path | Purpose |
|---|---|---|
| BROWSE | `oscilloscope/instances` | List instances |
| CREATE | `oscilloscope/instances` | Create an instance |
| READ | `oscilloscope/instances/<name>/state/opstate` | Read capture state |
| WRITE | `oscilloscope/instances/<name>/cfg/buffer` | Configure recording |
| BROWSE | `oscilloscope/instances/<name>/cfg/channels` | List channels |
| CREATE | `oscilloscope/instances/<name>/cfg/channels` | Add a channel |
| WRITE | `oscilloscope/instances/<name>/cfg/trigger` | Configure automatic trigger |
| BROWSE | `oscilloscope/instances/<name>/cfg/diagrams` | Find generated diagram |
| BROWSE | `oscilloscope/instances/<name>/cfg/diagrams/<diagram>/views` | List views |
| CREATE | `oscilloscope/instances/<name>/cfg/diagrams/<diagram>/views` | Add a view |
| CREATE | `oscilloscope/instances/<name>/cmd/start` | Arm a capture |
| CREATE | `oscilloscope/instances/<name>/cmd/stop` | Stop a fallback capture |
| READ | `oscilloscope/instances/<name>/rec-values/allsignals` | Read all data |
| DELETE | `oscilloscope/instances/<name>` | Delete after stopping |

## Data Layer access contract

Use the following request and verification rules for every access. A
successful `CREATE` or `WRITE` response confirms only that the request was
accepted; it does not prove that the capture is correctly configured or
contains usable data.

### Writes and commands

- `CREATE oscilloscope/instances`: send a string payload such as
  `{"type":"string","value":"myOsc"}`. Use a unique camelCase name, then
  browse the instances and read `state/opstate`.
- `WRITE cfg/buffer`: send an object with `bufferType` (`REPEAT` or
  `SINGLESHOT`), `recordingInterval.value`, and `recordingTime.value`.
  Both time values are integer nanoseconds. Read `cfg/buffer` back and
  verify the cycle-aligned interval, recording time, and integral memory
  depth before starting.
- `CREATE cfg/channels`: send one object per channel with `name`, `alias`,
  `source`, `type`, and `unit`. Keep `alias` identical to `source`, then
  browse the channel list and verify every channel.
- `WRITE cfg/trigger`: send `triggerType`, channel `name`, string `level`,
  and numeric `preTrigger`. Use only the direction-specific automatic
  trigger for motion recordings and verify that the referenced channel
  exists.
- `CREATE cfg/diagrams/<diagram>/views`: send `source`, hexadecimal `color`,
  `visible`, and `connectionType`. Browse the views and verify one colored
  view per channel.
- `CREATE cmd/start`: send `{"type":"bool8","value":true}` only after all
  sources, channels, trigger, buffer, diagram, and views have been verified.
  Then read `state/opstate` while waiting for the user-started movement.
- `CREATE cmd/stop`: send `{"type":"bool8","value":true}` only for an
  explicitly requested fallback or cleanup. Read `state/opstate` until the
  stop has completed before reading or deleting the instance.

### Reads and browse results

- `BROWSE oscilloscope/instances` returns the configured instance names.
  Browse before choosing a unique name and again when checking creation.
- `READ state/opstate` returns the capture state. Use the named enum when
  available; otherwise use the zero-based mapping documented below.
- `BROWSE cfg/channels` returns the configured channel objects. Confirm the
  expected names and sources before starting.
- `BROWSE cfg/diagrams` returns target-generated diagram names. Use the
  returned name rather than assuming `Diagram_0` or `Diagram_1`.
- `BROWSE cfg/diagrams/<diagram>/views` returns the diagram views. Confirm
  that every channel has a visible, colored view.
- `READ rec-values/allsignals` is the only supported recording read on the
  verified target. Confirm that every expected channel has samples, a
  nonzero timestamp span, the expected direction, units, and range.

## General preconditions

1. Browse `oscilloscope/instances` and use a unique camelCase name.
2. Browse and read every source before creating its channel.
3. Read metadata when the type or unit is not known.
4. Browse `cfg/diagrams` immediately before creating views. The verified
   ctrlX OS 4.6 target creates `Diagram_1`; never assume `Diagram_0`.
5. Create and verify one colored view per channel before `cmd/start`.

An address ending in `/..` is a parent object, not a scalar channel. For
example, `.../actual/pos/..` returns position, velocity, acceleration, torque,
and distance-left together. Use one scalar source per channel.

For SI motion channels, use:

```text
motion/axs/<axis>/state/values/actual/pos/m
motion/axs/<axis>/state/values/actual/vel/m-per-s
motion/axs/<axis>/state/values/actual/acc/m-per-s^2
motion/axs/<axis>/state/values/actual/trq
```

## Motion test prerequisites

Use the repository `motion` skill as the authority for Motion state, units,
limits, and safety. Before arming:

- `motion/state/opstate` must be `Running`.
- The axis must be `DISABLED` or `STANDSTILL`, never `ERRORSTOP`,
  `DISCRETE_MOTION`, `CONTINUOUS_MOTION`, or a pending state.
- Read axis category, axis profile, configured units, and `cfg/lim`.
- The safe-corridor procedure below is for linear, non-modulo axes only.
  Rotary, modulo, kinematic, and coordinated tests need a dedicated Motion
  procedure.

Do not switch Motion modes, save Motion configuration, reset errors, or create
an axis from this skill.

## Standard one-movement recording

Each recording contains exactly one traverse. The opposite direction is used
for the next recording, never in the same recording.

For `posMin < posMax`, calculate:

```text
safeMin = posMin + 0.10 * (posMax - posMin)
safeMax = posMax - 0.10 * (posMax - posMin)
epsilon = 0.01 * (safeMax - safeMin)
```

Use either `safeMin -> safeMax` or `safeMax -> safeMin`. Never use the
configured limits themselves and never derive endpoints from the current
position. The selected baseline endpoint must be verified before arming.

The Motion Commissioning page is:

```text
/motion/axis-landing/commissioning/<axisName>
```

The agent may enter commissioning values but must not press its Start button.
The page sends a position command when the user presses Start; it does not
create a persistent motion profile.

## Automatic trigger and recording time

Calculate the traverse time from the actual profile values. For a trapezoidal
profile with distance `s`, velocity `v`, acceleration `a`, and deceleration
`d`:

```text
tAcc = v / a
tDec = v / d
sAcc = v^2 / (2 * a)
sDec = v^2 / (2 * d)

if sAcc + sDec < s:
    tTraverse = tAcc + tDec + (s - sAcc - sDec) / v
else:
    vPeak = sqrt(2 * s / (1/a + 1/d))
    tTraverse = vPeak / a + vPeak / d
```

Configure the sampling period and integer memory depth first. Derive the
recording time from them:

```text
recordingTimeRaw = 1.20 * tTraverse
sourceCycle = verified source or Motion update cycle
recordingInterval = sourceCycle * integerMultiplier
memoryDepth = ceil(recordingTimeRaw / recordingInterval)
recordingTime = memoryDepth * recordingInterval
preTrigger = 10
```

`preTrigger` is a percentage of the recording window. `recordingTime` is
written in nanoseconds, as is `recordingInterval`. Therefore:

```text
300 samples * 100 ms = 30 s
301 samples * 1 ms = 0.301 s
```

Do not choose an interval arbitrarily smaller than the source or Motion cycle.
Use the smallest verified cycle-aligned interval that the source supports,
normally one cycle or an integer multiple of it. If the cycle is unknown,
verify it through the Motion/scheduler documentation or UI before configuring
the capture; do not assume `1 ms`.

Always round the raw recording time up to a complete sample. Otherwise the UI
can report `memory depth not valid`. Verify both values after writing the
buffer; do not infer the UI time scale from the diagram alone.

After changing timing values in the Web UI, read `cfg/buffer` back through the
Data Layer and verify the conversion. The Data Layer values are authoritative.
Do not assume that a value displayed as milliseconds or seconds in the UI was
written with the same numeric scale. A capture must not be started until the
read-back interval, recording time, and derived integer memory depth match the
intended values.

For `safeMin -> safeMax`, use:

```json
{
  "type": "object",
  "value": {
    "triggerType": "RisingEdge",
    "name": "NRTpos1",
    "level": "<safeMin + epsilon in SI units>",
    "preTrigger": 10
  }
}
```

For `safeMax -> safeMin`, use `FallingEdge` and
`safeMax - epsilon`. Do not use `RisingFalling` at the midpoint when the
acceptance criterion is 10 % before and 10 % after one complete traverse.
Do not use `Manual` or `cmd/trigger`.

## Configure, arm, and read

Example channel:

```text
CREATE oscilloscope/instances/myOsc/cfg/channels
{
  "type": "object",
  "value": {
    "name": "NRTpos1",
    "alias": "motion/axs/MyAxis/state/values/actual/pos/m",
    "source": "motion/axs/MyAxis/state/values/actual/pos/m",
    "type": "NRT",
    "unit": "m"
  }
}
```

Example view:

```text
CREATE oscilloscope/instances/myOsc/cfg/diagrams/Diagram_1/views
{
  "type": "object",
  "value": {
    "source": "NRTpos1",
    "color": "#3498db",
    "visible": true,
    "connectionType": "LINE"
  }
}
```

Use `SINGLESHOT` for every normal finite traverse. Calculate its recording
time from the motion profile and round it to an integral memory depth. After
all verification:

```text
CREATE oscilloscope/instances/myOsc/cmd/start
{"type":"bool8","value":true}
```

Use an existing ctrlX browser tab and navigate it to:

```text
https://<device>/oscilloscope/<instanceName>
```

Open a new tab only if no ctrlX tab exists.

The verified state enum is zero-based:

| Value | State |
|---:|---|
| 0 | `NOT_CONFIGURED` |
| 1 | `CONFIGURED` |
| 2 | `STARTING` |
| 3 | `WAIT_FOR_TRIGGER` |
| 4 | `TRIGGERED` |
| 5 | `RECORDING_COMPLETED` |
| 6 | `RECORDING` |
| 7 | `ERROR` |
| 8 | `SAVEDATA` |

Read only the aggregate recording:

```text
READ oscilloscope/instances/myOsc/rec-values/allsignals
```

## Validate and reset

A successful start or trigger response proves only that configuration was
accepted. Validate channel names, nonempty samples, timestamp span, expected
position range, selected direction, units, and integral memory depth.

After reading the data:

1. Do not stop a normal `SINGLESHOT` capture manually. It must finish from its
   configured recording time.
2. Create the background power-off command:

   ```text
   CREATE motion/axs/<axisName>/cmd/power
   {"type":"bool8","value":false}
   ```

3. Verify PLCopen state `DISABLED`.
4. Do not command an automatic return move.

For NRT/SINGLESHOT on the verified virtual target, completion may remain in
`TRIGGERED` or `RECORDING`. Do not silently switch to `REPEAT` or stop the
capture automatically. Report the capture as incomplete and explain that a
time-resolved NRT result is unavailable on that target.

On the verified virtual rotational axis, `SINGLESHOT` with NRT position,
velocity, and acceleration channels returned empty slices even though the
axis moved and the automatic trigger fired. A `REPEAT` buffer with the same
automatic trigger produced samples. Use `REPEAT` only when the user explicitly
requests a diagnostic fallback; it is not part of the normal workflow.

## Troubleshooting

| Symptom | Action |
|---|---|
| `NOT_CONFIGURED` | Browse and read the exact source before creating it |
| `DL_SUBMODULE_FAILURE` at start | Verify NRT channel type, source, alias, and colored views |
| `DL_TYPE_MISMATCH` for a view | Add the required hexadecimal `color` |
| `DL_INVALID_VALUE` for instance name | Use camelCase only |
| `DL_INVALID_ADDRESS` for channel data | Read `rec-values/allsignals` |
| `memory depth not valid` | Round `recordingTime / recordingInterval` up to an integer |
| RT channel rejected | Use RT only when the exact source is registered below `datalayer/nodesrt` |
