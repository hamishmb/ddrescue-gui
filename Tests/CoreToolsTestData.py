#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# BackendTools test data for DDRescue-GUI
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
This module holds the data used for the backend tools tests.
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

#Functions to return test data.
def return_fake_commands():
    """Returns some fake commands to test the start_process function against to make sure it isn't losing output."""

    dictionary = {}
    dictionary[""" sh -c "echo 'This is a test of the fire alarm system'" """] = {}
    dictionary[""" sh -c "echo 'This is a test of the fire alarm system'" """]["Output"] = "This is a test of the fire alarm system"
    dictionary[""" sh -c "echo 'This is a test of the fire alarm system'" """]["Retval"] = 0
    dictionary[""" sh -c "echo 'This returns 2'; exit 2" """] = {}
    dictionary[""" sh -c "echo 'This returns 2'; exit 2" """]["Output"] = "This returns 2"
    dictionary[""" sh -c "echo 'This returns 2'; exit 2" """]["Retval"] = 2
    dictionary[""" sh -c "TIMES=1; while [ $TIMES -lt 6 ]; do echo 'Slow task'; sleep 2; TIMES=$(( $TIMES + 1 )); done" """] = {}
    dictionary[""" sh -c "TIMES=1; while [ $TIMES -lt 6 ]; do echo 'Slow task'; sleep 2; TIMES=$(( $TIMES + 1 )); done" """]["Output"] = "Slow task\n"*4 + "Slow task"
    dictionary[""" sh -c "TIMES=1; while [ $TIMES -lt 6 ]; do echo 'Slow task'; sleep 2; TIMES=$(( $TIMES + 1 )); done" """]["Retval"] = 0
    dictionary[""" sh -c "TIMES=1; while [ $TIMES -lt 6000 ]; do echo 'Fast Task'; sleep 0.001; TIMES=$(( $TIMES + 1 )); done" """] = {}
    dictionary[""" sh -c "TIMES=1; while [ $TIMES -lt 6000 ]; do echo 'Fast Task'; sleep 0.001; TIMES=$(( $TIMES + 1 )); done" """]["Output"] = "Fast Task\n"*5998 + "Fast Task"
    dictionary[""" sh -c "TIMES=1; while [ $TIMES -lt 6000 ]; do echo 'Fast Task'; sleep 0.001; TIMES=$(( $TIMES + 1 )); done" """]["Retval"] = 0

    return dictionary

def return_fake_filenames():
    """Returns some fake filenames to test the create_unique_key function against."""

    dictionary = {}
    dictionary["/dev/ewgrhtjerwhd"] = {}
    dictionary["/dev/ewgrhtjerwhd"]["Result"] = "...ev/ewgrhtjerwhd"
    dictionary["/home/hamish/Desktop/img.img"] = {}
    dictionary["/home/hamish/Desktop/img.img"]["Result"] = ["...Desktop/img.img", "...Desktop/img.i~2"]
    dictionary["/dev/sda"] = {}
    dictionary["/dev/sda"]["Result"] = "/dev/sda"
    dictionary["/home/hamish/Desktop/img2.img"] = {}
    dictionary["/home/hamish/Desktop/img2.img"]["Result"] = ["...Desktop/img.img", "...esktop/img2.img", "...Desktop/img.i~2"]

    return dictionary
