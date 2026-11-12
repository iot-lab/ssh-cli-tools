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

import asyncio
import os
import threading
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import asyncssh
from pytest import mark

from iotlabsshcli.open_linux import _nodes_grouped
from iotlabsshcli.sshlib import OpenLinuxSsh

from .open_linux_test import _GRENOBLE_NODES, _ROOT_NODES, _SACLAY_NODES


def _make_conn(exit_status: int = 0, stdout: str = "test") -> MagicMock:
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
    sftp.makedirs = AsyncMock()
    conn.start_sftp_client = MagicMock(return_value=sftp)

    return conn


@mark.parametrize("run_on_frontend", [False, True])
def test_run(run_on_frontend: bool) -> None:
    """Test running commands on ssh nodes."""
    config_ssh = {"user": "username", "exp_id": 123}
    groups = _nodes_grouped(_ROOT_NODES)
    node_ssh = OpenLinuxSsh(config_ssh, groups, verbose=True)

    conn_ok = _make_conn(exit_status=0)
    conn_fail = _make_conn(exit_status=1)

    def connect_side_effect(host: str, **_: Any) -> MagicMock:
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


def test_scp() -> None:
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
    # a file name alone: no directory to create
    conn.start_sftp_client.return_value.makedirs.assert_not_awaited()

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


class _NoAuthServer(asyncssh.SSHServer):  # pylint: disable=too-few-public-methods
    """An SSH server that lets everyone in."""

    def begin_auth(self, username: str) -> bool:
        """No authentication, whoever the user is."""
        del username
        return False


class _LocalSftp(threading.Thread):
    """An SFTP server on the loopback, the home of its users in a directory."""

    def __init__(self, home: Path) -> None:
        super().__init__(daemon=True)
        self.home = home
        self.port = 0
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()

    def run(self) -> None:
        asyncio.set_event_loop(self._loop)
        server = self._loop.run_until_complete(
            asyncssh.listen(
                "127.0.0.1",
                0,
                server_host_keys=[asyncssh.generate_private_key("ssh-ed25519")],
                server_factory=_NoAuthServer,
                sftp_factory=lambda chan: asyncssh.SFTPServer(chan, chroot=str(self.home)),
            )
        )
        self.port = server.sockets[0].getsockname()[1]
        self._ready.set()
        self._loop.run_forever()
        server.close()
        self._loop.run_until_complete(server.wait_closed())
        self._loop.close()

    def __enter__(self) -> "_LocalSftp":
        self.start()
        assert self._ready.wait(10)
        return self

    def __exit__(self, *_: Any) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self.join(10)


def test_scp_creates_the_remote_directory(tmp_path: Path) -> None:
    """Test copying a file in a directory the SSH frontend does not have yet.

    The first copy of an account: on a real SFTP server, a mock of it takes
    any path.
    """
    source = tmp_path / "firmware.elf"
    source.write_bytes(b"firmware")
    home = tmp_path / "home"
    home.mkdir()
    groups = {"saclay.iot-lab.info": ["node-a8-1.saclay.iot-lab.info"]}
    node_ssh = OpenLinuxSsh({"user": "username", "exp_id": 123}, groups)
    connect = asyncssh.connect

    with _LocalSftp(home) as server:

        def local_connect(_: str, **kwargs: Any) -> Any:
            return connect("127.0.0.1", server.port, **kwargs)

        with patch(
            "iotlabsshcli.sshlib.open_linux_ssh.asyncssh.connect",
            side_effect=local_connect,
        ):
            first = node_ssh.scp(str(source), "shared/.iotlabsshcli/firmware.elf")
            again = node_ssh.scp(str(source), "shared/.iotlabsshcli/firmware.elf")

    assert first == {"0": ["saclay.iot-lab.info"]}
    assert (home / "shared" / ".iotlabsshcli" / "firmware.elf").read_bytes() == b"firmware"
    # the directory is there the next time
    assert again == first


def test_run_with_ssh_key() -> None:
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


def test_wait_all_boot() -> None:
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
