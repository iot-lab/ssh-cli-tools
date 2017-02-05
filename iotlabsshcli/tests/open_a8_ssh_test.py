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

from pytest import raises
from pssh.exceptions import AuthenticationException, ConnectionErrorException

from iotlabsshcli.open_a8 import _nodes_grouped
from iotlabsshcli.sshlib import OpenA8Ssh, OpenA8SshAuthenticationException
from iotlabsshcli.sshlib.open_a8_ssh import _nodes_from_groups
from .compat import patch

_NODES = ['a8-{}.{}.iot-lab.info'.format(n, s)
          for n in range(1, 6) for s in ['saclay', 'grenoble']]
_ROOT_NODES = ['node-{}'.format(node) for node in _NODES]


@patch('pssh.ParallelSSHClient.run_command')
def test_open_a8_ssh_run(run_command):
    """Test running commands on ssh nodes."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }

    test_command = 'test'
    groups = _nodes_grouped(_ROOT_NODES)

    node_ssh = OpenA8Ssh(config_ssh, groups, verbose=True)
    node_ssh.run(test_command)

    run_command.call_count = len(_ROOT_NODES)
    run_command.assert_called_with(test_command)

    # Raise an exception
    run_command.side_effect = AuthenticationException()
    with raises(OpenA8SshAuthenticationException):
        node_ssh.run(test_command)


@patch('scp.SCPClient._open')
@patch('scp.SCPClient.put')
@patch('pssh.SSHClient')
@patch('pssh.SSHClient._connect')
def test_open_a8_ssh_scp(connect, client, put, _open):
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

    assert ret is None

    # Simulating an exception
    connect.side_effect = AuthenticationException()

    with raises(OpenA8SshAuthenticationException):
        node_ssh.scp(src, dst)


@patch('pssh.SSHClient')
@patch('pssh.SSHClient._connect_tunnel')
def test_open_a8_ssh_wait(connect, client, capsys):
    # pylint: disable=unused-argument
    """Test wait for ssh nodes to be available."""
    config_ssh = {
        'user': 'username',
        'exp_id': 123,
    }
    groups = _nodes_grouped(_ROOT_NODES)

    # normal boot
    node_ssh = OpenA8Ssh(config_ssh, groups, verbose=True)
    ret = node_ssh.wait(120)
    out, err = capsys.readouterr()

    assert len(out.split('\n')) == len(_ROOT_NODES) + 1

    assert ret == {'0': _nodes_from_groups(groups)}

    # Simulating an exception
    connect.side_effect = AuthenticationException()

    with raises(OpenA8SshAuthenticationException):
        node_ssh.wait(120)

    # All nodes failing
    connect.side_effect = ConnectionErrorException()
    ret = node_ssh.wait(2)

    out, err = capsys.readouterr()
    assert len(out.split('\n')) == len(_ROOT_NODES) + 1
    assert ret == {'1': _nodes_from_groups(groups)}
