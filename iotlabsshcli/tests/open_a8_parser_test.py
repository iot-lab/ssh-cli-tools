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

"""Tests for iotlabsshcli.parser.open_a8 package."""

from iotlabsshcli.parser import open_a8_parser

from .iotlabsshcli_mock import MainMock
from .compat import patch

# pylint: disable=too-many-public-methods
# pylint: disable=too-few-public-methods


class TestMainNodeParser(MainMock):
    """Test open-a8-cli main parser."""

    _nodes = ['a8-{0}.saclay.iot-lab.info'.format(i) for i in range(1, 6)]
    _root_nodes = ['node-{0}'.format(node) for node in _nodes]

    @patch('iotlabsshcli.open_a8.flash_m3')
    @patch('iotlabcli.parser.common.list_nodes')
    def test_main_update_m3(self, list_nodes, update_m3):
        """Run the parser.node.main with update-m3 subparser function."""

        update_m3.return_value = {'result': 'test'}
        list_nodes.return_value = self._nodes

        args = ['flash-m3', 'firmware.elf', '-l', 'saclay,a8,1-5']
        open_a8_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        update_m3.assert_called_with({'user': 'username'}, self._root_nodes,
                                     'firmware.elf', verbose=False)

        args = ['flash-m3', 'firmware.elf']
        open_a8_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, None, None)
        update_m3.assert_called_with({'user': 'username'}, self._root_nodes,
                                     'firmware.elf', verbose=False)

    @patch('iotlabsshcli.open_a8.reset_m3')
    @patch('iotlabcli.parser.common.list_nodes')
    def test_main_reset_m3(self, list_nodes, reset_m3):
        """Run the parser.node.main with reset-m3 subparser function."""
        reset_m3.return_value = {'result': 'test'}
        list_nodes.return_value = self._nodes

        args = ['reset-m3', '-l', 'saclay,a8,1-5']
        open_a8_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        reset_m3.assert_called_with({'user': 'username'}, self._root_nodes,
                                    verbose=False)

        args = ['reset-m3']
        open_a8_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, None, None)
        reset_m3.assert_called_with({'user': 'username'}, self._root_nodes,
                                    verbose=False)

    @patch('iotlabsshcli.open_a8.wait_for_boot')
    @patch('iotlabcli.parser.common.list_nodes')
    def test_main_wait_for_boot(self, list_nodes, wait_for_boot):
        """Run the parser.node.main with wait-for-boot subparser function."""
        wait_for_boot.return_value = {'result': 'test'}
        list_nodes.return_value = self._nodes

        args = ['wait-for-boot', '-l', 'saclay,a8,1-5']
        open_a8_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        wait_for_boot.assert_called_with({'user': 'username'},
                                         self._root_nodes,
                                         max_wait=120,
                                         verbose=False)

        args = ['wait-for-boot', "--max-wait", '10', '-l', 'saclay,a8,1-5']
        open_a8_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, [self._nodes], None)
        wait_for_boot.assert_called_with({'user': 'username'},
                                         self._root_nodes,
                                         max_wait=10,
                                         verbose=False)

        args = ['wait-for-boot']
        open_a8_parser.main(args)
        list_nodes.assert_called_with(self.api, 123, None, None)
        wait_for_boot.assert_called_with({'user': 'username'},
                                         self._root_nodes,
                                         max_wait=120,
                                         verbose=False)

    def test_main_unknown_function(self):
        """Run the parser.node.main with an unknown function."""
        args = ['unknown-cmd']
        self.assertRaises(SystemExit, open_a8_parser.main, args)

    def test_run_unknown_function(self):
        """Run the parser.node.main with an unknown function."""
        args = ['unknown-cmd']
        parser = open_a8_parser.parse_options()
        self.assertRaises(TypeError, open_a8_parser.open_a8_parse_and_run,
                          parser, args)
