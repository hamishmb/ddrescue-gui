#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DDRescue-GUI Main Script
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

# pylint: disable=too-many-lines,global-statement,import-error,no-name-in-module,wrong-import-order
# pylint: disable=ungrouped-imports,logging-not-lazy
#
# Reason (too-many-lines): Not a module
# Reason (global-statement): Need to use global at times.
# Reason (import-error): Lots of false positives, some libs not present in older wx builds.
# Reason (no-name-in-module): As above.
# Reason (wrong-import-order): False positives.
# Reason (ungrouped-imports): Can't group wx imports due to module changes.
# Reason (logging-not-lazy): This is a more readable way of logging.

"""
This is the main script that you use to start DDRescue-GUI.
"""

#Do future imports to support python 2.
#Use unicode strings rather than ASCII strings, as they fix potential problems.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

#Import other modules
from distutils.version import LooseVersion

import threading
import getopt
import logging
import time
import subprocess
import os
import sys
import plistlib
import traceback
import ast
import requests

import getdevinfo

import wx
import wx.lib.stattext
import wx.lib.statbmp

#Compatibility with wxPython 4.
if int(wx.version()[0]) >= 4:
    import wx.adv
    from wx.adv import SplashScreen as wxSplashScreen
    from wx.adv import Animation as wxAnimation
    from wx.adv import AnimationCtrl as wxAnimationCtrl
    from wx.adv import AboutDialogInfo as wxAboutDialogInfo
    from wx.adv import AboutBox as wxAboutBox

else:
    import wx.animate
    from wx import SplashScreen as wxSplashScreen
    from wx.animate import Animation as wxAnimation
    from wx.animate import AnimationCtrl as wxAnimationCtrl
    from wx import AboutDialogInfo as wxAboutDialogInfo
    from wx import AboutBox as wxAboutBox

#Make unicode an alias for str in Python 3.
if sys.version_info[0] == 3:
    #Disable cos necessary to keep supporting python 2.
    unicode = str #pylint: disable=redefined-builtin,invalid-name

    #Plist hack for Python 3.
    plistlib.readPlistFromString = plistlib.loads #pylint: disable=no-member

#Define global variables.
VERSION = "2.1.0"
RELEASE_DATE = "27/4/2020"
RELEASE_TYPE = "Stable"

session_ending = False
DDRESCUE_VERSION = "1.25" #Default to latest version.
CLASSIC_WXPYTHON = int(wx.version()[0]) < 4
APPICON = None
SETTINGS = {}
DISKINFO = {}

def usage():
    """
    Outputs information on cmdline options for the user.
    """

    print("\nUsage: DDRescue-GUI.py [OPTION]\n\n")
    print("Options:\n")
    print("       -h, --help:                   Show this help message")
    print("       -q, --quiet:                  Show only warnings, errors and critical errors")
    print("                                     in the log file. Very unhelpful for debugging,")
    print("                                     and not recommended.")
    print("       -v, --verbose:                Enable logging of info messages, as well as")
    print("                                     warnings, errors and critical errors.")
    print("                                     Not the best for debugging, but acceptable if")
    print("                                     there is little disk space.")
    print("       -d, --debug:                  Log lots of boring debug messages, as well as")
    print("                                     information, warnings, errors and critical")
    print("                                     errors. Usually used for diagnostic purposes.")
    print("                                     The default, as it's very helpful if problems")
    print("                                     are encountered, and the user needs help\n")
    print("       -t, --tests                   Run all unit tests.")
    print("DDRescue-GUI "+VERSION+" is released under the GNU GPL Version 3")
    print("Copyright (C) Hamish McIntyre-Bhatty 2013-2020")

#Determine if running on Linux or Mac.
if "wxGTK" in wx.PlatformInfo:
    #Set the resource path to /usr/share/ddrescue-gui/
    RESOURCEPATH = '/usr/share/ddrescue-gui'
    LINUX = True

    #Check if we're running on Parted Magic.
    PARTED_MAGIC = ("PartedMagic" in os.uname()[1])

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

#Import platform-specific modules
if LINUX:
    import getdevinfo.linux #pylint: disable=wrong-import-position

else:
    import getdevinfo.macos #pylint: disable=wrong-import-position

if __name__ == "__main__":
    #Check all cmdline options are valid.
    try:
        OPTS = getopt.getopt(sys.argv[1:], "hqvd", ["help", "quiet", "verbose", "debug"])[0]

    except getopt.GetoptError as err:
        #Invalid option. Show the help message and then exit.
        #Show the error.
        print(unicode(err))
        usage()
        sys.exit(2)

    #Determine the option(s) given, and change the level of logging based on cmdline options.
    LOGGER_LEVEL = logging.DEBUG

    for o, a in OPTS:
        if o in ["-q", "--quiet"]:
            LOGGER_LEVEL = logging.WARNING

        elif o in ["-v", "--verbose"]:
            LOGGER_LEVEL = logging.INFO

        elif o in ["-d", "--debug"]:
            LOGGER_LEVEL = logging.DEBUG

        elif o in ["-h", "--help"]:
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    #Set up logging with default logging mode as debug.
    logger = logging.getLogger("DDRescue-GUI")

    #Try to find a free log file name.
    #Prevents accidental overwriting, and allows multiple instances.
    LOG_SUFFIX = 1

    while True:
        if os.path.isfile("/tmp/ddrescue-gui.log"+"."+unicode(LOG_SUFFIX)):
            LOG_SUFFIX += 1
            continue

        logging.basicConfig(filename="/tmp/ddrescue-gui.log"+"."+unicode(LOG_SUFFIX),
                            format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
                            datefmt='%d/%m/%Y %I:%M:%S %p')

        break

    logger.setLevel(LOGGER_LEVEL)

    #Import modules here to make sure logger level is set correctly.
    import Tools.core as CoreTools
    import Tools.mount_tools as MountingTools
    import Tools.DDRescueTools.setup as DDRescueTools

    CoreTools.LOG_SUFFIX = LOG_SUFFIX

    #Set up MountingTools.
    MountingTools.SETTINGS = SETTINGS

    #Log which OS we're running on (helpful for debugging).
    if LINUX:
        logger.debug("Detected LINUX...")

        if PARTED_MAGIC:
            logger.debug("Detected Parted Magic...")

    else:
        logger.debug("Detected Mac OS X...")

#Begin Disk Information Handler thread.
class GetDiskInformation(threading.Thread):
    """
    Used to get disk information without blocking the GUI thread.
    Calls parent.receive_diskinfo when info has ben retrieved.
    """

    def __init__(self, parent):
        """
        Initialize and start the thread.

        Args:
            parent (object).                The parent window that started the
                                            thread.
        """

        self.parent = parent
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """
        Use GetDevInfo module to get disk information.
        """

        #Use a module I've written to collect data about connected Disks, and return it.
        wx.CallAfter(self.parent.receive_diskinfo, self.get_info())

    def get_info(self): #pylint: disable=no-self-use
        """
        Get disk information as a privileged user.

        Returns:
            dict.
                If successful:         The disk information.
                If unsuccessful:       An empty dictionary.
        """

        output = CoreTools.start_process(cmd=sys.executable+" "+RESOURCEPATH
                                         +"/Tools/run_getdevinfo.py",
                                         return_output=True,
                                         privileged=True)[1]

        #Success! Now use ast to convert the returned string to a dictionary.
        try:
            return ast.literal_eval(output)

        except (SyntaxError, ValueError, TypeError) as error:
            #If this fails for some reason, just return an empty dictionary.
            logger.error("GetDiskInformation().get_info(): Error: "+unicode(error))
            return {}

#End Disk Information Handler thread.
#Begin Starter Class
class MyApp(wx.App):
    """
    The wxPython app. Must be declared for application to work.
    This is how the application is started.
    """

    def OnInit(self): #pylint: disable=invalid-name, no-self-use
        """
        Used to show the splash screen, which then starts the rest of the
        application.
        """

        splash = ShowSplash()
        splash.Show()
        return True

    def MacReopenApp(self): #pylint: disable=invalid-name
        """
        Called when the doc icon is clicked, shows the top-level window again
        even if it's minimised. Makes the GUI work in a more intuitive way on
        macOS.
        """

        self.GetTopWindow().Raise()

#End Starter Class
#Begin splash screen
class ShowSplash(wxSplashScreen): #pylint: disable=too-few-public-methods,no-member
    """
    A simple class used to display the splash screen on startup.
    After that, it starts the rest of the application.
    """

    def __init__(self, parent=None):
        """
        Prepare and display a splash screen.

        Args:
            parent (object).                The parent window that started the
                                            thread.
        """

        #Convert the image to a bitmap.
        splash = wx.Image(name=RESOURCEPATH+"/images/splash.png").ConvertToBitmap()

        self.already_exited = False

        #Display the splash screen.
        if CLASSIC_WXPYTHON:
            wxSplashScreen.__init__(self, splash, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
                                    2500, parent)

        else:
            wxSplashScreen.__init__(self, splash,
                                    wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT,
                                    2500, parent)

        self.Bind(wx.EVT_CLOSE, self.on_exit)

        #Make sure it's painted, which fixes the problem with the previous
        #temperamental splash screen.
        wx.GetApp().Yield()

    def on_exit(self, event=None):
        """
        Close the splash screen and start MainWindow.

        Kwargs:
            event[=None] (object).              The event object passed by
                                                wxPython when the splash times
                                                out.
        """
        self.Hide()

        if self.already_exited is False:
            #Stop this from executing twice when the splash is clicked.
            self.already_exited = True
            main_frame = MainWindow()
            APP.SetTopWindow(main_frame)
            main_frame.Show(True)

            #Skip handling the event so the main frame starts.
            event.Skip()

#End splash screen
#Begin Custom wx.TextCtrl Class.
class CustomTextCtrl(wx.TextCtrl): #pylint: disable=too-many-ancestors
    """
    A custom wx.TextCtrl that provides features that are broken on Linux and macOS.

    Features:
        A version of PositionToXY() that works on macOS.
        A version of XYToPosition() that works on macOS and fixes a bug on Linux.
        carriage_return(): Handles carriage returns correctly.
        up_one_line(): Moves insertion point up one line.

    """

    def __init__(self, parent, wx_id, value, style):
        """
        Initialise the custom wx.TextCtrl.

        Args:
            parent (object).                The parent window that started the
                                            thread.

            wx_id (int).                    The wxPython ID that this widget
                                            will use.

            value (string).                 Initial contents of the text box.
            style (int).                    The style of the text control.

        """
        wx.TextCtrl.__init__(self, parent, wx_id, value=value, style=style)

    def update(self, line):
        """
        Append the given line to the contents of the output box. Counts carriage
        returns and up-one-lines so that an auxiliary method
        (add_line) can handle them.

        Args:
            line (string).          The line to add.
        """


        crs = []
        uols = []
        char_number = 0

        for char in line:
            char_number += 1

            if char == "\r":
                crs.append(char_number)

            elif char == "¬":
                uols.append(char_number)

        char_number = 0
        temp_line = ""

        for char in line:
            char_number += 1

            if char_number not in crs and char_number not in uols:
                temp_line += char
                if char == "\n":
                    self.add_line(temp_line, crs, uols, char_number)
                    temp_line = ""

            else:
                self.add_line(temp_line, crs, uols, char_number)
                temp_line = ""

    def add_line(self, data, crs, uols, char_number):
        """
        Adds a new line to the custom output box. Also handles calling
        carriage_return() and up_one_line() when required. Receives the data
        chunks and other information from the update method.

        Args:
            data (string).                      The chunk of text to add to the
                                                output box.

            crs (list).                         A list of character numbers where
                                                the character is a carriage
                                                return.

            uols (list).                        As above, for up-one-line
                                                sequences.

            char_number (int).                  The character number we are at in
                                                the line (the character after
                                                the last character in our chunk
                                                of text).
        """

        insertion_point = self.GetInsertionPoint()
        self.Replace(insertion_point, insertion_point+len(data), data)

        if char_number in crs:
            self.carriage_return()

        elif char_number in uols:
            self.up_one_line()

    def PositionToXY(self, insertion_point): #pylint: disable=invalid-name,arguments-differ
        """
        A custom version of wx.TextCtrl.PositionToXY() that works on OS X
        (the built-in one isn't implemented on OS X).

        Args:
            insertion_point (int).          The insertion point we want to get
                                            the row and column numbers for.

        Returns:
            tuple(int, int).

                1st element:        The column.
                2nd element:        The row.

        .. note::
            The stock version of this method is still not implemented on OS X
            on wxPython 4 (it returns random numbers).
        """

        #Count the number and position of newline characters.
        text = self.GetRange(0, insertion_point)

        newlines = [0] #Count the start of the text as a newline.
        counter = 0
        for char in text:
            counter += 1

            if char == "\n":
                newlines.append(counter)

        #Find the last newline before our insertion point.
        for newline in newlines:
            if newlines.index(newline)+1 == len(newlines) or newline == insertion_point:
                #This is the last newline in the text, or the newline at our insertion point,
                #and is therefore the one we want.
                last_new_line = newline
                break

            elif newline < insertion_point:
                pass

            else:
                #When this is triggered, the previous newline (last iteration of the loop)
                #is the one we want.
                index = newlines.index(newline)
                last_new_line = newlines[index-1]
                break

        #Figure out what column we're in (how many chars after the last newline).
        column = insertion_point - last_new_line

        #Figure out which line we're on (the number of the last newline).
        row = newlines.index(last_new_line)

        return column, row

    def XYToPosition(self, column, row): #pylint: disable=invalid-name,arguments-differ
        """
        A custom version of wx.TextCtrl.XYToPosition() that works on OS X
        (the built-in one isn't implemented on OS X).

        Args:
            column (int).               The column we want to get the integer
                                        position for.

            row (int).                  The row we want to get the integer
                                        position for.

        Returns:
            int.                        The position.

        .. note::
            This is also helpful for Linux because the built-in one has a quirk:
            when you're at the end of the text, it always returns -1.

        .. note::
            As of wxPython 4, this is still not implemented on macOS.
        """

        #Count the number and position of newline characters.
        text = self.GetValue()

        newlines = [0] #Count the start of the text as a newline.
        counter = 0
        for char in text:
            counter += 1

            if char == "\n":
                newlines.append(counter)

        #Get the last newline.
        last_new_line = newlines[row]

        #Our position should be that number plus our column.
        position = last_new_line + column

        return position

    def carriage_return(self):
        """
        Handles carriage returns in output. This is done by going back to the last
        newline in the box - any new text will now overwrite what is there.
        """

        #Get the text up to the current insertion point.
        text = self.GetRange(0, self.GetInsertionPoint())

        #Find the last newline char in the text.
        newline_numbers = []
        counter = 0

        for char in text:
            if char == "\n":
                newline_numbers.append(counter)

            counter += 1

        if newline_numbers != []:
            last_newline = newline_numbers[-1]

        else:
            #Hacky bit to make the new insertion point 0 :)
            last_newline = -1

        #Set the insertion point to just after that newline, unless we're already there,
        #and in that case set the insertion point just after the previous newline.
        new_insertion_point = last_newline + 1

        self.SetInsertionPoint(new_insertion_point)

    def up_one_line(self):
        """
        Handles (control sequence to go up one line) in the output. This
        is done by moving the insertion point so we are up one line, but in the
        same column (if possible).
        """

        #Go up one line.
        #Get our column and line numbers.
        column, line = self.PositionToXY(self.GetInsertionPoint())

        #We go up one line, but stay in the same column, so find the integer position of the new
        #insertion point.
        new_insertion_point = self.XYToPosition(column, line-1)

        if new_insertion_point == -1:
            #Invalid column/line! Maybe we reached the start of the text?
            #Do nothing but log the error.
            logger.warning("CustomTextCtrl().up_one_line(): Invalid new insertion point when "
                           "trying to move up one line! This might mean we've reached the "
                           "start of the text in the output box.")

        else:
            #Set the new insertion point.
            self.SetInsertionPoint(new_insertion_point)

