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

"""Tests for iotlabsshcli.parser.open_linux package."""

import jmespath

from iotlabsshcli.parser import open_linux_parser

from .iotlabsshcli_mock import MainMock
from .compat import patch, Mock

# pylint: disable=too-many-public-methods
# pylint: disable=too-few-public-methods


class TestMainNodeParser(MainMock):
    """Test open-linux-cli main parser."""

    _nodes = ['a8-{0}.saclay.iot-lab.info'.format(i) for i in range(1, 6)]
    _root_nodes = ['node-{0}'.format(node) for node in _nodes]

    @patch('iotlabsshcli.open_linux.flash')
    @patch('iotlabcli.parser.common.list_nodes')
    def test_main_flash(self, list_nodes, flash):
        """Run the parser.node.main with update subparser function."""

        flash.return_value = {'result': 'test'}
        list_nodes.return_value = self._nodes

        args = ['flash', 'firmware.elf', '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        flash.assert_called_with({'user': 'username', 'exp_id': 123},
                                 self._root_nodes, 'firmware.elf',
                                 verbose=False)

        exp_info_res = {"items": [{"network_address": node}
                                  for node in self._nodes]}
        with patch.object(self.api, 'get_experiment_info',
                          Mock(return_value=exp_info_res)):
            list_nodes.return_value = []
            args = ['flash', 'firmware.elf']
            open_linux_parser.main(args)
            list_nodes.assert_called_with(self.api, 123, None, None)
            flash.assert_called_with({'user': 'username', 'exp_id': 123},
                                     self._root_nodes, 'firmware.elf',
                                     verbose=False)

    @patch('iotlabsshcli.open_linux.reset')
    @patch('iotlabcli.parser.common.list_nodes')
    def test_main_reset(self, list_nodes, reset):
        """Run the parser.node.main with reset subparser function."""
        reset.return_value = {'result': 'test'}
        list_nodes.return_value = self._nodes

        args = ['reset', '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        reset.assert_called_with({'user': 'username', 'exp_id': 123},
                                 self._root_nodes,
                                 verbose=False)

        exp_info_res = {"items": [{"network_address": node}
                                  for node in self._nodes]}
        with patch.object(self.api, 'get_experiment_info',
                          Mock(return_value=exp_info_res)):
            list_nodes.return_value = []
            args = ['reset']
            open_linux_parser.main(args)
            list_nodes.assert_called_with(self.api, 123, None, None)
            reset.assert_called_with({'user': 'username', 'exp_id': 123},
                                     self._root_nodes, verbose=False)

    @patch('iotlabsshcli.open_linux.wait_for_boot')
    @patch('iotlabcli.parser.common.list_nodes')
    def test_main_wait_for_boot(self, list_nodes, wait_for_boot):
        """Run the parser.node.main with wait-for-boot subparser function."""
        wait_for_boot.return_value = {'result': 'test'}
        list_nodes.return_value = self._nodes

        args = ['wait-for-boot', '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        wait_for_boot.assert_called_with({'user': 'username', 'exp_id': 123},
                                         self._root_nodes,
                                         max_wait=120,
                                         verbose=False)

        args = ['wait-for-boot', "--max-wait", '10', '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        wait_for_boot.assert_called_with({'user': 'username', 'exp_id': 123},
                                         self._root_nodes,
                                         max_wait=10,
                                         verbose=False)

        exp_info_res = {"items": [{"network_address": node}
                                  for node in self._nodes]}
        with patch.object(self.api, 'get_experiment_info',
                          Mock(return_value=exp_info_res)):
            list_nodes.return_value = []
            args = ['wait-for-boot']
            open_linux_parser.main(args)
            list_nodes.assert_called_with(self.api, 123, None, None)
            wait_for_boot.assert_called_with({'user': 'username',
                                              'exp_id': 123},
                                             self._root_nodes,
                                             max_wait=120,
                                             verbose=False)

    @patch('iotlabsshcli.open_linux.run_script')
    @patch('iotlabcli.parser.common.list_nodes')
    def test_main_run_script(self, list_nodes, run_script):
        """Run the parser.node.main with run-script subparser function."""
        run_script.return_value = {'result': 'test'}
        list_nodes.return_value = self._nodes

        args = ['run-script', 'script.sh', '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        run_script.assert_called_with({'user': 'username', 'exp_id': 123},
                                      self._root_nodes,
                                      'script.sh', False, verbose=False)

        args = ['run-script', 'script.sh', '--frontend', '-l',
                'saclay,a8,1-5']
        open_linux_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        run_script.assert_called_with({'user': 'username', 'exp_id': 123},
                                      self._root_nodes,
                                      'script.sh', True, verbose=False)

        exp_info_res = {"items": [{"network_address": node}
                                  for node in self._nodes]}
        with patch.object(self.api, 'get_experiment_info',
                          Mock(return_value=exp_info_res)):
            list_nodes.return_value = []
            args = ['run-script', 'script.sh']
            open_linux_parser.main(args)
            list_nodes.assert_called_with(self.api, 123, None, None)
            run_script.assert_called_with({'user': 'username', 'exp_id': 123},
                                          self._root_nodes,
                                          'script.sh', False, verbose=False)

    @patch('iotlabsshcli.open_linux.run_cmd')
    @patch('iotlabcli.parser.common.list_nodes')
    def test_main_run_cmd(self, list_nodes, run_cmd):
        """Run the parser.node.main with run-cmd subparser function."""
        run_cmd.return_value = {'result': 'test'}
        list_nodes.return_value = self._nodes

        args = ['run-cmd', 'uname -a', '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        run_cmd.assert_called_with({'user': 'username', 'exp_id': 123},
                                   self._root_nodes,
                                   'uname -a', False, verbose=False)

        args = ['run-cmd', 'uname -a', '--frontend', '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        run_cmd.assert_called_with({'user': 'username', 'exp_id': 123},
                                   self._root_nodes,
                                   'uname -a', True, verbose=False)

        exp_info_res = {"items": [{"network_address": node}
                                  for node in self._nodes]}
        with patch.object(self.api, 'get_experiment_info',
                          Mock(return_value=exp_info_res)):
            list_nodes.return_value = []
            args = ['run-cmd', 'uname -a']
            open_linux_parser.main(args)
            list_nodes.assert_called_with(self.api, 123, None, None)
            run_cmd.assert_called_with({'user': 'username', 'exp_id': 123},
                                       self._root_nodes,
                                       'uname -a', False, verbose=False)

    @patch('iotlabsshcli.open_linux.copy_file')
    @patch('iotlabcli.parser.common.list_nodes')
    def test_main_copy_file(self, list_nodes, copy_file):
        """Run the parser.node.main with copy-file subparser function."""
        copy_file.return_value = {'result': 'test'}
        list_nodes.return_value = self._nodes

        args = ['copy-file', 'script.sh', '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        copy_file.assert_called_with({'user': 'username', 'exp_id': 123},
                                     self._root_nodes,
                                     'script.sh', verbose=False)

        exp_info_res = {"items": [{"network_address": node}
                                  for node in self._nodes]}
        with patch.object(self.api, 'get_experiment_info',
                          Mock(return_value=exp_info_res)):
            list_nodes.return_value = []
            args = ['copy-file', 'script.sh']
            open_linux_parser.main(args)
            list_nodes.assert_called_with(self.api, 123, None, None)
            copy_file.assert_called_with({'user': 'username', 'exp_id': 123},
                                         self._root_nodes,
                                         'script.sh', verbose=False)

    def test_main_unknown_function(self):
        """Run the parser.node.main with an unknown function."""
        args = ['unknown-cmd']
        self.assertRaises(SystemExit, open_linux_parser.main, args)

    @patch('iotlabcli.parser.common.list_nodes')
    def test_run_unknown_function(self, list_nodes):
        # pylint:disable=unused-argument
        """Run the parser.node.main with an unknown function."""
        parser = open_linux_parser.parse_options()
        parser.command = 'unknown-cmd'
        parser.username = 'username'
        parser.password = 'password'
        parser.experiment_id = 'experiment_id'
        parser.nodes_list = []
        parser.exclude_nodes_list = []
        self.assertRaises(ValueError,
                          open_linux_parser.open_linux_parse_and_run, parser)

    @patch('iotlabsshcli.open_linux.reset')
    @patch('iotlabcli.parser.common.list_nodes')
    @patch('iotlabcli.parser.common.print_result')
    def test_reset_jmespath(self, print_result, list_nodes, reset):
        """Run reset subparser function with jmespath options."""
        reset.return_value = {'result': 'test'}
        list_nodes.return_value = self._nodes

        args = ['--jmespath=\'test\'', '--fmt=\'int\'', 'reset',
                '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)

        print_result.assert_called_once()
        args, _ = print_result.call_args
        self.assertEqual(len(args), 3)
        self.assertEqual(args[0], {'result': 'test'})
        self.assertTrue(isinstance(args[1], jmespath.parser.ParsedResult))
        self.assertEqual(args[2], 'int')

        args = ['reset', '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)
        print_result.assert_called_once()
        args, _ = print_result.call_args
        self.assertEqual(len(args), 3)
        self.assertEqual(args[0], {'result': 'test'})
        self.assertEqual(args[1], None)
        self.assertEqual(args[2], None)

    @patch('iotlabsshcli.open_linux.reset')
    @patch('iotlabsshcli.open_linux.flash')
    @patch('iotlabcli.parser.common.list_nodes')
    @patch('iotlabcli.parser.common.print_result')
    def test_deprecated_parser(self, print_result, list_nodes, flash, reset):
        """Run deprecated subparsers."""
        reset.return_value = flash.return_value = {'result': 'test'}
        list_nodes.return_value = self._nodes

        # call deprecated subparser
        args = ['reset-m3', '-h']
        self.assertRaises(SystemExit, open_linux_parser.main, args)

        args = ['flash-m3', 'firmware.elf', '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)
        print_result.assert_called_once()
        args, _ = print_result.call_args
        self.assertEqual(len(args), 3)
        self.assertEqual(args[0], {'result': 'test'})
        self.assertEqual(args[1], None)
        self.assertEqual(args[2], None)

        args = ['reset-m3', '-l', 'saclay,a8,1-5']
        open_linux_parser.main(args)
        print_result.assert_called_once()
        args, _ = print_result.call_args
        self.assertEqual(len(args), 3)
        self.assertEqual(args[0], {'result': 'test'})
        self.assertEqual(args[1], None)
        self.assertEqual(args[2], None)
