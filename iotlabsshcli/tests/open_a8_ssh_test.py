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

from pytest import raises, mark
from pssh.exceptions import AuthenticationException, ConnectionErrorException

from iotlabsshcli.open_a8 import _nodes_grouped
from iotlabsshcli.sshlib import OpenA8Ssh, OpenA8SshAuthenticationException
from .compat import patch

_SITES = ['saclay', 'grenoble']
_NODES = ['a8-{}.{}.iot-lab.info'.format(n, s)
          for n in range(1, 6) for s in _SITES]
_ROOT_NODES = ['node-{}'.format(node) for node in _NODES]


@mark.parametrize('run_on_frontend', [False, True])
@patch('pssh.clients.ParallelSSHClient.run_command')
@patch('pssh.clients.ParallelSSHClient.join')
def test_run(join, run_command, run_on_frontend):
    # pylint: disable=unused-argument
    """Test running commands on ssh nodes."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }

    test_command = 'test'
    groups = _nodes_grouped(_ROOT_NODES)

    node_ssh = OpenA8Ssh(config_ssh, groups, verbose=True)

    # Print output of run_command
    if run_on_frontend:
        run_command.return_value = dict(
            ("{}.iot-lab.info".format(site),
             {'stdout': ['test'], 'exit_code': 0})
            for site in _SITES)
    else:
        run_command.return_value = dict(
            (node,
             {'stdout': ['test'], 'exit_code': 0})
            for node in _ROOT_NODES)

    node_ssh.run(test_command, with_proxy=not run_on_frontend)
    assert run_command.call_count == len(groups)
    run_command.assert_called_with(test_command, stop_on_errors=False)


@patch('scp.SCPClient._open')
@patch('scp.SCPClient.put')
@patch('paramiko.SSHClient')
@patch('paramiko.SSHClient.connect')
def test_scp(connect, client, put, _open):
    # pylint: disable=unused-argument
    """Test wait for ssh nodes to be available."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }

    src = 'test_src'
    dst = 'test_dst'

    groups = _nodes_grouped(_ROOT_NODES)

    node_ssh = OpenA8Ssh(config_ssh, groups, verbose=True)
    ret = node_ssh.scp(src, dst)

    assert ret == {'0': ['saclay.iot-lab.info', 'grenoble.iot-lab.info']}

    connect.side_effect = ConnectionErrorException()
    ret = node_ssh.scp(src, dst)

    assert ret == {'1': ['saclay.iot-lab.info', 'grenoble.iot-lab.info']}

    # Simulating an exception
    # pylint: disable=redefined-variable-type
    connect.side_effect = AuthenticationException()

    with raises(OpenA8SshAuthenticationException):
        node_ssh.scp(src, dst)


@patch('pssh.clients.ParallelSSHClient.run_command')
@patch('pssh.clients.ParallelSSHClient.join')
def test_wait_all_boot(join, run_command):
    # pylint: disable=unused-argument
    """Test wait for ssh nodes to be available."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }

    test_command = 'test'
    groups = _nodes_grouped(_ROOT_NODES)

    # normal boot
    node_ssh = OpenA8Ssh(config_ssh, groups, verbose=True)

    # Print output of run_command
    run_command.return_value = dict(
        (node,
         {'stdout': ['test'], 'exit_code': 0})
        for node in _ROOT_NODES)

    node_ssh.wait(120)
    assert run_command.call_count == len(_SITES)
    run_command.assert_called_with('uptime', stop_on_errors=False)
    run_command.reset_mock()

    node_ssh.run(test_command)
    assert run_command.call_count == len(_SITES)
    run_command.assert_called_with(test_command, stop_on_errors=False)


@patch('pssh.clients.ParallelSSHClient.run_command')
@patch('pssh.clients.ParallelSSHClient.join')
def test_authentication_exception(join, run_command):
    # pylint: disable=unused-argument
    """Test SSH authentication exception with parallel-ssh
    run_command and stop_on_errors=False option.
    """
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }

    test_command = 'test'
    groups = _nodes_grouped(_ROOT_NODES)

    # normal boot
    node_ssh = OpenA8Ssh(config_ssh, groups, verbose=True)

    # Print output of run_command
    run_command.return_value = dict(
        ("{}.iot-lab.info".format(site),
         {'stdout': None, 'exit_code': None})
        for site in _SITES)

    with raises(OpenA8SshAuthenticationException):
        node_ssh.run(test_command)

    # only one iteration as there is an exception
    assert run_command.call_count == 1
    run_command.assert_called_with(test_command, stop_on_errors=False)
