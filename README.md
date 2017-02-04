## SSH CLI Tools

SSH CLI Tools provides a set of commands for interacting remotely and easily
with IoT-Lab Open A8 nodes. See [here](https://www.iot-lab.info/hardware/a8/)
to get more information on this kind of node.

All available actions provided by SSH CLI Tools are available as sub-commands
of `open-a8-cli`.

The provided sub-commands are:

| Sub-command  | Function |
| ------------ | -------- |
| `flash-m3`   | Flash the given firmware on the M3 MCU of the A8 node. |
| `reset-m3`   | Reset the M3 node. |
| `wait-for-boot`  | Block the execution until all given nodes have booted or maximum wait time has expired |
| `run-script`  | Run a given script in background on the given nodes |

SSH CLI Tools can be used in conjunction with the
[IoT-Lab CLI Tools](https://github.com/iot-lab/cli-tools) commands like
`auth-cli` and `experiment-cli`.

### Installation:

[build-icon]: https://travis-ci.org/iot-lab/ssh-cli-tools.svg?branch=master
[build-page]: https://travis-ci.org/iot-lab/ssh-cli-tools
[coverage-icon]: https://codecov.io/gh/iot-lab/ssh-cli-tools/branch/master/graph/badge.svg
[coverage-page]: https://codecov.io/gh/iot-lab/ssh-cli-tools

[![build][build-icon]][build-page]  [![codecov][coverage-icon]][coverage-page]

You need python [pip](https://pip.pypa.io/en/stable/).
Pip version >= 9.0 is known to work ; you may need to upgrade.
See INSTALLING.md for details on installation options.

To do a system-wide install of the ssh-cli-tools,
clone this repository and use pip (or pip3 for Python 3):
```
$ git clone https://github.com/iot-lab/ssh-cli-tools.git
$ cd ssh-cli-tools
$ sudo pip install .
```
### Requirement:

### Requirements:

Open A8 nodes are reachable through a gateway SSH server (eg. IoT-LAB SSH
frontend). For this reason you must verify that your SSH public key used by
ssh-cli-tools has been recorded in your IoT-LAB user profile. You can find how
to configure your IoT-LAB SSH access in this
[tutorial](https://www.iot-lab.info/tutorials/configure-your-ssh-access/).

### Examples:

* Start an experiment, wait for it ot be ready, wait for all A8 boot
```
$ experiment-cli submit -d 120 -l saclay,a8,1-10
{
    "id": 65535
}
$ experiment-cli wait
Waiting that experiment 65535 gets in state Running
"Running"
$ open-a8-cli wait-for-boot
{
    "wait-for-boot": {
        "0": [
            "node-a8-2.saclay.iot-lab.info",
            "node-a8-3.saclay.iot-lab.info",
            "node-a8-5.saclay.iot-lab.info",
            "node-a8-6.saclay.iot-lab.info",
            "node-a8-7.saclay.iot-lab.info",
            "node-a8-9.saclay.iot-lab.info",
            "node-a8-10.saclay.iot-lab.info"
        ],
        "1": [
            "node-a8-4.saclay.iot-lab.info",
            "node-a8-8.saclay.iot-lab.info"
        ]
    }
}
```
Note: node-a8-4 and node-a8-8 are broken in Saclay.
* Flash a firmware on the M3 of the working nodes:
```
$ open-a8-cli flash-m3 <firmware.elf> -l saclay,a8,2-3+5-7+9-10
{
    "flash-m3": {
        "0": [
            "node-a8-2.saclay.iot-lab.info",
            "node-a8-3.saclay.iot-lab.info",
            "node-a8-5.saclay.iot-lab.info",
            "node-a8-6.saclay.iot-lab.info",
            "node-a8-7.saclay.iot-lab.info",
            "node-a8-9.saclay.iot-lab.info",
            "node-a8-10.saclay.iot-lab.info"
        ]
    }
}
```
* Run the script `/tmp/test.sh` on `node-a8-2` in saclay:
```
$ open-a8-cli run-script /tmp/test.sh -l saclay,a8,2
{
    "run-script": {
        "0": [
            "node-a8-2.saclay.iot-lab.info"
        ]
    }
}
```
* Reset the M3 of one A8 node:
```
$ open-a8-cli reset-m3 -l saclay,a8,2
{
    "reset-m3": {
        "0": [
            "node-a8-2.saclay.iot-lab.info"
        ]
    }
}
```
* Use the `--verbose` option to get the commands output:
```
$ open-a8-cli --verbose reset-m3 -l saclay,a8,2
Connecting via SSH proxy saclay.iot-lab.info:22 -> node-a8-2:22
[node-a8-2]	Open On-Chip Debugger 0.9.0-dirty (2016-04-15-00:55)
[node-a8-2]	Licensed under GNU GPL v2
[node-a8-2]	For bug reports, read
[node-a8-2]	http://openocd.org/doc/doxygen/bugs.html
[node-a8-2]	adapter speed: 1000 kHz
[...]
[node-a8-2]	TargetName         Type       Endian TapName            State
[node-a8-2]	--  ------------------ ---------- ------ ------------------ ------------
[node-a8-2]	0* stm32f1x.cpu       cortex_m   little stm32f1x.cpu       running
[node-a8-2]	Info : JTAG tap: stm32f1x.cpu tap/device found: 0x3ba00477 (mfg: 0x23b, part: 0xba00, ver: 0x3)
[node-a8-2]	Info : JTAG tap: stm32f1x.bs tap/device found: 0x06414041 (mfg: 0x020, part: 0x6414, ver: 0x0)
[node-a8-2]	shutdown command invoked
[node-a8-2]	Return Value: 0
{
    "reset-m3": {
        "0": [
            "node-a8-2.saclay.iot-lab.info"
        ]
    }
}
```
