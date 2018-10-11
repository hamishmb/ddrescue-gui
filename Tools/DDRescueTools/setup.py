#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# DDRescue Tools (setup scripts) in the Tools Package for DDRescue-GUI Version 2.0.0
# This file is part of DDRescue-GUI.
# Copyright (C) 2013-2018 Hamish McIntyre-Bhatty
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
Used to set up the GUI to use the correct version of tools for
the user's version of ddrescue.
"""

#Do future imports to prepare to support python 3.
#Use unicode strings rather than ASCII strings, as they fix potential problems.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

#Import modules.
import types
import sys

#Import tools modules.
from . import allversions
from . import one_point_forteen
from . import one_point_eighteen
from . import one_point_twenty
from . import one_point_twenty_one
from . import one_point_twenty_two

#Make unicode an alias for str in Python 3.
if sys.version_info[0] == 3:
    unicode = str #pylint: disable=redefined-builtin,invalid-name

#Get a list of functions in all of our ddrescue tools modules.
FUNCTIONS = []

for Module in (allversions, one_point_forteen, one_point_eighteen, one_point_twenty,
               one_point_twenty_one, one_point_twenty_two):

    for function in dir(Module):
        if isinstance(Module.__dict__.get(function), types.FunctionType):
            FUNCTIONS.append(vars(Module)[function])

def setup_for_ddrescue_version(ddrescue_version):
    """
    Selects the correct tools for our version of ddrescue.
    """

    #Select the best tools if we have an unsupported version of ddrescue.
    minor_version = int(ddrescue_version.split(".")[1])

    if minor_version < 14:
        #Too old.
        best_version = "1.14"

    elif minor_version > 23:
        #Too new.
        best_version = "1.23"

    elif minor_version == 18:
        #Fix for v1.18.1.
        best_version = "1.18"

    else:
        #Supported version.
        best_version = ddrescue_version

    suitable_functions = []

    for function in FUNCTIONS: #pylint: disable=redefined-outer-name
        if best_version in function.SUPPORTEDVERSIONS:
            suitable_functions.append(function)

    return suitable_functions
