#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# BackendTools test functions for DDRescue-GUI
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
If you're wondering why this is here, it's so that there are some known good/sane
functions to aid testing the ones in BackendTools.
"""

#Do other imports.
import subprocess
import threading
import time
import os
import shlex
import sys
import wx

#Determine if running on LINUX or Mac.
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

#Begin Mac Authentication Window.
class AuthWindow(wx.Frame): #pylint: disable=too-many-ancestors,too-many-instance-attributes
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
        """
        Create all text items for AuthenticationWindow.
        """

        self.title_text = wx.StaticText(self.panel, -1,
                                        "DDRescue-GUI requires authentication.")
        self.body_text = wx.StaticText(self.panel, -1, "DDRescue-GUI requires authentication "
                                       + "to\nperform privileged actions.")

        self.password_text = wx.StaticText(self.panel, -1, "Password:")

        bold_font = self.title_text.GetFont()
        bold_font.SetWeight(wx.BOLD)
        self.password_text.SetFont(bold_font)

    def create_buttons(self):
        """
        Create all buttons for AuthenticationWindow
        """
        self.auth_button = wx.Button(self.panel, -1, "Authenticate")

    def create_other_widgets(self):
        """
        Create all other widgets for AuthenticationWindow
        """
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
        """
        Setup sizers for AuthWindow
        """
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
        """
        Bind all events for AuthenticationWindow
        """
        self.Bind(wx.EVT_TEXT_ENTER, self.on_auth_attempt, self.password_field)
        self.Bind(wx.EVT_BUTTON, self.on_auth_attempt, self.auth_button)

    def on_auth_attempt(self, event=None): #pylint: disable=unused-argument
        """
        Check the password is correct. If not, then either warn the user to
        try again. If so, exit as all we need to do is pre-authenticate on
        macOS.

        Kwargs:
            event.      The event object passed by wxpython (optional).
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
        Check if we have cached authentication.

        Returns:
            bool.           True = We have cached authentication.
                            False = We don't.
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
        Preauthenticates macOS users with the auth dialog. If we are already
        pre-authenticated, just return immediately.
        """

        global AUTH_DIALOG_OPEN

        #Use cached credentials rather than open the auth window if possible.
        if AuthWindow.test_auth():
            AUTH_DIALOG_OPEN = False
            return

        AUTH_DIALOG_OPEN = True

        AuthWindow().Show()

    def on_exit(self, event=None): #pylint: disable=unused-argument
        """
        Close AuthWindow() and exit
        """
        global AUTH_DIALOG_OPEN
        AUTH_DIALOG_OPEN = False

        self.Destroy()

#End Mac Authentication Window.

def get_helper(cmd):
    """
    Figure out which helper script to use for this command.

    Args:
        cmd (string).           The command(s) about to be run.

    Returns:
        string.                 "pkexec" + <the helper script needed>
                                + the command(s) to run.
    """
    helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux.sh"

    if "run_getdevinfo.py" in cmd:
        helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux_getdevinfo.sh"

    elif "umount" in cmd or "kpartx -d" in cmd:
        helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux_umount.sh"

    elif ("mount" in cmd or "kpartx -l" in cmd or "kpartx -a" in cmd or "lsblk" in cmd
          or "partprobe" in cmd):
        #Note: These are only used in the process of mounting files.
        helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux_mount.sh"

    elif " ddrescue " in cmd and "killall" not in cmd:
        helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux_ddrescue.sh"

    else:
        helper = "/usr/share/ddrescue-gui/Tools/helpers/runasroot_linux.sh"

    return "pkexec "+helper

def start_process(cmd, return_output=False, privileged=False):
    """
    Start a given process, and return the output and return value if needed.

    Args:
        cmd (string).               The command(s) to run.

    Kwargs:
        return_output[=False]       Whether to return the output or not. If not
                                    specified, the default is False.

        privileged[=False]          Whether to execute the command(s) with
                                    elevated privileges or not. If not specified
                                    the default is False.

    Returns:
        May return multiple types:

        int.                    If return_output is not specified or set to
                                False, return the return value of the command(s).

        tuple(int, string).     Otherwise, return a tuple with the return value,
                                and then a string with new lines delimited by
                                newline characters.

    """
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

            #Make sure the throbber plays properly and the window is responsive.
            while AUTH_DIALOG_OPEN:
                wx.GetApp().Yield()
                time.sleep(0.04)

            #Set up the environemt here - sudo will clear it if we do it the
            #wrong way.
            if "/Tools/run_getdevinfo.py" in cmd:
                #Fix import paths on macOS.
                #This is necessary because the support for running extra python processes
                #in py2app is poor.
                major = sys.version_info[0]
                minor = sys.version_info[1]

                environ = 'LC_ALL="C" PYTHONHOME="'+RESOURCEPATH+'" PYTHONPATH="' \
                          + RESOURCEPATH+'/lib/python'+str(major)+str(minor)+'.zip:' \
                          + RESOURCEPATH+'/lib/python'+str(major)+str(minor)+':' \
                          + RESOURCEPATH+'/lib/python'+str(major)+str(minor)+'/lib-dynload:' \
                          + RESOURCEPATH+'/lib/python'+str(major)+str(minor)+'/site-packages.zip:' \
                          + RESOURCEPATH+'/lib/python'+str(major)+str(minor)+'/site-packages" '

            else:
                environ = 'LC_ALL="C" '

            cmd = "sudo -SH "+environ+cmd

    environ = dict(os.environ, LC_ALL="C")

    cmd = shlex.split(cmd)

    runcmd = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, env=environ,
                              shell=False)

    #Save the output, and runcmd.returncode,
    #as they tend to reset fairly quickly. Handle unicode properly.
    output = read(runcmd)

    retval = int(runcmd.returncode)

    if privileged and (retval == 126 or retval == 127):
        #Try again, auth dismissed / bad password 3 times.
        #A lot of recursion is allowed (~1000 times), so this shouldn't be a problem.
        return start_process(cmd=origcmd, return_output=return_output, privileged=privileged)

    if not return_output:
        #Return the return code back to whichever function ran this process, so it handles errors.
        return retval

    else:
        #Return the return code, as well as the output.
        return retval, '\n'.join(output)

def read(cmd, testing=False):
    """
    Read the cmd's output character by character. Also make sure everything is
    converted to unicode. Break lines by the newline and
    (carriage return) characters. Also handle null characters by
    removing them from the output.

    Args:
        cmd.            The subprocess object that represents the command.

    Kwargs:
        testing[=False].        Used during unit tests, disables some of the
                                cleanup done to the output. **Do not use in
                                production.**

    Returns:
        list.                   A list where each line in the (cleaned up)
                                output is a new item in the list.

    """

    #Get ready to run the command(s).
    #Read up to 100 empty "" characters after the process finishes to
    #make sure we get all the output.
    counter = 0
    line = bytes(b"")
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
            line = bytes(b"")

    #Catch it if there's not a newline at the end.
    if line != b"":
        #Interpret as Unicode and remove "NULL" characters.
        line = line.decode("UTF-8", errors="ignore").replace("\x00", "")

        if testing:
            line_list.append(line)

        else:
            line_list.append(line.replace("\n", "").replace("\r", ""))

    return line_list

def is_mounted(partition, mount_point=None):
    """Checks if the given partition is mounted.
    partition is the given partition to check.
    If mount_point is specified, check if the partition is mounted there,
    rather than just if it's mounted.

    Return boolean True/False.
    """

    if mount_point is None:
        mount_info = start_process("mount", return_output=True)[1]

        mounted = False

        #OS X fix: Handle paths with /tmp in them, as paths with /private/tmp.
        if not LINUX and "/tmp" in partition:
            partition = partition.replace("/tmp", "/private/tmp")

        #LINUX fix: Accept any mount_point when called with just one argument.
        for line in mount_info.split("\n"):
            if len(line) != 0:
                if line.split()[0] == partition or line.split()[2] == partition:
                    mounted = True
                    break

    else:
        #Check where it's mounted to.
        mounted = False

        #OS X fix: Handle paths with /tmp in them, as paths with /private/tmp.
        if not LINUX and "/tmp" in mount_point:
            mount_point = mount_point.replace("/tmp", "/private/tmp")

        if get_mount_point(partition) == mount_point:
            mounted = True

    return mounted

def get_mount_point(partition):
    """
    Returns the mount_point of the given partition, if any.
    Otherwise, return None
    """

    mount_info = start_process("mount", return_output=True)[1]
    mount_point = None

    for line in mount_info.split("\n"):
        split_line = line.split()

        if len(split_line) != 0:
            if partition == split_line[0]:
                mount_point = split_line[2]
                break

    return mount_point

def mount_disk(partition, mount_point, options=""):
    """
    Mounts the given partition.
    partition is the partition to mount.
    mount_point is where you want to mount the partition.
    options is non-mandatory and contains whatever options you want to pass to the mount command.
    The default value for options is an empty string.
    """

    mount_info = start_process("mount", return_output=True)[1]

    #There is a partition mounted here. Check if it's ours.
    if mount_point == get_mount_point(partition):
        #The correct partition is already mounted here.
        return 0

    elif mount_point in mount_info:
        #Something else is in the way. Unmount that partition, and continue.
        if unmount_disk(mount_point) != 0:
            return False

    #Create the dir if needed.
    if os.path.isdir(mount_point) is False:
        os.makedirs(mount_point)

    #Mount the device to the mount point.
    #Use diskutil on OS X.
    if LINUX:
        retval = start_process("mount "+options+" "+partition+" "+mount_point, privileged=True)

    else:
        retval = start_process("diskutil mount "+options+" "+partition+" -mount_point "+mount_point, privileged=True)

    return retval

def unmount_disk(disk):
    """Unmount the given disk"""
    #Check if it is mounted.
    if is_mounted(disk) is False:
        #The disk isn't mounted.
        #Set retval to 0.
        retval = 0

    else:
        #The disk is mounted.
        #Unmount it.
        if LINUX:
            retval = start_process(cmd="umount "+disk, return_output=False, privileged=True)

        else:
            retval = start_process(cmd="diskutil umount "+disk, return_output=False, privileged=True)

    #Return the return value
    return retval
