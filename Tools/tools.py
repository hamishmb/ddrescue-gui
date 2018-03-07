#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Tools Package for DDRescue-GUI Version 1.8
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
import logging
import plistlib
import time
import wx

#Make unicode an alias for str in Python 3.
if sys.version_info[0] == 3:
    unicode = str

    #Plist hack for Python 3.
    plistlib.readPlistFromString = plistlib.loads

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

#Set up logging.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def start_process(cmd, return_output=False):
    """Start a given process, and return output and return value if needed"""
    logger.debug("start_process(): Starting process: "+cmd)
    runcmd = subprocess.Popen("LC_ALL=C "+cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, shell=True)

    while runcmd.poll() is None:
        time.sleep(0.25)

    #Save runcmd.stdout.readlines, and runcmd.returncode,
    #as they tend to reset fairly quickly. Handle unicode properly.
    output = []

    for line in runcmd.stdout.readlines():
        output.append(line.decode("UTF-8", errors="ignore"))

    retval = int(runcmd.returncode)

    #Log this info in a debug message.
    logger.debug("start_process(): Process: "+cmd+": Return Value: "
                 +unicode(retval)+", output: \"\n\n"+''.join(output)+"\"\n")

    if not return_output:
        #Return the return code back to whichever function ran this process, so it handles errors.
        return retval

    else:
        #Return the return code, as well as the output.
        return retval, ''.join(output)

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
                                "1.21", "1.22", "1.23"):
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

def determine_output_file_type(SETTINGS, disk_info):
    """Determines output File Type (partition or Device)"""
    if SETTINGS["InputFile"] in disk_info:
		#Read from disk_info if possible (OutputFile type = InputFile type)
        output_file_type = disk_info[SETTINGS["InputFile"]]["Type"]
        retval = 0
        output = ""

        if output_file_type == "Device":
            if LINUX:
                retval, output = start_process(cmd="kpartx -l "+SETTINGS["OutputFile"],
                                               return_output=True)
                output = output.split("\n")

            else:
                retval, output = mac_run_hdiutil(options="imageinfo "+SETTINGS["OutputFile"]
                                                 +" -plist")

    else:
        if LINUX:
            #If list of partitions is empty (or 1 partition), we have a partition.
            retval, output = start_process(cmd="kpartx -l "+SETTINGS["OutputFile"],
                                           return_output=True)
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

    retval, output = start_process(cmd="hdiutil "+options, return_output=True)

    #Handle this common error - image in use.
    if "Resource temporarily unavailable" in output or retval != 0:
        logger.warning("mac_run_hdiutil(): Attempting to fix hdiutil resource error...")
        #Fix by detaching all disks - certain disks eg system disk will fail, but it should fix
        #our problem. On OS X >= 10.11 can check for "(disk image)", but cos we support 10.9 &
        #10.10, we have to just detach all possible disks and ignore failures. No need for
        #try-except cos start_process doesn't throw errors.
        for line in start_process(cmd="diskutil list", return_output=True)[1].split("\n"):
            try:
                if line.split()[0].split("/")[1] == "dev":
                    #This is a line with a device name on it.
                    logger.warning("mac_run_hdiutil(): Attempting to detach "+line.split()[0]+"...")
                    start_process(cmd="hdiutil detach "+line.split()[0])

            except IndexError:
                pass

        #Try again.
        retval, output = start_process(cmd="hdiutil "+options, return_output=True)

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
        os.makedirs(mount_point)

    #Mount the device to the mount point.
    #Use diskutil on OS X.
    if LINUX:
        retval = start_process("mount "+options+" "+partition+" "+mount_point)

    else:
        retval = start_process("diskutil mount "+options+" "+" -mountPoint "
                               +mount_point+" "+partition)

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
            retval = start_process(cmd="umount "+disk, return_output=False)

        else:
            retval = start_process(cmd="diskutil umount "+disk, return_output=False)

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
        result = (disk[0:7] not in ["/dev/sr", "/dev/fd"] and disk[-1].isdigit() and disk[0:8] in disk_info.keys())

    else:
        result = ("s" in disk.split("disk")[1])

    logger.info("is_partition(): result: "+str(result)+"...")

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
