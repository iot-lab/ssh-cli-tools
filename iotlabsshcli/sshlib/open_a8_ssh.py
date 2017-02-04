# -*- coding:utf-8 -*-
"""iotlabsshcli package implementing a ssh lib using fabric."""

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


import sys
import time
from pssh import ParallelSSHClient, SSHClient, utils
from pssh.exceptions import AuthenticationException, ConnectionErrorException
from scp import SCPClient


def _print_output(output, hosts):
    """Display command output for each host."""
    for host in hosts:
        for _ in output[host]['stdout']:
            pass


def _node_fqdn(node, site):
    """Return the fully qualifed domain name of a node.

    >>> _node_fqdn("node-a8-1", "saclay")
    'node-a8-1.saclay.iot-lab.info'
    """
    return '{}.{}.iot-lab.info'.format(node, site)


def _cleanup_result(result):
    """Return empty list from results.

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
        if len(value) == 0:
            key_to_del.append(key)
    for key in key_to_del:
        del result[key]

    return result


def _nodes_from_groups(group):
    """Return the full node list from nodes grouped by sites.
    >>> _nodes_from_groups({'saclay': ['node-a8-1', 'node-a8-2'],
    ...                     'grenoble': ['node-a8-10', 'node-a8-11']})
    ['node-a8-10.grenoble.iot-lab.info', 'node-a8-11.grenoble.iot-lab.info', \
'node-a8-1.saclay.iot-lab.info', 'node-a8-2.saclay.iot-lab.info']
    """
    result = []
    for site, nodes in sorted(group.items()):
        for node in nodes:
            result.append(_node_fqdn(node, site))

    return result


def _all_nodes_in_results(nodes, results):
    """Verify all nodes are successful or failed.
    >>> _all_nodes_in_results([1, 2, 3, 4], { '0': [1, 2], '1': [3, 4]})
    False
    >>> _all_nodes_in_results([1, 2, 3, 4], { '0': [1, 2, 3, 4], '1': []})
    True
    >>> _all_nodes_in_results([1, 2, 3, 4], { '0': [], '1': [1, 2, 3, 4]})
    True
    """
    return (sorted(nodes) == sorted(results["0"]) or
            sorted(nodes) == sorted(results["1"]))


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

    def run(self, command):
        """Run ssh command using Parallel SSH."""
        result = {"0": [], "1": []}
        for site in self.groups:
            client = ParallelSSHClient(self.groups[site],
                                       user='root',
                                       proxy_host='{}'
                                                  '.iot-lab.info'.format(site),
                                       proxy_user=self.config_ssh['user'])
            try:
                output = client.run_command(command)
                client.join(output)
            except AuthenticationException:
                raise OpenA8SshAuthenticationException(site)
            else:
                for host in self.groups[site]:
                    result['1' if output[host]['exit_code'] else '0'].append(
                        '{}.{}.iot-lab.info'.format(host, site))
                if self.verbose:
                    _print_output(output, self.groups[site])
        return _cleanup_result(result)

    def scp(self, src, dst):
        """Copy file to hosts using Parallel SSH copy_file"""
        sites = ['{}.iot-lab.info'.format(site) for site in self.groups]
        for site in sites:
            try:
                ssh = SSHClient(site, user=self.config_ssh['user'])
            except AuthenticationException:
                raise OpenA8SshAuthenticationException(site)
            else:
                with SCPClient(ssh.client.get_transport()) as scp:
                    scp.put(src, dst)
                ssh.client.close()
        return

    def wait(self, max_wait):
        """Wait for requested A8 nodes until they boot"""
        result = {"0": [], "1": []}
        whole_nodes = _nodes_from_groups(self.groups)

        start_time = time.time()
        while (start_time + max_wait > time.time() and
               not _all_nodes_in_results(whole_nodes, result)):
            for site, nodes in self.groups.items():
                for node in nodes:
                    if _node_fqdn(node, site) in result["0"]:
                        continue
                    if self._try_connection(node, site):
                        result["0"].append(_node_fqdn(node, site))

            time.sleep(2)
        for node in whole_nodes:
            if node not in result["0"]:
                result["1"].append(node)

        return _cleanup_result(result)

    def _try_connection(self, node, site):
        dev_null = sys.stderr = open('/dev/null', 'w')
        result = False
        try:
            client = SSHClient(node, user='root',
                               proxy_host='{}.iot-lab.info'
                               .format(site),
                               proxy_user=self.config_ssh['user'])
        except AuthenticationException:
            raise OpenA8SshAuthenticationException(site)
        except ConnectionErrorException:
            if self.verbose:
                print("Node {} not ready."
                      .format(_node_fqdn(node, site)))
        else:
            client.client.close()
            if self.verbose:
                print("Node {} ready."
                      .format(_node_fqdn(node, site)))
            result = True
        finally:
            dev_null.close()

        return result
