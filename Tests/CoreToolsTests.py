#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# CoreTools tests for DDRescue-GUI
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
from Tools import core as CoreTools #pylint: disable=import-error

#Import test data and functions.
from . import CoreToolsTestData as Data
from . import CoreToolsTestFunctions as Functions

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

class TestStartProcess(unittest.TestCase):
    """Tests for start_process()"""

    def setUp(self):
        self.commands = Data.return_fake_commands()

    def tearDown(self):
        del self.commands

    def test_start_process(self):
        """Simple test for start_process()"""
        for command in self.commands.keys():
            retval, output = CoreTools.start_process(cmd=command, return_output=True)
            self.assertEqual(retval, self.commands[command]["Retval"])
            self.assertEqual(output, self.commands[command]["Output"])

class TestCreateUniqueKey(unittest.TestCase):
    """Tests for create_unique_key()"""

    def setUp(self):
        self.keys_dictionary = {}
        self.filenames = Data.return_fake_filenames()

    def tearDown(self):
        del self.keys_dictionary
        del self.filenames

    def test_create_unique_key(self):
        """Simple test for create_unique_key()"""
        for _file in self.filenames:
            key = CoreTools.create_unique_key(self.keys_dictionary, _file, 15)
            self.assertTrue(key in self.filenames[_file]["Result"])
            self.keys_dictionary[key] = ""