#End Custom wx.TextCtrl Class.
#Begin Main Window.
class MainWindow(wx.Frame): #pylint: disable=too-many-instance-attributes,too-many-public-methods,too-many-ancestors
    """
    DDRescue-GUI's main window.
    """

    def __init__(self):
        """
        Initialize MainWindow
        """
        wx.Frame.__init__(self, None, title="DDRescue-GUI", size=(956, 360),
                          style=wx.DEFAULT_FRAME_STYLE)

        self.panel = wx.Panel(self)
        self.SetClientSize(wx.Size(956, 360))

        print("DDRescue-GUI Version "+VERSION+" Starting up...")
        logger.info("DDRescue-GUI Version "+VERSION+" Starting up...")
        logger.info("Release date: "+RELEASE_DATE)
        logger.info("Running on Python version: "+unicode(sys.version_info)+"...")
        logger.info("Running on wxPython version: "+wx.version()+"...")
        logger.info("Checking for ddrescue...")

        logger.info("Determining ddrescue version...")
        global DDRESCUE_VERSION
        DDRESCUE_VERSION = CoreTools.determine_ddrescue_version()

        #Set the frame's icon.
        global APPICON
        APPICON = wx.Icon(RESOURCEPATH+"/images/Logo.png", wx.BITMAP_TYPE_PNG)
        wx.Frame.SetIcon(self, APPICON)

        #Set some variables
        logger.debug("MainWindow().__init__(): Setting some essential variables...")
        self.set_vars()
        self.define_vars()
        self.starting_up = True

        #Create a Statusbar in the bottom of the window and set the text.
        logger.debug("MainWindow().__init__(): Creating Status Bar...")
        self.make_status_bar()

        #Add text
        logger.debug("MainWindow().__init__(): Creating text...")
        self.create_text()

        #Create some buttons
        logger.debug("MainWindow().__init__(): Creating buttons...")
        self.create_buttons()

        #Create the choiceboxes.
        logger.debug("MainWindow().__init__(): Creating choiceboxes...")
        self.create_choice_boxes()

        #Create other widgets.
        logger.debug("MainWindow().__init__(): Creating all other widgets...")
        self.create_other_widgets()

        #Create the menus.
        logger.debug("MainWindow().__init__(): Creating menus...")
        self.create_menus()

        #Update the Disk info.
        logger.debug("MainWindow().__init__(): Updating Disk info...")
        self.get_diskinfo()

        #Set up sizers.
        logger.debug("MainWindow().__init__(): Setting up sizers...")
        self.setup_sizers()

        #Bind all events.
        logger.debug("MainWindow().__init__(): Binding events...")
        self.bind_events()

        #Make sure the window is displayed properly.
        self.on_detailed_info()
        self.on_terminal_output()
        self.list_ctrl.SetColumnWidth(0, 150)

        #Call Layout() on self.panel() to ensure it displays properly.
        self.panel.Layout()

        #Raise the window to the top on macOS - otherwise it starts in the background.
        #This is a bit ugly, but it works. Yay for Stack Overflow.
        #stackoverflow.com/questions/10901067/getting-a-window-to-the-top-in-wxpython-for-mac
        if not LINUX:
            subprocess.Popen(['osascript', '-e', '''\
                              tell application "System Events"
                              set procName to name of first process whose unix id is %s
                              end tell
                              tell application procName to activate
                              ''' % os.getpid()])

        #Check for updates.
        wx.CallLater(10000, self.check_for_updates, starting_up=True)

        logger.info("MainWindow().__init__(): Ready. Waiting for events...")

    def set_vars(self):
        """
        Set some essential variables
        """
        global SETTINGS

        #DDRescue version.
        SETTINGS["DDRescueVersion"] = DDRESCUE_VERSION

        #Basic settings and info.
        SETTINGS["InputFile"] = None
        SETTINGS["OutputFile"] = None
        SETTINGS["MapFile"] = None
        SETTINGS["RecoveringData"] = False
        SETTINGS["CheckedSettings"] = False

        #DDRescue's options.
        SETTINGS["DirectAccess"] = "-d"
        SETTINGS["OverwriteOutputFile"] = ""
        SETTINGS["Reverse"] = ""
        SETTINGS["Preallocate"] = ""
        SETTINGS["NoSplit"] = ""
        SETTINGS["BadSectorRetries"] = "-r 2"
        SETTINGS["MaxErrors"] = ""
        SETTINGS["ClusterSize"] = "-c 128"

        #Set the wildcards and make it easy for the user to find his/her home directory
        #(helps make DDRescue-GUI more user friendly).
        if LINUX:
            self.input_wildcard = "(S)ATA HDDs/USB Drives|sd*|Optical Drives|sr*|Floppy Drives|" \
                                 "fd*|IMG Disk Image (*.img)|*.img|" \
                                 "ISO (CD/DVD) Disk Image (*.iso)|*.iso|All Files/Disks (*)|*"

            self.output_wildcard = "IMG Disk Image (*.img)|*.img|" \
                                  "ISO (CD/DVD) Disk Image (*.iso)|*.iso|(S)ATA HDDs/USB Drives|" \
                                  "sd*|Floppy Drives|fd*|All Files/Disks (*)|*"

        else:
            self.input_wildcard = "Disk Drives|disk*|IMG Disk Image (*.img)|*.img|" \
                                 "DMG Disk Image (*.dmg)|*.dmg|ISO (CD/DVD) Disk Image (*.iso)|" \
                                 "*.iso|All Files/Disks (*)|*"

            self.output_wildcard = "IMG Disk Image (*.img)|*.img|DMG Disk Image (*.dmg)|*.dmg|" \
                                  "ISO (CD/DVD) Disk Image (*.iso)|*.iso"

        self.user_homedir = os.environ['HOME']

        #Define these to make pylint happy and prevent possible errors later.
        self.recovered_data = None
        self.disk_capacity = None
        self.aborted_recovery = None
        self.runtime_secs = None

    def define_vars(self):
        """
        Defines some variables used elsewhere in this class/instance
        """
        #Define these here to prevent adding checks to see if they're defined later.
        #This way, we don't lose these after a reset either.
        self.custom_input_paths = {}
        self.custom_output_paths = {}
        self.custom_map_paths = {}

    def make_status_bar(self):
        """
        Create and set up a statusbar
        """
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetFieldsCount(2)
        self.status_bar.SetStatusWidths([-1, 165])
        self.status_bar.SetStatusText("Ready.", 0)
        self.status_bar.SetStatusText("v"+VERSION+" ("+RELEASE_DATE+")", 1)

    def create_text(self):
        """
        Create all text for MainWindow
        """
        self.title_text = wx.StaticText(self.panel, -1, "Welcome to DDRescue-GUI!")
        self.input_text = wx.StaticText(self.panel, -1, "Image Source:")
        self.map_text = wx.StaticText(self.panel, -1, "Recovery Map File "
                                      "(previously called logfile):")

        self.output_text = wx.StaticText(self.panel, -1, "Image Destination:")

        #Also create special text for showing and hiding recovery info and terminal output.
        self.detailed_info_text = wx.lib.stattext.GenStaticText(self.panel, -1, "Detailed Info")
        self.terminal_output_text = wx.lib.stattext.GenStaticText(self.panel, -1, "Terminal Output")

        #And some text for basic recovery information.
        self.time_elapsed_text = wx.StaticText(self.panel, -1, "Time Elapsed:")
        self.time_remaining_text = wx.StaticText(self.panel, -1, "Estimated Time Remaining:")

    def create_buttons(self):
        """
        Create all buttons for MainWindow
        """
        self.settings_button = wx.Button(self.panel, -1, "Settings")
        self.update_disk_info_button = wx.Button(self.panel, -1, "Update Disk Info")
        self.show_disk_info_button = wx.Button(self.panel, -1, "Disk Information")
        self.control_button = wx.Button(self.panel, -1, "Start")

    def create_choice_boxes(self):
        """
        Create all choiceboxes for MainWindow
        """
        self.input_choice_box = wx.Choice(self.panel, -1, choices=['-- Please Select --',
                                                                   'Specify Path/File',
                                                                   'Enter Custom Path'])

        self.map_choice_box = wx.Choice(self.panel, -1, choices=['-- Please Select --',
                                                                 'Specify Path/File',
                                                                 'Enter Custom Path',
                                                                 'None (not recommended)'])

        if not LINUX:
            self.map_choice_box.SetToolTip(wx.ToolTip("Please ignore the macOS overwrite prompt "
                                                      + "given here when restarting a recovery - "
                                                      + "the file will not be overwritten"))

        self.output_choice_box = wx.Choice(self.panel, -1, choices=['-- Please Select --',
                                                                    'Specify Path/File',
                                                                    'Enter Custom Path'])

        if not LINUX:
            self.output_choice_box.SetToolTip(wx.ToolTip("Please ignore the macOS overwrite "
                                                         "prompt given here when restarting a "
                                                         "recovery - the file will not be "
                                                         "overwritten"))

        #Set the default value.
        self.input_choice_box.SetStringSelection("-- Please Select --")
        self.map_choice_box.SetStringSelection("-- Please Select --")
        self.output_choice_box.SetStringSelection("-- Please Select --")

    def create_other_widgets(self):
        """
        Create all other widgets for MainWindow
        """
        #Create the animation for the throbber.
        throb = wxAnimation(RESOURCEPATH+"/images/Throbber.gif")
        self.throbber = wxAnimationCtrl(self.panel, -1, throb)
        self.throbber.SetInactiveBitmap(wx.Bitmap(RESOURCEPATH+"/images/ThrobberRest.png",
                                                  wx.BITMAP_TYPE_PNG))

        self.throbber.SetClientSize(wx.Size(30, 30))

        #Create the list control for the detailed info.
        self.list_ctrl = wx.ListCtrl(self.panel, -1,
                                     style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_VRULES)

        self.list_ctrl.InsertColumn(0, heading="Category", format=wx.LIST_FORMAT_CENTRE,
                                    width=150)

        self.list_ctrl.InsertColumn(1, heading="Value", format=wx.LIST_FORMAT_CENTRE,
                                    width=-1)

        self.list_ctrl.SetMinSize(wx.Size(50, 240))

        #Create a text control for terminal output.
        self.output_box = CustomTextCtrl(self.panel, -1, "",
                                         style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP)

        self.output_box.SetBackgroundColour((0, 0, 0))
        self.output_box.SetDefaultStyle(wx.TextAttr(wx.WHITE))
        self.output_box.SetMinSize(wx.Size(50, 240))

        #Create the arrows.
        img1 = wx.Image(RESOURCEPATH+"/images/ArrowDown.png", wx.BITMAP_TYPE_PNG)
        img2 = wx.Image(RESOURCEPATH+"/images/ArrowRight.png", wx.BITMAP_TYPE_PNG)

        if CLASSIC_WXPYTHON:
            self.down_arrow_image = wx.BitmapFromImage(img1)
            self.right_arrow_image = wx.BitmapFromImage(img2)

        else:
            self.down_arrow_image = wx.Bitmap(img1)
            self.right_arrow_image = wx.Bitmap(img2)

        self.arrow1 = wx.lib.statbmp.GenStaticBitmap(self.panel, -1, self.down_arrow_image)
        self.arrow2 = wx.lib.statbmp.GenStaticBitmap(self.panel, -1, self.down_arrow_image)

        #Create the progress bar.
        self.progress_bar = wx.Gauge(self.panel, -1, 5000)

    def setup_sizers(self): #pylint: disable=too-many-statements
        """
        Setup sizers for MainWindow
        """
        #Make the main boxsizer.
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        #Make the file choices sizer.
        file_choices_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Make the input sizer.
        input_sizer = wx.BoxSizer(wx.VERTICAL)

        #Add items to the input sizer.
        input_sizer.Add(self.input_text, 1, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)
        input_sizer.Add(self.input_choice_box, 1, wx.BOTTOM|wx.ALIGN_CENTER, 10)

        #Make the log sizer.
        map_sizer = wx.BoxSizer(wx.VERTICAL)

        #Add items to the log sizer.
        map_sizer.Add(self.map_text, 1, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)
        map_sizer.Add(self.map_choice_box, 1, wx.BOTTOM|wx.ALIGN_CENTER, 10)

        #Make the output sizer.
        output_sizer = wx.BoxSizer(wx.VERTICAL)

        #Add items to the output sizer.
        output_sizer.Add(self.output_text, 1, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 10)
        output_sizer.Add(self.output_choice_box, 1, wx.BOTTOM|wx.ALIGN_CENTER, 10)

        #Add items to the file choices sizer.
        file_choices_sizer.Add(input_sizer, 1, wx.ALIGN_CENTER)
        file_choices_sizer.Add(map_sizer, 1, wx.ALIGN_CENTER)
        file_choices_sizer.Add(output_sizer, 1, wx.ALIGN_CENTER)

        #Make the button sizer.
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the button sizer.
        button_sizer.Add(self.settings_button, 1, wx.RIGHT|wx.ALIGN_CENTER|wx.EXPAND, 10)
        button_sizer.Add(self.update_disk_info_button, 1, wx.ALIGN_CENTER|wx.EXPAND, 10)
        button_sizer.Add(self.show_disk_info_button, 1, wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 10)

        #Make the throbber sizer.
        throbber_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the throbber sizer.
        throbber_sizer.Add(self.arrow1, 0, wx.LEFT|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        throbber_sizer.Add(self.detailed_info_text, 1,
                           wx.LEFT|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 10)

        throbber_sizer.Add(self.throbber, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER
                           |wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE, 10)

        throbber_sizer.Add(self.arrow2, 0, wx.RIGHT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 10)
        throbber_sizer.Add(self.terminal_output_text, 1,
                           wx.RIGHT|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 10)

        #Make the info sizer.
        self.info_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the info sizer.
        self.info_sizer.Add(self.list_ctrl, 1, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 22)
        self.info_sizer.Add(self.output_box, 1, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 22)

        #Make the info text sizer.
        info_text_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the info text sizer.
        info_text_sizer.Add(self.time_elapsed_text, 1, wx.RIGHT|wx.ALIGN_CENTER, 22)
        info_text_sizer.Add(self.time_remaining_text, 1, wx.LEFT|wx.ALIGN_CENTER, 22)

        #arrow1 is horizontal when starting, so hide self.list_ctrl.
        self.info_sizer.Detach(self.list_ctrl)
        self.list_ctrl.Hide()

        #arrow2 is horizontal when starting, so hide self.output_box.
        self.info_sizer.Detach(self.output_box)
        self.output_box.Hide()

        #Insert some empty space. (Fixes a GUI bug in classic wxPython).
        if CLASSIC_WXPYTHON:
            self.info_sizer.Add((1, 1), 1, wx.EXPAND)

        #Make the progress sizer.
        self.progress_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the progress sizer.
        self.progress_sizer.Add(self.progress_bar, 1, wx.ALL|wx.ALIGN_CENTER, 10)
        self.progress_sizer.Add(self.control_button, 0, wx.ALL|wx.ALIGN_RIGHT, 10)

        #Add items to the main sizer.
        self.main_sizer.Add(self.title_text, 0, wx.TOP|wx.ALIGN_CENTER, 10)
        self.main_sizer.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 10)
        self.main_sizer.Add(file_choices_sizer, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 10)
        self.main_sizer.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 10)
        self.main_sizer.Add(button_sizer, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 10)
        self.main_sizer.Add(wx.StaticLine(self.panel), 0, wx.TOP|wx.EXPAND, 10)
        self.main_sizer.Add(throbber_sizer, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 5)
        self.main_sizer.Add(self.info_sizer, 1, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER|wx.EXPAND, 10)
        self.main_sizer.Add(info_text_sizer, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 10)
        self.main_sizer.Add(self.progress_sizer, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER|wx.EXPAND, 10)

        #Get the sizer set up for the frame.
        self.panel.SetSizer(self.main_sizer)
        self.main_sizer.SetMinSize(wx.Size(1056, 360))
        self.main_sizer.SetSizeHints(self)

    def create_menus(self):
        """
        Create the menus
        """
        file_menu = wx.Menu()
        edit_menu = wx.Menu()
        view_menu = wx.Menu()
        help_menu = wx.Menu()

        #Add Menu Items.
        self.menu_exit = file_menu.Append(wx.ID_EXIT, "&Quit", "Close DDRescue-GUI")

        self.menu_settings = edit_menu.Append(wx.ID_ANY, "&Settings", "Recovery Settings")
        self.menu_mount = edit_menu.Append(wx.ID_ANY, "&Mount Disk", "Mount a file/device")
        self.menu_disk_info = view_menu.Append(wx.ID_ANY, "&Disk Information",
                                               "Information about all detected Disks")

        self.menu_privacy_policy = view_menu.Append(wx.ID_ANY, "&Privacy Policy",
                                                    "View DDRescue-GUI's privacy policy")

        self.menu_docs = help_menu.Append(wx.ID_ANY, "&User Guide",
                                          "View DDRescue-GUI's User Guide")

        self.menu_updates = help_menu.Append(wx.ID_ANY, "&Check for Updates",
                                             "Check for updates to DDRescue-GUI")

        self.menu_about = help_menu.Append(wx.ID_ABOUT, "&About DDRescue-GUI",
                                           "Information about DDRescue-GUI")

        #Creating the menubar.
        self.menu_bar = wx.MenuBar()

        #Adding menus to the menu_bar.
        self.menu_bar.Append(file_menu, "&File")
        self.menu_bar.Append(edit_menu, "&Edit")
        self.menu_bar.Append(view_menu, "&View")
        self.menu_bar.Append(help_menu, "&Help")

        #Adding the menu_bar to the Frame content.
        self.SetMenuBar(self.menu_bar)

    def bind_events(self):
        """
        Bind all events for MainWindow
        """
        #Menus.
        self.Bind(wx.EVT_MENU, self.check_for_updates, self.menu_updates)
        self.Bind(wx.EVT_MENU, self.show_settings, self.menu_settings)
        self.Bind(wx.EVT_MENU, self.on_mount, self.menu_mount)
        self.Bind(wx.EVT_MENU, self.show_userguide, self.menu_docs)
        self.Bind(wx.EVT_MENU, self.on_about, self.menu_about)
        self.Bind(wx.EVT_MENU, self.show_dev_info, self.menu_disk_info)
        self.Bind(wx.EVT_MENU, self.show_privacy_policy, self.menu_privacy_policy)

        #Choiceboxes.
        self.Bind(wx.EVT_CHOICE, self.set_input_file, self.input_choice_box)
        self.Bind(wx.EVT_CHOICE, self.set_output_file, self.output_choice_box)
        self.Bind(wx.EVT_CHOICE, self.set_map_file, self.map_choice_box)

        #Buttons.
        self.Bind(wx.EVT_BUTTON, self.on_control_button, self.control_button)
        self.Bind(wx.EVT_BUTTON, self.get_diskinfo, self.update_disk_info_button)
        self.Bind(wx.EVT_BUTTON, self.show_settings, self.settings_button)
        self.Bind(wx.EVT_BUTTON, self.show_dev_info, self.show_disk_info_button)

        #text.
        self.detailed_info_text.Bind(wx.EVT_LEFT_DOWN, self.on_detailed_info)
        self.terminal_output_text.Bind(wx.EVT_LEFT_DOWN, self.on_terminal_output)

        #Prevent focus on Output Box.
        self.output_box.Bind(wx.EVT_SET_FOCUS, self.focus_on_control_button)

        #Images.
        self.arrow1.Bind(wx.EVT_LEFT_DOWN, self.on_detailed_info)
        self.arrow2.Bind(wx.EVT_LEFT_DOWN, self.on_terminal_output)

        #Size events.
        self.Bind(wx.EVT_SIZE, self.on_size)

        #on_exit events.
        self.Bind(wx.EVT_QUERY_END_SESSION, self.on_session_end)
        self.Bind(wx.EVT_MENU, self.on_exit, self.menu_exit)
        self.Bind(wx.EVT_CLOSE, self.on_exit)

    def focus_on_control_button(self, event=None): #pylint: disable=unused-argument
        """
        Focus on the control button instead of the TextCtrl, and reset the insertion point back
        after 30 milliseconds, preventing the user from changing the insertion point and messing
        the formatting up.
        """

        #Just a slightly hacky way of trying to make sure the user can't change the insertion
        #point! Works unless you start doing silly stuff like tapping on the output box
        #constantly :)
        self.control_button.SetFocus()
        insertion_point = self.output_box.GetInsertionPoint()
        wx.CallLater(30, self.output_box.SetInsertionPoint, insertion_point)

    def on_size(self, event=None):
        """
        Auto resize the list_ctrl columns when the window is resized.
        """

        #Force the width and height of the list_ctrl to be the right size,
        #as the sizer won't shrink it on wxpython > 2.8.12.1.
        #NB: Not needed on wxPython 4:
        if not CLASSIC_WXPYTHON:
            if event is not None:
                event.Skip()
        #Get the width and height of the frame.
        width = self.GetClientSize()[0]

        #Calculate the correct width for the list_ctrl.
        if self.output_box.IsShown():
            list_ctrl_width = (width - 88)//2

        else:
            list_ctrl_width = (width - 44)

        #Set the size.
        self.list_ctrl.SetColumnWidth(1, list_ctrl_width - 150)
        self.list_ctrl.SetClientSize(wx.Size(list_ctrl_width, 240))

        if event is not None:
            event.Skip()

    def on_detailed_info(self, event=None): #pylint: disable=unused-argument
        """
        Show/Hide the detailed info, and rotate the arrow next to the text label.
        """
        #Get the width and height of the frame.
        width = self.GetClientSize()[0]

        if self.list_ctrl.IsShown() or self.starting_up:
            self.arrow1.SetBitmap(self.right_arrow_image)

            #arrow1 is now horizontal, so hide self.list_ctrl.
            self.info_sizer.Detach(self.list_ctrl)
            self.list_ctrl.Hide()

            if self.output_box.IsShown() is False:
                self.SetClientSize(wx.Size(width, 360))

                #Insert some empty space.
                self.info_sizer.Add((1, 1), 1, wx.EXPAND)

        else:
            self.arrow1.SetBitmap(self.down_arrow_image)

            #arrow1 is now vertical, so show self.ListCtrl2
            if self.output_box.IsShown() is False:

                #Remove the empty space.
                self.info_sizer.Clear()

            self.info_sizer.Insert(0, self.list_ctrl, 1,
                                   wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 22)

            self.list_ctrl.Show()
            self.SetClientSize(wx.Size(width, 600))

        #Call Layout() on self.panel() and self.on_size() to ensure it displays properly.
        self.on_size()
        self.panel.Layout()
        self.main_sizer.SetSizeHints(self)

    def on_terminal_output(self, event=None): #pylint: disable=unused-argument
        """
        Show/Hide the terminal output, and rotate the arrow next to the text
        label.
        """
        #Get the width and height of the frame.
        width = self.GetClientSize()[0]

        if self.output_box.IsShown() or self.starting_up:
            self.arrow2.SetBitmap(self.right_arrow_image)

            #arrow2 is now horizontal, so hide self.output_box.
            self.info_sizer.Detach(self.output_box)
            self.output_box.Hide()

            if self.list_ctrl.IsShown() is False:
                self.SetClientSize(wx.Size(width, 360))
                #Insert some empty space.
                self.info_sizer.Add((1, 1), 1, wx.EXPAND)

        else:
            self.arrow2.SetBitmap(self.down_arrow_image)

            #arrow2 is now vertical, so show self.output_box.
            if self.list_ctrl.IsShown():
                self.info_sizer.Insert(1, self.output_box, 1,
                                       wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 22)

            else:
                #Remove the empty space.
                self.info_sizer.Clear()
                self.info_sizer.Insert(0, self.output_box, 1,
                                       wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 22)

            self.output_box.Show()
            self.SetClientSize(wx.Size(width, 600))

        #Call Layout() on self.panel() and self.on_size to ensure it displays properly.
        self.on_size()
        self.panel.Layout()
        self.main_sizer.SetSizeHints(self)

    def get_diskinfo(self, event=None): #pylint: disable=unused-argument
        """
        Call the thread to get Disk info, disable the update button,
        and start the throbber
        """

        logger.info("MainWindow().get_diskinfo(): Getting new Disk information...")
        self.update_status_bar("Getting new Disk information... Please wait...")

        #Disable stuff to prevent problems.
        self.settings_button.Disable()
        self.update_disk_info_button.Disable()
        self.show_disk_info_button.Disable()
        self.input_choice_box.Disable()
        self.output_choice_box.Disable()
        self.menu_disk_info.Enable(False)
        self.menu_settings.Enable(False)
        self.menu_mount.Enable(False)

        #Call the thread and get the throbber going.
        GetDiskInformation(self)
        self.throbber.Play()

    def receive_diskinfo(self, info):
        """
        Get new Disk info, stop the throbber and call the function that updates
        the choiceboxes for input and output file selection.
        """
        logger.info("MainWindow().receive_diskinfo(): Getting new Disk information...")
        global DISKINFO
        DISKINFO.clear()
        DISKINFO.update(info)

        #Update the file choices.
        self.update_file_choices()
        self.starting_up = False

        #Stop the throbber and enable stuff again.
        self.throbber.Stop()

        self.settings_button.Enable()
        self.update_disk_info_button.Enable()
        self.show_disk_info_button.Enable()
        self.input_choice_box.Enable()
        self.output_choice_box.Enable()
        self.menu_disk_info.Enable()
        self.menu_settings.Enable()
        self.menu_mount.Enable()

        #Fix a display on on Fedora/GNOME3 w/ py3.
        self.panel.Layout()

    def update_file_choices(self):
        """
        Update the disk entries in the choiceboxes
        """

        logger.info("MainWindow().update_file_choices(): Updating the GUI with the "
                    "new Disk information...")

        #Keep the user's current selections and any custom paths added to the choiceboxes
        #while we update them.
        logger.info("MainWindow().update_file_choices(): Updating choiceboxes...")

        #Grab Current selection.
        current_input_string_selection = self.input_choice_box.GetStringSelection()
        current_output_string_selection = self.output_choice_box.GetStringSelection()

        #Set all the items.
        self.input_choice_box.SetItems(['-- Please Select --', 'Specify Path/File',
                                        'Enter Custom Path']
                                       + sorted(list(DISKINFO) + list(self.custom_input_paths)))

        self.output_choice_box.SetItems(['-- Please Select --', 'Specify Path/File',
                                         'Enter Custom Path']
                                        + sorted(list(DISKINFO)
                                                 + list(self.custom_output_paths)))

        #Set the current selections again, if we can
        #(if the selection is a Disk, it may have been removed).
        if self.input_choice_box.FindString(current_input_string_selection) != -1:
            self.input_choice_box.SetStringSelection(current_input_string_selection)

        else:
            self.input_choice_box.SetStringSelection('-- Please Select --')

        if self.output_choice_box.FindString(current_output_string_selection) != -1:
            self.output_choice_box.SetStringSelection(current_output_string_selection)

        else:
            self.output_choice_box.SetStringSelection('-- Please Select --')

        #Notify the user with the statusbar.
        self.update_status_bar("Ready.")

    def file_choice_handler(self, _type, user_selection, default_dir, wildcard, style):
        """
        Handle file dialogs for set_input_file, set_output_file, and set_map_file.

        Args:
            _type (string).         The type of file we're handling. "Input",
                                    "Output", or "Map".

            user_selection (string):        The option the user selected in the
                                            choice box.

            default_dir (string):           The default directory any file dialogs
                                            are to use.

            wildcard (string):              The wildcard that any file dialogs
                                            are to use.

            style (int):                    The style that any file dialogs are
                                            to use.

        """

        #pylint: disable=too-many-arguments
        #TODO Refactor, too long.
        #Setup.
        key = _type+"File"

        if _type == "Input":
            choice_box = self.input_choice_box
            paths = self.custom_input_paths
            others = ["OutputFile", "MapFile"]

        elif _type == "Output":
            choice_box = self.output_choice_box
            paths = self.custom_output_paths
            others = ["InputFile", "MapFile"]

        else:
            choice_box = self.map_choice_box
            paths = self.custom_map_paths
            others = ["InputFile", "OutputFile"]

        SETTINGS[key] = user_selection

        if user_selection == "-- Please Select --":
            logger.info("MainWindow().file_choice_handler(): "+_type+" file reset..")
            SETTINGS[key] = None

            #Return to prevent TypeErrors later.
            return

        #Handle having no map file.
        elif user_selection == "None (not recommended)":
            dialog = wx.MessageDialog(self.panel, "You have not chosen to use a map file. "
                                      "If you do not use one, you will have to start from "
                                      "scratch in the event of a power outage, or if "
                                      "DDRescue-GUI is interrupted. Additionally, you "
                                      "can't do a multi-stage recovery without a map file.\n\n"
                                      "Are you really sure you do not want to use a mapfile?",
                                      "DDRescue-GUI - Warning", wx.YES_NO | wx.ICON_EXCLAMATION)

            if dialog.ShowModal() == wx.ID_YES:
                logger.warning("MainWindow().file_choice_handler(): User isn't using a map file, "
                               "despite our warning!")

                SETTINGS[key] = ""

            else:
                logger.info("MainWindow().file_choice_handler(): User decided against not using "
                            "a map file. Good!")

                SETTINGS[key] = None
                choice_box.SetStringSelection("-- Please Select --")

            dialog.Destroy()

        elif user_selection == "Specify Path/File":
            file_dialog = wx.FileDialog(self.panel, "Select "+_type+" Path/File...",
                                        defaultDir=default_dir, wildcard=wildcard, style=style)

            #Gracefully handle it if the user closed the dialog without selecting a file.
            if file_dialog.ShowModal() != wx.ID_OK:
                logger.info("MainWindow().file_choice_handler(): User declined custom file "
                            "selection. Resetting choice box for "+key+"...")

                choice_box.SetStringSelection("-- Please Select --")
                SETTINGS[key] = None
                return

            #Get the file.
            user_selection = file_dialog.GetPath()

            #Handle it according to cases depending on its _type.
            if _type in ["Output", "Map"]:
                if _type == "Output":
                    #Automatically add a file extension of .img if there isn't any (3-letter)
                    #file extension (fixes bugs on OS X).
                    if "/dev" not in user_selection and user_selection[-4] != ".":
                        user_selection += ".img"

                else:
                    #Automatically add a file extension of .log for map files if extension is wrong
                    #or missing.
                    if user_selection[-4:] != ".log":
                        user_selection += ".log"

                #Don't allow user to save output or map files in root's home dir on Pmagic.
                if PARTED_MAGIC and user_selection[0:5] == "/root":
                    logger.warning("MainWindow().file_choice_handler(): "+_type+" File is in "
                                   "root's home directory on Parted Magic! There is no space "
                                   "here, warning user and declining selection...")

                    dlg = wx.MessageDialog(self.panel, "You can't save the "+_type+" file in "
                                           "root's home directory in Parted Magic! There's "
                                           "not enough space there, please select a new folder. "
                                           "Note: / is cleared on shutdown on parted magic, "
                                           "as pmagic is a live disk, so you probably want "
                                           "to store the file on a different disk drive.",
                                           'DDRescue-GUI - Error!', wx.OK | wx.ICON_ERROR)

                    dlg.ShowModal()
                    dlg.Destroy()
                    choice_box.SetStringSelection("-- Please Select --")
                    SETTINGS[key] = None
                    return

            logger.info("MainWindow().file_choice_handler(): User selected custom file: "
                        +user_selection+"...")

            SETTINGS[key] = user_selection

            #Handle custom paths properly.
            #If it's in the dictionary or in DISKINFO, don't add it.
            if user_selection in paths.values():
                #Set the selection using the unique key in the paths dictionary.
                unique_key = None

                for _key in paths:
                    if paths[_key] == user_selection:
                        unique_key = _key
                        break

                choice_box.SetStringSelection(unique_key)

            elif user_selection in list(DISKINFO):
                #No need to add it to the choice box.
                choice_box.SetStringSelection(user_selection)

            else:
                #Get a unique key for the dictionary using the tools function.
                unique_key = CoreTools.create_unique_key(paths, user_selection, 30)

                #Use it to organise the data.
                paths[unique_key] = user_selection
                choice_box.Append(unique_key)
                choice_box.SetStringSelection(unique_key)

        elif user_selection == "Enter Custom Path":
            te_dialog = wx.TextEntryDialog(self.panel, "Enter a custom path.")

            #Gracefully handle it if the user closed the dialog without selecting a file.
            if te_dialog.ShowModal() != wx.ID_OK:
                logger.info("MainWindow().file_choice_handler(): User declined custom text "
                            "entry. Resetting choice box for "+key+"...")

                choice_box.SetStringSelection("-- Please Select --")
                SETTINGS[key] = None
                return

            #Get the path.
            user_selection = te_dialog.GetValue()

            #Handle it according to cases depending on its _type.
            if _type in ["Output", "Map"]:
                if _type == "Output":
                    #Automatically add a file extension of .img if there isn't any (3-letter)
                    #file extension (fixes bugs on OS X).
                    if "/dev" not in user_selection and user_selection[-4] != ".":
                        user_selection += ".img"

                else:
                    #Automatically add a file extension of .log for map files if extension is wrong
                    #or missing.
                    if user_selection[-4:] != ".log":
                        user_selection += ".log"

                #Don't allow user to save output or map files in root's home dir on Pmagic.
                if PARTED_MAGIC and user_selection[0:5] == "/root":
                    logger.warning("MainWindow().file_choice_handler(): "+_type+" File is in "
                                   "root's home directory on Parted Magic! There is no space "
                                   "here, warning user and declining selection...")

                    dlg = wx.MessageDialog(self.panel, "You can't save the "+_type+" file in "
                                           "root's home directory in Parted Magic! There's "
                                           "not enough space there, please select a new folder. "
                                           "Note: / is cleared on shutdown on parted magic, "
                                           "as pmagic is a live disk, so you probably want "
                                           "to store the file on a different disk drive.",
                                           'DDRescue-GUI - Error!', wx.OK | wx.ICON_ERROR)

                    dlg.ShowModal()
                    dlg.Destroy()
                    choice_box.SetStringSelection("-- Please Select --")
                    SETTINGS[key] = None
                    return

            logger.info("MainWindow().file_choice_handler(): User selected custom file: "
                        +user_selection+"...")

            SETTINGS[key] = user_selection

            #Handle custom paths properly.
            #If it's in the dictionary or in DISKINFO, don't add it.
            if user_selection in paths.values():
                #Set the selection using the unique key in the paths dictionary.
                unique_key = None

                for _key in paths:
                    if paths[_key] == user_selection:
                        unique_key = _key
                        break

                choice_box.SetStringSelection(unique_key)

            elif user_selection in list(DISKINFO):
                #No need to add it to the choice box.
                choice_box.SetStringSelection(user_selection)

            else:
                #Get a unique key for the dictionary using the tools function.
                unique_key = CoreTools.create_unique_key(paths, user_selection, 30)

                #Use it to organise the data.
                paths[unique_key] = user_selection
                choice_box.Append(unique_key)
                choice_box.SetStringSelection(unique_key)

        if (user_selection not in [None, "-- Please Select --"] and user_selection in \
           [SETTINGS[others[0]], SETTINGS[others[1]]]):

            #Has same value as one of the other main settings! Declining user suggestion.
            logger.warning("MainWindow().file_choice_handler(): Current setting has the same "
                           "value as one of the other main settings! Resetting and warning "
                           "user...")

            dlg = wx.MessageDialog(self.panel, "Your selection is the same as one of the other "
                                   "file selection choiceboxes!", 'DDRescue-GUI - Error!',
                                   wx.OK | wx.ICON_ERROR)

            dlg.ShowModal()
            dlg.Destroy()
            choice_box.SetStringSelection("-- Please Select --")
            SETTINGS[key] = None

        if user_selection[0:3] == "...":
            #Get the full path name to set the inputfile to.
            SETTINGS[key] = paths[user_selection]

        #Handle special cases if the file is the output file.
        if _type == "Output" and SETTINGS[key] is not None:
            #Check with the user if the output file already exists.
            if os.path.exists(SETTINGS[key]):
                logger.info("MainWindow().file_choice_handler(): Selected file already exists! "
                            "Showing warning to user...")

                dialog = wx.MessageDialog(self.panel, "The file you selected already exists!\n\n"
                                          "If you're doing a multi-stage recovery, *and you've "
                                          "selected a mapfile*, DDRescue-GUI will resume where "
                                          "it left off on the previous run, and it is safe to "
                                          "continue.\n\nOtherwise, you will lose data on this "
                                          "file or device.\n\nPlease be sure you selected the "
                                          "right file or device. Do you want to accept this as "
                                          "your output file?", 'DDRescue-GUI -- Warning!',
                                          wx.YES_NO | wx.ICON_EXCLAMATION)

                if dialog.ShowModal() == wx.ID_YES:
                    logger.warning("MainWindow().file_choice_handler(): Accepted already-present "
                                   "file as output file!")

                else:
                    logger.info("MainWindow().file_choice_handler(): User declined the selection. "
                                "Resetting OutputFile...")

                    SETTINGS[key] = None
                    choice_box.SetStringSelection("-- Please Select --")

                    #Disable this too to prevent accidental enabling if previous selection
                    #was a device.
                    SETTINGS["OverwriteOutputFile"] = ""

                    #Call Layout() on self.panel() to ensure it displays properly.
                    self.panel.Layout()

                    return

                dialog.Destroy()

            #If the file selected is a Disk, enable the overwrite output file option,
            #else disable it.
            if SETTINGS[key][0:5] == "/dev/":
                logger.info("MainWindow().file_choice_handler(): OutputFile is a disk so enabling "
                            "ddrescue's overwrite mode...")

                SETTINGS["OverwriteOutputFile"] = "-f"

            else:
                logger.info("MainWindow().file_choice_handler(): OutputFile isn't a disk so "
                            "disabling ddrescue's overwrite mode...")

                SETTINGS["OverwriteOutputFile"] = ""

        #Call Layout() on self.panel() to ensure it displays properly.
        self.panel.Layout()

    def set_input_file(self, event=None): #pylint: disable=unused-argument
        """
        Get the input file/Disk by calling self.file_choice_handler.
        """
        logger.debug("MainWindow().SelectInputFile(): Calling File Choice Handler...")
        default_dir = "/dev"

        self.file_choice_handler(_type="Input",
                                 user_selection=self.input_choice_box.GetStringSelection(),
                                 default_dir=default_dir, wildcard=self.input_wildcard,
                                 style=wx.FD_OPEN)

    def set_output_file(self, event=None): #pylint: disable=unused-argument
        """
        Get the output file/Disk by calling self.file_choice_handler.
        """
        logger.debug("MainWindow().SelectInputFile(): Calling File Choice Handler...")

        self.file_choice_handler(_type="Output",
                                 user_selection=self.output_choice_box.GetStringSelection(),
                                 default_dir=self.user_homedir, wildcard=self.output_wildcard,
                                 style=wx.FD_SAVE)

    def set_map_file(self, event=None): #pylint: disable=unused-argument
        """
        Get the map file position/name by calling self.file_choice_handler.
        """

        logger.debug("MainWindow().SelectMapFile(): Calling File Choice Handler...")
        self.file_choice_handler(_type="Map",
                                 user_selection=self.map_choice_box.GetStringSelection(),
                                 default_dir=self.user_homedir, wildcard="Map Files (*.log)|*.log",
                                 style=wx.FD_SAVE)

    def show_userguide(self, event=None): #pylint: disable=unused-argument,no-self-use
        """
        Open a web browser and show the user guide.
        """
        logger.debug("MainWindow().show_userguide(): Opening browser...")

        if LINUX:
            cmd = "xdg-open"

        else:
            cmd = "open"

        subprocess.Popen(cmd
                         + " https://www.hamishmb.com/html/Docs/ddrescue-gui.php",
                         shell=True)

    def on_about(self, event=None): #pylint: disable=unused-argument, no-self-use
        """
        Show the about box.
        """

        logger.debug("MainWindow().on_about(): Showing about box...")
        aboutbox = wxAboutDialogInfo()
        aboutbox.SetIcon(APPICON)
        aboutbox.Name = "DDRescue-GUI"
        aboutbox.Version = VERSION
        aboutbox.Copyright = "(C) 2013-2020 Hamish McIntyre-Bhatty"
        aboutbox.Description = "GUI frontend for GNU ddrescue\n\nPython version " \
                               + sys.version.split()[0] \
                               + "\nwxPython version " + wx.version() \
                               + "\nGNU ddrescue version " + SETTINGS["DDRescueVersion"] \
                               + "\nGetDevInfo version " + getdevinfo.getdevinfo.VERSION

        aboutbox.WebSite = ("http://www.hamishmb.com", "My Website")
        aboutbox.Developers = ["Hamish McIntyre-Bhatty", "Minnie McIntyre-Bhatty (GUI Design)"]
        aboutbox.Artists = ["Bhuna https://www.instagram.com/bhuna42/",
                            "Holly McIntyre-Bhatty (Old Artwork)",
                            "Hamish McIntyre-Bhatty (Throbber designs)"]

        aboutbox.License = "DDRescue-GUI is free software: you can redistribute it and/or " \
                           "modify it\nunder the terms of the GNU General Public License " \
                           "version 3 or, \nat your option, any later version.\n\nDDRescue-GUI " \
                           "is distributed in the hope that it will be useful,\nbut WITHOUT " \
                           "ANY WARRANTY; without even the implied warranty of\n" \
                           "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  " \
                           "See the\nGNU General Public License for more details. \n\nYou " \
                           "should have received a copy of the GNU General Public License\n" \
                           "along with DDRescue-GUI.  If not, see <http://www.gnu.org/licenses/>" \
                           ".\n\nGNU ddrescue is released under the GPLv2, may be\n" \
                           "redistributed in accordance with the terms of the GPLv2 or newer," \
                           "and is \nbundled with the macOS version of DDRescue-GUI.\n\n" \
                           "Terminal-notifier is released under the MIT license (compatible " \
                           "with the GPL),\nmay be redistributed with GPL software, and is also\n" \
                           "bundled with the macOS version of DDRescue-GUI.\n\n" \
                           "Python and wxPython are also bundled with the macOS version of\n" \
                           "DDRescue-GUI.\n\n" \
                           "Please note: I am NOT\nthe author of GNU ddrescue," \
                           "terminal-notifier, Python, or wxPython.\n\nFor more " \
                           "information on GNU ddrescue, and\nfor the source code, visit\n" \
                           "http://www.gnu.org/software/ddrescue/ddrescue.html\n\nFor more " \
                           "information on terminal-notifier, and\nfor the source code, visit\n" \
                           "https://github.com/julienXX/terminal-notifier.\n\nFor more " \
                           "information on wxPython, and for the source code,\n visit " \
                           "https://wxpython.org\n\nFor more information on Python,\nand for" \
                           "the source code, visit https://www.python.org"

        #Show the about box
        wxAboutBox(aboutbox)

    def show_settings(self, event=None): #pylint: disable=unused-argument
        """
        Show the settings Window, but only if input and output files have already been selected.
        """

        #If input and output files are set (do not equal None) then continue.
        if None not in [SETTINGS["InputFile"], SETTINGS["OutputFile"]]:
            SettingsWindow(self).Show()

        else:
            dlg = wx.MessageDialog(self.panel, 'Please select input and output files first!',
                                   'DDRescue-GUI - Error!', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def show_dev_info(self, event=None): #pylint: disable=unused-argument
        """
        Show the Disk Information Window.
        """
        DiskInfoWindow(self).Show()

    def show_privacy_policy(self, event=None): #pylint: disable=unused-argument
        """
        Show the Privacy Policy Window
        """
        PrivPolWindow(self).Show()

    def check_for_updates(self, event=None, starting_up=False): #pylint: disable=unused-argument
        """
        Check for updates using the plist-formatted update file
        on my website. If some startup, only display info to the
        user if there was an update. Otherwise (aka requested by user),
        always display the information.

        Kwargs:
            starting_up[=True] (boolean).   If the GUI is starting up, specify
                                            True, otherwise leave unspecified.
        """
        logger.info("MainWindow().check_for_updates(): Checking for updates...")

        CoreTools.send_notification("Checking for updates...")

        try:
            updateinfo = \
            requests.get("https://www.hamishmb.com/files/updateinfo/ddrescue-gui.plist",
                         timeout=5)

            #Raise an error if our status code was bad.
            updateinfo.raise_for_status()

            updateinfo = updateinfo.text

        except requests.exceptions.RequestException:
            #Flag to user.
            CoreTools.send_notification("Failed to check for updates!")

            #Also send a message dialog.
            if not starting_up:
                wx.MessageDialog(self.panel, "Couldn't check for updates!\n"
                                 + "Are you connected to the internet?",
                                 "DDRescue-GUI - Update Check Failure",
                                 wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP,
                                 pos=wx.DefaultPosition).ShowModal()
            return

        #Process the update info.
        infotext = ""
        update_recommended = False

        updateinfo = plistlib.readPlistFromString(updateinfo.encode())

        #Determine the latest version for our kind of release.
        if RELEASE_TYPE == "Stable":
            #Compare your stable version to the current stable version.
            versions = [VERSION, updateinfo["CurrentStableVersion"]]

        elif RELEASE_TYPE == "Development":
            #Compare your version to both dev and stable versions.
            #This is in case a stable release has superseeded your dev release.
            versions = [VERSION, updateinfo["CurrentStableVersion"],
                        updateinfo["CurrentDevVersion"]]

        #Order the list so the last entry has the latest version number.
        versions = sorted(versions, key=LooseVersion)

        #Compare the versions.
        if versions[-1] == VERSION and RELEASE_TYPE == "Stable":
            #We have the latest stable version.
            infotext += "You are running the latest version of DDRescue-GUI.\n"

        elif versions[-1] == VERSION and RELEASE_TYPE == "Development":
            #We have the latest dev version.
            infotext += "You are running the latest development version of DDRescue-GUI.\n"

        elif VERSION == updateinfo["CurrentStableVersion"] and RELEASE_TYPE == "Stable":
            #We are running the latest stable version, but there is a dev version
            #that is newer.
            infotext += "You are running the latest version of DDRescue-GUI.\n"

        elif VERSION == updateinfo["CurrentDevVersion"] and RELEASE_TYPE == "Development":
            #We are running a development version, but it has been superseeded by a
            #new stable release. We should update.
            update_recommended = True

            infotext += "You are running an old development version of DDRescue-GUI.\n"
            infotext += "You should update to the newer, stable version "
            infotext += updateinfo["CurrentStableVersion"]+".\n"

        elif RELEASE_TYPE == "Development":
            #We are running an old dev build. We should update.
            update_recommended = True

            infotext += "You are running an old development version of DDRescue-GUI.\n"
            infotext += "You could update to the latest stable version "
            infotext += updateinfo["CurrentStableVersion"]+",\n"
            infotext += "or the latest development version "+updateinfo["CurrentDevVersion"]+".\n"

        elif RELEASE_TYPE == "Stable":
            #We are running an old stable build. We should update.
            update_recommended = True

            infotext += "You are running an old stable version of DDRescue-GUI.\n"
            infotext += "You should update to the latest stable version "
            infotext += updateinfo["CurrentStableVersion"]+".\n"

        #Note if the release date doesn't match for the latest stable build.
        if (RELEASE_TYPE == "Stable" and VERSION == updateinfo["CurrentStableVersion"]
                and RELEASE_DATE != updateinfo["CurrentStableReleaseDate"]):

            infotext += "\nYour release date doesn't match that of the current stable version.\n"
            infotext += "Are you running a git build?"

        #Send a notification about the update status.
        if update_recommended:
            logger.warning("MainWindow().check_for_updates(): Update is recommended. "
                           "Sending notification...")

            CoreTools.send_notification("Updates are available")

            #Add info about where to download updates.
            infotext += "\nThe latest version of DDRescue-GUI can be downloaded from:\n"
            infotext += "https://www.hamishmb.com/html/downloads.php?program_name=ddrescue-gui\n"

            #Add info about new release.
            infotext += "\nDetails of the new release:\n\n"
            infotext += updateinfo["CurrentStableVersionDetails"]

            #Note for pmagic users.
            if PARTED_MAGIC:
                infotext += "\nThere is probably a newer version of Parted Magic that "
                infotext += "provides an update to this program."

        else:
            logger.warning("MainWindow().check_for_updates(): No update required."
                           "Sending notification...")

            CoreTools.send_notification("Up to date")

        #If asked by the user, or if there's an update and we aren't on pmagic,
        #show the update status.
        if not starting_up or (update_recommended and not PARTED_MAGIC):
            logger.debug("MainWindow().check_for_updates(): Showing the user the update info...")

            wx.MessageDialog(self.panel, infotext, "DDRescue-GUI - Update Status",
                             wx.OK | wx.ICON_INFORMATION | wx.STAY_ON_TOP,
                             pos=wx.DefaultPosition).ShowModal()

    def on_control_button(self, event=None): #pylint: disable=unused-argument
        """
        Handle events from the control button, as its purpose changes during and after recovery.
        Call self.on_abort() when clicked during a recovery.
        Call self.on_start() otherwise.
        """

        if SETTINGS["RecoveringData"]:
            self.on_abort()

        else:
            self.on_start()

    def on_mount(self, event=None): #pylint: disable=unused-argument
        """
        When the user asks to mount a file, handle this and show FinishedWindow in order to carry
        out the request.
        """
        #Ask the user for the file to mount.
        logger.info("MainWindow().on_mount(): Asking user for file/device to mount...")

        file_dialog = wx.FileDialog(self.panel, "Select Device/File...",
                                    defaultDir="/home", wildcard=self.input_wildcard,
                                    style=wx.FD_OPEN)

        #Gracefully handle it if the user closed the dialog without selecting a file.
        if file_dialog.ShowModal() != wx.ID_OK:
            logger.info("MainWindow().on_mount(): User cancelled the operation.")

            return

        #Get the file.
        SETTINGS["InputFile"] = SETTINGS["OutputFile"] = file_dialog.GetPath()

        logger.info("MainWindow().on_mount(): Got file "+SETTINGS["InputFile"]
                    + ". Opening FinishedWindow...")

        self.recovered_data = "0 Bytes"
        self.disk_capacity = "0 Bytes"

        FinishedWindow(self, self.disk_capacity, self.recovered_data).Show()

    def on_start(self): #pylint: disable=too-many-statements
        """
        Check the settings, prepare to start ddrescue, unmount the input file
        if needed, and start the backend thread.
        """
        logger.info("MainWindow().on_start(): Checking settings...")
        self.update_status_bar("Preparing to start ddrescue...")

        if SETTINGS["CheckedSettings"] is False:
            logger.error("MainWindow().on_start(): The settings haven't been checked properly! "
                         "Aborting recovery...")

            dlg = wx.MessageDialog(self.panel, "Please check the settings before starting the "
                                   "recovery.", "DDRescue-GUI - Warning",
                                   wx.OK | wx.ICON_EXCLAMATION)

            dlg.ShowModal()
            dlg.Destroy()
            self.update_status_bar("Ready.")

        elif None not in [SETTINGS["InputFile"], SETTINGS["MapFile"], SETTINGS["OutputFile"]]:
            #Attempt to unmount input/output Disks now, if needed.
            logger.info("MainWindow().on_start(): Unmounting input and output files if needed...")

            for disk in [SETTINGS["InputFile"], SETTINGS["OutputFile"]]:
                if disk not in DISKINFO:
                    #Assume this is a partition, or that it can be unmounted like one.
                    if CoreTools.is_mounted(disk):
                        #Unmount the disk.
                        logger.debug("MainWindow().on_start(): Unmounting "+disk+"...")

                        self.update_status_bar("Unmounting "+disk+". This may take a "
                                               "few moments...")

                        wx.GetApp().Yield()
                        retval = CoreTools.unmount_disk(disk)

                    logger.info("MainWindow().on_start(): "+disk+" is a file (or not in collected "
                                "disk info), ignoring it...")
                    continue

                if CoreTools.is_mounted(disk) or not CoreTools.is_partition(disk, DISKINFO):
                    #The Disk is mounted, or may have partitions that are mounted.
                    if CoreTools.is_partition(disk, DISKINFO):
                        #Unmount the disk.
                        logger.debug("MainWindow().on_start(): "+disk+" is a partition. "
                                     "Unmounting "+disk+"...")

                        self.update_status_bar("Unmounting "+disk+". This may take a "
                                               "few moments...")

                        wx.GetApp().Yield()
                        retval = CoreTools.unmount_disk(disk)

                    else:
                        #Unmount any partitions belonging to the device.
                        logger.debug("MainWindow().on_start(): "+disk+" is a device. Unmounting "
                                     "any partitions contained by "+disk+"...")

                        self.update_status_bar("Unmounting "+disk+"'s partitions. This may take "
                                               "a few moments...")

                        wx.GetApp().Yield()

                        retvals = []
                        retval = 0

                        for partition in DISKINFO[disk]["Partitions"]:
                            logger.info("MainWindow().on_start(): Unmounting "+partition+"...")
                            retvals.append(CoreTools.unmount_disk(partition))

                        #Check the return values, and raise an error if any of them aren't 0.
                        for integer in retvals:
                            if integer != 0:
                                retval = integer
                                break

                    #Check it worked.
                    if retval != 0:
                        #It didn't. Warn the user, and exit the function.
                        logger.info("MainWindow().on_start(): Failed! Warning user...")
                        dlg = wx.MessageDialog(self.panel, "Could not unmount disk "+disk+"! "
                                               "Please close all other programs and anything "
                                               "that may be accessing this disk (or any of "
                                               "its partitions), like the file manager perhaps, "
                                               "and try again.", "DDRescue-GUI - Error!",
                                               wx.OK | wx.ICON_ERROR)

                        dlg.ShowModal()
                        dlg.Destroy()
                        self.update_status_bar("Ready.")
                        return

                    else:
                        logger.info("MainWindow().on_start(): Success...")

                else:
                    logger.info("MainWindow().on_start(): "+disk+" is not mounted...")

            #Create the items for self.list_ctrl.
            width = self.list_ctrl.GetClientSize()[0]

            #First column.
            #Compatibility with wxpython < 4.
            if CLASSIC_WXPYTHON:
                self.list_ctrl.InsertItem = self.list_ctrl.InsertStringItem

            self.list_ctrl.InsertItem(0, label="Recovered Data")
            self.list_ctrl.InsertItem(1, label="Unreadable Data")
            self.list_ctrl.InsertItem(2, label="Current Read Rate")
            self.list_ctrl.InsertItem(3, label="Average Read Rate")
            self.list_ctrl.InsertItem(4, label="Bad Sectors")
            self.list_ctrl.InsertItem(5, label="Input position")
            self.list_ctrl.InsertItem(6, label="Output position")
            self.list_ctrl.InsertItem(7, label="Time Since Last Read")
            self.list_ctrl.SetColumnWidth(0, 150)

            #Second column.
            #Compatibility with wxpython < 4.
            if CLASSIC_WXPYTHON:
                self.list_ctrl.SetItem = self.list_ctrl.SetStringItem

            self.list_ctrl.SetItem(0, 1, label="Unknown")
            self.list_ctrl.SetItem(1, 1, label="Unknown")
            self.list_ctrl.SetItem(2, 1, label="Unknown")
            self.list_ctrl.SetItem(3, 1, label="Unknown")
            self.list_ctrl.SetItem(4, 1, label="Unknown")
            self.list_ctrl.SetItem(5, 1, label="Unknown")
            self.list_ctrl.SetItem(6, 1, label="Unknown")
            self.list_ctrl.SetItem(7, 1, label="Unknown")
            self.list_ctrl.SetColumnWidth(1, width - 150)

            logger.info("MainWindow().on_start(): Settings check complete. Starting up "
                        "BackendThread()...")

            self.update_status_bar("Starting up ddrescue...")
            wx.GetApp().Yield()

            #Notify the user.
            CoreTools.send_notification("Beginning Recovery...")

            #Disable and enable all necessary items.
            self.settings_button.Disable()
            self.update_disk_info_button.Disable()
            self.input_choice_box.Disable()
            self.output_choice_box.Disable()
            self.map_choice_box.Disable()
            self.menu_exit.Enable(False)
            self.menu_settings.Enable(False)
            self.menu_mount.Enable(False)
            self.control_button.SetLabel("Abort")

            #Handle any unexpected errors.
            try:
                #Start the backend thread.
                BackendThread(self)

            except Exception:
                logger.critical("Unexpected error \n\n"+unicode(traceback.format_exc())
                                + "\n\n while recovering data. Warning user and exiting.")

                CoreTools.emergency_exit("There was an unexpected error:\n\n"
                                         + unicode(traceback.format_exc())
                                         + "\n\nWhile recovering data!")

        else:
            logger.error("MainWindow().on_start(): One or more of InputFile, OutputFile or "
                         "MapFile hasn't been set! Aborting Recovery...")

            dlg = wx.MessageDialog(self.panel, "Please set the Input file, map file and Output "
                                   "file correctly before starting!", "DDRescue-GUI - Error!",
                                   wx.OK | wx.ICON_ERROR)

            dlg.ShowModal()
            dlg.Destroy()
            self.update_status_bar("Ready.")

    #The next functions are to update the display with info from the backend.
    def set_progress_bar_range(self, _range):
        """
        Set the progress bar's range.

        Args:
            _range (int).               The range to set the progress bar to use.
        """

        logger.debug("MainWindow().set_progress_bar_range(): Setting range "+unicode(_range)
                     + " for self.progress_bar...")

        self.progress_bar.SetRange(_range)

    def update_time_elapsed(self, time_elapsed):
        """
        Update the time elapsed text.

        Args:
            time_elapsed (string).      The label to use for the time elapsed
                                        text.
        """
        self.time_elapsed_text.SetLabel(time_elapsed)

    def update_time_remaining(self, time_left):
        """
        Update the time remaining text.

        Args:
            time_remaining (string).    The label to use for the time remaining
                                        text.
        """
        self.time_remaining_text.SetLabel("Time Remaining: "+time_left)

    def update_recovered_data(self, recovered_data):
        """
        Update the recovered data info.

        Args:
            recovered_data (string).    The amount of data recovered so far.
        """
        #Compatibility with wxpython < 4.
        if CLASSIC_WXPYTHON:
            self.list_ctrl.SetItem = self.list_ctrl.SetStringItem

        self.list_ctrl.SetItem(0, 1, label=recovered_data)

    def update_error_size(self, error_size):
        """
        Update the error size info.

        Args:
            error_size (string).    The amount of unreadable data so far.
        """
        #Compatibility with wxpython < 4.
        if CLASSIC_WXPYTHON:
            self.list_ctrl.SetItem = self.list_ctrl.SetStringItem

        self.list_ctrl.SetItem(1, 1, label=error_size)

    def update_current_read_rate(self, current_read_rate):
        """
        Update the current read rate info.

        Args:
            current_rate_rate (string).     The current read rate.
        """
        #Compatibility with wxpython < 4.
        if CLASSIC_WXPYTHON:
            self.list_ctrl.SetItem = self.list_ctrl.SetStringItem

        self.list_ctrl.SetItem(2, 1, label=current_read_rate)

    def update_average_read_rate(self, average_read_rate):
        """
        Update the average read rate info.

        Args:
            average_read_rate (string).     The average read rate.
        """
        #Compatibility with wxpython < 4.
        if CLASSIC_WXPYTHON:
            self.list_ctrl.SetItem = self.list_ctrl.SetStringItem

        self.list_ctrl.SetItem(3, 1, label=average_read_rate)

    def update_num_errors(self, num_errors):
        """
        Update the num errors info.

        Args:
            num_errors (string).        The number of read errors so far.
        """
        #Compatibility with wxpython < 4.
        if CLASSIC_WXPYTHON:
            self.list_ctrl.SetItem = self.list_ctrl.SetStringItem

        self.list_ctrl.SetItem(4, 1, label=num_errors)

    def update_input_pos(self, input_pos):
        """
        Update the input position info.

        Args:
            input_pos (string).         The current position in the input file
                                        or device.
        """
        #Compatibility with wxpython < 4.
        if CLASSIC_WXPYTHON:
            self.list_ctrl.SetItem = self.list_ctrl.SetStringItem

        self.list_ctrl.SetItem(5, 1, label=input_pos)

    def update_output_pos(self, output_pos):
        """
        Update the output position info.

        Args:
            output_pos (string).        The current position in the output file
                                        or device.
        """
        #Compatibility with wxpython < 4.
        if CLASSIC_WXPYTHON:
            self.list_ctrl.SetItem = self.list_ctrl.SetStringItem

        self.list_ctrl.SetItem(6, 1, label=output_pos)

    def update_time_since_last_read(self, last_read):
        """
        Update the time since last successful read info.

        Args:
            last_read (string).     The amount of time that has passed since
                                    ddrescue successfully read any data from
                                    the input file.
        """
        #Compatibility with wxpython < 4.
        if CLASSIC_WXPYTHON:
            self.list_ctrl.SetItem = self.list_ctrl.SetStringItem

        self.list_ctrl.SetItem(7, 1, label=last_read)

    def update_status_bar(self, messeage):
        """
        Update the status bar with a new message.

        Args:
            message (string).           The message to set the status bar to.
        """
        logger.debug("MainWindow().update_status_bar(): New status bar message: "+messeage)
        self.status_bar.SetStatusText(messeage, 0)

    def update_progress(self, recovered_data, disk_capacity):
        """
        Update the progress bar and the title.

        Args:
            recovered_data (int).           The amount of data currently recovered
                                            (units vary based on disk size).

            disk_capacity (int).            The capacity (or size) of the input
                                            file or disk.
        """
        self.progress_bar.SetValue(recovered_data)
        self.SetTitle(unicode(int(recovered_data * 100 // disk_capacity))+"%" + " - DDRescue-GUI")

    def on_abort(self):
        """
        Abort the recovery.
        """

        #Ask ddrescue to exit.
        logger.info("MainWindow().on_abort(): Attempting to stop ddrescue...")

        if LINUX:
            CoreTools.start_process("killall -s INT ddrescue",
                                    privileged=True)

        else:
            CoreTools.start_process("killall -INT ddrescue",
                                    privileged=True)

        self.aborted_recovery = True #pylint: disable=attribute-defined-outside-init

        #Disable control button.
        self.control_button.Disable()

        if not session_ending:
            #Notify user with throbber.
            self.throbber.Play()

            #Prompt user to try again in 10 seconds time.
            wx.CallLater(10000, self.prompt_to_kill_ddrescue)

    def prompt_to_kill_ddrescue(self):
        """
        Prompts the user to try killing ddrescue again if it's not exiting.
        This sometimes happens if the system is overloaded, or if a disk is
        taking a very long time to timeout/fail a read operation.
        """
        #If we're still recovering data, prompt the user to try killing ddrescue again.
        if SETTINGS["RecoveringData"]:
            logger.warning("MainWindow().prompt_to_kill_ddrescue(): ddrescue is still running 5 "
                           "seconds after attempted abort! Asking user whether to wait or try "
                           "stop it again...")

            dlg = wx.MessageDialog(self.panel, "ddrescue is still running. Do you want to try to "
                                   "stop ddrescue again, or wait for five more seconds? Click yes "
                                   "to stop ddrescue and no to wait.",
                                   "DDRescue is still running!", wx.YES_NO|wx.ICON_QUESTION)

            #Set nice yes/no labels if possible.
            if dlg.SetYesNoLabels("Stop DDRescue", "Wait"):
                dlg.SetMessage("ddrescue is still running. Do you want to try to stop "
                               "ddrescue again, or wait for a few more seconds?")

            if dlg.ShowModal() == wx.ID_YES:
                logger.warning("MainWindow().prompt_to_kill_ddrescue(): Trying to stop "
                               "ddrescue again...")

                self.on_abort()

            else:
                #Prompt user to try again in 5 seconds time.
                logger.info("MainWindow().prompt_to_kill_ddrescue(): Asking user again in 10 "
                            "seconds time if ddrescue hasn't stopped...")

                wx.CallLater(10000, self.prompt_to_kill_ddrescue)

            dlg.Destroy()

    def on_recovery_ended(self, result, disk_capacity, recovered_data, return_code=None):
        """
        Called by the backend thread to show FinishedWindow and update the
        main window when a recovery is completed or aborted by the user, or
        when a recovery errors out for some reason.

        Args:
            result (string).        The reason why the recovery ended. Used to
                                    let the user know what is happening. Values
                                    are "NoInitialStatus", "BadReturnCode", and
                                    "Success".

            disk_capacity (string).    The capacity of the input file or disk.
            recovered_data (string).   The amount of data we recovered.

        Kwargs:
            return_code[=None] (int).       GNU ddrescue's return code. Useful if
                                            the recovery failed for some reason.
        """

        #Return immediately if session is ending.
        if session_ending:
            return

        self.disk_capacity = disk_capacity #pylint: disable=attribute-defined-outside-init
        self.recovered_data = recovered_data #pylint: disable=attribute-defined-outside-init

        #Stop the throbber.
        self.throbber.Stop()

        #Set time remaining to 0s (sometimes doesn't happen).
        self.update_time_remaining("0 seconds")

        #Handle any errors.
        if self.aborted_recovery:
            logger.info("MainWindow().on_recovery_ended(): ddrescue was aborted by the user...")

            #Notify the user.
            CoreTools.send_notification("Recovery was aborted by user.")

            dlg = wx.MessageDialog(self.panel, "Your recovery has been aborted as you requested."
                                   "\n\nNote: Your recovered data may be incomplete at this "
                                   "point, so you may now want to run a second recovery to try "
                                   "and grab the remaining data. If you wish to, you may now use "
                                   "DDRescue-GUI to mount your destination drive/file so you can "
                                   "access your data, although some/all of it may be unreadable "
                                   "in its current state.", "DDRescue-GUI - Information",
                                   wx.OK | wx.ICON_INFORMATION)

            dlg.ShowModal()
            dlg.Destroy()

        elif result == "NoInitialStatus":
            logger.error("MainWindow().on_recovery_ended(): We didn't get ddrescue's initial "
                         "status! This probably means ddrescue aborted immediately. Maybe "
                         "settings are incorrect?")

            #Notify the user.
            CoreTools.send_notification("Recovery Error! ddrescue aborted immediately. See "
                                        "GUI for more info.")

            dlg = wx.MessageDialog(self.panel, "We didn't get ddrescue's initial status! This "
                                   "probably means ddrescue aborted immediately. Please check "
                                   "all of your settings, and try again. Here is ddrescue's "
                                   "output, which may tell you what went wrong:\n\n"
                                   + self.output_box.GetValue(), "DDRescue-GUI - Error!",
                                   wx.OK | wx.ICON_ERROR)

            dlg.ShowModal()
            dlg.Destroy()

        elif result == "BadReturnCode":
            logger.error("MainWindow().on_recovery_ended(): ddrescue exited with nonzero exit "
                         "status "+unicode(return_code)+"! Perhaps the output file/disk is full?")

            #Notify the user.
            CoreTools.send_notification("Recovery Error! ddrescue exited with exit status "
                                        + unicode(return_code)+"!")

            dlg = wx.MessageDialog(self.panel, "ddrescue exited with nonzero exit status "
                                   + unicode(return_code)+"! Perhaps the output file/disk is "
                                   "full? Please check all of your settings, and try again. "
                                   "Here is ddrescue's output, which may tell you what went "
                                   "wrong:\n\n"+self.output_box.GetValue(),
                                   "DDRescue-GUI - Error!", wx.OK | wx.ICON_ERROR)

            dlg.ShowModal()
            dlg.Destroy()

        elif result == "Success":
            logger.info("MainWindow().on_recovery_ended(): Recovery finished!")

            #Check if we got all the data.
            if self.progress_bar.GetValue() >= self.progress_bar.GetRange():
                message = "Your recovery is complete, with all data recovered from your source " \
                          "disk/file.\n\nNote: If you wish to, you may now use DDRescue-GUI to " \
                          "mount your destination drive/file so you can access your data."

                #Notify the user.
                CoreTools.send_notification("Recovery finished with all data!")

            else:
                message = "Your recovery is finished, but not all of your data appears to have " \
                          "been recovered. You may now want to run a second recovery to try and " \
                          "grab the remaining data. If you wish to, you may now use " \
                          "DDRescue-GUI to mount your destination drive/file so you can access " \
                          "your data, although some/all of it may be unreadable in its current " \
                          "state."

                #Notify the user.
                CoreTools.send_notification("Recovery finished, but not all data was "
                                            "recovered.")

            dlg = wx.MessageDialog(self.panel, message, "DDRescue-GUI - Information",
                                   wx.OK | wx.ICON_INFORMATION)

            dlg.ShowModal()
            dlg.Destroy()

        #Disable the control button.
        self.control_button.Disable()

        FinishedWindow(self, disk_capacity, recovered_data).Show()

    def restart(self):
        """
        Restart and reset MainWindow, so MainWindow is as it was when
        DDRescue-GUI was started.
        """

        logger.info("MainWindow().restart(): Reloading and resetting MainWindow...")
        self.update_status_bar("Restarting, please wait...")

        #Set everything back the way it was before
        self.SetTitle("DDRescue-GUI")
        self.update_disk_info_button.Enable()
        self.control_button.Enable()
        self.settings_button.Enable()
        self.input_choice_box.Enable()
        self.output_choice_box.Enable()
        self.map_choice_box.Enable()
        self.menu_about.Enable(True)
        self.menu_exit.Enable(True)
        self.menu_disk_info.Enable(True)
        self.menu_settings.Enable(True)
        self.menu_mount.Enable()

        #Reset recovery information.
        self.output_box.Clear()
        self.list_ctrl.ClearAll()
        self.list_ctrl.InsertColumn(0, heading="Category", format=wx.LIST_FORMAT_CENTRE,
                                    width=-1)

        self.list_ctrl.InsertColumn(1, heading="Value", format=wx.LIST_FORMAT_CENTRE, width=-1)
        self.control_button.SetLabel("Start")
        self.time_remaining_text.SetLabel("Time Remaining:")
        self.time_elapsed_text.SetLabel("Time Elapsed:")

        #Reset the progress_bar
        self.progress_bar.SetValue(0)

        #Reset essential variables.
        self.set_vars()

        #Update choice dialogs and reset checked settings to False
        self.update_file_choices()

        #Reset the choice dialogs.
        self.input_choice_box.SetStringSelection("-- Please Select --")
        self.output_choice_box.SetStringSelection("-- Please Select --")
        self.map_choice_box.SetStringSelection("-- Please Select --")

        #Get new Disk info.
        self.get_diskinfo()

        logger.info("MainWindow().restart(): Done. Waiting for events...")
        self.update_status_bar("Ready.")

    def on_session_end(self, event):
        """
        Attempt to veto e.g. a shutdown/logout event if recovering data.
        """
        #FIXME This does not seem to work on Linux. What about macOS?
        #Check if we can veto the shutdown.
        logging.warning("MainWindow().on_session_end(): Attempting to veto system shutdown / "
                        "logoff...")

        if event.CanVeto() and SETTINGS["RecoveringData"]:
            #Veto the shutdown and warn the user.
            event.Veto(True)
            logging.info("MainWindow().on_session_end(): Vetoed system shutdown / logoff...")
            dlg = wx.MessageDialog(self.panel, "You can't shutdown or logoff while recovering "
                                   "data!", "DDRescue-GUI - Error!", wx.OK | wx.ICON_ERROR)

            dlg.ShowModal()
            dlg.Destroy()

        else:
            #Set on_session_end to True, call on_exit. TODO clean up better if eg doing a recovery.
            logging.critical("MainWindow().on_session_end(): Cannot veto system shutdown / "
                             "logoff! Cleaning up...")

            global session_ending #pylint: disable=global-statement
            session_ending = True
            self.on_exit()

    def on_exit(self, event=None, just_finished_recovery=False): #pylint: disable=too-many-branches,unused-argument,line-too-long
        """
        Exit DDRescue-GUI, if certain conditions are met (for example we
        aren't in the middle of a recovery). Also offer to save the log
        file for debugging / error-reporting purposes.

        Kwargs:
            just_finished_recovery (bool).
                True -                  Display FinishedWindow if user cancels
                                        the exit attempt.

                False -                 The default, do nothing if user cancels
                                        the exit attempt.
        """

        logger.info("MainWindow().on_exit(): Preparing to exit...")

        #Check if the session is ending.
        if session_ending:
            #Stop the backend thread, delete the log file and exit ASAP.
            #FIXME check this works.
            self.on_abort()
            logging.shutdown()
            os.remove("/tmp/ddrescue-gui.log"+"."+unicode(LOG_SUFFIX))
            self.Destroy()

        #Check if DDRescue-GUI is recovering data.
        if SETTINGS["RecoveringData"]:
            logger.error("MainWindow().on_exit(): Can't exit while recovering data! Aborting exit "
                         "attempt...")

            dlg = wx.MessageDialog(self.panel, "You can't exit DDRescue-GUI while recovering "
                                   "data!", "DDRescue-GUI - Error!", wx.OK | wx.ICON_ERROR)

            dlg.ShowModal()
            dlg.Destroy()
            return

        logger.info("MainWindow().on_exit(): Double-checking the exit attempt with the user...")
        dlg = wx.MessageDialog(self.panel, 'Are you sure you want to exit?',
                               'DDRescue-GUI - Question!', wx.YES_NO | wx.ICON_QUESTION)

        answer = dlg.ShowModal()
        dlg.Destroy()

        if answer == wx.ID_YES:
            #Run the exit sequence
            logger.info("MainWindow().on_exit(): Exiting...")

            #Shutdown the logger.
            logging.shutdown()

            #Prompt user to save the log file.
            dlg = wx.MessageDialog(self.panel, "Do you want to keep DDRescue-GUI's log file? For "
                                   "privacy reasons, DDRescue-GUI will delete its log file when "
                                   "closing. If you want to save it, which is helpful for "
                                   "debugging if something went wrong, click yes, and otherwise "
                                   "click no.", "DDRescue-GUI - Question",
                                   style=wx.YES_NO | wx.ICON_QUESTION)

            answer = dlg.ShowModal()
            dlg.Destroy()

            if answer == wx.ID_YES:
                #Trap pogram in loop in case same log file as Recovery map file is picked
                #for destination.
                while True:
                    #Ask the user where to save it.
                    dlg = wx.FileDialog(self.panel, "Save log file to...",
                                        defaultDir=self.user_homedir,
                                        wildcard="Log Files (*.log)|*.log",
                                        style=wx.FD_SAVE)

                    answer = dlg.ShowModal()
                    _file = dlg.GetPath()
                    dlg.Destroy()

                    if answer == wx.ID_OK:
                        if _file == SETTINGS["MapFile"]:
                            dlg = wx.MessageDialog(self.panel, "Error! Your chosen file is the "
                                                   "same as the recovery map file! This log file "
                                                   "contains only debugging information for "
                                                   "DDRescue-GUI, and you must not overwrite "
                                                   "the recovery map file with this file. Please "
                                                   "select a new destination file.",
                                                   "DDRescue-GUI - Error", wx.OK | wx.ICON_ERROR)

                            dlg.ShowModal()
                            dlg.Destroy()

                        else:
                            #Copy it to the specified path.
                            if CoreTools.start_process("cp /tmp/ddrescue-gui.log"+"."
                                                       + unicode(LOG_SUFFIX)+" "+_file) == 0:

                                dlg = wx.MessageDialog(self.panel, "Done! DDRescue-GUI will now "
                                                       "exit", "DDRescue-GUI - Information",
                                                       wx.OK | wx.ICON_INFORMATION)

                                dlg.ShowModal()
                                dlg.Destroy()
                                break

                            else:
                                dlg = wx.MessageDialog(self.panel, "DDRescue-GUI does not have "
                                                       + "permission to write to that file or "
                                                       + "directory! Please select a new file "
                                                       + "and try again.",
                                                       "DDRescue-GUI - Information",
                                                       wx.OK | wx.ICON_INFORMATION)

                                dlg.ShowModal()
                                dlg.Destroy()


                    else:
                        dlg = wx.MessageDialog(self.panel, "Okay, DDRescue-GUI will now exit "
                                               "without saving the log file.",
                                               "DDRescue-GUI - Information",
                                               wx.OK | wx.ICON_INFORMATION)

                        dlg.ShowModal()
                        dlg.Destroy()
                        break

            else:
                dlg = wx.MessageDialog(self.panel, "Okay, DDRescue-GUI will now exit without "
                                       "saving the log file.", "DDRescue-GUI - Information",
                                       wx.OK | wx.ICON_INFORMATION)

                dlg.ShowModal()
                dlg.Destroy()

            #Delete the log file.
            os.remove("/tmp/ddrescue-gui.log"+"."+unicode(LOG_SUFFIX))

            self.Destroy()

        else:
            #Check if exit was initated by finisheddlg.
            logger.warning("MainWindow().on_exit(): User cancelled exit attempt! "
                           "Aborting exit attempt...")

            if just_finished_recovery:
                #If so return to finisheddlg.
                logger.info("MainWindow().on_exit(): Showing FinishedWindow() again...")
                FinishedWindow(self, self.disk_capacity, self.recovered_data).Show()

#End Main Window
#Begin Disk Info Window
class DiskInfoWindow(wx.Frame): #pylint: disable=too-many-ancestors
    """
    DDRescue-GUI's disk information window.
    """

    def __init__(self, parent):
        """
        Initialize DiskInfoWindow.

        Args:
            parent (object).                The parent window that started this
                                            window.
        """
        wx.Frame.__init__(self, wx.GetApp().TopWindow, title="DDRescue-GUI - Disk Information",
                          size=(780, 310), style=wx.DEFAULT_FRAME_STYLE)

        self.panel = wx.Panel(self)
        self.SetClientSize(wx.Size(780, 310))
        self.parent = parent
        wx.Frame.SetIcon(self, APPICON)

        logger.debug("DiskInfoWindow().__init__(): Creating widgets...")
        self.create_widgets()

        logger.debug("DiskInfoWindow().__init__(): Setting up sizers...")
        self.setup_sizers()

        logger.debug("DiskInfoWindow().__init__(): Binding events...")
        self.bind_events()

        #Use already-present info for the list ctrl if possible.
        if 'DISKINFO' in globals():
            logger.debug("DiskInfoWindow().__init__(): Updating list ctrl with Disk info "
                         "already present...")

            self.update_list_ctrl()

        #Call Layout() on self.panel() to ensure it displays properly.
        self.panel.Layout()

        logger.info("DiskInfoWindow().__init__(): Ready. Waiting for events...")

    def create_widgets(self):
        """
        Create all widgets for DiskInfoWindow
        """
        self.title_text = wx.StaticText(self.panel, -1, "Here are all the detected disks on "
                                        "your computer")

        self.list_ctrl = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT|wx.LC_VRULES)
        self.okay_button = wx.Button(self.panel, -1, "Okay")
        self.refresh_button = wx.Button(self.panel, -1, "Refresh")

        #Disable the refresh button if we're recovering data.
        if SETTINGS["RecoveringData"]:
            self.refresh_button.Disable()

        #Create the animation for the throbber.
        throb = wxAnimation(RESOURCEPATH+"/images/Throbber.gif")
        self.throbber = wxAnimationCtrl(self.panel, -1, throb)
        self.throbber.SetInactiveBitmap(wx.Bitmap(RESOURCEPATH+"/images/ThrobberRest.png",
                                                  wx.BITMAP_TYPE_PNG))

        self.throbber.SetClientSize(wx.Size(30, 30))

    def setup_sizers(self):
        """
        Set up the sizers for DiskInfoWindow
        """
        #Make a button boxsizer.
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add each object to the bottom sizer.
        bottom_sizer.Add(self.refresh_button, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_LEFT, 10)
        bottom_sizer.Add((20, 20), 1)
        bottom_sizer.Add(self.throbber, 0, wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
        bottom_sizer.Add((20, 20), 1)
        bottom_sizer.Add(self.okay_button, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_RIGHT, 10)

        #Make a boxsizer.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        #Add each object to the main sizer.
        main_sizer.Add(self.title_text, 0, wx.ALL|wx.CENTER, 10)
        main_sizer.Add(self.list_ctrl, 1, wx.EXPAND|wx.ALL, 10)
        main_sizer.Add(bottom_sizer, 0, wx.EXPAND|wx.ALL ^ wx.TOP, 10)

        #Get the sizer set up for the frame.
        self.panel.SetSizer(main_sizer)
        main_sizer.SetMinSize(wx.Size(780, 310))
        main_sizer.SetSizeHints(self)

    def bind_events(self):
        """
        Bind all events for DiskInfoWindow
        """
        self.Bind(wx.EVT_BUTTON, self.get_diskinfo, self.refresh_button)
        self.Bind(wx.EVT_BUTTON, self.on_exit, self.okay_button)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_CLOSE, self.on_exit)

    def on_size(self, event=None):
        """
        Auto resize the list_ctrl columns
        """
        width = self.list_ctrl.GetClientSize()[0]

        self.list_ctrl.SetColumnWidth(0, int(width * 0.15))
        self.list_ctrl.SetColumnWidth(1, int(width * 0.1))
        self.list_ctrl.SetColumnWidth(2, int(width * 0.1))
        self.list_ctrl.SetColumnWidth(3, int(width * 0.3))
        self.list_ctrl.SetColumnWidth(4, int(width * 0.15))
        self.list_ctrl.SetColumnWidth(5, int(width * 0.2))

        if event is not None:
            event.Skip()

    def get_diskinfo(self, event=None): #pylint: disable=unused-argument
        """
        Call the thread to get Disk info, disable the refresh button, and start
        the throbber
        """
        logger.info("DiskInfoWindow().UpdateDevInfo(): Generating new Disk info...")
        self.refresh_button.Disable()
        self.throbber.Play()
        GetDiskInformation(self)

    def receive_diskinfo(self, info):
        """
        Get Disk data, call self.update_list_ctrl(), and then call
        MainWindow().update_file_choices() to refresh the file choices with the new info.

        Args:
            info (dict).            The new disk information.
        """

        global DISKINFO
        DISKINFO.clear()
        DISKINFO.update(info)

        #Update the list control.
        logger.debug("DiskInfoWindow().UpdateDevInfo(): Calling self.update_list_ctrl()...")
        self.update_list_ctrl()

        #Send update signal to mainwindow.
        logger.debug("DiskInfoWindow().UpdateDevInfo(): Calling "
                     "self.parent.update_file_choices()...")

        wx.CallAfter(self.parent.update_file_choices)

        #Stop the throbber and enable the refresh button.
        self.throbber.Stop()
        self.refresh_button.Enable()

    def update_list_ctrl(self, event=None): #pylint: disable=unused-argument
        """
        Update the list control
        """
        logger.debug("DiskInfoWindow().update_list_ctrl(): Clearing all objects in list ctrl...")
        self.list_ctrl.ClearAll()

        #Create the columns.
        logger.debug("DiskInfoWindow().update_list_ctrl(): Inserting columns into list ctrl...")
        self.list_ctrl.InsertColumn(0, heading="Name", format=wx.LIST_FORMAT_CENTRE)
        self.list_ctrl.InsertColumn(1, heading="Type", format=wx.LIST_FORMAT_CENTRE)
        self.list_ctrl.InsertColumn(2, heading="Vendor", format=wx.LIST_FORMAT_CENTRE)
        self.list_ctrl.InsertColumn(3, heading="Product", format=wx.LIST_FORMAT_CENTRE)
        self.list_ctrl.InsertColumn(4, heading="Size", format=wx.LIST_FORMAT_CENTRE)
        self.list_ctrl.InsertColumn(5, heading="Description", format=wx.LIST_FORMAT_CENTRE)

        #Add info from the custom module.
        logger.debug("DiskInfoWindow().update_list_ctrl(): Adding Disk info to list ctrl...")

        #Do all of the data at the same time.
        number = -1
        disks = list(DISKINFO)
        disks.sort()

        headings = ("Name", "Type", "Vendor", "Product", "Capacity", "Description")

        for disk in disks:
            number += 1
            column = 0

            for heading in headings:
                if column == 0:
                    #Compatibility with wxpython < 4.
                    if CLASSIC_WXPYTHON:
                        self.list_ctrl.InsertItem = self.list_ctrl.InsertStringItem

                    self.list_ctrl.InsertItem(number, label=DISKINFO[disk][heading])

                else:
                    #Compatibility with wxpython < 4.
                    if CLASSIC_WXPYTHON:
                        self.list_ctrl.SetItem = self.list_ctrl.SetStringItem

                    self.list_ctrl.SetItem(number, column,
                                           label=DISKINFO[disk][heading])

                column += 1

        #Auto Resize the columns.
        self.on_size()

    def on_exit(self, event=None): #pylint: disable=unused-argument
        """
        Exit DiskInfoWindow
        """
        logger.info("DiskInfoWindow().on_exit(): Closing DiskInfoWindow...")
        self.Destroy()

#End Disk Info Window
#Begin settings Window
class SettingsWindow(wx.Frame): #pylint: disable=too-many-instance-attributes,too-many-ancestors
    """
    DDRescue-GUI's settings window
    """

    def __init__(self, parent):
        """
        Initialize SettingsWindow
        """
        wx.Frame.__init__(self, wx.GetApp().TopWindow, title="DDRescue-GUI - Settings",
                          size=(569, 479), style=wx.DEFAULT_FRAME_STYLE)

        self.panel = wx.Panel(self)
        self.SetClientSize(wx.Size(569, 479))
        self.parent = parent
        wx.Frame.SetIcon(self, APPICON)

        #Notify MainWindow that this has been run.
        logger.debug("SettingsWindow().__init__(): Setting CheckedSettings to True...")
        SETTINGS["CheckedSettings"] = True

        #Create all of the widgets first.
        logger.debug("SettingsWindow().__init__(): Creating buttons...")
        self.create_buttons()

        logger.debug("SettingsWindow().__init__(): Creating text...")
        self.create_text()

        logger.debug("SettingsWindow().__init__(): Creating Checkboxes...")
        self.create_check_boxes()

        logger.debug("SettingsWindow().__init__(): Creating Choiceboxes...")
        self.create_choice_boxes()

        #Then setup the sizers and bind events, and finally the options in the window.
        logger.debug("SettingsWindow().__init__(): Setting up sizers...")
        self.setup_sizers()

        logger.debug("SettingsWindow().__init__(): Binding events...")
        self.bind_events()

        logger.debug("SettingsWindow().__init__(): Setting up options...")
        self.setup_options()

        #Call Layout() on self.panel() to ensure it displays properly.
        self.panel.Layout()

        self.exit_button.SetFocus()

        logger.info("SettingsWindow().__init__(): Ready. Waiting for events...")

    def create_buttons(self):
        """
        Create all buttons for SettingsWindow
        """
        self.fast_button = wx.Button(self.panel, -1, "Set to fastest recovery")
        self.best_button = wx.Button(self.panel, -1, "Set to best recovery")
        self.default_button = wx.Button(self.panel, -1, "Balanced (default)")
        self.exit_button = wx.Button(self.panel, -1, "Save settings and close")

    def create_text(self):
        """
        Create all text for SettingsWindow
        """
        self.title_text = wx.StaticText(self.panel, -1, "Welcome to settings.")
        self.bad_sector_retries_text = wx.StaticText(self.panel, -1, "No. of times to retry "
                                                     "bad sectors:")

        self.max_errors_text = wx.StaticText(self.panel, -1, "Maximum number of errors before "
                                             "exiting:")

        self.cluster_size_text = wx.StaticText(self.panel, -1, "Number of clusters to copy at "
                                               "a time:")

        self.presets_text = wx.StaticText(self.panel, -1, "Presets:")


    def create_check_boxes(self):
        """
        Create all CheckBoxes for SettingsWindow, and set their default states (all unchecked)
        """

        self.direct_disk_access_check_box = wx.CheckBox(self.panel, -1, "Use Direct Disk Access "
                                                        "(Recommended, but untick if recovering "
                                                        "from a file)")

        self.overwrite_output_file_check_box = wx.CheckBox(self.panel, -1, "Overwrite output "
                                                           "file/disk (Enable if recovering to "
                                                           "a disk)")

        self.reverse_check_box = wx.CheckBox(self.panel, -1, "Read the input file/disk backwards")
        self.preallocate_check_box = wx.CheckBox(self.panel, -1, "Preallocate space on disk for "
                                                 "output file/disk")

        self.no_split_check_box = wx.CheckBox(self.panel, -1, "Do a soft run (don't attempt to "
                                              "read bad sectors)")

    def create_choice_boxes(self):
        """
        Create all ChoiceBoxes for SettingsWindow, and call self.set_default_recovery_settings()
        """

        self.bad_sector_retries_choice = wx.Choice(self.panel, -1,
                                                   choices=['0', '1', 'Default (2)', '3',
                                                            '5', 'Forever'])

        self.max_errors_choice = wx.Choice(self.panel, -1,
                                           choices=['Default (Infinite)', '1000', '500',
                                                    '100', '50', '10'])

        self.cluster_size_choice = wx.Choice(self.panel, -1,
                                             choices=['256', 'Default (128)', '64', '32'])

        #Set default settings.
        self.set_default_recovery_settings()

    def setup_sizers(self):
        """
        Set up all sizers for SettingsWindow.
        """
        #Make a sizer for each choicebox with text, and add the objects for each sizer.
        #Retry bad sectors sizer.
        bad_sector_retries_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bad_sector_retries_sizer.Add(self.bad_sector_retries_text, 1,
                                     wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 10)

        bad_sector_retries_sizer.Add(self.bad_sector_retries_choice, 1,
                                     wx.RIGHT|wx.ALIGN_CENTER, 10)

        #Max errors sizer.
        max_errors_sizer = wx.BoxSizer(wx.HORIZONTAL)
        max_errors_sizer.Add(self.max_errors_text, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 10)
        max_errors_sizer.Add(self.max_errors_choice, 1, wx.RIGHT|wx.ALIGN_CENTER, 10)

        #Cluster Size Sizer.
        cluster_size_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cluster_size_sizer.Add(self.cluster_size_text, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 10)
        cluster_size_sizer.Add(self.cluster_size_choice, 1, wx.RIGHT|wx.ALIGN_CENTER, 10)

        #Make a sizer for the best and fastest recovery buttons now, and add the objects.
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.best_button, 3, wx.LEFT|wx.EXPAND, 10)
        button_sizer.Add((20, 20), 1)
        button_sizer.Add(self.fast_button, 3, wx.RIGHT|wx.EXPAND, 10)

        #Now create and add all objects to the main sizer in order.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        #Checkboxes.
        main_sizer.Add(self.title_text, 3, wx.CENTER|wx.TOP, 10)
        main_sizer.Add(self.direct_disk_access_check_box, 3, wx.CENTER|wx.ALL, 5)
        main_sizer.Add(self.reverse_check_box, 3, wx.CENTER|wx.ALL, 5)
        main_sizer.Add(self.preallocate_check_box, 3, wx.CENTER|wx.ALL, 5)
        main_sizer.Add(self.no_split_check_box, 3, wx.CENTER|wx.ALL, 5)
        main_sizer.Add(self.overwrite_output_file_check_box, 3, wx.CENTER|wx.ALL, 5)

        #Choice box sizers.
        main_sizer.Add(bad_sector_retries_sizer, 4, wx.CENTER|wx.EXPAND|wx.ALL, 10)
        main_sizer.Add(max_errors_sizer, 4, wx.CENTER|wx.EXPAND|wx.ALL, 10)
        main_sizer.Add(cluster_size_sizer, 4, wx.CENTER|wx.EXPAND|wx.ALL, 10)

        #Add the buttons, and the button sizer.
        main_sizer.Add(wx.StaticLine(self.panel), 0, wx.ALL|wx.EXPAND, 10)
        main_sizer.Add(self.presets_text, 4, wx.CENTER)
        main_sizer.Add(self.default_button, 4, wx.CENTER|wx.ALL, 10)
        main_sizer.Add(button_sizer, 4, wx.CENTER|wx.EXPAND|wx.ALL, 10)
        main_sizer.Add(self.exit_button, 4, wx.CENTER|wx.ALL, 10)

        #Get the main sizer set up for the frame.
        self.panel.SetSizer(main_sizer)
        main_sizer.SetMinSize(wx.Size(569, 479))
        main_sizer.SetSizeHints(self)

    def bind_events(self):
        """
        Bind all events for SettingsWindow.
        """
        self.Bind(wx.EVT_CHECKBOX, self.set_soft_run, self.no_split_check_box)
        self.Bind(wx.EVT_BUTTON, self.set_default_recovery_settings, self.default_button)
        self.Bind(wx.EVT_BUTTON, self.set_fast_recovery_settings, self.fast_button)
        self.Bind(wx.EVT_BUTTON, self.set_best_recovery_settings, self.best_button)
        self.Bind(wx.EVT_BUTTON, self.save_options, self.exit_button)
        self.Bind(wx.EVT_CLOSE, self.save_options)

    def setup_options(self):
        """
        Set all options in the window so we remember them if the user checks back
        """
        #Checkboxes:
        #Direct disk access setting.
        self.direct_disk_access_check_box.SetValue(SETTINGS["DirectAccess"] == "-d")

        #Overwrite output disk setting.
        self.overwrite_output_file_check_box.SetValue(SETTINGS["OverwriteOutputFile"] == "-f")

        #Reverse (read data from the end to the start of the input file) setting.
        self.reverse_check_box.SetValue(SETTINGS["Reverse"] == "-R")

        #Preallocate (preallocate space in the output file) setting.
        self.preallocate_check_box.SetValue(SETTINGS["Preallocate"] == "-p")

        #NoSplit (Don't split failed blocks) option.
        if SETTINGS["NoSplit"] == "-n":
            self.no_split_check_box.SetValue(True)

            #Disable self.bad_sector_retries_choice.
            self.bad_sector_retries_choice.Disable()

        else:
            self.no_split_check_box.SetValue(False)

            #Enable self.bad_sector_retries_choice.
            self.bad_sector_retries_choice.Enable()

        #ChoiceBoxes:
        #Retry bad sectors option.
        if SETTINGS["BadSectorRetries"] == "-r 2":
            self.bad_sector_retries_choice.SetSelection(2)

        elif SETTINGS["BadSectorRetries"] == "-r -1":
            self.bad_sector_retries_choice.SetSelection(5)

        else:
            self.bad_sector_retries_choice.SetSelection(int(SETTINGS["BadSectorRetries"][3:]))

        #Maximum errors before exiting option.
        if SETTINGS["MaxErrors"] == "":
            self.max_errors_choice.SetStringSelection("Default (Infinite)")

        else:
            self.max_errors_choice.SetStringSelection(SETTINGS["MaxErrors"][3:])

        #ClusterSize (No. of sectors to copy at a time) option.
        if SETTINGS["ClusterSize"] == "-c 128":
            self.cluster_size_choice.SetStringSelection("Default (128)")

        else:
            self.cluster_size_choice.SetStringSelection(SETTINGS["ClusterSize"][3:])

    def set_soft_run(self, event=None): #pylint: disable=unused-argument
        """
        Set up SettingsWindow based on the value of self.no_split_check_box
        (the "do soft run" CheckBox).
        """

        logger.debug("SettingsWindow().set_soft_run(): Do soft run: "
                     + unicode(self.no_split_check_box.GetValue())
                     + ". Setting up SettingsWindow accordingly...")

        if self.no_split_check_box.IsChecked():
            self.bad_sector_retries_choice.SetSelection(0)
            self.bad_sector_retries_choice.Disable()

        else:
            self.bad_sector_retries_choice.Enable()
            self.set_default_recovery_settings()

    def set_default_recovery_settings(self, event=None): #pylint: disable=unused-argument
        """
        Set selections for the Choiceboxes to default settings.
        """
        logger.debug("SettingsWindow().set_default_recovery_settings(): Setting up SettingsWindow "
                     "for default recovery settings...")

        if self.bad_sector_retries_choice.IsEnabled():
            self.bad_sector_retries_choice.SetSelection(2)

        self.max_errors_choice.SetSelection(0)
        self.cluster_size_choice.SetSelection(1)

        self.default_button.SetFocus()

    def set_fast_recovery_settings(self, event=None): #pylint: disable=unused-argument
        """
        Set selections for the Choiceboxes to fast recovery settings.
        """
        logger.debug("SettingsWindow().set_fast_recovery_settings(): Setting up SettingsWindow "
                     "for fast recovery settings...")

        if self.bad_sector_retries_choice.IsEnabled():
            self.bad_sector_retries_choice.SetSelection(0)

        self.max_errors_choice.SetSelection(0)
        self.cluster_size_choice.SetSelection(0)

        self.fast_button.SetFocus()

    def set_best_recovery_settings(self, event=None): #pylint: disable=unused-argument
        """
        Set selections for the Choiceboxes to best recovery settings.
        """
        logger.debug("SettingsWindow().set_best_recovery_settings(): Setting up SettingsWindow "
                     "for best recovery settings...")

        if self.bad_sector_retries_choice.IsEnabled():
            self.bad_sector_retries_choice.SetSelection(2)

        self.max_errors_choice.SetSelection(0)
        self.cluster_size_choice.SetSelection(3)

        self.best_button.SetFocus()

    def save_options(self, event=None): #pylint: disable=unused-argument
        """
        Save all options, and exit SettingsWindow.
        """
        logger.info("SettingsWindow().save_options(): Saving Options...")

        #Checkboxes:
        #Direct disk access setting.
        if self.direct_disk_access_check_box.IsChecked():
            SETTINGS["DirectAccess"] = "-d"

        else:
            SETTINGS["DirectAccess"] = ""

        logger.info("SettingsWindow().save_options(): Use Direct Disk Access: "
                    + unicode(bool(SETTINGS["DirectAccess"]))+".")

        #Overwrite output Disk setting.
        if self.overwrite_output_file_check_box.IsChecked():
            SETTINGS["OverwriteOutputFile"] = "-f"

        else:
            SETTINGS["OverwriteOutputFile"] = ""

        logger.info("SettingsWindow().save_options(): Overwriting output file: "
                    +unicode(bool(SETTINGS["OverwriteOutputFile"]))+".")

        #Disk Size setting (OS X only).
        if LINUX is False:
            #If the input file is in DISKINFO, use the Capacity from that.
            if SETTINGS["InputFile"] in DISKINFO:
                SETTINGS["DiskSize"] = "-s "+DISKINFO[SETTINGS["InputFile"]]["RawCapacity"]
                logger.info("SettingsWindow().save_options(): Using disk size: "
                            +SETTINGS["DiskSize"]+".")

            #TODO determine disk size in bytes if not in disk info. Not sure how yet.
            #Otherwise, it isn't needed.
            else:
                SETTINGS["DiskSize"] = ""

        else:
            SETTINGS["DiskSize"] = ""

        #Reverse (read data from the end to the start of the input file) setting.
        if self.reverse_check_box.IsChecked():
            SETTINGS["Reverse"] = "-R"

        else:
            SETTINGS["Reverse"] = ""

        logger.info("SettingsWindow().save_options(): Reverse direction of read operations: "
                    + unicode(bool(SETTINGS["Reverse"]))+".")

        #Preallocate (preallocate space in the output file) setting.
        if self.preallocate_check_box.IsChecked():
            SETTINGS["Preallocate"] = "-p"

        else:
            SETTINGS["Preallocate"] = ""

        logger.info("SettingsWindow().save_options(): Preallocate disk space: "
                    + unicode(bool(SETTINGS["Preallocate"]))+".")

        #NoSplit (Don't split failed blocks) option.
        if self.no_split_check_box.IsChecked():
            SETTINGS["NoSplit"] = "-n"

        else:
            SETTINGS["NoSplit"] = ""

        logger.info("SettingsWindow().save_options(): Split failed blocks: "
                    + unicode(not bool(SETTINGS["NoSplit"]))+".")

        #ChoiceBoxes:
        #Retry bad sectors option.
        bad_sector_retries_selection = self.bad_sector_retries_choice.GetCurrentSelection()

        if bad_sector_retries_selection == 2:
            SETTINGS["BadSectorRetries"] = "-r 2"

        elif bad_sector_retries_selection == 5:
            SETTINGS["BadSectorRetries"] = "-r -1"

        else:
            SETTINGS["BadSectorRetries"] = "-r "+unicode(bad_sector_retries_selection)

        logger.info("SettingsWindow().save_options(): Retrying bad sectors "
                    + SETTINGS["BadSectorRetries"][3:]+" times.")

        #Maximum errors before exiting option.
        max_errors_selection = self.max_errors_choice.GetStringSelection()

        if max_errors_selection == "Default (Infinite)":
            SETTINGS["MaxErrors"] = ""
            logger.info("SettingsWindow().save_options(): Allowing an infinite number of "
                        "errors before exiting.")

        else:
            SETTINGS["MaxErrors"] = "-e "+max_errors_selection
            logger.info("SettingsWindow().save_options(): Allowing "+SETTINGS["MaxErrors"][3:]
                        + " errors before exiting.")

        #ClusterSize (No. of sectors to copy at a time) option.
        cluster_size_selection = self.cluster_size_choice.GetStringSelection()

        if cluster_size_selection == "Default (128)":
            SETTINGS["ClusterSize"] = "-c 128"

        else:
            SETTINGS["ClusterSize"] = "-c "+cluster_size_selection

        logger.info("SettingsWindow().save_options(): ClusterSize is "
                    + SETTINGS["ClusterSize"][3:]+".")

        #BlockSize detection.
        logger.info("SettingsWindow().save_options(): Determining blocksize of input file...")

        if LINUX:
            function = getdevinfo.linux.get_block_size

        else:
            function = getdevinfo.macos.get_block_size

        SETTINGS["InputFileBlockSize"] = function(SETTINGS["InputFile"])

        if SETTINGS["InputFileBlockSize"] is not None:
            logger.info("SettingsWindow().save_options(): BlockSize of input file: "
                        + SETTINGS["InputFileBlockSize"]+" (bytes).")

            SETTINGS["InputFileBlockSize"] = "-b "+SETTINGS["InputFileBlockSize"]

        else:
            #Input file is standard file, don't set blocksize, notify user.
            SETTINGS["InputFileBlockSize"] = ""
            logger.info("SettingsWindow().save_options(): Input file is a standard file, "
                        "and therefore has no blocksize.")

        #Finally, exit
        logger.info("SettingsWindow().save_options(): Finished saving options. "
                    "Closing settings Window...")

        self.Destroy()

#End settings Window
#Begin Privacy Policy Window.
class PrivPolWindow(wx.Frame): #pylint: disable=too-many-ancestors
    """
    DDRescue-GUI's privacy policy window.
    """

    def __init__(self, parent):
        """
        Initialize PrivPolWindow

        Args:
            parent (object).                The parent window that started the
                                            thread.
        """
        wx.Frame.__init__(self, parent=wx.GetApp().TopWindow,
                          title="DDRescue-GUI - Privacy Policy", size=(400, 310),
                          style=wx.DEFAULT_FRAME_STYLE)

        self.panel = wx.Panel(self)
        self.SetClientSize(wx.Size(400, 310))
        self.parent = parent
        wx.Frame.SetIcon(self, APPICON)

        logger.debug("PrivPolWindow().__init__(): Creating widgets...")
        self.create_widgets()

        logger.debug("PrivPolWindow().__init__(): Setting up sizers...")
        self.setup_sizers()

        logger.debug("PrivPolWindow().__init__(): Binding Events...")
        self.bind_events()

        #Call Layout() on self.panel() to ensure it displays properly.
        self.panel.Layout()

        logger.debug("PrivPolWindow().__init__(): Ready. Waiting for events...")

    def create_widgets(self):
        """
        Create all widgets for PrivPolWindow
        """
        #Make a text box to contain the policy's text.
        self.text_box = wx.TextCtrl(self.panel, -1, "",
                                    style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_WORDWRAP)

        #Populate the text box.
        self.text_box.LoadFile(RESOURCEPATH+"/other/privacypolicy.txt")

        #Scroll the text box back up to the top.
        self.text_box.SetInsertionPoint(0)

        #Make a button to close the dialog.
        self.close_button = wx.Button(self.panel, -1, "Okay")

    def setup_sizers(self):
        """
        Set up sizers for PrivPolWindow
        """
        #Make a boxsizer.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        #Add each object to the main sizer.
        main_sizer.Add(self.text_box, 1, wx.EXPAND|wx.ALL, 10)
        main_sizer.Add(self.close_button, 0, wx.BOTTOM|wx.CENTER, 10)

        #Get the sizer set up for the frame.
        self.panel.SetSizer(main_sizer)
        main_sizer.SetMinSize(wx.Size(400, 310))
        main_sizer.SetSizeHints(self)

    def bind_events(self):
        """
        Bind events so we can close this window.
        """
        self.Bind(wx.EVT_BUTTON, self.on_close, self.close_button)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event=None): #pylint: disable=unused-argument
        """
        Close PrivPolWindow.
        """
        self.Destroy()

#End Privacy Policy Window.
#Begin Finished Window
class FinishedWindow(wx.Frame): #pylint: disable=too-many-instance-attributes,too-many-ancestors
    """
    This is displayed after a recovery is finished/aborted.
    Used to provide the user w/ options to restart the GUI,
    mount the output file, or close the GUI.
    """

    def __init__(self, parent, disk_capacity, recovered_data):
        """
        Initialize FinishedWindow.
        Args:
            parent (object).                The parent window that started the
                                            thread.

            disk_capacity (string).         The capacity (or size) of the output
                                            file/device.

            recovered_data (string).        The amount of data successfully
                                            recovered from the output file/device.
        """
        wx.Frame.__init__(self, wx.GetApp().TopWindow, title="DDRescue-GUI - Finished!",
                          size=(350, 120), style=wx.DEFAULT_FRAME_STYLE)

        self.panel = wx.Panel(self)
        self.SetClientSize(wx.Size(350, 120))
        self.parent = parent

        self.disk_capacity = disk_capacity
        self.recovered_data = recovered_data

        self.output_file_type = None
        self.output_file_mount_point = None
        self.output_file_device_name = None

        wx.Frame.SetIcon(self, APPICON)

        logger.debug("FinishedWindow().__init__(): Creating buttons...")
        self.create_buttons()

        logger.debug("FinishedWindow().__init__(): Creating text...")
        self.create_text()

        logger.debug("FinishedWindow().__init__(): Setting up sizers...")
        self.setup_sizers()

        logger.debug("FinishedWindow().__init__(): Binding events...")
        self.bind_events()

        #Call Layout() on self.panel() to ensure it displays properly.
        self.panel.Layout()

        logger.info("FinishedWindow().__init__(): Ready. Waiting for events...")

    def create_buttons(self):
        """
        Create all buttons for FinishedWindow.
        """
        self.restart_button = wx.Button(self.panel, -1, "Reset")
        self.mount_button = wx.Button(self.panel, -1, "Mount Image/Disk")
        self.browse_button = wx.Button(self.panel, -1, "Open File Viewer")
        self.quit_button = wx.Button(self.panel, -1, "Quit")

        self.browse_button.Disable()

    def create_text(self):
        """
        Create all text for FinishedWindow.
        """
        self.stats_text = wx.StaticText(self.panel, -1, "Successfully recovered "
                                        + self.recovered_data+" out of "+self.disk_capacity+".")

        self.top_text = wx.StaticText(self.panel, -1, "Your recovered data is at:")
        self.path_text = wx.StaticText(self.panel, -1, SETTINGS["OutputFile"])

    def setup_sizers(self):
        """
        Set up all sizers for FinishedWindow.
        """
        #Make a button boxsizer.
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add each object to the button sizer.
        button_sizer.Add(self.restart_button, 4, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
        button_sizer.Add((5, 5), 1)
        button_sizer.Add(self.mount_button, 8, wx.ALIGN_CENTER_VERTICAL)
        button_sizer.Add((5, 5), 1)
        button_sizer.Add(self.quit_button, 4, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)

        #Make a browse button boxsizer.
        browse_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add each object to the browse button sizer.
        browse_button_sizer.Add((5, 5), 1)
        browse_button_sizer.Add(self.browse_button, 0, wx.ALIGN_CENTER_VERTICAL)
        browse_button_sizer.Add((5, 5), 1)

        #Make a boxsizer.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        #Add each object to the main sizer.
        main_sizer.Add(self.stats_text, 1, wx.ALL ^ wx.BOTTOM|wx.CENTER, 10)
        main_sizer.Add(self.top_text, 1, wx.ALL ^ wx.BOTTOM|wx.CENTER, 10)
        main_sizer.Add(self.path_text, 1, wx.ALL ^ wx.BOTTOM|wx.CENTER, 10)
        main_sizer.Add(browse_button_sizer, 0, wx.TOP|wx.BOTTOM|wx.EXPAND, 10)
        main_sizer.Add(button_sizer, 0, wx.BOTTOM|wx.EXPAND, 10)

        #Get the sizer set up for the frame.
        self.panel.SetSizer(main_sizer)
        main_sizer.SetMinSize(wx.Size(350, 120))
        main_sizer.SetSizeHints(self)

    def restart(self, event=None): #pylint: disable=unused-argument
        """
        Close FinishedWindow and call MainWindow().restart() to re-display and reset MainWindow.
        """

        logger.debug("FinishedWindow().restart(): Triggering restart and "
                     "closing FinishedWindow()...")

        wx.CallAfter(self.parent.restart)
        self.Destroy()

    def on_mount(self, event=None): #pylint: disable=unused-argument
        """
        Triggered when mount button is pressed, used to initiate mounting the
        output file/device.
        """
        if self.mount_button.GetLabel() == "Mount Image/Disk":
            #Change some stuff if it worked.
            if MountingTools.Core.mount_output_file():
                self.top_text.SetLabel("Your recovered data is now mounted at:")
                self.path_text.SetLabel(MountingTools.Core.output_file_mountpoint)
                self.mount_button.SetLabel("Unmount Image/Disk")
                self.restart_button.Disable()
                self.quit_button.Disable()
                self.browse_button.Enable()

                dlg = wx.MessageDialog(self.panel, "Your output file is now mounted. Leave "
                                       "DDRescue-GUI open and click unmount when you're finished.",
                                       "DDRescue-GUI - Information",
                                       style=wx.OK | wx.ICON_INFORMATION, pos=wx.DefaultPosition)

                dlg.ShowModal()
                dlg.Destroy()

        else:
            #Change some stuff if it worked.
            if MountingTools.Core.unmount_output_file():
                self.top_text.SetLabel("Your recovered data is at:")
                self.path_text.SetLabel(SETTINGS["OutputFile"])
                self.mount_button.SetLabel("Mount Image/Disk")
                self.restart_button.Enable()
                self.quit_button.Enable()
                self.browse_button.Disable()

        #Call Layout() on self.panel() to ensure it displays properly.
        self.panel.Layout()

        wx.CallAfter(self.parent.update_status_bar, "Finished")

    def on_browse(self, event=None): #pylint: disable=unused-argument
        """
        Open the file viewer and browse the mounted volume.
        """
        logger.info("FinishedWindow().on_browse(): Opening file viewer at "
                    +MountingTools.Core.output_file_mountpoint+"...")

        if LINUX:
            subprocess.Popen("xdg-open "+MountingTools.Core.output_file_mountpoint,
                             shell=True)

        else:
            subprocess.Popen("open "+MountingTools.Core.output_file_mountpoint,
                             shell=True)

    def on_exit(self, event=None): #pylint: disable=unused-argument
        """
        Close FinishedWindow and trigger closure of MainWindow.
        """
        logger.info("FinishedWindow().on_exit(): Closing FinishedWindow() and calling "
                    "self.parent.on_exit()...")

        self.Destroy()
        wx.CallAfter(self.parent.on_exit, just_finished_recovery=True)

    def bind_events(self):
        """
        Bind all events for FinishedWindow.
        """
        self.Bind(wx.EVT_BUTTON, self.restart, self.restart_button)
        self.Bind(wx.EVT_BUTTON, self.on_mount, self.mount_button)
        self.Bind(wx.EVT_BUTTON, self.on_browse, self.browse_button)
        self.Bind(wx.EVT_BUTTON, self.on_exit, self.quit_button)
        self.Bind(wx.EVT_CLOSE, self.on_exit)

#End Finished Window
#Begin Elapsed Time Thread.
class ElapsedTimeThread(threading.Thread):
    """
    Keeps track of elapsed time during a recovery.
    A separate thread is used for this because
    wx.Timer wasn't working on macOS, and the
    BackendThread blocks if ddrescue pauses.
    """

    def __init__(self, parent):
        """
        Initialize and start the thread.

        Args:
            parent (object).                The parent window that started this
                                            window."""
        self.parent = parent

        #This starts a little after ddrescue, so start at 2 seconds.
        self.runtime_secs = 2

        threading.Thread.__init__(self)
        self.start()

    def run(self):
        """
        Main body of the thread, started with self.start().
        """
        while SETTINGS["RecoveringData"]:
            #Elapsed time.
            self.runtime_secs += 1

            #Convert between Seconds, Minutes, Hours, and Days to make the value as
            #understandable as possible.
            if self.runtime_secs <= 60:
                run_time = self.runtime_secs
                unit = " seconds"

            elif self.runtime_secs >= 60 and self.runtime_secs <= 3600:
                run_time = self.runtime_secs//60
                unit = " minutes"

            elif self.runtime_secs > 3600 and self.runtime_secs <= 86400:
                run_time = round(self.runtime_secs/3600, 2)
                unit = " hours"

            elif self.runtime_secs > 86400:
                run_time = round(self.runtime_secs/86400, 2)
                unit = " days"

            #Update the text.
            wx.CallAfter(self.parent.update_time_elapsed, "Time Elapsed: "+unicode(run_time)+unit)

            #Wait for a second.
            time.sleep(1)

#End Elapsed Time Thread
#Begin Backend Thread
class BackendThread(threading.Thread): #pylint: disable=too-many-instance-attributes
    """
    Handles getting input from ddrescue during a recovery,
    and forwards it back to the GUI thread as required.
    """

    def __init__(self, parent):
        """
        Initialize and start the thread.

        Args:
            parent (object).                The parent window that started the
                                            thread."""
        self.parent = parent

        #Set the below values to sensible defaults to prevent errors if we never get
        #any info from ddrescue.
        self.old_status = ""
        self.got_initial_status = False
        self.input_pos = "0 B"
        self.disk_capacity = "An unknown amount of"
        self.disk_capacity_unit = "B"
        self.recovered_data = 0
        self.recovered_data_unit = "B"

        #These don't matter in the same way, so set them to None.
        self.time_since_last_read = None
        self.error_size = None
        self.time_remaining = None
        self.current_read_rate = None
        self.average_read_rate = None
        self.average_read_rate_unit = None
        self.num_errors = None
        self.output_pos = None

        threading.Thread.__init__(self)
        self.start()

    def run(self): #TODO refactor me.
        """
        Main body of the thread, started with self.start().
        """
        logger.debug("MainBackendThread(): Setting up ddrescue tools...")

        #Find suitable functions.
        suitable_functions = DDRescueTools.setup_for_ddrescue_version(SETTINGS["DDRescueVersion"])

        #Define all of these functions here under their correct names.
        for function in suitable_functions:
            vars(self)[function.__name__] = function

        #Prepare to start ddrescue.
        logger.debug("MainBackendThread(): Preparing to start ddrescue...")
        options_list = [SETTINGS["DirectAccess"], SETTINGS["OverwriteOutputFile"],
                        SETTINGS["DiskSize"], SETTINGS["Reverse"], SETTINGS["Preallocate"],
                        SETTINGS["NoSplit"], SETTINGS["BadSectorRetries"], SETTINGS["MaxErrors"],
                        SETTINGS["ClusterSize"], SETTINGS["InputFileBlockSize"],
                        SETTINGS["InputFile"], SETTINGS["OutputFile"], SETTINGS["MapFile"]]

        if LINUX:
            exec_list = ["pkexec", RESOURCEPATH+"/Tools/helpers/runasroot_linux_ddrescue.sh",
                         "ddrescue", "-v"]

        else:
            exec_list = ["sudo", "-SH", RESOURCEPATH+"/ddrescue", "-v"]

        for option in options_list:
            #Handle direct disk access on OS X.
            if LINUX is False and options_list.index(option) == 0 and option != "":
                #If we're recovering from a file, don't enable direct disk access (it won't work).
                if SETTINGS["InputFile"][0:5] != "/dev/":
                    #Make sure "-d" isn't added to the exec_list if this is a file we're reading
                    #from. It doesn't work on macOS.
                    #(continue to next iteration of loop w/o adding).
                    continue

                #Remove InputFile and switch it with a string that uses /dev/rdisk (raw disk)
                #instead of /dev/disk.
                options_list.pop(10)
                options_list.insert(10, "/dev/r" + SETTINGS["InputFile"].split("/dev/")[1])

            elif option != "":
                exec_list.append(option)

        #Start ddrescue.
        logger.debug("MainBackendThread(): Running ddrescue with: '"+' '.join(exec_list)+"'...")

        #Ensure the rest of the program knows we are recovering data.
        SETTINGS["RecoveringData"] = True

        if not LINUX:
            #Pre-auth with the auth dialog if needed.
            CoreTools.start_process(cmd="echo 'Preauthenticating'", privileged=True)

        cmd = subprocess.Popen(exec_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        line = ""
        char = " " #Set this so the while loop executes at least once.

        #Give ddrescue plenty of time to start.
        time.sleep(2)

        #Grab information from ddrescue. (After ddrescue exits, attempt to keep reading chars until
        #the last attempt gave an empty string)
        while cmd.poll() is None or char != "":
            char = cmd.stdout.read(1).decode("utf-8")
            line += char

            #If this is the end of the line, process it, and send the results to the GUI thread.
            if char == "\n":
                tidy_line = line.replace("\n", "").replace("\r", "").replace("\x1b[A", "")

                if tidy_line != "":
                    try:
                        self.process_line(tidy_line)

                    except Exception:
                        #Handle unexpected errors. Can happen once in normal operation on
                        #ddrescue v1.22+. TODO make smarter, don't fill log with these.
                        #TODO suppress 1st error if on new versions.
                        logger.warning("MainBackendThread(): Unexpected error parsing ddrescue's "
                                       "output! Can happen once on newer versions of ddrescue "
                                       "(1.22+) in normal operation. Are you running a "
                                       "newer/older version of ddrescue than we support?")

                #The ¬ is being used to denote where the output box should go up
                #one line before continuing to write. A bit like a carriage return
                #but the other way around.
                wx.CallAfter(self.parent.output_box.update, line.replace("\x1b[A", "¬"))

                #Reset line.
                line = ""

        #Parse any remaining lines afterwards.
        if line != "":
            tidy_line = line.replace("\n", "").replace("\r", "").replace("\x1b[A", "")
            self.process_line(tidy_line)

        #Let the GUI know that we are no longer recovering any data.
        SETTINGS["RecoveringData"] = False

        #Check if we got ddrescue's init status, and if ddrescue exited with a status other
        #than 0. Handle errors in case someone is running DDRescue-GUI on an unsupported version
        #of ddrescue.
        #Prepare values.
        tmp_return_code = int(cmd.returncode)

        if not self.got_initial_status:
            logger.error("MainBackendThread(): We didn't get the initial status before "
                         "ddrescue exited! Something has gone wrong. Telling MainWindow "
                         "and exiting...")

            tmp_result = "NoInitialStatus"

        elif tmp_return_code != 0:
            logger.error("MainBackendThread(): ddrescue exited with exit status "
                         + unicode(cmd.returncode)+"! Something has gone wrong. Telling "
                         "MainWindow and exiting...")

            tmp_result = "BadReturnCode"

        else:
            logger.info("MainBackendThread(): ddrescue finished recovering data. Telling "
                        "MainWindow and exiting...")

            tmp_result = "Success"

        try:
            tmp_disk_capacity = unicode(self.disk_capacity)+" "+self.disk_capacity_unit
            tmp_recovered_data = unicode(int(self.recovered_data))+" "+self.recovered_data_unit

        except Exception:
            logger.error("MainBackendThread(): Unexpected error while trying to process recovery "
                         "information to on_recovery_ended()! Continuing anyway. Are you "
                         "running a newer/older version of ddrescue than we support?")

            tmp_disk_capacity = "Unknown Size"
            tmp_recovered_data = "Unknown Size"

        wx.CallAfter(self.parent.on_recovery_ended, disk_capacity=tmp_disk_capacity,
                     recovered_data=tmp_recovered_data, result=tmp_result,
                     return_code=tmp_return_code)

    def process_line(self, line): #pylint: disable=too-many-statements, too-many-branches
        """
        Process a given line to get ddrescue's current status and recovery information
        and send it to the GUI Thread
        """

        split_line = line.split()

        if split_line[0] == "About":
            #All versions of ddrescue (1.14 - 1.25).

            #Initial status.
            logger.info("MainBackendThread().Processline(): Got Initial Status. "
                        "Setting up the progressbar...")

            self.got_initial_status = True

            #pylint: disable=no-member
            self.disk_capacity, self.disk_capacity_unit = self.get_initial_status(split_line)

            wx.CallAfter(self.parent.set_progress_bar_range, self.disk_capacity)

            #Start time elapsed thread.
            ElapsedTimeThread(self.parent)

        elif split_line[0] == "ipos:" and int(SETTINGS["DDRescueVersion"].split(".")[1]) < 21:
            #Versions 1.14 - 1.20.

            #pylint: disable=no-member
            self.input_pos, self.num_errors, self.average_read_rate, self.average_read_rate_unit \
            = self.get_inputpos_numerrors_averagereadrate(split_line)

            wx.CallAfter(self.parent.update_input_pos, self.input_pos)
            wx.CallAfter(self.parent.update_num_errors, self.num_errors)
            wx.CallAfter(self.parent.update_average_read_rate, unicode(self.average_read_rate)
                         + " "+self.average_read_rate_unit)

        elif split_line[0] == "opos:":
            #Versions 1.14 - 1.20 & 1.21 - 1.25.

            if int(SETTINGS["DDRescueVersion"].split(".")[1]) >= 21:
                #Get average read rate (ddrescue 1.21 - 1.25).
                (self.output_pos, self.average_read_rate, self.average_read_rate_unit) = \
                self.get_outputpos_average_read_rate(split_line) #pylint: disable=no-member

                wx.CallAfter(self.parent.update_average_read_rate, unicode(self.average_read_rate)
                             + " "+self.average_read_rate_unit)

            else:
                #Output Pos and time since last read (1.14 - 1.20).
                (self.output_pos, self.time_since_last_read) = \
                self.get_outputpos_time_since_last_read(split_line) #pylint: disable=no-member

                wx.CallAfter(self.parent.update_time_since_last_read, self.time_since_last_read)

            #Get remaining time on ddrescue 1.20
            if int(SETTINGS["DDRescueVersion"].split(".")[1]) == 20:
                #pylint: disable=no-member
                self.time_remaining = self.get_time_remaining(split_line)
                wx.CallAfter(self.parent.update_time_remaining, self.time_remaining)

            wx.CallAfter(self.parent.update_output_pos, self.output_pos)

        elif split_line[0] == "non-tried:":
            #Unreadable data (ddrescue 1.21 - 1.25).

            #pylint: disable=no-member
            self.error_size = self.get_unreadable_data(split_line)

            wx.CallAfter(self.parent.update_error_size, self.error_size)

        elif split_line[0] in ("time", "percent"): #Time since last read (ddrescue v1.20 - 1.25).
            #pylint: disable=no-member
            self.time_since_last_read = self.get_time_since_last_read(split_line)

            wx.CallAfter(self.parent.update_time_since_last_read, self.time_since_last_read)

        elif split_line[0] == "rescued:" and int(SETTINGS["DDRescueVersion"].split(".")[1]) >= 21:
            #Recovered data and number of errors (ddrescue 1.21 - 1.25).

            #Don't crash if we're reading the initial status from the logfile.
            try:
                #pylint: disable=no-member
                (self.recovered_data, self.recovered_data_unit, self.num_errors) = \
                self.get_recovered_data_num_errors(split_line)

                #Change the unit of measurement of the current amount of recovered data if needed.
                (self.recovered_data, self.recovered_data_unit) = \
                CoreTools.change_units(float(self.recovered_data), self.recovered_data_unit,
                                       self.disk_capacity_unit)

                self.recovered_data = round(self.recovered_data, 3)

                wx.CallAfter(self.parent.update_recovered_data, unicode(self.recovered_data)
                             + " "+self.recovered_data_unit)

                wx.CallAfter(self.parent.update_num_errors, self.num_errors)
                wx.CallAfter(self.parent.update_progress, self.recovered_data, self.disk_capacity)

            except AttributeError:
                pass

        elif ("rescued:" in line and split_line[0] not in ("rescued:", "pct")) or "ipos:" in line:
            #Versions 1.14 - 1.20 & 1.21 - 1.25

            if int(SETTINGS["DDRescueVersion"].split(".")[1]) >= 21:
                status, info = line.split("ipos:")

            else:
                status, info = line.split("rescued:")

            #Status line.
            if status != self.old_status:
                wx.CallAfter(self.parent.update_status_bar, status)
                self.old_status = status

            split_line = info.split()

            if int(SETTINGS["DDRescueVersion"].split(".")[1]) >= 21:
                #pylint: disable=no-member
                self.current_read_rate, self.input_pos = self.get_current_rate_inputpos(split_line)

                wx.CallAfter(self.parent.update_input_pos, self.input_pos)

            else:
                (self.current_read_rate, self.error_size, self.recovered_data,
                 self.recovered_data_unit) = \
                self.get_current_rate_error_size_recovered_data(split_line) #pylint: disable=no-member,line-too-long

                #Change the unit of measurement of the current amount of recovered data if needed.
                (self.recovered_data, self.recovered_data_unit) = \
                CoreTools.change_units(float(self.recovered_data), self.recovered_data_unit,
                                       self.disk_capacity_unit)

                self.recovered_data = round(self.recovered_data, 3)

                #Calculate remaining time if not on ddrescue 1.20.
                if int(SETTINGS["DDRescueVersion"].split(".")[1]) != 20:
                    #pylint: disable=no-member
                    self.time_remaining = self.get_time_remaining(self.average_read_rate,
                                                                  self.average_read_rate_unit,
                                                                  self.disk_capacity,
                                                                  self.disk_capacity_unit,
                                                                  self.recovered_data)

                    wx.CallAfter(self.parent.update_time_remaining, self.time_remaining)

                wx.CallAfter(self.parent.update_error_size, self.error_size)
                wx.CallAfter(self.parent.update_recovered_data, unicode(self.recovered_data)
                             + " "+self.recovered_data_unit)

                wx.CallAfter(self.parent.update_progress, self.recovered_data, self.disk_capacity)

            wx.CallAfter(self.parent.update_current_read_rate, self.current_read_rate)

        elif split_line[0] == "pct" and int(SETTINGS["DDRescueVersion"].split(".")[1]) >= 21:
            #pylint: disable=no-member
            self.time_remaining = self.get_time_remaining(split_line)
            wx.CallAfter(self.parent.update_time_remaining, self.time_remaining)

        elif "pct" not in line:
            #Probably a status line (maybe the initial one).
            status = line

            if status != self.old_status:
                wx.CallAfter(self.parent.update_status_bar, status)
                self.old_status = status

#End Backend thread
if __name__ == "__main__":
    APP = MyApp(False)
    APP.MainLoop()
