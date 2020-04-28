#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DDRescue Tools for ddrescue v1.14 (or newer) in the Tools Package for DDRescue-GUI
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
Tools for ddrescue v1.14 or newer.
"""

import sys
import os

from . import decorators

#Allow imports of modules & packages 1 level up.
sys.path.insert(0, os.path.abspath('..'))

#Import tools.
from Tools import core as CoreTools #pylint: disable=import-error

@decorators.define_versions
def get_inputpos_numerrors_averagereadrate(split_line): #pylint: disable=invalid-name
    """
    Get Input Position, Number of Errors, and Average Read Rate values.

    Args:
        split_line (string):        The line from ddrescue's output that contains
                                    the information, split by whitespace.

    Works with ddrescue versions: 1.14,1.15,1.16,1.17,1.18,1.19,1.20
    """

    return (' '.join(split_line[1:3]).replace(",", ""),
            split_line[4].replace(",", ""), split_line[7], split_line[8])

@decorators.define_versions
def get_outputpos_time_since_last_read(split_line): #pylint: disable=invalid-name
    """
    Get Output Position and Time Since Last Successful Read values.

    Args:
        split_line (string):        The line from ddrescue's output that contains
                                    the information, split by whitespace.

    Works with ddrescue versions: 1.14,1.15,1.16,1.17
    """
    #Find the index where "read:" is, and get all useful information after that.
    read_index = split_line.index("read:")

    return (' '.join(split_line[1:3]).replace(",", ""), ' '.join(split_line[read_index+1:]))

@decorators.define_versions
def get_current_rate_error_size_recovered_data(split_line): #pylint: disable=invalid-name
    """
    Get Current Read Rate, Error Size, and Recovered Data values.

    Args:
        split_line (string):        The line from ddrescue's output that contains
                                    the information, split by whitespace.

    Works with ddrescue versions: 1.14,1.15,1.16,1.17,1.18,1.19,1.20
    """

    return (' '.join(split_line[7:9]), ' '.join(split_line[3:5]).replace(",", ""),
            split_line[0], split_line[1][:2])

@decorators.define_versions
def get_time_remaining(average_read_rate, average_read_rate_unit, disk_capacity,
                       disk_capacity_unit, recovered_data):
    """
    Calculate remaining time based on the average read rate and the current amount
    of data recovered.

    Returns:
        string.             The remaining time in human-readable form eg
                            "10.2 minutes", "4.3 days" etc, or "Unknown"
                            if unable to calculate.

    Works with ddrescue versions: 1.14,1.15,1.16,1.17,1.18,1.19
    """

    #Make sure everything's in the correct units.
    new_average_read_rate = CoreTools.change_units(float(average_read_rate),
                                                   average_read_rate_unit,
                                                   disk_capacity_unit)[0]

    try:
        #Perform the calculation and round it.
        result = (int(disk_capacity) - recovered_data) / new_average_read_rate

        #Convert between Seconds, Minutes, Hours, and Days to make the value as
        #understandable as possible.
        if result <= 60:
            return str(int(round(result)))+" seconds"

        elif result >= 60 and result <= 3600:
            return str(round(result/60, 1))+" minutes"

        elif result > 3600 and result <= 86400:
            return str(round(result/3600, 2))+" hours"

        elif result > 86400:
            return str(round(result/86400, 2))+" days"

    except ZeroDivisionError:
        pass

    return "Unknown"
