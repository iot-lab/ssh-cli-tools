# -*- coding: utf-8 -*-

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

"""Tests for iotlabsshcli.open_linux package."""

import os.path
from pytest import mark

from iotlabsshcli.open_linux import reset, flash, wait_for_boot, run_script
from iotlabsshcli.open_linux import run_cmd, copy_file
from iotlabsshcli.open_linux import (_RESET_CMD, _FLASH_CMD,
                                     _RUN_SCRIPT_CMD,
                                     _QUIT_SCRIPT_CMD, _MAKE_EXECUTABLE_CMD)
from .compat import patch

_SACLAY_NODES = ['node-a8-{}.saclay.iot-lab.info'.format(n)
                 for n in range(1, 6)]
_GRENOBLE_NODES = ['node-a8-{}.grenoble.iot-lab.info'.format(n)
                   for n in range(1, 4)]
_ROOT_NODES = _SACLAY_NODES + _GRENOBLE_NODES


@patch('iotlabsshcli.sshlib.OpenLinuxSsh.run')
@patch('iotlabsshcli.sshlib.OpenLinuxSsh.scp')
def test_open_linux_flash(scp, run):
    """Test flashing a firmware."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }
    firmware = '/tmp/firmware.elf'
    remote_fw = os.path.join('shared/.iotlabsshcli',
                             os.path.basename(firmware))
    scp.return_value = {'0': ['saclay.iot-lab.info'],
                        '1': ['grenoble.iot-lab.info']}

    return_value = {'0': _SACLAY_NODES}
    run.return_value = return_value
    return_value.get('1', []).extend(_GRENOBLE_NODES)
    ret = flash(config_ssh, _ROOT_NODES, firmware)

    assert ret == {'flash': return_value}
    scp.assert_called_once_with(firmware, remote_fw)
    assert run.call_count == 1
    run.mock_calls[0].assert_called_with(
        _FLASH_CMD.format(fw=remote_fw, bin="")
    )

    # Cover the case where a .bin firmware is used
    scp.call_count = 0
    run.call_count = 0
    firmware = '/tmp/firmware.bin'
    remote_fw = os.path.join('shared/.iotlabsshcli',
                             os.path.basename(firmware))
    ret = flash(config_ssh, _ROOT_NODES, firmware)

    assert ret == {'flash': return_value}
    scp.assert_called_once_with(firmware, remote_fw)
    assert run.call_count == 1
    run.mock_calls[0].assert_called_with(
        _FLASH_CMD.format(fw=remote_fw, bin="--bin")
    )


@patch('iotlabsshcli.sshlib.OpenLinuxSsh.run')
def test_open_linux_reset(run):
    """Test resetting co-microcontroller."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }
    return_value = {'0': 'test'}
    run.return_value = return_value

    ret = reset(config_ssh, _ROOT_NODES)
    assert ret == {'reset': return_value}

    run.assert_called_once_with(_RESET_CMD)


@patch('iotlabsshcli.sshlib.OpenLinuxSsh.wait')
def test_open_linux_wait_for_boot(wait):
    """Test wait for Linux boot."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }
    return_value = {'0': 'test'}
    wait.return_value = return_value

    ret = wait_for_boot(config_ssh, _ROOT_NODES)
    assert ret == {'wait-for-boot': return_value}

    wait.assert_called_once_with(120)


@mark.parametrize('run_on_frontend', [False, True])
@patch('iotlabsshcli.sshlib.OpenLinuxSsh.run')
@patch('iotlabsshcli.sshlib.OpenLinuxSsh.scp')
def test_open_linux_run_script(scp, run, run_on_frontend):
    """Test run script on Linux nodes."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }
    screen = '{user}-{exp_id}'.format(**config_ssh)
    script = '/tmp/script.sh'
    remote_script = os.path.join('shared/.iotlabsshcli',
                                 os.path.basename(script))
    script_data = {'screen': screen,
                   'path': remote_script}
    scp.return_value = {'0': ['saclay.iot-lab.info'],
                        '1': ['grenoble.iot-lab.info']}
    if not run_on_frontend:
        return_value = {'0': _SACLAY_NODES}
    else:
        return_value = {'0': ['saclay.iot-lab.info']}
    run.side_effect = [return_value for _n in range(3)]

    if not run_on_frontend:
        return_value.get('1', []).extend(['grenoble.iot-lab.info'])
    else:
        return_value.get('1', []).extend(_GRENOBLE_NODES)
    ret = run_script(config_ssh, _ROOT_NODES, script,
                     run_on_frontend=run_on_frontend)

    assert ret == {'run-script': return_value}
    scp.assert_called_once_with(script, remote_script)
    assert run.call_count == 3

    run.mock_calls[0].assert_called_with(
        _MAKE_EXECUTABLE_CMD.format(os.path.dirname(remote_script)),
        with_proxy=False)
    run.mock_calls[1].assert_called_with(
        _QUIT_SCRIPT_CMD.format(**script_data),
        with_proxy=not run_on_frontend)
    run.mock_calls[2].assert_called_with(
        _RUN_SCRIPT_CMD.format(**script_data),
        use_pty=False,
        with_proxy=not run_on_frontend)


@patch('iotlabsshcli.sshlib.OpenLinuxSsh.scp')
def test_open_linux_copy_file(scp):
    """Test copy file on the SSH frontend."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }
    file_path = '/tmp/script.sh'
    remote_file = os.path.join('shared/.iotlabsshcli',
                               os.path.basename(file_path))
    return_value = {'0': 'test'}
    scp.return_value = return_value

    ret = copy_file(config_ssh, _ROOT_NODES, file_path)
    assert ret == {'copy-file': return_value}

    scp.assert_called_once_with(file_path, remote_file)


@mark.parametrize('run_on_frontend', [False, True])
@patch('iotlabsshcli.sshlib.OpenLinuxSsh.run')
def test_open_linux_run_cmd(run, run_on_frontend):
    """Test run command on Linux nodes."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }
    cmd = 'uname -a'
    return_value = {'0': 'test'}
    run.return_value = return_value

    ret = run_cmd(config_ssh, _ROOT_NODES, cmd,
                  run_on_frontend=run_on_frontend)
    run.assert_called_once_with(cmd, with_proxy=not run_on_frontend)
    assert ret == {'run-cmd': return_value}
