#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# DDRescue Tools for ddrescue v1.14 (or newer) in the Tools Package for DDRescue-GUI
# This file is part of DDRescue-GUI.
# Copyright (C) 2013-2019 Hamish McIntyre-Bhatty
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

#Do future imports to prepare to support python 3.
#Use unicode strings rather than ASCII strings, as they fix potential problems.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

from . import decorators

#Make unicode an alias for str in Python 3.
if sys.version_info[0] == 3:
    unicode = str #pylint: disable=redefined-builtin,invalid-name

@decorators.define_versions
def get_inputpos_numerrors_averagereadrate(split_line): #pylint: disable=invalid-name
    """
    Get Input Position, Number of Errors, and Average Read Rate.
    Works with ddrescue versions: 1.14,1.15,1.16,1.17,1.18,1.19,1.20
    """

    return (' '.join(split_line[1:3]).replace(",", ""),
            split_line[4].replace(",", ""), split_line[7], split_line[8])

@decorators.define_versions
def get_outputpos_time_since_last_read(split_line): #pylint: disable=invalid-name
    """
    Get Output Position and Time Since Last Successful Read.
    Works with ddrescue versions: 1.14,1.15,1.16,1.17
    """

    return (' '.join(split_line[1:3]).replace(",", ""), ' '.join(split_line[-2:]))

@decorators.define_versions
def get_current_rate_error_size_recovered_data(split_line): #pylint: disable=invalid-name
    """
    Get Current Read Rate, Error Size, and Recovered Data.
    Works with ddrescue versions: 1.14,1.15,1.16,1.17,1.18,1.19,1.20
    """

    return (' '.join(split_line[7:9]), ' '.join(split_line[3:5]).replace(",", ""),
            split_line[0], split_line[1][:2])
