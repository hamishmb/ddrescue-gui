#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DDRescue Tools for ddrescue v1.22 (or newer) in the Tools Package for DDRescue-GUI
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
Tools for ddrescue v1.22 or newer.
"""

from . import decorators

@decorators.define_versions
def get_recovered_data_num_errors(split_line):
    """
    Get Recovered Data and Number of Errors values.

    Args:
        split_line (string):        The line from ddrescue's output that contains
                                    the information, split by whitespace.

    Works with ddrescue versions: 1.22,1.23,1.24,1.25,1.26,1.27,1.28
    """
    return split_line[1], split_line[2][:2], split_line[5].replace(",", "")
