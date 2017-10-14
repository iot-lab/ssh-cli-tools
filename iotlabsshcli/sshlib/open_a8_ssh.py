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
import time
from pssh.pssh_client import ParallelSSHClient, SSHClient
from pssh import utils
from pssh.exceptions import AuthenticationException, ConnectionErrorException
from scp import SCPClient


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
    """ Extend result dictionnary values with new result
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


class OpenA8SshAuthenticationException(Exception):
    """Raised when an authentication error occurs on one site"""

    def __init__(self, site):
        msg = ('Cannot connect to IoT-LAB server on site '
               '"{}", check your SSH configuration.'.format(site))
        super(OpenA8SshAuthenticationException, self).__init__(msg)
        self.msg = msg


class OpenA8Ssh(object):
    """Implement SshAPI for Parallel SSH."""

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
            proxy_host = '{}.iot-lab.info'.format(site) if with_proxy else None
            hosts = hosts if with_proxy else ['{}.iot-lab.info'.format(site)]
            result_cmd = self.run_command(command,
                                          hosts=hosts,
                                          user=self.config_ssh['user'],
                                          verbose=self.verbose,
                                          proxy_host=proxy_host,
                                          **kwargs)
            result = _extend_result(result, result_cmd)

        return _cleanup_result(result)

    def scp(self, src, dst):
        """Copy file to  using Parallel SSH copy_file"""
        result = {"0": [], "1": []}
        sites = ['{}.iot-lab.info'.format(site) for site in self.groups]
        for site in sites:
            try:
                ssh = SSHClient(site, user=self.config_ssh['user'], timeout=10)
            except AuthenticationException:
                raise OpenA8SshAuthenticationException(site)
            except ConnectionErrorException:
                result["1"].append(site)
            else:
                with SCPClient(ssh.client.get_transport()) as scp:
                    scp.put(src, dst)
                ssh.client.close()
                result["0"].append(site)
        return _cleanup_result(result)

    def wait(self, max_wait):
        """Wait for requested A8 nodes until they boot"""
        result = {"0": [], "1": []}
        start_time = time.time()
        groups = self.groups.copy()
        while (start_time + max_wait > time.time() and
               not _check_all_nodes_processed(groups)):
            for site, hosts in groups.copy().items():
                proxy_host = '{}.iot-lab.info'.format(site)
                result_cmd = self.run_command("uptime",
                                              hosts=hosts,
                                              user=self.config_ssh['user'],
                                              verbose=self.verbose,
                                              proxy_host=proxy_host)
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
            client = ParallelSSHClient(hosts, user='root',
                                       proxy_host=proxy_host,
                                       proxy_user=user,
                                       timeout=timeout)
        else:
            client = ParallelSSHClient(hosts, user=user, timeout=timeout)
        output = client.run_command(command, stop_on_errors=False,
                                    **kwargs)
        client.join(output)
        for host in hosts:
            if host not in output:
                # Pssh AuthenticationException duplicate output dict key
                # {'saclay.iot-lab.info': {'exception': ...},
                # {'saclay.iot-lab.info_qzhtyxlt': {'exception': ...}}
                site = next(iter(sorted(output)))
                raise OpenA8SshAuthenticationException(site)
            result['0' if output[host]['exit_code'] == 0
                   else '1'].append(host)
        if verbose:
            for host in hosts:
                # Pssh >= 1.0.0: stdout is None instead of generator object
                # when you have ConnectionErrorException
                stdout = output[host].get('stdout')
                if stdout:
                    for _ in stdout:
                        pass

        return result