class TestSendNotification(unittest.TestCase):
    """Tests for send_notification()"""

    def setUp(self):
        self.app = wx.App()

    def tearDown(self):
        self.app.Destroy()
        del self.app

    def test_send_notification(self):
        """Simple test for send_notification()"""
        #Tell the user we are about to send a notification.
        dlg = wx.MessageDialog(None, "DDRescue-GUI's CoreTools tests are about to send you a "
                               +"notification to test that notifications are working. You will "
                               +"then be prompted to confirm if they are working or not.",
                               "DDRescue-GUI - Tests", wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        #Send it.
        CoreTools.send_notification("Test Message from unit tests.")

        #Ask the user if they got it.
        dlg = wx.MessageDialog(None, "Did you see the notification? Note that on some "
                               +"systems they can take up to 10 seconds "
                               +"to come through. Mac users: check your "
                               +"notification centre.", "DDRescue-GUI - Tests",
                               wx.YES_NO | wx.ICON_QUESTION)

        result = dlg.ShowModal()
        dlg.Destroy()

        wx.GetApp().Yield()

        self.assertEqual(result, wx.ID_YES)

class TestIsMounted(unittest.TestCase):
    """Tests for is_mounted()"""

    def setUp(self):
        self.app = wx.App()

        #Get a device path from the user to test against.
        global POTENTIAL_PARTITION_PATH

        self.path = POTENTIAL_PARTITION_PATH

        if POTENTIAL_PARTITION_PATH == "":
            dlg = wx.TextEntryDialog(None, "DDRescue-GUI needs a partition name to test against.\n"
                                     +"No data on your device will be modified. Suggested: "
                                     +"insert a USB disk and leave it mounted.\nNote: Do not use "
                                     +"your device while these tests are running, or it may "
                                     +"interfere with the tests.", "DDRescue-GUI Tests",
                                     POTENTIAL_PARTITION_PATH, style=wx.OK)

            dlg.ShowModal()
            self.path = dlg.GetValue()
            dlg.Destroy()
            POTENTIAL_PARTITION_PATH = self.path

        #Save it for autocomplete with other dialogs.
        POTENTIAL_PARTITION_PATH = self.path

    def tearDown(self):
        #Check if anything is mounted at our temporary mount point.
        if Functions.is_mounted(self.path):
            Functions.unmount_disk(self.path)

        #Remove the mount point.
        if os.path.isdir("/tmp/ddrescueguimtpt"):
            if os.path.isdir("/tmp/ddrescueguimtpt/subdir"):
                os.rmdir("/tmp/ddrescueguimtpt/subdir")

            os.rmdir("/tmp/ddrescueguimtpt")

        self.app.Destroy()
        del self.app
        del self.path

    def test_is_mounted1(self):
        """Test #1: Check if it's detected when a disk is mounted."""
        #If not mounted, mount it
        if not Functions.is_mounted(self.path):
            self.assertEqual(CoreTools.mount_disk(self.path, "/tmp/ddrescueguimtpt"), 0)

        self.assertTrue(CoreTools.is_mounted(self.path))

    def test_is_mounted2(self):
        """Test #2: Check if it's detected when a disk isn't mounted."""
        #Unmount it.
        Functions.unmount_disk(self.path)

        self.assertFalse(CoreTools.is_mounted(self.path))

class TestGetMountPoint(unittest.TestCase):
    """Tests for get_mount_point()"""

    def setUp(self):
        self.app = wx.App()

        #Get a device path from the user to test against.
        global POTENTIAL_PARTITION_PATH

        self.path = POTENTIAL_PARTITION_PATH

        if POTENTIAL_PARTITION_PATH == "":
            dlg = wx.TextEntryDialog(None, "DDRescue-GUI needs a partition name to test against.\n"
                                     +"No data on your device will be modified. Suggested: "
                                     +"insert a USB disk and leave it mounted.\nNote: Do not use "
                                     +"your device while these tests are running, or it may "
                                     +"interfere with the tests.", "DDRescue-GUI Tests",
                                     POTENTIAL_PARTITION_PATH, style=wx.OK)

            dlg.ShowModal()
            self.path = dlg.GetValue()
            dlg.Destroy()
            POTENTIAL_PARTITION_PATH = self.path

        self.mount_point = Functions.get_mount_point(self.path)

        #Save it for autocomplete with other dialogs.
        POTENTIAL_PARTITION_PATH = self.path

    def tearDown(self):
        self.app.Destroy()
        del self.app
        del self.path

    def test_get_mount_point1(self):
        """Test #1: Get mount point of a mounted disk."""
        #Mount disk if not mounted.
        if not Functions.is_mounted(self.path):
            Functions.mount_disk(self.path, "/tmp/ddrescueguimtpt")

        #Get mount point and verify.
        self.assertEqual(CoreTools.get_mount_point(self.path),
                         Functions.get_mount_point(self.path))

    def test_get_mount_point2(self):
        """Test #2: Get mount point of an unmounted disk."""
        #Unmount disk.
        Functions.unmount_disk(self.path)

        #Get mount point.
        self.assertIsNone(CoreTools.get_mount_point(self.path))

class TestMountDisk(unittest.TestCase):
    """Tests for mount_disk()"""

    def setUp(self):
        self.app = wx.App()

        #Get a device path from the user to test against.
        global POTENTIAL_PARTITION_PATH

        self.path = POTENTIAL_PARTITION_PATH
        self.path2 = ""

        if POTENTIAL_PARTITION_PATH == "":
            dlg = wx.TextEntryDialog(None, "DDRescue-GUI needs a partition name to test against.\n"
                                     +"No data on your device will be modified. Suggested: "
                                     +"insert a USB disk and leave it mounted.\nNote: Do not use "
                                     +"your device while these tests are running, or it may "
                                     +"interfere with the tests.", "DDRescue-GUI Tests",
                                     POTENTIAL_PARTITION_PATH, style=wx.OK)

            dlg.ShowModal()
            self.path = dlg.GetValue()
            dlg.Destroy()
            POTENTIAL_PARTITION_PATH = self.path

        self.mount_point = Functions.get_mount_point(self.path)

        if self.mount_point is None:
            self.mount_point = "/tmp/ddrescueguimtpt"
            os.mkdir(self.mount_point)

    def tearDown(self):
        self.app.Destroy()

        #Unmount.
        CoreTools.unmount_disk(self.path)

        del self.app
        del self.path

        if os.path.isdir("/tmp/ddrescueguimtpt"):
            if os.path.isdir("/tmp/ddrescueguimtpt/subdir"):
                os.rmdir("/tmp/ddrescueguimtpt/subdir")

            os.rmdir("/tmp/ddrescueguimtpt")

    def test_mount_disk1(self):
        """Test #1: Mounting a disk that is already mounted."""
        Functions.mount_disk(self.path, self.mount_point)

        #partition should be mounted, so we should pass this without doing anything.
        self.assertEqual(CoreTools.mount_disk(self.path, self.mount_point), 0)

        Functions.unmount_disk(self.path)

    def test_mount_disk2(self):
        """Test #2: Mounting a disk that isn't already mounted."""
        #Unmount disk.
        Functions.unmount_disk(self.path)

        self.assertEqual(CoreTools.mount_disk(self.path, self.mount_point), 0)

        Functions.unmount_disk(self.path)

    def test_mount_partition3(self):
        """Test #3: Mounting a disk where there is another disk in the way."""
        #Get another device path from the user to test against.
        dlg = wx.TextEntryDialog(None, "DDRescue-GUI needs a second (different) partition name to "
                                 +"test against.\nNo data on your device will be modified. "
                                 +"Suggested: insert a USB disk and leave it mounted.\nNote: "
                                 +"Do not use your device while these tests are running, or it "
                                 +"may interfere with the tests.", "DDRescue-GUI Tests",
                                 "", style=wx.OK)
        dlg.ShowModal()
        self.path2 = dlg.GetValue()
        dlg.Destroy()

        #Unmount both partitions.
        for partition in [self.path, self.path2]:
            Functions.unmount_disk(partition)

        #Mount the 2nd one on the desired path for the 1st one.
        CoreTools.mount_disk(self.path2, self.mount_point)

        #Now try to mount the first one there.
        CoreTools.mount_disk(self.path, self.mount_point)

        #Now the 2nd should have been unmounted to get it out of the way,
        #and the 1st should be there.
        self.assertFalse(Functions.is_mounted(self.path2, self.mount_point))
        self.assertTrue(Functions.is_mounted(self.path, self.mount_point))

        Functions.unmount_disk(self.path)

        #Clean up.
        del self.path2

    def test_mount_partition4(self):
        """Test #4: Mounting a disk in the subdir of the usual mount point (sanity check)."""
        #Unmount partition.
        Functions.unmount_disk(self.path)

        #Try to mount in subdir of usual mount point.
        CoreTools.mount_disk(self.path, self.mount_point+"/subdir")

        #Check is mounted.
        self.assertTrue(Functions.is_mounted(self.path, self.mount_point+"/subdir"))

        #Unmount.
        CoreTools.unmount_disk(self.path)

        #Clean up.
        if os.path.isdir(self.mount_point+"/subdir"):
            os.rmdir(self.mount_point+"/subdir")

