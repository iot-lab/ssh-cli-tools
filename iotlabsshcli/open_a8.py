# -*- coding:utf-8 -*-
"""iotlabsshcli parser for Open A8 cli."""

# This file is a part of IoT-LAB ssh-cli-tools
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

from __future__ import print_function

import os.path

from collections import OrderedDict
from iotlabsshcli.sshlib import OpenA8Ssh, OpenA8SshAuthenticationException


def _nodes_grouped(nodes):
    """Group nodes per site from a list of nodes.
    >>> _nodes_grouped([])
    OrderedDict()
    >>> _nodes_grouped(['node-a8-1.grenoble.iot-lab.info',
    ...                 'node-a8-2.grenoble.iot-lab.info',
    ...                 'node-a8-2.saclay.iot-lab.info',
    ...                 'node-a8-2.lille.iot-lab.info'])
    ... # doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('grenoble', ['node-a8-1', 'node-a8-2']),
    ('saclay', ['node-a8-2']), ('lille', ['node-a8-2'])])
    """
    result = OrderedDict()
    for host in nodes:
        node = host.split('.')[0]
        site = host.split('.')[1]
        if site not in result:
            result.update({site: [node]})
        else:
            result[site].append(node)

    return result


_MKDIR_DST_CMD = 'mkdir -p {}'
_UPDATE_M3_CMD = 'source /etc/profile && /usr/bin/flash_a8_m3 {}'
_RESET_M3_CMD = 'source /etc/profile && /usr/bin/reset_a8_m3'
_MAKE_EXECUTABLE_CMD = 'chmod +x {}'
_RUN_SCRIPT_CMD = 'screen -S {screen} -dm bash -c \"{path}\"'
_QUIT_SCRIPT_CMD = 'screen -X -S {screen} quit'


def flash_m3(config_ssh, nodes, firmware, verbose=False):
    """Flash the firmware of M3 of open A8 nodes."""
    # Configure ssh and remote firmware names.
    groups = _nodes_grouped(nodes)
    ssh = OpenA8Ssh(config_ssh, groups, verbose=verbose)
    remote_fw = os.path.join('~/A8/.iotlabsshcli', os.path.basename(firmware))

    # Create firmware destination directory
    try:
        ssh.run(_MKDIR_DST_CMD.format(os.path.dirname(remote_fw)))
    except OpenA8SshAuthenticationException as exc:
        print(exc.msg)
        result = {"1": nodes}
    else:
        # Copy firmware on sites.
        ssh.scp(firmware, remote_fw)

        # Run firmware update.
        result = ssh.run(_UPDATE_M3_CMD.format(remote_fw))

    return {"flash-m3": result}


def reset_m3(config_ssh, nodes, verbose=False):
    """Reset the M3 of open A8 nodes."""

    # Configure ssh.
    groups = _nodes_grouped(nodes)
    ssh = OpenA8Ssh(config_ssh, groups, verbose=verbose)

    # Run M3 reset command.
    try:
        result = ssh.run(_RESET_M3_CMD)
    except OpenA8SshAuthenticationException as exc:
        print(exc.msg)
        result = {"1": nodes}

    return {"reset-m3": result}


def wait_for_boot(config_ssh, nodes, max_wait=120, verbose=False):
    """Reset the M3 of open A8 nodes."""

    # Configure ssh.
    groups = _nodes_grouped(nodes)
    ssh = OpenA8Ssh(config_ssh, groups, verbose=verbose)

    # Wait for A8 boot
    try:
        result = ssh.wait(max_wait)
    except OpenA8SshAuthenticationException as exc:
        print(exc.msg)
        result = {"1": nodes}

    return {"wait-for-boot": result}


def run_script(config_ssh, nodes, script, verbose=False):
    """Run a script in background on the A8 nodes."""

    # Configure ssh.
    groups = _nodes_grouped(nodes)
    ssh = OpenA8Ssh(config_ssh, groups, verbose=verbose)

    screen = '{user}-{exp_id}'.format(**config_ssh)
    remote_script = os.path.join('~/A8/.iotlabsshcli',
                                 os.path.basename(script))
    script_data = {'screen': screen,
                   'path': remote_script}

    # Create destination directory
    ssh.run(_MKDIR_DST_CMD.format(os.path.dirname(remote_script)))

    # Copy script on sites.
    ssh.scp(script, remote_script)

    # Make script executable
    ssh.run(_MAKE_EXECUTABLE_CMD.format(remote_script))

    # Kill any running script
    ssh.run(_QUIT_SCRIPT_CMD.format(**script_data))

    # Run script on all nodes
    result = ssh.run(_RUN_SCRIPT_CMD.format(**script_data))

    return {"run-script": result}
