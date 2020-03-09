#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DDRescue Tools (decorators) in the Tools Package for DDRescue-GUI
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
Decorators for DDRescue tools
"""

#Do future imports to prepare to support python 3.
#Use unicode strings rather than ASCII strings, as they fix potential problems.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

#Make unicode an alias for str in Python 3.
if sys.version_info[0] == 3:
    unicode = str #pylint: disable=redefined-builtin,invalid-name

def define_versions(function):
    """
    Reads the function docstring to find the ddrescue versions the function
    supports. This is used on all of the tools in the modules in the
    DDRescueTools package.

    This information is saved in the function's SUPPORTEDVERSIONS attribute.

    Args:
        function.       The function object that we are creating the attribute
                        for.
    """

    function.SUPPORTEDVERSIONS = []

    for version in function.__doc__.split("Works with ddrescue versions: ")[1].split(","):
        function.SUPPORTEDVERSIONS.append(version.replace(" ", "").replace("\n", ""))

    return function
