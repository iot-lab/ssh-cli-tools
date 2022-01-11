# -*- coding:utf-8 -*-
"""iotlabsshcli parser for Open Linux nodes cli."""

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
from iotlabcli.helpers import deprecate_warn_cmd
import iotlabsshcli.open_linux


def parse_options():
    """Parse command line option."""
    parent_parser = argparse.ArgumentParser(add_help=False)
    common.add_auth_arguments(parent_parser, False)
    parent_parser.add_argument('-v', '--version',
                               action='version',
                               version=iotlabsshcli.__version__)

    # We create top level parser
    parser = argparse.ArgumentParser(
        parents=[parent_parser],
    )

    common.add_expid_arg(parser)
    common.add_output_formatter(parser)

    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True  # needed for python 3.

    # pylint: disable=super-with-arguments
    class DeprecateHelpFormatter(argparse.HelpFormatter):
        """ Add drepecated help formatter """

        def add_usage(self, usage, actions, groups, prefix=None):
            # self._prog = iotlab-ssh flash-m3 | reset-m3
            old_cmd = self._prog.split()[-1]
            new_cmd = old_cmd.split('-')[0]
            deprecate_warn_cmd(old_cmd, new_cmd, 20)
            return super(DeprecateHelpFormatter, self).add_usage(usage,
                                                                 actions,
                                                                 groups,
                                                                 prefix)

    update_parser = subparsers.add_parser('flash',
                                          parents=[parent_parser],
                                          help='Flash node\'s '
                                               'co-microcontroller')
    update_parser.add_argument('firmware', help='firmware path.')
    # nodes list or exclude list
    common.add_nodes_selection_list(update_parser)

    # reset parser
    reset_parser = subparsers.add_parser('reset',
                                         parents=[parent_parser],
                                         help='Reset node\'s '
                                              'co-microcontroller')
    # nodes list or exclude list
    common.add_nodes_selection_list(reset_parser)

    # wait-for-boot parser
    boot_parser = subparsers.add_parser('wait-for-boot',
                                        parents=[parent_parser],
                                        help='Waits until Linux nodes '
                                             'have boot')
    boot_parser.add_argument('--max-wait',
                             type=int,
                             default=120,
                             help='Maximum waiting delay for nodes boot '
                                  '(in seconds)')
    # nodes list or exclude list
    common.add_nodes_selection_list(boot_parser)

    # run-script parser
    run_script_parser = subparsers.add_parser('run-script',
                                              parents=[parent_parser],
                                              help='Run a script in '
                                                   'background on Linux '
                                                   'nodes')
    run_script_parser.add_argument('script', help='script path.')
    run_script_parser.add_argument('--frontend', action='store_true',
                                   help='Execution on SSH frontend')
    # nodes list or exclude list
    common.add_nodes_selection_list(run_script_parser)

    # run-cmd parser
    run_cmd_parser = subparsers.add_parser('run-cmd',
                                           parents=[parent_parser],
                                           help='Run a command on Linux nodes')
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
                                                  ' (~/shared/.iotlabsshcli)')
    copy_file_parser.add_argument('file_path', help='File path')
    # nodes list or exclude list
    common.add_nodes_selection_list(copy_file_parser)

    parser.add_argument('--verbose',
                        action='store_true',
                        help='Set verbose output')

    # update-m3 parser
    help_msg = 'DEPRECATED: use flash subcommand instead'
    update_m3_parser = \
        subparsers.add_parser('flash-m3', help=help_msg,
                              parents=[parent_parser],
                              formatter_class=DeprecateHelpFormatter)
    update_m3_parser.add_argument('firmware', help='firmware path.')
    # nodes list or exclude list
    common.add_nodes_selection_list(update_m3_parser)

    # reset-m3 parser
    help_msg = 'DEPRECATED: use reset subcommand instead'
    reset_m3_parser = \
        subparsers.add_parser('reset-m3', help=help_msg,
                              parents=[parent_parser],
                              formatter_class=DeprecateHelpFormatter)
    # nodes list or exclude list
    common.add_nodes_selection_list(reset_m3_parser)

    return parser


def open_linux_parse_and_run(opts):
    """Parse namespace 'opts' object."""
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

    # Only keep Linux nodes
    nodes = [f'node-{node}'
             for node in nodes
             if node.startswith('a8') or node.startswith('rpi3')]

    command = opts.command
    res = None
    if command == 'reset':
        res = iotlabsshcli.open_linux.reset(config_ssh, nodes,
                                            verbose=opts.verbose)
    elif command == 'flash':
        res = iotlabsshcli.open_linux.flash(config_ssh, nodes,
                                            opts.firmware,
                                            verbose=opts.verbose)
    elif command == 'wait-for-boot':
        res = iotlabsshcli.open_linux.wait_for_boot(config_ssh, nodes,
                                                    max_wait=opts.max_wait,
                                                    verbose=opts.verbose)
    elif command == 'run-script':
        res = iotlabsshcli.open_linux.run_script(config_ssh, nodes,
                                                 opts.script,
                                                 opts.frontend,
                                                 verbose=opts.verbose)
    elif command == 'run-cmd':
        res = iotlabsshcli.open_linux.run_cmd(config_ssh, nodes,
                                              opts.cmd,
                                              opts.frontend,
                                              verbose=opts.verbose)
    elif command == 'copy-file':
        res = iotlabsshcli.open_linux.copy_file(config_ssh, nodes,
                                                opts.file_path,
                                                verbose=opts.verbose)
    if command == 'reset-m3':
        deprecate_warn_cmd('reset-m3', 'reset', 7)
        res = iotlabsshcli.open_linux.reset(config_ssh, nodes,
                                            verbose=opts.verbose)
    elif command == 'flash-m3':
        deprecate_warn_cmd('flash-m3', 'flash', 7)
        res = iotlabsshcli.open_linux.flash(config_ssh, nodes,
                                            opts.firmware,
                                            verbose=opts.verbose)

    if res is None:
        raise ValueError(f'Unknown command {command}')

    return res


def main(args=None):
    """Open Linux SSH cli parser."""
    args = args or sys.argv[1:]  # required for easy testing.
    parser = parse_options()
    common.main_cli(open_linux_parse_and_run, parser, args)
