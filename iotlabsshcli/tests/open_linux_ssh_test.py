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

import os
from unittest.mock import AsyncMock, MagicMock, patch

import asyncssh
from pytest import mark

from iotlabsshcli.open_linux import _nodes_grouped
from iotlabsshcli.sshlib import OpenLinuxSsh

from .open_linux_test import _GRENOBLE_NODES, _ROOT_NODES, _SACLAY_NODES


def _make_conn(exit_status=0, stdout="test"):
    """Return a mock asyncssh connection usable as an async context manager."""
    run_result = MagicMock()
    run_result.exit_status = exit_status
    run_result.stdout = stdout

    conn = MagicMock()
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=False)
    conn.run = AsyncMock(return_value=run_result)

    sftp = MagicMock()
    sftp.__aenter__ = AsyncMock(return_value=sftp)
    sftp.__aexit__ = AsyncMock(return_value=False)
    sftp.put = AsyncMock()
    conn.start_sftp_client = MagicMock(return_value=sftp)

    return conn


@mark.parametrize("run_on_frontend", [False, True])
def test_run(run_on_frontend):
    """Test running commands on ssh nodes."""
    config_ssh = {"user": "username", "exp_id": 123}
    groups = _nodes_grouped(_ROOT_NODES)
    node_ssh = OpenLinuxSsh(config_ssh, groups, verbose=True)

    conn_ok = _make_conn(exit_status=0)
    conn_fail = _make_conn(exit_status=1)

    def connect_side_effect(host, **_):
        return conn_ok if "saclay" in host else conn_fail

    with patch(
        "iotlabsshcli.sshlib.open_linux_ssh.asyncssh.connect",
        side_effect=connect_side_effect,
    ):
        ret = node_ssh.run("test", with_proxy=not run_on_frontend)

    if run_on_frontend:
        assert ret == {"0": ["saclay.iot-lab.info"], "1": ["grenoble.iot-lab.info"]}
    else:
        assert ret == {"0": _SACLAY_NODES, "1": _GRENOBLE_NODES}


def test_scp():
    """Test copying a file to SSH frontend nodes."""
    config_ssh = {"user": "username", "exp_id": 123}
    groups = _nodes_grouped(_ROOT_NODES)
    node_ssh = OpenLinuxSsh(config_ssh, groups, verbose=True)

    conn = _make_conn()

    with patch(
        "iotlabsshcli.sshlib.open_linux_ssh.asyncssh.connect",
        return_value=conn,
    ):
        ret = node_ssh.scp("test_src", "test_dst")

    assert conn.start_sftp_client.call_count == 2
    assert set(ret["0"]) == {"saclay.iot-lab.info", "grenoble.iot-lab.info"}
    assert ret.get("1", []) == []

    conn.start_sftp_client.return_value.put.side_effect = asyncssh.SFTPError(
        asyncssh.FX_FAILURE, "error"
    )
    with patch(
        "iotlabsshcli.sshlib.open_linux_ssh.asyncssh.connect",
        return_value=conn,
    ):
        ret = node_ssh.scp("test_src", "test_dst")

    assert set(ret["1"]) == {"saclay.iot-lab.info", "grenoble.iot-lab.info"}
    assert ret.get("0", []) == []


def test_run_with_ssh_key():
    """Test that a configured SSH_KEY is forwarded as client_keys."""
    config_ssh = {"user": "username", "exp_id": 123}
    groups = _nodes_grouped(_ROOT_NODES)
    node_ssh = OpenLinuxSsh(config_ssh, groups)

    conn = _make_conn(exit_status=0)

    with patch("iotlabsshcli.sshlib.open_linux_ssh.SSH_KEY", "~/.ssh/id_rsa"):
        with patch(
            "iotlabsshcli.sshlib.open_linux_ssh.asyncssh.connect",
            return_value=conn,
        ) as mock_connect:
            node_ssh.run("uptime")

    call_kwargs = mock_connect.call_args_list[0][1]
    assert "client_keys" in call_kwargs
    assert call_kwargs["client_keys"] == [os.path.expanduser("~/.ssh/id_rsa")]


def test_wait_all_boot():
    """Test waiting for ssh nodes to become available."""
    config_ssh = {"user": "username", "exp_id": 123}
    groups = _nodes_grouped(_ROOT_NODES)
    node_ssh = OpenLinuxSsh(config_ssh, groups, verbose=True)

    conn = _make_conn(exit_status=0)

    with patch(
        "iotlabsshcli.sshlib.open_linux_ssh.asyncssh.connect",
        return_value=conn,
    ):
        result = node_ssh.wait(120)

    assert result == {"0": sorted(_ROOT_NODES)}
