---
name: service-indicator
description: "Use to retrieve health status information about drives and motors. This is important for condition monitoring and shows the consumed lifetime of the drives and motors."
license: Proprietary. LICENSE.txt has complete terms
---

# Service Indicator

For this skill to work the `Service Indicator App` and `Drive Connect App` need to be installed.
In addition the license `SWL-XC*-SIN-SIN**********-BANN` is needed.

## List of Drives

The list of the drives can be found in the data layer below `service-indicator/devices`.
Each drive can have one or multiple subdevices.

## Drive Status

The following nodes provide the current health state of the drives.

| Operation | Path | Node Description | Advanced description |
|-----------|------|-------------|----------------|
| READ | `service-indicator/devices/<drive-id>/subdevices/<subdevice-id>/drive-health` | Status of the Drive | |
| READ | `service-indicator/devices/<drive-id>/subdevices/<subdevice-id>/drive-used-lifetime-estimated` | Consumed life time | |

## Motor Status

The following nodes provide the current health state of the motors.

| Operation | Path | Node Description | Advanced description |
|-----------|------|-------------|----------------|
| READ | `service-indicator/devices/<drive-id>/subdevices/<subdevice-id>/motor-health` | Status of the Motor | |
| READ | `service-indicator/devices/<drive-id>/subdevices/<subdevice-id>/motor-used-lifetime-estimated` | Consumed life time | |

## Further Support

If the status of a motor or drive is not OK, then give a hint to contact the Bosch Rexroth Service at `https://www.boschrexroth.com/en/id/contact/contact-locator/` or call by phone `+49 9352 405060`
