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

"""Tests for iotlabsshcli.open_a8 package."""

import os.path
from iotlabsshcli.open_a8 import reset_m3, flash_m3, wait_for_boot
from iotlabsshcli.open_a8 import _RESET_M3_CMD, _UPDATE_M3_CMD, _MKDIR_DST_CMD
from iotlabsshcli.sshlib import OpenA8SshAuthenticationException
from .compat import patch

# pylint: disable=too-many-public-methods
# pylint: disable=too-few-public-methods

_NODES = ['a8-{}.{}.iot-lab.info'.format(n, s)
          for n in range(1, 6) for s in ['saclay', 'grenoble']]
_ROOT_NODES = ['node-{}'.format(node) for node in _NODES]


@patch('iotlabsshcli.sshlib.OpenA8Ssh.run')
@patch('iotlabsshcli.sshlib.OpenA8Ssh.scp')
def test_open_a8_flash_m3(scp, run):
    """Test flashing an M3."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }
    firmware = '/tmp/firmware.elf'
    remote_fw = os.path.join('~/A8/.iotlabsshcli', os.path.basename(firmware))
    return_value = {'0': 'test'}
    run.return_value = return_value

    ret = flash_m3(config_ssh, _ROOT_NODES, firmware)

    assert ret == {'flash-m3': return_value}
    scp.assert_called_once_with(firmware, remote_fw)
    assert run.call_count == 2
    run.mock_calls[0].assert_called_with(
        _MKDIR_DST_CMD.format(os.path.dirname(remote_fw)))
    run.mock_calls[1].assert_called_with(_UPDATE_M3_CMD.format(remote_fw))

    # Raise an exception
    run.side_effect = OpenA8SshAuthenticationException('test')
    ret = flash_m3(config_ssh, _ROOT_NODES, firmware)
    assert ret == {'flash-m3': {'1': _ROOT_NODES}}


@patch('iotlabsshcli.sshlib.OpenA8Ssh.run')
def test_open_a8_reset_m3(run):
    """Test resetting an M3."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }
    return_value = {'0': 'test'}
    run.return_value = return_value

    ret = reset_m3(config_ssh, _ROOT_NODES)
    assert ret == {'reset-m3': return_value}

    run.assert_called_once_with(_RESET_M3_CMD)

    # Raise an exception
    run.side_effect = OpenA8SshAuthenticationException('test')
    ret = reset_m3(config_ssh, _ROOT_NODES)
    assert ret == {'reset-m3': {'1': _ROOT_NODES}}


@patch('iotlabsshcli.sshlib.OpenA8Ssh.wait')
def test_open_a8_wait_for_boot(wait):
    """Test wait for A8 boot."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }
    return_value = {'0': 'test'}
    wait.return_value = return_value

    ret = wait_for_boot(config_ssh, _ROOT_NODES)
    assert ret == {'wait-for-boot': return_value}

    wait.assert_called_once_with(120)

    # Raise an exception
    wait.side_effect = OpenA8SshAuthenticationException('test')
    ret = wait_for_boot(config_ssh, _ROOT_NODES)
    assert ret == {'wait-for-boot': {'1': _ROOT_NODES}}
