#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MountingTools tests for DDRescue-GUI
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
These are the backend tools tests.
"""

#Do future imports to prepare to support python 3.
#Use unicode strings rather than ASCII strings, as they fix potential problems.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

#Import modules
import unittest
import os
import sys
import wx
import wx.adv

#Allow imports of modules & packages 1 level up.
sys.path.insert(0, os.path.abspath('..'))

#Import tools.
from Tools import mount_tools as MountingTools #pylint: disable=import-error

#Make unicode an alias for str in Python 3.
if sys.version_info[0] == 3:
    unicode = str #pylint: disable=redefined-builtin

#Set up resource path and determine OS.
if "wxGTK" in wx.PlatformInfo:
    LINUX = True

    #Check if we're running on Parted Magic.
    PARTED_MAGIC = (os.uname()[1] == "PartedMagic")

elif "wxMac" in wx.PlatformInfo:
    LINUX = False
    PARTED_MAGIC = False

#Set up autocomplete vars.
POTENTIAL_DEVICE_PATH = ""
POTENTIAL_PARTITION_PATH = ""

class TestMacRunHdiutil(unittest.TestCase):
    """Tests for mac_run_hdiutil()"""

    def setUp(self):
        self.app = wx.App()
        self.path = ""

    def tearDown(self):
        self.app.Destroy()
        del self.app

    @unittest.skipUnless(not LINUX, "Mac-specific test")
    def test_mac_run_hdiutil(self):
        """Simple test for mac_run_hdiutil()"""
        #TODO Add more tests for when "resource is temporarily unavailable" errors happen
        #FIXME Very basic test.
        #TODO Create image to test against?
        #TODO Test against a device too.
        #Get a device path from the user to test against.
        global POTENTIAL_DEVICE_PATH

        self.path = POTENTIAL_DEVICE_PATH

        if POTENTIAL_DEVICE_PATH == "":
            dlg = wx.TextEntryDialog(None, "DDRescue-GUI needs a device name to test against.\n"
                                     +"No data on your device will be modified. Suggested: "
                                     +"insert a USB disk and leave it mounted.\nNote: Do not use "
                                     +"your device while these tests are running, or it may "
                                     +"interfere with the tests.", "DDRescue-GUI Tests",
                                     POTENTIAL_DEVICE_PATH, style=wx.OK)

            dlg.ShowModal()
            self.path = dlg.GetValue()
            dlg.Destroy()
            POTENTIAL_DEVICE_PATH = self.path

        self.assertEqual(MountingTools.Mac.run_hdiutil("info")[0], 0)
