#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Tools Package for DDRescue-GUI
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

# pylint: disable=no-member
#
#Reason (no-member): False positives, API changes.

"""
This is the tools package for DDRescue-GUI.
"""

#Do future imports to prepare to support python 3.
#Use unicode strings rather than ASCII strings, as they fix potential problems.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

#Import other modules.
import os
import sys
import subprocess
import threading
import shlex
import logging
import plistlib
import time
import wx

#Make unicode an alias for str in Python 3.
if sys.version_info[0] == 3:
    unicode = str #pylint: disable=redefined-builtin,invalid-name
    str = bytes #pylint: disable=redefined-builtin,invalid-name

    #Plist hack for Python 3.
    plistlib.readPlistFromString = plistlib.loads #pylint: disable=no-member

#Determine if running on Linux or Mac.
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

AUTH_DIALOG_OPEN = False
APPICON = None

#Set up logging.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#Begin Mac Authentication Window.
class AuthWindow(wx.Frame): #pylint: disable=too-many-instance-attributes
    """
    A simple authentication dialog that is used when elevated privileges are required.
    Until version 2.0.0, this was used to start the GUI, but since that release, privileges
    are only escalated when required to improve security.

    This is used to pre-authenticate on macOS if needed, before running a privileged
    task with sudo.
    """

    def __init__(self):
        """Inititalize AuthWindow"""
        wx.Frame.__init__(self, None, title="DDRescue-GUI - Authenticate", size=(600, 400),
                          style=(wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
                          ^ (wx.RESIZE_BORDER | wx.MINIMIZE_BOX))

        self.panel = wx.Panel(self)

        #Set the frame's icon.
        global APPICON
        APPICON = wx.Icon(RESOURCEPATH+"/images/Logo.png", wx.BITMAP_TYPE_PNG)
        wx.Frame.SetIcon(self, APPICON)

        self.create_text()
        self.create_buttons()
        self.create_other_widgets()
        self.setup_sizers()
        self.bind_events()

        #Call Layout() on self.panel() to ensure it displays properly.
        self.panel.Layout()

        #Give the password field focus, so the user can start typing immediately.
        self.password_field.SetFocus()

    def create_text(self):
        """Create all text for AuthenticationWindow"""
        self.title_text = wx.StaticText(self.panel, -1,
                                        "DDRescue-GUI requires authentication.")
        self.body_text = wx.StaticText(self.panel, -1, "DDRescue-GUI requires authentication "
                                       + "to\nperform privileged actions.")

        self.password_text = wx.StaticText(self.panel, -1, "Password:")

        bold_font = self.title_text.GetFont()
        bold_font.SetWeight(wx.BOLD)
        self.password_text.SetFont(bold_font)

    def create_buttons(self):
        """Create all buttons for AuthenticationWindow"""
        self.auth_button = wx.Button(self.panel, -1, "Authenticate")

    def create_other_widgets(self):
        """Create all other widgets for AuthenticationWindow"""
        #Create the image.
        img = wx.Image(RESOURCEPATH+"/images/Logo.png", wx.BITMAP_TYPE_PNG)
        self.program_logo = wx.StaticBitmap(self.panel, -1, wx.Bitmap(img))

        #Create the password field.
        self.password_field = wx.TextCtrl(self.panel, -1, "",
                                          style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)

        self.password_field.SetBackgroundColour((255, 255, 255))

        #Create the throbber.
        self.busy = wx.adv.Animation(RESOURCEPATH+"/images/Throbber.gif")
        self.green_pulse = wx.adv.Animation(RESOURCEPATH+"/images/GreenPulse.gif")
        self.red_pulse = wx.adv.Animation(RESOURCEPATH+"/images/RedPulse.gif")

        self.throbber = wx.adv.AnimationCtrl(self.panel, -1, self.green_pulse)
        self.throbber.SetInactiveBitmap(wx.Bitmap(RESOURCEPATH+"/images/ThrobberRest.png",
                                                  wx.BITMAP_TYPE_PNG))

        self.throbber.SetClientSize(wx.Size(30, 30))

    def setup_sizers(self):
        """Setup sizers for AuthWindow"""
        #Make the main boxsizer.
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        #Make the top sizer.
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Make the top text sizer.
        top_text_sizer = wx.BoxSizer(wx.VERTICAL)

        #Add items to the top text sizer.
        top_text_sizer.Add(self.title_text, 0, wx.ALIGN_LEFT|wx.EXPAND)
        top_text_sizer.Add(self.body_text, 0, wx.TOP|wx.ALIGN_LEFT|wx.EXPAND, 10)

        #Add items to the top sizer.
        top_sizer.Add(self.program_logo, 0, wx.LEFT|wx.ALIGN_CENTER, 18)
        top_sizer.Add(top_text_sizer, 1, wx.LEFT|wx.ALIGN_CENTER, 29)

        #Make the password sizer.
        password_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the password sizer.
        password_sizer.Add(self.password_text, 0, wx.LEFT|wx.ALIGN_CENTER, 12)
        password_sizer.Add(self.password_field, 1, wx.LEFT|wx.ALIGN_CENTER, 22)
        password_sizer.Add(self.throbber, 0, wx.LEFT|wx.ALIGN_CENTER|wx.FIXED_MINSIZE, 10)

        #Make the button sizer.
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #Add items to the button sizer.
        button_sizer.Add(self.auth_button, 1, wx.LEFT|wx.ALIGN_CENTER|wx.EXPAND, 10)

        #Add items to the main sizer.
        main_sizer.Add(top_sizer, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 10)
        main_sizer.Add(password_sizer, 0, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER|wx.EXPAND, 10)
        main_sizer.Add(button_sizer, 1, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER|wx.EXPAND, 10)

        #Get the sizer set up for the frame.
        self.panel.SetSizer(main_sizer)

        #Call Layout() on self.panel() to ensure it displays properly.
        self.panel.Layout()

        main_sizer.SetSizeHints(self)

    def bind_events(self):
        """Bind all events for AuthenticationWindow"""
        self.Bind(wx.EVT_TEXT_ENTER, self.on_auth_attempt, self.password_field)
        self.Bind(wx.EVT_BUTTON, self.on_auth_attempt, self.auth_button)

    def on_auth_attempt(self, event=None): #pylint: disable=unused-argument
        """
        Check the password is correct,
        then either warn the user or call self.start_ddrescuegui().
        """

        #Disable the auth button (stops you from trying twice in quick succession).
        self.auth_button.Disable()

        #Check the password is right.
        password = self.password_field.GetLineText(0)
        cmd = subprocess.Popen("LC_ALL=C sudo -S echo 'Authentication Succeeded'",
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)

        #Send the password to sudo through stdin,
        #to avoid showing the user's password in the system/activity monitor.
        cmd.stdin.write(password.encode()+b"\n")
        cmd.stdin.close()

        self.throbber.SetAnimation(self.busy)
        self.throbber.Play()

        while cmd.poll() is None:
            #wx.GetApp().Yield()
            time.sleep(0.04)

        output = cmd.stdout.read().decode("utf-8")

        if "Authentication Succeeded" in output:
            #Set the password field colour to green and disable the cancel button.
            self.password_field.SetBackgroundColour((192, 255, 192))
            self.password_field.SetValue("ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789!£$%^&*()_+")

            #Play the green pulse for one second.
            self.throbber.SetAnimation(self.green_pulse)
            self.throbber.Play()
            wx.CallLater(1000, self.throbber.Stop)
            wx.CallLater(1100, self.on_exit)

        else:
            #Re-enable auth button.
            self.auth_button.Enable()

            #Shake the window
            x_pos, y_pos = self.GetPosition()
            count = 0

            while count <= 6:
                if count % 2 == 0:
                    x_pos -= 10

                else:
                    x_pos += 10

                time.sleep(0.02)
                self.SetPosition((x_pos, y_pos))
                #wx.GetApp().Yield()
                count += 1

            #Set the password field colour to pink, and select its text.
            self.password_field.SetBackgroundColour((255, 192, 192))
            self.password_field.SetSelection(0, -1)
            self.password_field.SetFocus()

            #Play the red pulse for one second.
            self.throbber.SetAnimation(self.red_pulse)
            self.throbber.Play()
            wx.CallLater(1000, self.throbber.Stop)

    def test_auth(): #pylint: disable=no-method-argument
        """
        Check if we have cached authentication
        If so, return True.
        Otherwise return False.
        """

        #Check the password is right.
        cmd = subprocess.Popen("LC_ALL=C sudo -S echo 'Authentication Succeeded'",
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)

        #Send the password to sudo through stdin,
        #to avoid showing the user's password in the system/activity monitor.
        cmd.stdin.close()

        while cmd.poll() is None:
            time.sleep(0.04)

        output = cmd.stdout.read().decode("utf-8")

        return "Authentication Succeeded" in output

    def run(): #pylint: disable=no-method-argument
        """
        Preauthenticates macOS users with the auth dialog.
        """

        global AUTH_DIALOG_OPEN

        #Use cached credentials rather than open the auth window if possible.
        if AuthWindow.test_auth():
            AUTH_DIALOG_OPEN = False
            return

        AUTH_DIALOG_OPEN = True

        AuthWindow().Show()

    def on_exit(self, event=None): #pylint: disable=unused-argument
        """Close AuthWindow() and exit"""
        global AUTH_DIALOG_OPEN
        AUTH_DIALOG_OPEN = False

        self.Destroy()

#End Mac Authentication Window.

def get_helper(cmd):
    """Figure out which helper script to use."""
    helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux.sh"

    if "run_getdevinfo.py" in cmd:
        helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux_getdevinfo.sh"

    elif "umount" in cmd or "kpartx -d" in cmd:
        helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux_umount.sh"

    elif ("mount" in cmd or "kpartx -l" in cmd or "kpartx -a" in cmd or "lsblk" in cmd
          or "partprobe" in cmd):
        #Note: These are only used in the process of mounting files.
        helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux_mount.sh"

    elif "ddrescue" in cmd and "killall" not in cmd:
        helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux_ddrescue.sh"

    else:
        helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux.sh"

    return "pkexec "+helper

def start_process(cmd, return_output=False, privileged=False):
    """Start a given process, and return output and return value if needed"""
    #Save the command as it was passed, in case we need
    #to call recursively (pkexec auth failure/dismissal).
    origcmd = cmd

    #If this is to be a privileged process, add the helper script to the cmdline.
    if privileged:
        if LINUX:
            helper = get_helper(cmd)

            cmd = helper+" "+cmd

        else:
            #Pre-authenticate with the auth dialog. Not py2 compatible, but only used
            #on OS X builds, which are py3-only anyway.
            if threading.current_thread() == threading.main_thread():
                AuthWindow.run()

            else:
                wx.CallAfter(AuthWindow.run)

                #Prevent a race condition.
                global AUTH_DIALOG_OPEN
                AUTH_DIALOG_OPEN = True

            while AUTH_DIALOG_OPEN:
                wx.GetApp().Yield()
                time.sleep(0.04)

            #Set up the environemt here - sudo will clear it if we do it the
            #wrong way.
            if "/Tools/run_getdevinfo.py" in cmd:
                #Fix import paths on macOS.
                #This is necessary because the support for running extra python processes
                #in py2app is poor.
                #TODO: Will probably need to change w/ new major version of Py 3 eg 3.7, 3.8.
                environ = 'LC_ALL="C" PYTHONHOME="'+RESOURCEPATH+'" PYTHONPATH="' \
                          + RESOURCEPATH+'/lib/python37.zip:' \
                          + RESOURCEPATH+'/lib/python3.7:' \
                          + RESOURCEPATH+'/lib/python3.7/lib-dynload:' \
                          + RESOURCEPATH+'/lib/python3.7/site-packages.zip:' \
                          + RESOURCEPATH+'/lib/python3.7/site-packages" '

            else:
                environ = 'LC_ALL="C" '

            cmd = "sudo -SH "+environ+cmd

    environ = dict(os.environ, LC_ALL="C") #pylint: disable=redefined-variable-type

    cmd = shlex.split(cmd)

    logger.debug("start_process(): Starting process: "+' '.join(cmd))
    runcmd = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, env=environ,
                              shell=False)

    #Save the output, and runcmd.returncode,
    #as they tend to reset fairly quickly. Handle unicode properly.
    output = read(runcmd)

    retval = int(runcmd.returncode)

    #Log this info in a debug message.
    logger.debug("start_process(): Process: "+' '.join(cmd)+": Return Value: "
                 +unicode(retval)+", output: \"\n\n"+'\n'.join(output)+"\"\n")

    if privileged and (retval == 126 or retval == 127):
        #Try again, auth dismissed / bad password 3 times.
        #A lot of recursion is allowed (~1000 times), so this shouldn't be a problem.
        logger.debug("start_process(): Bad auth or dismissed by user. Trying again...")
        return start_process(cmd=origcmd, return_output=return_output, privileged=privileged)

    if not return_output:
        #Return the return code back to whichever function ran this process, so it handles errors.
        return retval

    else:
        #Return the return code, as well as the output.
        return retval, '\n'.join(output)

