# -*- coding:utf-8 -*-
"""iotlabsshcli parser for Open Linux nodes cli."""

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

import os.path
from collections import OrderedDict
from iotlabsshcli.sshlib import OpenLinuxSsh


def _nodes_grouped(nodes):
    """Group nodes per site from a list of nodes.
    >>> _nodes_grouped([])
    OrderedDict()
    >>> _nodes_grouped(['node-a8-1.grenoble.iot-lab.info',
    ...                 'node-a8-2.grenoble.iot-lab.info',
    ...                 'node-a8-2.saclay.iot-lab.info',
    ...                 'node-a8-2.lille.iot-lab.info'])
    ... # doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('grenoble.iot-lab.info',
                  ['node-a8-1.grenoble.iot-lab.info',
                   'node-a8-2.grenoble.iot-lab.info']),
                 ('saclay.iot-lab.info', ['node-a8-2.saclay.iot-lab.info']),
                 ('lille.iot-lab.info', ['node-a8-2.lille.iot-lab.info'])])
    """
    result = OrderedDict()
    for host in nodes:
        site = host.split('.', 1)[1]
        if site not in result:
            result.update({site: [host]})
        else:
            result[site].append(host)
    return result


_FLASH_CMD = 'source /etc/profile && /usr/bin/iotlab_flash {}'
_RESET_CMD = 'source /etc/profile && /usr/bin/iotlab_reset'
_MAKE_EXECUTABLE_CMD = 'chmod +x {}'
_RUN_SCRIPT_CMD = 'screen -S {screen} -dm bash -c \"{path}\"'
_QUIT_SCRIPT_CMD = 'screen -X -S {screen} quit'
_REMOTE_SHARED_DIR = 'shared/.iotlabsshcli'


def flash(config_ssh, nodes, firmware, verbose=False):
    """Flash the firmware of co-microcontroller """
    failed_hosts = []
    # configure ssh and remote firmware names.
    groups = _nodes_grouped(nodes)
    ssh = OpenLinuxSsh(config_ssh, groups, verbose=verbose)
    remote_fw = os.path.join(_REMOTE_SHARED_DIR, os.path.basename(firmware))
    # copy the firmware to the site SSH servers
    # scp create remote directory if it doesn't exist
    result = ssh.scp(firmware, remote_fw)
    # We delete failed hosts for the next command
    if '1' in result:
        failed_hosts = [ssh.groups.pop(res) for res in result['1']]
    # Run firmware update.
    result = ssh.run(_FLASH_CMD.format(remote_fw))
    for hosts in failed_hosts:
        result.setdefault('1', []).extend(hosts)
    return {"flash": result}


def reset(config_ssh, nodes, verbose=False):
    """Reset co-microcontroller """

    # Configure ssh
    groups = _nodes_grouped(nodes)
    ssh = OpenLinuxSsh(config_ssh, groups, verbose=verbose)
    # Run reset command
    return {"reset": ssh.run(_RESET_CMD)}


def wait_for_boot(config_ssh, nodes, max_wait=120, verbose=False):
    """Wait for the open Linux nodes boot """

    # Configure ssh.
    groups = _nodes_grouped(nodes)
    ssh = OpenLinuxSsh(config_ssh, groups, verbose=verbose)
    # Wait for boot
    return {"wait-for-boot": ssh.wait(max_wait)}


def run_cmd(config_ssh, nodes, cmd, run_on_frontend=False, verbose=False):
    """Run a command on the Linux nodes or SSH frontend servers """

    # Configure ssh.
    groups = _nodes_grouped(nodes)
    ssh = OpenLinuxSsh(config_ssh, groups, verbose=verbose)
    return {"run-cmd": ssh.run(cmd, with_proxy=not run_on_frontend)}


def copy_file(config_ssh, nodes, file_path, verbose=False):
    """Copy a file to SSH frontend servers """

    # Configure ssh.
    groups = _nodes_grouped(nodes)
    ssh = OpenLinuxSsh(config_ssh, groups, verbose=verbose)
    # relative path with native client
    remote_file = os.path.join(_REMOTE_SHARED_DIR, os.path.basename(file_path))
    result = ssh.scp(file_path, remote_file)
    return {"copy-file": result}


def _get_failed_result(groups, result, run_on_frontend):
    """Returns failed nodes or SSH frontend servers list.

    We delete failed hosts for the next commands in the groups
    """
    failed = []
    if '1' in result and result['1']:
        if not run_on_frontend:
            # nodes list
            for site in result['1']:
                failed.extend(groups[site])
                del groups[site]
        else:
            # servers list
            failed.extend(result['1'])
            all(map(groups.pop, result['1']))
    return failed


def run_script(config_ssh, nodes, script, run_on_frontend=False,
               verbose=False):
    """Run a script in background on Linux nodes or SSH frontend servers """

    # Configure ssh.
    failed_hosts = []
    groups = _nodes_grouped(nodes)
    ssh = OpenLinuxSsh(config_ssh, groups, verbose=verbose)
    screen = '{user}-{exp_id}'.format(**config_ssh)
    remote_script = os.path.join(_REMOTE_SHARED_DIR, os.path.basename(script))
    script_data = {'screen': screen, 'path': remote_script}
    # Copy script on SSH frontend servers
    scp_result = ssh.scp(script, remote_script)
    failed_hosts.append(_get_failed_result(ssh.groups, scp_result,
                                           run_on_frontend))
    # Make script executable
    run_result = ssh.run(_MAKE_EXECUTABLE_CMD.format(remote_script),
                         with_proxy=False)
    failed_hosts.append(_get_failed_result(ssh.groups, run_result,
                                           run_on_frontend))
    # Try cleanup and kill any running script (don't check the result)
    ssh.run(_QUIT_SCRIPT_CMD.format(**script_data),
            with_proxy=not run_on_frontend)
    # Run script
    result = ssh.run(_RUN_SCRIPT_CMD.format(**script_data),
                     with_proxy=not run_on_frontend, use_pty=False)
    for hosts in filter(None, failed_hosts):
        result.setdefault('1', []).extend(hosts)
    return {"run-script": result}
