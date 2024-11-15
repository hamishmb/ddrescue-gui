#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DDRescue Tools for ddrescue v1.20 (or newer) in the Tools Package for DDRescue-GUI
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
Tools for ddrescue v1.20 or newer.
"""

from . import decorators

@decorators.define_versions
def get_time_since_last_read(split_line):
    """
    Get Time Since Last Read value.

    Args:
        split_line (string):        The line from ddrescue's output that contains
                                    the information, split by whitespace.

    Works with ddrescue versions: 1.20,1.21,1.22,1.23,1.24,1.25,1.26,1.27,1.28
    """
    #Find the index where "read:" is, and get all useful information after that.
    read_index = split_line.index("read:")

    return ' '.join(split_line[read_index+1:])

@decorators.define_versions
def get_time_remaining(split_line):
    """
    Get Time Since Last Read value.

    Args:
        split_line (string):        The line from ddrescue's output that contains
                                    the information, split by whitespace.

    Works with ddrescue versions: 1.20,1.21,1.22,1.23,1.24,1.25,1.26,1.27,1.28
    """
    #Find where "remaining" is in the line, and return all data elements after that.
    remaining_index = split_line.index("remaining")

    return ' '.join(split_line[remaining_index+2:])