def read(cmd, testing=False): #pylint: disable=redefined-variable-type
    """
    Read the cmd's output char by char, but do as little processing as
    possible to improve startup performance
    """

    #Get ready to run the command(s).
    #Read up to 100 empty "" characters after the process finishes to
    #make sure we get all the output.
    counter = 0
    line = str(b"")
    line_list = []

    while cmd.poll() is None or counter < 100:
        char = cmd.stdout.read(1)

        if char == b"":
            counter += 1
            continue

        line += char

        if char in (b"\n", b"\r"):
            #Interpret as Unicode and remove "NULL" characters.
            line = line.decode("UTF-8", errors="ignore").replace("\x00", "")

            if testing:
                line_list.append(line)

            else:
                line_list.append(line.replace("\n", "").replace("\r", ""))

            #Reset line.
            line = str(b"")

    #Catch it if there's not a newline at the end.
    if line != b"":
        #Interpret as Unicode and remove "NULL" characters.
        line = line.decode("UTF-8", errors="ignore").replace("\x00", "")

        if testing:
            line_list.append(line)

        else:
            line_list.append(line.replace("\n", "").replace("\r", ""))

    return line_list

def determine_ddrescue_version():
    """
    Used to determine the version of ddrescue installed on the system,
    or (for macOS) bundled with the GUI.

    Handles -pre and -rc versions too, by stripping that information
    from the version string and warning the user.
    """

    #Use correct command.
    if LINUX:
        cmd = "ddrescue --version"

    else:
        cmd = RESOURCEPATH+"/ddrescue --version"

    ddrescue_version = \
    start_process(cmd=cmd, return_output=True)[1].split("\n")[0].split(" ")[-1]

    logger.info("ddrescue version "+ddrescue_version+"...")

    #Remove the -rc and -pre flags if they exist.
    #But note if we are running a prerelease version so we can warn the user.
    prerelease = False

    if "-rc" in ddrescue_version:
        prerelease = True
        ddrescue_version = ddrescue_version.split("-rc")[0]

    elif "-pre" in ddrescue_version:
        prerelease = True
        ddrescue_version = ddrescue_version.split("-pre")[0]

    #Ignore any monitor changes. eg: treat 1.19.5 as 1.19 - strip anything after that off.
    ddrescue_version = '.'.join(ddrescue_version.split(".")[:2])

    #Warn if not on a supported version.
    if ddrescue_version not in ("1.14", "1.15", "1.16", "1.17", "1.18", "1.18.1", "1.19", "1.20",
                                "1.21", "1.22", "1.23", "1.24"):
        logger.warning("Unsupported ddrescue version "+ddrescue_version+"! "
                       "Please upgrade DDRescue-GUI if possible.")

        dlg = wx.MessageDialog(None, "You are using an unsupported version of ddrescue! "
                               "You are strongly advised to upgrade "
                               "DDRescue-GUI if there is an update available. "
                               "You can use this GUI anyway, but you may find "
                               "there are formatting or other issues when "
                               "performing your recovery.",
                               'DDRescue-GUI - Unsupported ddrescue version!',
                               wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    #Warn if on a prerelease version.
    if prerelease:
        logger.warning("Running on a prerelease version of ddrescue! "
                       "This may cause bugs/errors in the GUI, and may "
                       "result in an unsuccessful recovery.")

        dlg = wx.MessageDialog(None, "You are using a prerelease version of ddrescue! "
                               "You can contnue anyway, but you may find "
                               "there are formatting or other issues when "
                               "performing your recovery, or that your recovery "
                               "is unsuccessful.",
                               'DDRescue-GUI - Prerelease ddrescue version!',
                               wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    return ddrescue_version

def create_unique_key(dictionary, data, length):
    """
    Create a unqiue dictionary key of length for dictionary dictionary for the item data.
    The unique key is created by adding a number on the the end of data,
    while keeping it at the correct length.
    The key will also start with '...'.
    """

    #Only add numbers to the key if needed.
    if "..."+data[-length:] in dictionary.keys():
        #digit to add to the end of the key.
        digit = 0
        key = data

        while True:
            #Add a digit to the end of the key to get a new key, repeat until the key is unique.
            digit_length = len(unicode(digit))

            if key[-digit_length:] == digit and key[-digit_length-1] == "~":
                #Remove the old non-unique digit and underscore at the end.
                key = key[0:-digit_length-1]

            #Add 1 to the digit.
            digit += 1

            key = key+unicode(digit)
            key = key[-length:]

            if "..."+key not in dictionary.keys():
                #Yay! Unique!
                key = "..."+key

    else:
        key = data[-length:]
        key = "..."+key

    #Remove '...' if key is shorter than length+3 chars (to account for...).
    if len(key) < length+3:
        key = key[3:]

    return key

def send_notification(msg):
    """Send a notification, created to reduce clutter in the rest of the code."""
    if LINUX:
        #Use notify-send. *** Sometimes doesn't work as root. Find uid of logged-in user? ***
        start_process(cmd="notify-send 'DDRescue-GUI' '"+msg
                      +"' -i /usr/share/pixmaps/ddrescue-gui.png", return_output=False)

    else:
        #Use Terminal-notifier.
        start_process(cmd=RESOURCEPATH
                      +"""/other/terminal-notifier.app/Contents/MacOS/terminal-notifier """ \
                      +"""-title "DDRescue-GUI" -message \""""+msg+"""\" """ \
                      +"""-sender org.pythonmac.unspecified.DDRescue-GUI """ \
                      +"""-group \"DDRescue-GUI\"""",
                      return_output=False)

def determine_output_file_type(SETTINGS, disk_info): #pylint: disable=invalid-name
    """Determines output File Type (partition or Device)"""
    if SETTINGS["InputFile"] in disk_info:
		#Read from disk_info if possible (OutputFile type = InputFile type)
        output_file_type = disk_info[SETTINGS["InputFile"]]["Type"]
        retval = 0
        output = ""

        if output_file_type == "Device":
            if LINUX:
                retval, output = start_process(cmd="kpartx -l "+SETTINGS["OutputFile"],
                                               return_output=True, privileged=True)
                output = output.split("\n")

            else:
                retval, output = mac_run_hdiutil(options="imageinfo "+SETTINGS["OutputFile"]
                                                 +" -plist")

    else:
        if LINUX:
            #If list of partitions is empty (or 1 partition), we have a partition.
            retval, output = start_process(cmd="kpartx -l "+SETTINGS["OutputFile"],
                                           return_output=True, privileged=True)
            output = output.split("\n")

        else:
            retval, output = mac_run_hdiutil(options="imageinfo "+SETTINGS["OutputFile"]
                                             +" -plist")

        if output == [""] or len(output) == 1 or "whole disk" in output:
            output_file_type = "partition"

        else:
            output_file_type = "Device"

    if not LINUX and output != "":
        #Parse the plist (Property List).
        output = plistlib.readPlistFromString(output.encode())

    return output_file_type, retval, output

def mac_get_device_name_mount_point(output):
    """
    Get the device name and mount point of an output file,
    given output from hdiutil mount -plist
    """

    #Parse the plist (Property List).
    try:
        hdiutil_output = plistlib.readPlistFromString(output.encode())

    except UnicodeDecodeError:
        return None, None, "UnicodeError"

    #Find the disk and get the mountpoint.
    if len(hdiutil_output["system-entities"]) > 1:
        mounted_disk = hdiutil_output["system-entities"][1]

    else:
        mounted_disk = hdiutil_output["system-entities"][0]

    return mounted_disk["dev-entry"], mounted_disk["mount-point"], True

def mac_run_hdiutil(options):
    """
    Runs hdiutil on behalf of the rest of the program when called.
    Tries to handle and fix hdiutil errors if they occur.
    """

    retval, output = start_process(cmd="hdiutil "+options, return_output=True, privileged=True)

    #Handle this common error - image in use.
    if "Resource temporarily unavailable" in output or retval != 0:
        logger.warning("mac_run_hdiutil(): Attempting to fix hdiutil resource error...")
        #Fix by detaching all disks - certain disks eg system disk will fail, but it should fix
        #our problem. On OS X >= 10.11 can check for "(disk image)", but cos we support 10.9 &
        #10.10, we have to just detach all possible disks and ignore failures. No need for another
        #try-except cos start_process doesn't throw errors.
        for line in start_process(cmd="diskutil list", return_output=True)[1].split("\n"):
            try:
                if line.split()[0].split("/")[1] == "dev":
                    #This is a line with a device name on it.
                    logger.warning("mac_run_hdiutil(): Attempting to detach "
                                   + line.split()[0]+"...")

                    start_process(cmd="hdiutil detach "+line.split()[0], privileged=True)

            except IndexError:
                pass

        #Try again.
        retval, output = start_process(cmd="hdiutil "+options, return_output=True, privileged=True)

    return retval, output

def is_mounted(partition, mount_point=None):
    """
    Checks if the given partition is mounted.
    partition is the given partition to check.
    If mount_point is specified, check if the partition is mounted there,
    rather than just if it's mounted.
    Return boolean True/False.
    """

    if mount_point is None:
        logger.debug("is_mounted(): Checking if "+partition+" is mounted...")
        mount_info = start_process("mount", return_output=True)[1]

        disk_is_mounted = False

        #OS X fix: Handle paths with /tmp in them, as paths with /private/tmp.
        if not LINUX and "/tmp" in partition:
            partition = partition.replace("/tmp", "/private/tmp")

        #LINUX fix: Accept any mountpoint when called with just one argument.
        for line in mount_info.split("\n"):
            if len(line) != 0:
                if line.split()[0] == partition or line.split()[2] == partition:
                    disk_is_mounted = True
                    break

    else:
        #Check where it's mounted to.
        logger.debug("is_mounted(): Checking if "+partition+" is mounted at "+mount_point+"...")

        disk_is_mounted = False

        #OS X fix: Handle paths with /tmp in them, as paths with /private/tmp.
        if not LINUX and "/tmp" in mount_point:
            mount_point = mount_point.replace("/tmp", "/private/tmp")

        if get_mount_point(partition) == mount_point:
            disk_is_mounted = True

    if disk_is_mounted:
        logger.debug("is_mounted(): It is. Returning True...")
        return True

    else:
        logger.debug("is_mounted(): It isn't. Returning False...")
        return False

def get_mount_point(partition):
    """Returns the mountpoint of the given partition, if any.
    Otherwise, return None"""
    logger.info("get_mount_point(): Trying to get mount point of partition "+partition+"...")

    mount_info = start_process("mount", return_output=True)[1]
    mount_point = None

    for line in mount_info.split("\n"):
        split_line = line.split()

        if len(split_line) != 0:
            if partition == split_line[0]:
                mount_point = split_line[2]
                break

    if mount_point != None:
        logger.info("get_mount_point(): Found it! mount_point is "+mount_point+"...")

    else:
        logger.info("get_mount_point(): Didn't find it...")

    return mount_point

def mount_disk(partition, mount_point, options=""):
    """Mounts the given partition.
    partition is the partition to mount.
    mount_point is where you want to mount the partition.
    options is non-mandatory and contains whatever options you want to pass to the mount command.
    The default value for options is an empty string.
    """
    if options != "":
        logger.info("mount_disk(): Preparing to mount "+partition+" at "+mount_point
                    +" with extra options "+options+"...")

    else:
        logger.info("mount_disk(): Preparing to mount "+partition+" at "+mount_point
                    +" with no extra options...")

    mount_info = start_process("mount", return_output=True)[1]

    #There is a partition mounted here. Check if it's ours.
    if mount_point == get_mount_point(partition):
        #The correct partition is already mounted here.
        logger.debug("mount_disk(): partition: "+partition+" was already mounted at: "
                     +mount_point+". Continuing...")
        return 0

    elif mount_point in mount_info:
        #Something else is in the way. Unmount that partition, and continue.
        logger.warning("mount_disk(): Unmounting filesystem in the way at "+mount_point+"...")
        if unmount_disk(mount_point) != 0:
            logger.error("mount_disk(): Couldn't unmount "+mount_point
                         +", preventing the mounting of "+partition+"! Skipping mount attempt.")
            return False

    #Create the dir if needed.
    if os.path.isdir(mount_point) is False:
        start_process("mkdir -p "+mount_point, privileged=True)

    #Mount the device to the mount point.
    #Use diskutil on OS X.
    if LINUX:
        retval = start_process("mount "+options+" "+partition+" "+mount_point, privileged=True)

    else:
        retval = start_process("diskutil mount "+options+" "+" -mountPoint "
                               +mount_point+" "+partition, privileged=True)

    if retval == 0:
        logger.debug("mount_disk(): Successfully mounted partition!")

    else:
        logger.warning("mount_disk(): Failed to mount partition!")

    return retval

def unmount_disk(disk):
    """Unmount the given disk"""
    logger.debug("unmount_disk(): Checking if "+disk+" is mounted...")

    #Check if it is mounted.
    if not is_mounted(disk):
        #The disk isn't mounted.
        #Set retval to 0 and log this.
        retval = 0
        logger.info("unmount_disk(): "+disk+" was not mounted. Continuing...")

    else:
        #The disk is mounted.
        logger.debug("unmount_disk(): Unmounting "+disk+"...")

        #Unmount it.
        if LINUX:
            retval = start_process(cmd="umount "+disk, return_output=False, privileged=True)

        else:
            retval = start_process(cmd="diskutil umount "+disk, return_output=False, privileged=True)

        #Check that this worked okay.
        if retval != 0:
            #It didn't, for some strange reason.
            logger.warning("unmount_disk(): Unmounting "+disk+": Failed!")

        else:
            logger.info("unmount_disk(): Unmounting "+disk+": Success!")

    #Return the return value
    return retval

def is_partition(disk, disk_info):
    """Check if the given disk is a partition"""
    logger.debug("is_partition(): Checking if disk: "+disk+" is a partition...")

    if LINUX:
        result = (disk[0:7] not in ["/dev/sr", "/dev/fd"] and disk[-1].isdigit()
                  and disk[0:8] in disk_info.keys())

    else:
        result = ("s" in disk.split("disk")[1])

    logger.info("is_partition(): result: "+unicode(result)+"...")

    return result

def emergency_exit(msg):
    """Handle emergency exits. Warn the user, log, and exit to terminal with the given message"""
    logger.critical("CoreEmergencyExit(): Emergency exit has been triggered! "
                    +"Giving user message dialog and saving the logfile...")
    logger.critical("CoreEmergencyExit(): The error is: "+msg)

    #Warn the user.
    dialog = wx.MessageDialog(None, "Emergency exit triggered.\n\n"+msg
                              +"\n\nYou'll now be asked for a location to save the log file."
                              +"\nIf you email me at hamishmb@live.co.uk with the contents of "
                              +"that file I'll be happy to help you fix this problem."
                              , "DDRescue-GUI - Emergency Exit!", wx.OK | wx.ICON_ERROR)
    dialog.ShowModal()
    dialog.Destroy()

    #Shut down the logger.
    logging.shutdown()

    #Save the log file.
    while True:
        dialog = wx.FileDialog(None, "Enter File Name", defaultDir="/home", style=wx.SAVE)

        #Change the default dir on OS X.
        if not LINUX:
            dialog.SetDirectory("/Users")

        if dialog.ShowModal() == wx.ID_OK:
            log_file = dialog.GetPath()
            break

        else:
            #Warn the user.
            dialog = wx.MessageDialog(None, "Please enter a file name.",
                                      "DDRescue-GUI - Emergency Exit!", wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()

    start_process("mv -v /tmp/ddrescue-gui.log "+log_file)

    #Exit.
    dialog = wx.MessageDialog(None, "Done. DDRescue-GUI will now exit.",
                              "DDRescue-GUI - Emergency Exit!", wx.OK | wx.ICON_INFORMATION)
    dialog.ShowModal()
    dialog.Destroy()

    wx.Exit()
    sys.exit(msg)
