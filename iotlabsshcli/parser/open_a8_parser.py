# -*- coding:utf-8 -*-
"""iotlabsshcli parser for Open A8 cli."""

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
import argparse
from iotlabcli import auth
from iotlabcli import helpers
from iotlabcli import rest
from iotlabcli.parser import common
from iotlabcli.parser.common import _get_experiment_nodes_list
import iotlabsshcli.open_a8


def parse_options():
    """Parse command line option."""
    parent_parser = common.base_parser()
    # We create top level parser
    parser = argparse.ArgumentParser(
        parents=[parent_parser],
    )

    common.add_expid_arg(parser)

    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True  # needed for python 3.

    # update-m3 parser
    update_parser = subparsers.add_parser('flash-m3',
                                          parents=[parent_parser],
                                          help='Flash the M3 firmware of A8 '
                                               'nodes')
    update_parser.add_argument('firmware', help='firmware elf path.')
    # nodes list or exclude list
    common.add_nodes_selection_list(update_parser)

    # reset-m3 parser
    reset_parser = subparsers.add_parser('reset-m3',
                                         parents=[parent_parser],
                                         help='Reset the M3 of A8 nodes')
    # nodes list or exclude list
    common.add_nodes_selection_list(reset_parser)

    # wait-for-boot parser
    boot_parser = subparsers.add_parser('wait-for-boot',
                                        parents=[parent_parser],
                                        help='Waits until A8 nodes have boot')
    boot_parser.add_argument('--max-wait',
                             type=int,
                             default=120,
                             help='Maximum waiting delay for A8 nodes boot '
                                  '(in seconds)')
    # nodes list or exclude list
    common.add_nodes_selection_list(boot_parser)

    # run-script parser
    run_script_parser = subparsers.add_parser('run-script',
                                              parents=[parent_parser],
                                              help='Run a script in background'
                                                   ' on A8 nodes')
    run_script_parser.add_argument('script', help='script path.')
    run_script_parser.add_argument('--frontend', action='store_true',
                                   help='Execution on SSH frontend')
    # nodes list or exclude list
    common.add_nodes_selection_list(run_script_parser)

    # run-cmd parser
    run_cmd_parser = subparsers.add_parser('run-cmd',
                                           parents=[parent_parser],
                                           help='Run a command on A8 nodes')
    run_cmd_parser.add_argument('cmd', help='Command')
    run_cmd_parser.add_argument('--frontend', action='store_true',
                                help='Execution on SSH frontend')
    # nodes list or exclude list
    common.add_nodes_selection_list(run_cmd_parser)

    # copy-file parser
    copy_file_parser = subparsers.add_parser('copy-file',
                                             parents=[parent_parser],
                                             help='Copy file on'
                                                  ' SSH frontend directory'
                                                  ' (~/A8/.iotlabsshcli/)')
    copy_file_parser.add_argument('file_path', help='File path')
    # nodes list or exclude list
    common.add_nodes_selection_list(copy_file_parser)

    parser.add_argument('--verbose',
                        action='store_true',
                        help='Set verbose output')

    return parser


def open_a8_parse_and_run(opts):
    """Parse namespace 'opts' object and execute M3 fw update action."""
    user, passwd = auth.get_user_credentials(opts.username, opts.password)
    api = rest.Api(user, passwd)
    exp_id = helpers.get_current_experiment(api, opts.experiment_id)

    config_ssh = {
        'user': user,
        'exp_id': exp_id
    }

    nodes = common.list_nodes(api, exp_id, opts.nodes_list,
                              opts.exclude_nodes_list)

    # Only if nodes_list or exclude_nodes_list is not specify (nodes = [])
    if not nodes:
        nodes = _get_experiment_nodes_list(api, exp_id)

    # Only keep A8 nodes
    nodes = ["node-{0}".format(node)
             for node in nodes if node.startswith('a8')]

    command = opts.command
    if command == 'reset-m3':
        return iotlabsshcli.open_a8.reset_m3(config_ssh, nodes,
                                             verbose=opts.verbose)
    elif command == 'flash-m3':
        return iotlabsshcli.open_a8.flash_m3(config_ssh, nodes, opts.firmware,
                                             verbose=opts.verbose)
    elif command == 'wait-for-boot':
        return iotlabsshcli.open_a8.wait_for_boot(config_ssh, nodes,
                                                  max_wait=opts.max_wait,
                                                  verbose=opts.verbose)
    elif command == 'run-script':
        return iotlabsshcli.open_a8.run_script(config_ssh, nodes,
                                               opts.script,
                                               opts.frontend,
                                               verbose=opts.verbose)
    elif command == 'run-cmd':
        return iotlabsshcli.open_a8.run_cmd(config_ssh, nodes,
                                            opts.cmd,
                                            opts.frontend,
                                            verbose=opts.verbose)
    elif command == 'copy-file':
        return iotlabsshcli.open_a8.copy_file(config_ssh, nodes,
                                              opts.file_path,
                                              verbose=opts.verbose)
    else:  # pragma: no cover
        raise ValueError('Unknown command {0}'.format(command))


def main(args=None):
    """Open A8 SSH cli parser."""
    args = args or sys.argv[1:]  # required for easy testing.
    parser = parse_options()
    common.main_cli(open_a8_parse_and_run, parser, args)
