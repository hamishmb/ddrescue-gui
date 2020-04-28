#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DDRescue Tools (setup scripts) in the Tools Package for DDRescue-GUI
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
Used to set up the GUI to use the correct version of tools for
the user's version of ddrescue.
"""

#Import modules.
import types
import sys

#Import tools modules.
from . import allversions
from . import one_point_fourteen
from . import one_point_eighteen
from . import one_point_twenty
from . import one_point_twenty_one
from . import one_point_twenty_two

#Get a list of functions in all of our ddrescue tools modules.
FUNCTIONS = []

for Module in (allversions, one_point_fourteen, one_point_eighteen, one_point_twenty,
               one_point_twenty_one, one_point_twenty_two):

    for function in dir(Module):
        if isinstance(Module.__dict__.get(function), types.FunctionType):
            FUNCTIONS.append(vars(Module)[function])

def setup_for_ddrescue_version(ddrescue_version):
    """
    Selects and returns a list of the correct functions for our version of
    ddrescue.

    Args:
        ddrescue_version (str):             The version of ddrescue installed
                                            on the system. eg "1.25".

    Returns:
        list.                       A list of all the functions that are designed
                                    to work with this ddrescue version.

    """

    #Select the best tools if we have an unsupported version of ddrescue.
    minor_version = int(ddrescue_version.split(".")[1])

    if minor_version < 14:
        #Too old.
        best_version = "1.14"

    elif minor_version > 25:
        #Too new.
        best_version = "1.25"

    else:
        #Supported version.
        #NB: Ignore minor revisions eg 1.18.1.
        best_version = '.'.join(ddrescue_version.split(".")[0:2])

    suitable_functions = []

    for function in FUNCTIONS: #pylint: disable=redefined-outer-name
        if best_version in function.SUPPORTEDVERSIONS:
            suitable_functions.append(function)

    return suitable_functions
