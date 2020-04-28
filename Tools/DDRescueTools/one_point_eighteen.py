#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DDRescue Tools for ddrescue v1.18 (or newer) in the Tools Package for DDRescue-GUI
# This file is part of DDRescue-GUI.
# Copyright (C) 2013-2020 Hamish McIntyre-Bhatty
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
Tools for ddrescue v1.18 or newer.
"""

from . import decorators

@decorators.define_versions
def get_outputpos_time_since_last_read(split_line): #pylint: disable=invalid-name
    """
    Get Output Position and Time Since Last Successful Read values.

    Args:
        split_line (string):        The line from ddrescue's output that contains
                                    the information, split by whitespace.

    Works with ddrescue versions: 1.18,1.19,1.20
    """

    return ' '.join(split_line[1:3]).replace(",", ""), ' '.join(split_line[-3:-1])
