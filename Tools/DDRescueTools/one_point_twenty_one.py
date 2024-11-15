#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DDRescue Tools for ddrescue v1.21 (or newer) in the Tools Package for DDRescue-GUI
# This file is part of DDRescue-GUI.
# Copyright (C) 2013-2024 Hamish McIntyre-Bhatty
# DDRescue-GUI is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3 or,
# at your option, any later version.
#
# DDRescue-GUI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DDRescue-GUI.  If not, see <http://www.gnu.org/licenses/>.

"""
Tools for ddrescue v1.21 or newer.
"""

from . import decorators

@decorators.define_versions
def get_outputpos_average_read_rate(split_line):
    """
    Get Output Position and Average Read Rate values.

    Args:
        split_line (string):        The line from ddrescue's output that contains
                                    the information, split by whitespace.

    Works with ddrescue versions: 1.21,1.22,1.23,1.24,1.25,1.26,1.27,1.28
    """
    return ' '.join(split_line[1:3]).replace(",", ""), split_line[8], split_line[9]

@decorators.define_versions
def get_unreadable_data(split_line):
    """
    Get Unreadable Data value.

    Args:
        split_line (string):        The line from ddrescue's output that contains
                                    the information, split by whitespace.

    Works with ddrescue versions: 1.21,1.22,1.23,1.24,1.25,1.26,1.27,1.28
    """
    return ' '.join(split_line[4:6]).replace(",", "")

@decorators.define_versions
def get_recovered_data_num_errors(split_line):
    """
    Get Recovered Data and Number of Errors values.

    Args:
        split_line (string):        The line from ddrescue's output that contains
                                    the information, split by whitespace.

    Works with ddrescue versions: 1.21
    """
    return split_line[1], split_line[2][:2], split_line[4].replace(",", "")

@decorators.define_versions
def get_current_rate_inputpos(split_line):
    """
    Get Current Read Rate and Input Position values.

    Args:
        split_line (string):        The line from ddrescue's output that contains
                                    the information, split by whitespace.

    Works with ddrescue versions: 1.21,1.22,1.23,1.24,1.25,1.26,1.27,1.28
    """
    return ' '.join(split_line[7:9]), ' '.join(split_line[0:2]).replace(",", "")
