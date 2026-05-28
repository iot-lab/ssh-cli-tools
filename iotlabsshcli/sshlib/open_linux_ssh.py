# -*- coding:utf-8 -*-
"""iotlabsshcli package implementing a ssh lib using asyncssh."""

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

import asyncio
import os
import time
from typing import Any

import asyncssh


def _cleanup_result(result: dict[str, list[str]]) -> dict[str, list[str]]:
    """Remove empty list from result.

    >>> _cleanup_result({ '0': [], '1': []})
    {}
    >>> _cleanup_result({ '0': [1, 2, 3], '1': []})
    {'0': [1, 2, 3]}
    >>> _cleanup_result({ '0': [], '1': [1, 2, 3]})
    {'1': [1, 2, 3]}
    >>> sorted(_cleanup_result({ '0': [1, 2, 3], '1': [4, 5, 6]}).items())
    [('0', [1, 2, 3]), ('1', [4, 5, 6])]
    """
    key_to_del = []
    for key, value in result.items():
        if value == []:
            key_to_del.append(key)
    for key in key_to_del:
        del result[key]

    return result


def _extend_result(
    result: dict[str, list[str]], new_result: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Extend result dictionnary values with new result
    dictionnary values

    >>> result = {'0': [], '1': []}
    >>> result == _extend_result(
    ...    { '0': [], '1': []}, { '0': [], '1': []})
    True

    >>> result = {'0': ['node-a8-1.saclay.iot-lab.info'],
    ...           '1': []}
    >>> result == _extend_result({ '0': [], '1': []},
    ...    { '0': ['node-a8-1.saclay.iot-lab.info'], '1': []})
    True

    >>> result = {'0': ['node-a8-1.saclay.iot-lab.info',
    ...                 'node-a8-2.saclay.iot-lab.info'],
    ...           '1': ['node-a8-3.saclay.iot-lab.info']}
    >>> result == _extend_result(
    ...    { '0': ['node-a8-1.saclay.iot-lab.info'], '1': []},
    ...    { '0': ['node-a8-2.saclay.iot-lab.info'],
    ...      '1': ['node-a8-3.saclay.iot-lab.info']})
    True

    >>> result = {'0': ['node-a8-1.saclay.iot-lab.info',
    ...                 'node-a8-2.saclay.iot-lab.info'],
    ...           '1': ['node-a8-3.saclay.iot-lab.info']}
    >>> result ==_extend_result(
    ...    { '0': ['node-a8-1.saclay.iot-lab.info',
    ...            'node-a8-2.saclay.iot-lab.info'],
    ...      '1': ['node-a8-3.saclay.iot-lab.info']},
    ...    { '0': [], '1': ['node-a8-3.saclay.iot-lab.info']})
    True

    >>> result =  {'0': ['node-a8-1.saclay.iot-lab.info',
    ...                  'node-a8-2.saclay.iot-lab.info',
    ...                  'node-a8-3.saclay.iot-lab.info'],
    ...            '1': []}
    >>> result == _extend_result(
    ...    { '0': ['node-a8-1.saclay.iot-lab.info',
    ...            'node-a8-2.saclay.iot-lab.info'],
    ...      '1': ['node-a8-3.saclay.iot-lab.info']},
    ...    { '0': ['node-a8-3.saclay.iot-lab.info'], '1': []})
    True
    """
    result["0"] = sorted(list(set(result["0"] + new_result["0"])))
    result["1"] = sorted(list(set(result["1"]) - set(new_result["0"])))
    result["1"] = sorted(list(set(result["1"]) | set(new_result["1"])))
    return result


def _check_all_nodes_processed(result: dict[str, list[str]]) -> bool:
    """Verify all nodes are successful or failed.

    >>> _check_all_nodes_processed({ 'saclay': [], 'grenoble': []})
    True
    >>> _check_all_nodes_processed(
    ...    { 'saclay': ['node-a8-1.saclay.iot-lab.info'],
    ...      'grenoble': []})
    False
    >>> _check_all_nodes_processed(
    ...    { 'saclay': ['node-a8-1.saclay.iot-lab.info'],
    ...      'grenoble': ['node-a8-10.grenoble.iot-lab.info']})
    False
    """
    return not any(result.values())


# library uses SSH agent for authentication if no key is provided.
# As we don't have SSH agent launched on the SSH frontend server by
# default, we pass the key directly
SSH_KEY = "~/.ssh/id_rsa" if os.getenv("IOT_LAB_FRONTEND_FQDN") else None


class OpenLinuxSsh:
    """Implement SSH API using asyncssh."""

    def __init__(
        self, config_ssh: dict[str, Any], groups: dict[str, list[str]], verbose: bool = False
    ) -> None:
        self.config_ssh = config_ssh
        self.groups = groups
        self.verbose = verbose

    def run(self, command: str, with_proxy: bool = True, **kwargs: Any) -> dict[str, list[str]]:
        """Run ssh command on nodes, optionally through a proxy."""
        result = {"0": [], "1": []}
        for site, hosts in self.groups.items():
            proxy_host = site if with_proxy else None
            run_hosts = hosts if with_proxy else [site]
            result_cmd = asyncio.run(
                self._run_command(command, run_hosts, proxy_host=proxy_host, **kwargs)
            )
            result = _extend_result(result, result_cmd)
        return _cleanup_result(result)

    def scp(self, src: str, dst: str) -> dict[str, list[str]]:
        """Copy file to SSH frontend via SFTP."""
        result = {"0": [], "1": []}
        for site in self.groups:
            try:
                asyncio.run(self._copy_file(site, src, dst))
                result["0"].append(site)
            except (asyncssh.Error, OSError):
                result["1"].append(site)
        return _cleanup_result(result)

    def wait(self, max_wait: int) -> dict[str, list[str]]:
        """Wait for requested Linux nodes until they boot."""
        result = {"0": [], "1": []}
        start_time = time.time()
        groups = self.groups.copy()
        while start_time + max_wait > time.time() and not _check_all_nodes_processed(groups):
            for site, hosts in groups.copy().items():
                result_cmd = asyncio.run(self._run_command("uptime", hosts, proxy_host=site))
                groups[site] = result_cmd["1"]
                groups = _cleanup_result(groups)
                result = _extend_result(result, result_cmd)
        return _cleanup_result(result)

    def _connect_kwargs(self, timeout: int = 10) -> dict[str, Any]:
        kwargs = {"known_hosts": None, "connect_timeout": timeout}
        if SSH_KEY:
            kwargs["client_keys"] = [os.path.expanduser(SSH_KEY)]
        return kwargs

    async def _run_command(
        self,
        command: str,
        hosts: list[str],
        proxy_host: str | None = None,
        timeout: int = 10,
        **kwargs: Any,
    ) -> dict[str, list[str]]:
        tasks = [
            self._run_on_host(host, command, proxy_host=proxy_host, timeout=timeout, **kwargs)
            for host in hosts
        ]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        result = {"0": [], "1": []}
        for host, outcome in zip(hosts, outcomes):
            if isinstance(outcome, BaseException) or outcome[0] != 0:
                result["1"].append(host)
            else:
                if self.verbose and outcome[1]:
                    for line in outcome[1].splitlines():
                        print(line)
                result["0"].append(host)
        return result

    async def _run_on_host(
        self,
        host: str,
        command: str,
        proxy_host: str | None = None,
        timeout: int = 10,
        **kwargs: Any,
    ) -> tuple[int, str]:
        ck = self._connect_kwargs(timeout)
        if proxy_host:
            async with asyncssh.connect(
                proxy_host, username=self.config_ssh["user"], **ck
            ) as tunnel:
                async with asyncssh.connect(host, username="root", tunnel=tunnel, **ck) as conn:
                    result = await conn.run(command, **kwargs)
                    return result.exit_status, result.stdout or ""
        else:
            async with asyncssh.connect(host, username=self.config_ssh["user"], **ck) as conn:
                result = await conn.run(command, **kwargs)
                return result.exit_status, result.stdout or ""

    async def _copy_file(self, site: str, src: str, dst: str) -> None:
        ck = self._connect_kwargs()
        async with asyncssh.connect(site, username=self.config_ssh["user"], **ck) as conn:
            async with conn.start_sftp_client() as sftp:
                await sftp.put(src, dst)
