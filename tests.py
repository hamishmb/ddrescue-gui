#!/usr/bin/env python3
# Disabled coding declaration to maintain py2 compatibility for now.
# Unit tests for DDRescue-GUI
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
This file is used to start the test suites for DDRescue-GUI.
"""

#Do future imports to prepare to support python 3.
#Use unicode strings rather than ASCII strings, as they fix potential problems.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

#Import modules.
import unittest
import logging
import os
import getopt
import sys
import wx

#Make unicode an alias for str in Python 3.
if sys.version_info[0] == 3:
    unicode = str #pylint: disable=redefined-builtin,invalid-name

#Global vars.
VERSION = "2.1.0"

def usage():
    """Outputs usage information"""
    print("\nUsage: Tests.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:                   Display this help text.")
    print("       -d, --debug:                  Set logging level to debug; show all messages.")
    print("                                     Default: show only critical logging messages.\n")
    print("       -c, --coretools:              Run tests for CoreTools module.")
    print("       -m, --mountingtools:          Run tests for MountingTools module.")
    print("       -a, --all:                    Run all the tests. The default.\n")
    print("       -t, --tests:                  Ignored.")
    print("DDRescue-GUI "+VERSION+" is released under the GNU GPL VERSION 3")
    print("Copyright (C) Hamish McIntyre-Bhatty 2013-2020")

if __name__ == "__main__":
    #Check all cmdline options are valid.
    try:
        OPTIONS, ARGUMENTS = getopt.getopt(sys.argv[1:], "hdcmat", ["help", "debug", "coretools",
                                                                     "mountingtools",
                                                                     "all", "tests"])

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(unicode(err))
        usage()
        sys.exit(2)

    #Log only critical messages by default.
    LOGGER_LEVEL = logging.CRITICAL

    #Set up the logger (silence all except critical logging messages).
    logger = logging.getLogger("DDRescue-GUI")
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
                        datefmt='%d/%m/%Y %I:%M:%S %p')

    logger.setLevel(LOGGER_LEVEL)

    #We have to handle options twice for this to work - a bit strange, but it works.
    #Handle debugging mode here.
    for o, a in OPTIONS:
        if o in ["-d", "--debug"]:
            LOGGER_LEVEL = logging.DEBUG

    logger.setLevel(LOGGER_LEVEL)

    #Custom tools module.
    import Tools #pylint: disable=import-error
    from Tools import core as CoreTools #pylint: disable=import-error
    from Tools import mount_tools as MountingTools #pylint: disable=import-error

    #Import test modules.
    from Tests import CoreToolsTests #pylint: disable=import-error
    from Tests import MountingToolsTests #pylint: disable=import-error

    #Set up which tests to run based on options given.
    #TODO Set up full defaults when finished.
    TEST_SUITES = [CoreToolsTests, MountingToolsTests]

    for o, a in OPTIONS:
        if o in ["-c", "--coretools"]:
            TEST_SUITES = [CoreToolsTests]

        elif o in ("-m", "--mountingtools"):
            TEST_SUITES = [MountingToolsTests]

        elif o in ["-a", "--all"]:
            TEST_SUITES = [CoreToolsTests, MountingToolsTests]
            #TEST_SUITES.append(MainTests)

        elif o in ["-t", "--tests"]:
            pass

        elif o in ["-d", "--debug"]:
            LOGGER_LEVEL = logging.DEBUG

        elif o in ["-h", "--help"]:
            usage()
            sys.exit()

        else:
            assert False, "unhandled option"

    #Set up resource path and determine OS.
    if "wxGTK" in wx.PlatformInfo:
        #Set the resource path to /usr/share/ddrescue-gui/
        RESOURCEPATH = '/usr/share/ddrescue-gui'
        LINUX = True

        #Check if we're running on Parted Magic.
        PARTED_MAGIC = (os.uname()[1] == "PartedMagic")

    elif "wxMac" in wx.PlatformInfo:
        try:
            #Set the resource path from an environment variable,
            #as mac .apps can be found in various places.
            RESOURCEPATH = os.environ['RESOURCEPATH']

        except KeyError:
            #Use '.' as the rescource path instead as a fallback.
            RESOURCEPATH = "."

        LINUX = False
        PARTED_MAGIC = False

    #Setup test modules.
    CoreToolsTests.CoreTools = CoreTools
    CoreToolsTests.Tools = Tools

    MountingToolsTests.MountingTools = MountingTools
    MountingToolsTests.Tools = Tools

    for module in TEST_SUITES:
        print("\n\n---------------------------- Tests for "
              + unicode(module)+" ----------------------------\n\n")
        unittest.TextTestRunner(verbosity=2).run(unittest.TestLoader().loadTestsFromModule(module))
