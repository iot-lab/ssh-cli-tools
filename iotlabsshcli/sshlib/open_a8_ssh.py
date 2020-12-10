# -*- coding:utf-8 -*-
"""iotlabsshcli package implementing a ssh lib using parallel-ssh."""

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
import os
import time
import pssh
from pssh.clients import SSHClient
from pssh.clients import ParallelSSHClient
from pssh.exceptions import SFTPError, UnknownHostError
from pssh.exceptions import AuthenticationError
from pssh import utils


def _cleanup_result(result):
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


def _extend_result(result, new_result):
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


def _check_all_nodes_processed(result):
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
SSH_KEY = ('~/.ssh/id_rsa' if os.getenv('IOT_LAB_FRONTEND_FQDN')
           else None)


class OpenA8Ssh():
    """Implement SSH API for Parallel SSH."""

    def __init__(self, config_ssh, groups, verbose=False):
        self.config_ssh = config_ssh
        self.groups = groups
        self.verbose = verbose

        if self.verbose:
            utils.enable_logger(utils.logger)

    def run(self, command, with_proxy=True, **kwargs):
        """Run ssh command using Parallel SSH."""
        result = {"0": [], "1": []}
        for site, hosts in self.groups.items():
            proxy_host = site if with_proxy else None
            hosts = hosts if with_proxy else [site]
            result_cmd = self.run_command(command,
                                          hosts=hosts,
                                          user=self.config_ssh['user'],
                                          verbose=self.verbose,
                                          proxy_host=proxy_host,
                                          **kwargs)
            result = _extend_result(result, result_cmd)
        return _cleanup_result(result)

    def scp(self, src, dst):
        """Copy file to A8 node using Parallel SCP native client."""
        result = {"0": [], "1": []}
        sites = self.groups.keys()
        for site in sites:
            try:
                client = SSHClient(site, user=self.config_ssh['user'],
                                   pkey=SSH_KEY, timeout=10)
                client.copy_file(src, dst)
                result["0"].append(site)
            except (SFTPError, UnknownHostError, AuthenticationError,
                    pssh.exceptions.ConnectionError):
                result["1"].append(site)
        return _cleanup_result(result)

    def wait(self, max_wait):
        """Wait for requested A8 nodes until they boot."""
        result = {"0": [], "1": []}
        start_time = time.time()
        groups = self.groups.copy()
        while (start_time + max_wait > time.time() and
               not _check_all_nodes_processed(groups)):
            for site, hosts in groups.copy().items():
                result_cmd = self.run_command("uptime",
                                              hosts=hosts,
                                              user=self.config_ssh['user'],
                                              verbose=self.verbose,
                                              proxy_host=site)
                groups[site] = result_cmd["1"]
                groups = _cleanup_result(groups)
                result = _extend_result(result, result_cmd)
        return _cleanup_result(result)

    # pylint: disable=too-many-arguments
    @staticmethod
    def run_command(command, hosts, user, verbose=False, proxy_host=None,
                    timeout=10, **kwargs):
        """Run ssh command using Parallel SSH."""
        result = {"0": [], "1": []}
        if proxy_host:
            client = ParallelSSHClient(hosts, user='root', pkey=SSH_KEY,
                                       proxy_host=proxy_host,
                                       proxy_user=user,
                                       proxy_pkey=SSH_KEY,
                                       timeout=timeout)
        else:
            client = ParallelSSHClient(hosts, user=user, pkey=SSH_KEY,
                                       timeout=timeout)
        output = client.run_command(command, stop_on_errors=False,
                                    return_list=True,
                                    **kwargs)
        client.join(output)
        # output = pssh.output.HostOutput objects list
        for host in output:
            if host.exit_code == 0:
                if verbose and host.stdout:
                    for line in host.stdout:
                        print(line)
                result['0'].append(host.host)
            elif host.host is not None:
                result['1'].append(host.host)
        # find hosts that have raised Exception (Authentication, Connection)
        # host.exception = pssh.exceptions.* & host.host = None
        failed_hosts = list(set(hosts) - set(sum(result.values(), [])))
        if failed_hosts:
            result['1'].extend(failed_hosts)
        return result
