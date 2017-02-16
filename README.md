## SSH CLI Tools

SSH CLI Tools provides a set of commands for interacting remotely and easily
with IoT-Lab Open A8 nodes. See [here](https://www.iot-lab.info/hardware/a8/)
to get more information on this kind of node.

All available actions provided by SSH CLI Tools are available as sub-commands
of `open-a8-cli`.

The provided sub-commands are:

| Sub-command  | Function |
| ------------ | -------- |
| `flash-m3`   | Flash the given firmware on the M3 MCU of A8 nodes |
| `reset-m3`   | Reset the M3 node of A8 nodes |
| `wait-for-boot`   | Block the execution until all given A8 nodes have booted or maximum wait time has expired |
| `run-script`  | Run a given script in background (screen session) on the given A8 nodes |
| `run-cmd`   | Run a command on the given A8 nodes |
| `copy-file`   | Copy a file on SSH frontend homedir directory (~/A8/.iotlabsshcli) |

SSH CLI Tools can be used in conjunction with the
[IoT-Lab CLI Tools](https://github.com/iot-lab/cli-tools) commands like
`auth-cli` and `experiment-cli`.

### Installation:

[build-icon]: https://travis-ci.org/iot-lab/ssh-cli-tools.svg?branch=master
[build-page]: https://travis-ci.org/iot-lab/ssh-cli-tools/branches
[coverage-icon]: https://codecov.io/gh/iot-lab/ssh-cli-tools/branch/master/graph/badge.svg
[coverage-page]: https://codecov.io/gh/iot-lab/ssh-cli-tools/branch/master

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

### Requirements:

Open A8 nodes are reachable through a gateway SSH server (IoT-LAB SSH
frontend). For this reason you must verify that your SSH public key used by
ssh-cli-tools has been recorded in your IoT-LAB user profile. You can find how
to configure your IoT-LAB SSH access in this
[tutorial](https://www.iot-lab.info/tutorials/configure-your-ssh-access/).

### Examples:

#### Start an experiment, wait for it to be ready, wait for all A8 boot:
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
<b>Note:</b> node-a8-4 and node-a8-8 are broken in Saclay.

#### Flash a firmware on the M3 of the working node:
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

#### Reset the M3 of one A8 node:
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

#### Use the `--verbose` option to get the commands output:
```
$ open-a8-cli --verbose reset-m3 -l saclay,a8,2
Connecting via SSH proxy saclay.iot-lab.info:22 -> node-a8-2.saclay.iot-lab.info:22
[node-a8-2.saclay.iot-lab.info]	Open On-Chip Debugger 0.9.0-dirty (2016-04-15-00:55)
[node-a8-2.saclay.iot-lab.info]	Licensed under GNU GPL v2
[node-a8-2.saclay.iot-lab.info] For bug reports, read
[node-a8-2.saclay.iot-lab.info]	http://openocd.org/doc/doxygen/bugs.html
[node-a8-2.saclay.iot-lab.info]	adapter speed: 1000 kHz
[...]
[node-a8-2.saclay.iot-lab.info]	TargetName         Type       Endian TapName            State
[node-a8-2.saclay.iot-lab.info]	--  ------------------ ---------- ------ ------------------ ------------
[node-a8-2.saclay.iot-lab.info] 0* stm32f1x.cpu       cortex_m   little stm32f1x.cpu       running
[node-a8-2.saclay.iot-lab.info]	Info : JTAG tap: stm32f1x.cpu tap/device found: 0x3ba00477 (mfg: 0x23b, part: 0xba00, ver: 0x3)
[node-a8-2.saclay.iot-lab.info]	Info : JTAG tap: stm32f1x.bs tap/device found: 0x06414041 (mfg: 0x020, part: 0x6414, ver: 0x0)
[node-a8-2.saclay.iot-lab.info]	shutdown command invoked
[node-a8-2.saclay.iot-lab.info]	Return Value: 0
{
    "reset-m3": {
        "0": [
            "node-a8-2.saclay.iot-lab.info"
        ]
    }
}
```
#### Run a command on two A8 nodes:
```
$ open-a8-cli --verbose run-cmd "uname -a" -l saclay,a8,2-3
Connecting via SSH proxy saclay.iot-lab.info:22 -> node-a8-2.saclay.iot-lab.info:22
[node-a8-2.saclay.iot-lab.info]	Linux node-a8-2 3.18.5-iotlab+ #9 Thu Sep 1 16:17:22 CEST 2016 armv7l GNU/Linux
[node-a8-3.saclay.iot-lab.info]	Linux node-a8-3 3.18.5-iotlab+ #9 Thu Sep 1 16:17:22 CEST 2016 armv7l GNU/Linux
{
    "run-cmd": {
        "0": [
            "node-a8-2.saclay.iot-lab.info",
            "node-a8-3.saclay.iot-lab.info"
        ]
    }
}
```
#### Run a command on SSH frontend: 
```
$ open-a8-cli --verbose run-cmd "uname -a" --frontend
[saclay.iot-lab.info]	Linux saclay 3.16.0-4-amd64 #1 SMP Debian 3.16.36-1+deb8u1 (2016-09-03) x86_64 GNU/Linux
{
    "run-cmd": {
        "0": [
            "saclay.iot-lab.info"
        ]
    }
}
```
#### Copy file on SSH frontend homedir directory (~/A8/.iotlabsshcli):
```
$ open-a8-cli copy-file test.tar.gz 
{
    "run-cmd": {
        "0": [
            "saclay.iot-lab.info"
        ]
    }
}
$ open-a8-cli run-cmd "tar -xzvf ~/A8/.iotlabsshcli/test.tar.gz -C ~/A8/.iotlabsshcli/" --frontend
{
    "run-cmd": {
        "0": [
            "saclay.iot-lab.info"
        ]
    }
}
```
<b>Note:</b> A8 homedir directory is mounted (via NFS) by A8 nodes during experiment.

#### Run the script `/tmp/test.sh` on `node-a8-2` in saclay:
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
<b>Note:</b> a screen session is launched on the A8 node
to actually run the script and provide easy access to outputs if needed.
When the script ends, the screen session is terminated and the logs are gone.

```
root@node-a8-2:~# screen -ls
There is a screen on:
	1877.<login>-<exp_id>	(Detached)
1 Socket in /tmp/screens/S-root.
```
<b>Note:</b> similar to run command you can pass --frontend option if you want to launch a script
in background on the SSH frontend.
