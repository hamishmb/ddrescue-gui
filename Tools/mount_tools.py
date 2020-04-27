#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Destination file mounting tools in the Tools Package for DDRescue-GUI
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

# pylint: disable=no-member,logging-not-lazy,no-else-return
#
#Reason (no-member): False positives, API changes.
#Reason (logging-not-lazy): This is a more readable way of logging.
#Reason (no-else-return): Lots of false positives.

"""
This is the destination file mount tools module in the tools package for DDRescue-GUI.
"""

#Do future imports to prepare to support python 3.
#Use unicode strings rather than ASCII strings, as they fix potential problems.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import plistlib
import json
import logging
import wx

from . import core as CoreTools

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

#Dictionary variables.
SETTINGS = {}

#Set up logging.
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLogger("DDRescue-GUI").getEffectiveLevel())

# -------------------- CORE METHODS --------------------
class Core:
    """
    This class contains core methods used on both Linux and macOS
    """

    #The output file we're mounting.
    output_file = None

    #Holds the mount point of the output file/volume on it that we mounted.
    output_file_mountpoint = None

    #The type(s) of the output file. If we mount an LVM volume on a device,
    #this may be set to ["Device", "LVM"] for example.
    output_file_types = []

    #The device name(s) of the output file. If we mount an LVM volume, this
    #may be set to ["/dev/sde", "/dev/sde1"]. Corresponding indexes correlate
    #with the above variable.
    output_file_devicenames = []

    @classmethod
    def reset(cls):
        """
        Resets the state of this class, and triggers reset of the Linux and Mac classes.
        """
        cls.output_file = None
        cls.output_file_mountpoint = None
        cls.output_file_types = []
        cls.output_file_devicenames = []

        Linux.reset()
        Mac.reset()

    @classmethod
    def mount_output_file(cls):
        """
        Mount the output file in SETTINGS["OutputFile"].

        Returns:
            boolean.
                True - Success
                False - Failed
        """

        logger.info("Core.mount_output_file(): Mounting Disk: "+SETTINGS["OutputFile"]+"...")

        #Determine what type of OutputFile we have (Partition or Device).
        if LINUX:
            _type, success = Linux.determine_output_file_type(SETTINGS["OutputFile"])

        else:
            _type, success = Mac.determine_output_file_type(SETTINGS["OutputFile"])

        #If we failed, report to user.
        if not success:
            logger.error("Core.mount_output_file(): Error! Warning the user...")
            dlg = wx.MessageDialog(None, "Couldn't mount your output file. The hard disk "
                                   "image utility failed to run. This could mean your disk image "
                                   "is damaged, and you need to use a different tool to read it.",
                                   "DDRescue-GUI - Error!", style=wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        Core.output_file_devicenames.append(SETTINGS["OutputFile"])
        Core.output_file_types.append(_type)

        if "Partition" in Core.output_file_types:
		    #We have a partition.
            logger.debug("Core.mount_output_file(): Output file is a partition...")

            #Attempt to mount the disk.
            if LINUX:
                return Linux.mount_partition(SETTINGS["OutputFile"])

            else:
                return Mac.mount_partition(SETTINGS["OutputFile"], attach=True)
        else:
            #We have a device/container of some kind.
            if LINUX:
                return Linux.mount_device(SETTINGS["OutputFile"])

            else:
                return Mac.mount_device(SETTINGS["OutputFile"])

    @classmethod
    def unmount_output_file(cls):
        """
        Unmount the output file.

        Returns:
            boolean.
                True - Success
                False - Failed
        """

        logger.info("Core.unmount_output_file(): Attempting to unmount output file...")

        success = True

        #Unmount these in reverse order, otherwise it won't work.
        Core.output_file_devicenames.reverse()
        Core.output_file_types.reverse()

        for disk in Core.output_file_devicenames:
            logger.info("Core.unmount_output_file(): Unmounting "+disk+"...")

            #Try to umount the output file, if it has been mounted.
            if Core.output_file_mountpoint is not None:
                if CoreTools.unmount_disk(Core.output_file_mountpoint) == 0:
                    logger.info("Core.unmount_output_file(): Successfully unmounted "
                                "output file...")

                else:
                    logger.error("Core.unmount_output_file(): Error unmounting output "
                                 "file! Warning user...")

                    dlg = wx.MessageDialog(None, "It seems your output file is in use. "
                                           "Please close all applications that could be using it "
                                           "and try again.", "DDRescue-GUI - Warning",
                                           style=wx.OK | wx.ICON_INFORMATION)

                    dlg.ShowModal()
                    dlg.Destroy()
                    return False

            if LINUX:
                if not Linux.unmount_output_file(disk):
                    success = False

            else:
                if "/dev" in disk:
                    if not Mac.unmount_output_file(disk):
                        success = False

        #Reset everything if it worked.
        if success is True:
            Core.reset()

        return success

#------------------------------------ LINUX-SPECIFIC FUNCTIONS ------------------------------------
class Linux:
    """
    Linux-specific stuff for mounting the output file.
    """

    volume_group_name = None
    using_loop_device = False

    @classmethod
    def reset(cls):
        """
        Resets the state of this class to defaults.
        """
        cls.volume_group_name = None
        cls.using_loop_device = False

    @classmethod
    def determine_output_file_type(cls, output_file): #pylint: disable=invalid-name
        """
        Determines output File Type (partition or device).

        Returns:
            tuple(string, bool).

                1st element:                The type of the output file. "Partition",
                                            "Device", "LUKS", or "LVM".

                2nd element:                True - success, False - failed.
        """

        #Set a default.
        output_file_type = "unknown"

        #--------------- USING PARTED TO DETECT PARTITION TABLES AND FILESYSTEMS ---------------
        #If list of partitions is empty (or 1 partition), we have a partition.
        retval, output = CoreTools.start_process(cmd="parted -sm '"+output_file+"' print",
                                                 return_output=True, privileged=True)

        #NOTE: Exit code 1 on CD images, but still works.
        if retval not in (0, 1):
            return "unknown", False

        temp_output = output.split("\n")

        #Clean it up - errors from parted can mess this up.
        output = "unknown"

        for line in temp_output:
            if line == "":
                continue

            #All output lines end with a semicolon, and the first line can be ignored.
            if line[-1] == ";" and "BYT;" not in line:
                output = line
                break

        output = output.split(":")

        #FIXME will break if output file path has spaces in the name.
        #We want field 6 - the partition table type.
        try:
            #The type will be "loop" if this is a partition.
            if output[5] == "loop":
                output_file_type = "Partition"

            #If we have any valid partition table, this is a device.
            elif output[5] in ("msdos", "gpt", "mac", "pc98", "sun", "dvh", "bsd", "amiga",
                               "aix", "atari"):

                output_file_type = "Device"

        except IndexError:
            pass

        #--------------- DETECTING LUKS AND LVM CONTAINERS ---------------
        #Check if this is a LUKS or LVM container if parted didn't help.
        if output_file_type == "unknown":
            #Check for LUKS.
            if CoreTools.start_process(cmd="cryptsetup isLuks '"+output_file+"'",
                                       privileged=True) == 0:

                output_file_type = "LUKS"

            #Check for LVM.
            output = CoreTools.start_process(cmd="file -s '"+output_file+"'",
                                             return_output=True, privileged=True)[1]

            if "LVM" in output:
                output_file_type = "LVM"

        #Ask the user if we don't know what type the input file is.
        if output_file_type == "unknown":
            choices = ["Partition (single file system or CD/DVD image)",
                       "Device (multiple partitions)",
                       "LUKS (encrypted storage) Container",
                       "LVM Container"]

            dlg = wx.SingleChoiceDialog(wx.GetApp().TopWindow.panel,
                                        "What type of file/device did you recover from?",
                                        "DDRescue-GUI - Question", choices,
                                        pos=wx.DefaultPosition)

            if dlg.ShowModal() == wx.ID_OK:
                answer = dlg.GetStringSelection()
                dlg.Destroy()

            #If the user doesn't answer, give up.
            else:
                dlg.Destroy()
                return "unknown", False

            #The first word in our human-readable choices is the type.
            output_file_type = answer.split()[0]

        return output_file_type, True

    #--------------- FUNCTIONS FOR GETTING VOLUME INFORMATION ---------------
    @classmethod
    def get_volumes_std_device(cls, output_file):
        """
        Gets a list of volumes on the given output file or device name.
        This method expects the given file or device to be a standard device.

        Args:
            output_file (str):          The output file or device to get volumes for.

        Returns.
            list. The volumes that were found in human-readable form.
        """

        Linux.using_loop_device = False

        #Create a loop device if this is a file and a regular device.
        if "/dev/" not in output_file:
            Linux.using_loop_device = True

            logger.info("Linux.get_volumes_std_device(): Creating loop device...")

            kpartx_output = CoreTools.start_process(cmd="kpartx -av '"
                                                    + output_file+"'",
                                                    return_output=True, privileged=True)[1]

            kpartx_output = kpartx_output.split("\n")

            #Do a part probe to make sure the loop device has been searched.
            CoreTools.start_process(cmd="partprobe", privileged=True)

        #Get some Disk information.
        lsblk_output = CoreTools.start_process(cmd="lsblk -J -o NAME,FSTYPE,SIZE",
                                               return_output=True,
                                               privileged=True)[1].split("\n")

        #Remove any errors from lsblk in the output.
        cleaned_lsblk_output = []

        for line in lsblk_output:
            if "lsblk:" not in line:
                cleaned_lsblk_output.append(line)

        lsblk_output = '\n'.join(cleaned_lsblk_output)

        #Parse into a dictionary w/ json.
        try:
            lsblk_output = json.loads(lsblk_output)

        except ValueError as error:
            logger.error("Linux.get_volumes_std_device(): Failed to run lsblk. Error:"
                         +unicode(error))

            dlg = wx.MessageDialog(None, "Failed to gather information about the output file."
                                   "This could indicate a bug in the GUI, or a problem "
                                   "with your recovered image. It's possible the data you "
                                   "recovered is partially corrupted, and you need to use "
                                   "another tool to extract meaningful data from it.",
                                   "DDRescue-GUI - Error", style=wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

            return False

        if Linux.using_loop_device:
            #Get the name of the loop device.
            #The list comprehensions are needed because the kpartx output has the partitions only.
            #eg: add map loop1p1 (253:0): 0 251904 linear 7:1 2048

            try:
                #First, get the loop-and-partition section (eg loop1p1).
                temp = kpartx_output[0].split()[2]

                #Now get rid of the partition number to get just the loop device name.
                target_device = 'p'.join(temp.split("p")[0:2])


            except IndexError:
                return []

        else:
            target_device = output_file

        choices = []

        #Get the info related to this partition.
        for device in lsblk_output["blockdevices"]:
            #Ignore other devices.
            if device["name"] != target_device and "/dev/"+device["name"] != target_device:
                continue

            #Add all the partitions to the choices list.
            for disk in device["children"]:
                #Add stuff, trying to keep it human-readable.
                if disk["fstype"] is None:
                    disk["fstype"] = "None"

                choices.append("Partition "+disk["name"]
                               + ", Filesystem: "+disk["fstype"]
                               + ", Size: "+disk["size"])

        return choices

    @classmethod
    def get_volumes_luks(cls, output_file): #TODO
        """
        Gets a list of volumes on the given output file or device name.
        This method expects the given file or device to be a LUKS device.

        Args:
            output_file (str):          The output file or device to get volumes for.

        Returns.
            list. The volumes that were found in human-readable form.
        """

        return []

    @classmethod
    def get_volumes_lvm(cls, output_file):
        """
        Gets a list of volumes on the given output file or device name.
        This method expects the given file or device to be an LVM Physical Volume.

        Args:
            output_file (str):          The output file or device to get volumes for.

        Returns.
            list. The volumes that were found in human-readable form.
        """

        pv_device = None

        #First, set up a loop device if this is a file.
        if "/dev/" not in output_file:
            counter = 0

            while counter < 100:
                if not os.path.exists("/dev/loop"+unicode(counter)):
                    pv_device = "/dev/loop"+unicode(counter)
                    break

                counter += 1

            if pv_device is None:
                logger.error("Linux.get_volumes_lvm(): No free loop devices!")
                return []

            retval = CoreTools.start_process(cmd="losetup "+pv_device+" '"+output_file+"'",
                                             privileged=True)

            if retval != 0:
                logger.error("Linux.get_volumes_lvm(): Unable to set up loop device!")
                return []

        else:
            pv_device = output_file

        retval, output = CoreTools.start_process(cmd="pvs -y", return_output=True,
                                                 privileged=True)

        if retval != 0:
            logger.error("Linux.get_volumes_lvm(): Could not obtain information about LVM PVs!")
            return []

        #Read pvdisplay's output to find the volume group name for this device.
        for line in output.split("\n"):
            if pv_device in line:
                Linux.volume_group_name = line.split()[1]

        #Activate the volume group.
        retval = CoreTools.start_process(cmd="vgchange -a y "+Linux.volume_group_name,
                                         privileged=True)

        if retval != 0:
            logger.error("Linux.get_volumes_lvm(): Unable to activate volume group!")
            return []

        #Find logical volumes.
        retval, lvdisplay_output = CoreTools.start_process(cmd="lvdisplay -C --units M",
                                                           return_output=True,
                                                           privileged=True)
        if retval != 0:
            logger.error("Linux.get_volumes_lvm(): Unable to obtain information about LVM LVs!")
            return []

        lvdisplay_output = lvdisplay_output.split("\n")

        choices = []

        #Find all volumes that correspond to our volume group.
        for line in lvdisplay_output:
            if Linux.volume_group_name in line:
                splitline = line.split()

                choices.append("Volume "+splitline[0]
                               + ", Size: "+splitline[3])

        return choices

    #--------------- MOUNTING AND UNMOUNTING FUNCTIONS ---------------
    @classmethod
    def mount_partition(cls, partition):
        """
        Mounts the given file or device name as a single volume or partition.

        Args:
            partition (str):            The file or device to mount.

        Returns:
            Boolean.
                True - Success
                False - Failed
        """

        #We will mount the file/device in /tmp/ddrescue-gui/destination
        Core.output_file_mountpoint = "/tmp/ddrescue-gui/destination"

        retval = CoreTools.mount_disk(partition=partition,
                                      mount_point=Core.output_file_mountpoint,
                                      options="-r")

        if retval != 0:
            logger.error("Linux.mount_partition(): Error! Warning the user...")
            dlg = wx.MessageDialog(None, "Couldn't mount your output file. Most "
                                   "probably, the filesystem is damaged and you'll need to "
                                   "use another tool to read it from here. It could also be "
                                   "that your OS doesn't support this filesystem, or that "
                                   "the recovery is incomplete, as that can sometimes cause "
                                   "this problem.", "DDRescue-GUI - Error!",
                                   style=wx.OK | wx.ICON_ERROR)

            dlg.ShowModal()
            dlg.Destroy()
            return False

        return True

    @classmethod
    def mount_device(cls, output_file):
        """
        Mounts the given output file or device, expecting it to be a standard device
        or another kind of container for volumes - LUKS or LVM.

        Args:
            output_file (str).          The device or file to mount.

        Returns:
            Boolean.
                True - Success
                False - Failure
        """

        #TODO Warnings for LVM disks: make sure there are no duplicates before mounting.
        #Create a nice list of volumes for the user to pick from.
        choices = []

        logger.debug("Linux.mount_device(): Output file isn't a partition! Getting "
                     "list of contained volumes...")

        #Only look at the last type - this way if we're mounting a sub-partition, we'll collect
        #information for that, not the container it's inside.
        if Core.output_file_types[-1] == "Device":
            choices = Linux.get_volumes_std_device(output_file)

        #Unlock LUKS containers.
        elif Core.output_file_types[-1] == "LUKS":
            choices = Linux.get_volumes_luks(output_file)

        #Find LVM volumes.
        elif Core.output_file_types[-1] == "LVM":
            choices = Linux.get_volumes_lvm(output_file)

        #Check that this list isn't empty.
        if not choices:
            logger.error("Linux.mount_device(): Couldn't find any partitions "
                         "to mount!")

            dlg = wx.MessageDialog(None, "Couldn't find any partitions to mount! "
                                   "This could indicate a bug in the GUI, or a problem "
                                   "with your recovered image. It's possible the data you "
                                   "recovered is partially corrupted, and you need to use "
                                   "another tool to extract meaningful data from it.",
                                   "DDRescue-GUI - Error", style=wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

            return False

        if len(choices) >= 2:
            #Sort the list alphabetically (it can sometimes be out of order).
            choices.sort()

            #Ask the user which partition to mount.
            logger.debug("mount_output_file(): Asking user which partition to mount...")
            dlg = wx.SingleChoiceDialog(None, "Please select which partition you wish "
                                        "to mount.", "DDRescue-GUI - Select a Partition", choices)

            #Respond to the user's action.
            if dlg.ShowModal() != wx.ID_OK:
                Core.output_file_mountpoint = None
                logger.debug("mount_output_file(): User cancelled operation. "
                             "Cleaning up...")

                Core.unmount_output_file()
                return False

            #Get selected partition's name.
            full_selection = dlg.GetStringSelection()
            selected_partition = full_selection.split()[1].replace(",", "")

            dlg.Destroy()

        else:
            #There is only 1 choice so we'll pick that automatically.
            full_selection = choices[0]
            selected_partition = choices[0].split()[1].replace(",", "")

        #Attempt to mount, and handle it if the mount attempt failed.
        if Core.output_file_types[-1] == "Device":
            if Linux.using_loop_device:
                device_to_mount = "/dev/mapper/"+selected_partition

            else:
                device_to_mount = "/dev/"+selected_partition

        elif Core.output_file_types[-1] == "LUKS":
            #TODO
            pass

        elif Core.output_file_types[-1] == "LVM":
            device_to_mount = "/dev/"+Linux.volume_group_name+"/"+selected_partition

            #Add this partition to the list so it is unmounted before
            #deactivating the volume group.
            Core.output_file_types.append("Partition")
            Core.output_file_devicenames.append(device_to_mount)

        #Caveats for mounting LVM and LUKS volumes just selected.
        if Core.output_file_types[-1] == "Device" and "LVM" in full_selection:
            Core.output_file_types.append("LVM")
            Core.output_file_devicenames.append(device_to_mount)

            Linux.mount_device(device_to_mount)

        elif Core.output_file_types[-1] == "Device" and "LUKS" in full_selection:
            #TODO LUKS.
            pass

        else:
            if not Linux.mount_partition(device_to_mount):
                return False

        logger.info("Linux.mount_device(): Success! Waiting for user to finish "
                    "with it and prompt to unmount it...")

        return True

    @classmethod
    def unmount_output_file(cls, output_file): #TODO handle LUKS
        """
        Unmounts the output file or device. Handles partitions, devices, LVM and LUKS disks.

        Args:
            output_file (str).      The device or file to unmount.

        Returns:
            Boolean.
                True - Success
                False - Failed
        """

        #Pull down loops if the OutputFile is a Device.
        if Core.output_file_types[Core.output_file_devicenames.index(output_file)] == "Device":
            #This won't error on LINUX even if the loop device wasn't set up.
            logger.debug("unmount_output_file(): Pulling down loop device...")
            cmd = "kpartx -d '"+output_file+"'"

        #Deactivate volume group if needed.
        elif Core.output_file_types[Core.output_file_devicenames.index(output_file)] == "LVM":
            #Shouldn't cause an error if volume group is already unmounted.
            logger.debug("Linux.unmount_output_file(): Pulling down loop device...")
            cmd = "vgchange -a n "+Linux.volume_group_name

        elif Core.output_file_types[Core.output_file_devicenames.index(output_file)] == "Partition":
            #Partition, no extra command needed. Return True.
            return True

        if CoreTools.start_process(cmd=cmd, return_output=False, privileged=True) == 0:
            logger.info("Linux.unmount_output_file(): Successfully pulled down "
                        "loop device...")

            return True

        else:
            logger.info("Linux.unmount_output_file(): Failed to pull down the "
                        "loop device! Warning user...")

            dlg = wx.MessageDialog(None, "Couldn't finish unmounting your output file! "
                                   "Please close all applications that could be using it and "
                                   "try again.", "DDRescue-GUI - Warning",
                                   style=wx.OK | wx.ICON_INFORMATION)

            dlg.ShowModal()
            dlg.Destroy()
            return False

#------------------------------------ MACOS-SPECIFIC FUNCTIONS ------------------------------------
class Mac:
    """
    Macos-specific stuff for mounting the output file.
    """

    @classmethod
    def reset(cls):
        """
        Resets the state of this class to defaults.
        """
        pass

    @classmethod
    def determine_output_file_type(cls, output_file): #pylint: disable=invalid-name
        """
        Determines output File Type (partition or device)..

        Returns:
            tuple(string, bool).

                1st element:                The type of the output file. "Partition",
                                            "Device", "CD", "APFSStore", "APFSContainer"
                                            or "APFSVolume".

                2nd element:                True - success, False - failed.
        """

        retval, output = Mac.run_hdiutil(options="imageinfo '"+output_file
                                         +"' -plist")

        #If "whole disk" is in the output, this is a partition.
        if "whole disk" in output and not "APFS" in output:
            output_file_type = "Partition"

        #If there's an ISO9660 filesystem, treat this as a CD image.
        elif "ISO9660" in output:
            output_file_type = "CD"

        #APFS stuff.
        elif "Apple_APFS" in output:
            if "whole disk" in output:
                output_file_type = "APFSContainer"

            elif "unknown partition" in output:
                output_file_type = "APFSVolume"

            else:
                output_file_type = "APFSStore"

        else:
            output_file_type = "Device"

        logger.debug("determine_output_file_type(): Type is "+output_file_type+"...")

        return output_file_type, retval == 0

    @classmethod
    def attach_file(cls, output_file):
        """
        Attaches the given output file to the system as a read-only device.

        Args:
            output_file (str).          The output file to attach.

        Returns:
            tuple. Elements:
                1 - int.                 The return value from hdiutil attach.
                2 - str.                 The device name of the file, or None if attaching failed.
        """

        retval, output = Mac.run_hdiutil("attach '"+output_file
                                         + "' -nomount -readonly -plist")

        #Get the device name
        devicename, result = Mac.get_device_name(output)

        if not result:
            return retval, None

        return retval, devicename

    @classmethod
    def get_volumes_std_device(cls, output_file, cdimage=False):
        """
        Finds volumes contained by standard devices.

        Args:
            output_file (str).          The output file or device to investigate.

        Kwargs:
            cdimage[=False] (bool).     Whether or not we are finding volumes on a CD device/image.

        Returns.
            list. The volumes that were found in human-readable form.
        """

        hdiutil_imageinfo_output = Mac.run_hdiutil(options="imageinfo '"+output_file
                                                   +"' -plist")[1]

        #Fix for older macOS versions that put kernel messages in the output.
        temp = ""

        for line in hdiutil_imageinfo_output.split("\n"):
            if "nx_kernel_mount" not in line:
                temp += line                

        hdiutil_imageinfo_output = plistlib.readPlistFromString(temp.encode())

        #Get the block size of the image.
        blocksize = hdiutil_imageinfo_output["partitions"]["block-size"]

        output = hdiutil_imageinfo_output["partitions"]["partitions"]

        partno = 1
        choices = []

        for partition in output:
            size = unicode((partition["partition-length"] * blocksize) // 1000000)+" MB"

            if not cdimage:
                #Skip non-partition things and any "partitions" that don't have numbers.
                #CD images work differently, and we must ignore this rule.
                if "partition-number" not in partition and \
                    "APFS" not in partition["partition-hint"]:

                    continue

            else:
                #Ignore "partitions" that don't start at 0.
                if partition["partition-start"] != 0:
                    continue

                #Set the partition number for CD images.
                partition["partition-number"] = partno
                partno += 1

                #Ignore partition size for CD images.
                size = "N/A"

            choices.append("Partition "+unicode(partition["partition-number"])
                           + ", with size "+size)

        return choices

    @classmethod
    def get_volumes_apfs(cls, output_file):
        """
        Finds volumes contained by APFS containers.

        Args:
            output_file (str).          The output file or device to investigate.

        Returns.
            list. The volumes that were found in human-readable form.
        """

        hdiutil_imageinfo_output = Mac.run_hdiutil(options="imageinfo '"+output_file
                                                   +"' -plist")[1]

        #Fix for older macOS versions that put kernel messages in the output.
        temp = ""

        for line in hdiutil_imageinfo_output.split("\n"):
            if "nx_kernel_mount" not in line:
                temp += line                

        hdiutil_imageinfo_output = plistlib.readPlistFromString(temp.encode())

        #Get the block size of the image.
        blocksize = hdiutil_imageinfo_output["partitions"]["block-size"]

        output = hdiutil_imageinfo_output["partitions"]["partitions"]

        partno = 1
        choices = []

        for partition in output:
            #Skip non-partition things and any "partitions" that don't have numbers.
            #CD images work differently, and we must ignore this rule.
            if "partition-number" not in partition and "APFS" not in partition["partition-hint"]:
                continue

            #Set the partition number for APFS volumes.
            if "APFS" in partition["partition-hint"]:
                partition["partition-number"] = partno
                partno += 1

            choices.append("Partition "+unicode(partition["partition-number"])
                           + ", with size "+unicode((partition["partition-length"] \
                                                     * blocksize) // 1000000)
                           +" MB")

        return choices

    @classmethod
    def mount_partition(cls, partition, attach=False):
        """
        Mounts the given partition, also attaching the file if needed.

        Args:
            partition (str).            The partition or file to mount.

        Kwargs:
            attach[=False] (bool).      Whether to attach the file first.

        Returns:
            boolean.
                True - Success
                False - Failed
        """

        #Attach the file first if needed.
        if attach:
            retval, partition = Mac.attach_file(partition)

        #We will mount the file/device in /tmp/ddrescue-gui/destination
        Core.output_file_mountpoint = "/tmp/ddrescue-gui/destination"

        retval = CoreTools.mount_disk(partition=partition,
                                      mount_point=Core.output_file_mountpoint,
                                      options="readOnly")

        if retval != 0:
            logger.error("Mac.mount_partition(): Error! Warning the user...")
            dlg = wx.MessageDialog(None, "Couldn't mount your output file. Most "
                                   "probably, the filesystem is damaged and you'll need to "
                                   "use another tool to read it from here. It could also be "
                                   "that your OS doesn't support this filesystem, or that "
                                   "the recovery is incomplete, as that can sometimes cause "
                                   "this problem.", "DDRescue-GUI - Error!",
                                   style=wx.OK | wx.ICON_ERROR)

            dlg.ShowModal()
            dlg.Destroy()
            return False

        return True

    @classmethod
    def mount_device(cls, output_file): #TODO error handling
        """
        Mount the given device or file. This is expected to be a standard device or other
        container of volumes (eg an APFS container).

        Args:
            output_file (str).              The device or file to mount.

        Returns:
            Boolean.
                True - Success
                False - Failure
        """

        logger.debug("Mac.mount_device(): Output file isn't a partition! Getting "
                     "list of contained partitions...")

        #Only look at the last type - this way if we're mounting a sub-partition, we'll collect
        #information for that, not the container it's inside.
        if Core.output_file_types[-1] in ("Device", "APFSStore"):
            choices = Mac.get_volumes_std_device(output_file)

        elif Core.output_file_types[-1] == "CD":
            choices = Mac.get_volumes_std_device(output_file, cdimage=True)

        #APFS containers.
        elif Core.output_file_types[-1] in ("APFSContainer", "APFSVolume"):
            choices = Mac.get_volumes_apfs(output_file)

        #Check that this list isn't empty.
        if not choices:
            logger.error("Mac.mount_device(): Couldn't find any partitions "
                         "to mount! This could indicate a bug in the GUI, or a problem "
                         "with your recovered image. It's possible that the data you "
                         "recovered is partially corrupted, and you need to use "
                         "another tool to extract meaningful data from it.")

            dlg = wx.MessageDialog(None, "Couldn't find any partitions to mount! "
                                   "This could indicate a bug in the GUI, or a problem "
                                   "with your recovered image. It's possible the data you "
                                   "recovered is partially corrupted, and you need to use "
                                   "another tool to extract meaningful data from it.",
                                   "DDRescue-GUI - Error", style=wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

            return False

        if len(choices) >= 2:
            #Sort the list alphabetically (it can sometimes be out of order).
            choices.sort()

            #Ask the user which partition to mount.
            logger.debug("mount_output_file(): Asking user which partition to mount...")
            dlg = wx.SingleChoiceDialog(None, "Please select which partition you wish "
                                        "to mount.", "DDRescue-GUI - Select a Partition", choices)

            #Respond to the user's action.
            if dlg.ShowModal() != wx.ID_OK:
                Core.output_file_mountpoint = None
                logger.debug("mount_output_file(): User cancelled operation. "
                             "Cleaning up...")

                return False

            #Get selected partition's name.
            selected_partition = dlg.GetStringSelection().split()[1].replace(",", "")

            #Get selected partition's name.
            full_selection = dlg.GetStringSelection()
            selected_partition = full_selection.split()[1].replace(",", "")

            dlg.Destroy()

        else:
            #There is only 1 choice so we'll pick that automatically.
            full_selection = choices[0]
            selected_partition = choices[0].split()[1].replace(",", "")

        #Notify user of mount attempt.
        logger.info("Mac.mount_device(): Mounting partition "
                    + selected_partition+" of "+output_file+"...")

        #Attempt to mount the disk (this mounts all partitions inside),
        #and parse the resulting plist.
        (retval, mount_output) = \
        Mac.run_hdiutil("attach '"+output_file+"' -readonly -nomount -plist")

        mount_output = plistlib.readPlistFromString(mount_output.encode())

        #Handle it if the mount attempt failed.
        if retval != 0:
            logger.error("Mac.mount_device(): Error! Warning the user...")
            dlg = wx.MessageDialog(None, "Couldn't mount your output file. Most "
                                   "probably, the filesystem is damaged or unsupported "
                                   "and you'll need to use another tool to read it from "
                                   "here. It could also be that your recovery is incomplete, "
                                   "as that can sometimes cause this problem.",
                                   "DDRescue-GUI - Error!", style=wx.OK | wx.ICON_ERROR)

            dlg.ShowModal()
            dlg.Destroy()
            return False

        #We need to get the device name, so we can mount the partition we want.
        #Get the list of disks mounted.
        disks = mount_output["system-entities"]

        #Get the device name given to the output file.
        #Set this so if we don't find our partition, we can still unmount the image
        #when we report failure.
        Core.output_file_devicenames.append(disks[0]["dev-entry"])

        success = False

        if Core.output_file_types[-1] in ("Device", "APFSStore", "APFSContainer"):
            #Check that the filesystem the user wanted is among those that
            #have been marked mountable.
            for partition in disks:
                disk = partition["dev-entry"]

                if Core.output_file_types[-1] in ("Device", "APFSStore") \
                    and disk.split("s")[-1] != selected_partition:

                    continue

                #Find the type of this partition.
                _type, success = Mac.determine_output_file_type(disk)

                #Check if the partition we want is mountable
                if partition["potentially-mountable"] and _type == "Partition":
                    success = Mac.mount_partition(disk)
                    break

                #If this is an APFS container and we haven't reached the last
                #disk yet, keep going.
                elif Core.output_file_types[-1] == "APFSContainer" \
                    and disks.index(partition) != (len(disks) - 1):

                    continue

                #Handle APFS containers.
                elif _type == "APFSContainer":
                    Core.output_file_types.append("APFSContainer")
                    Core.output_file_devicenames.append(disk)

                    success = Mac.mount_device(disk)

                #Handle APFS stores.
                elif _type == "APFSStore":
                    Core.output_file_types.append("APFSStore")
                    Core.output_file_devicenames.append(disk)

                    success = Mac.mount_device(disk)

        elif Core.output_file_types[-1] == "CD":
            disk = disks[0]["dev-entry"]

            if disks[0]["potentially-mountable"]:
                success = Mac.mount_partition(disk)

        if not success:
            logger.info("Mac.mount_device(): Unsupported or damaged filesystem. "
                        "Warning user and cleaning up...")

            Core.unmount_output_file()
            dlg = wx.MessageDialog(None, "That filesystem is either not supported by "
                                   "macOS, or it is damaged (perhaps because the recovery is "
                                   "incomplete). Please try again and select a different "
                                   "partition.", "DDRescue-GUI - Error", wx.OK | wx.ICON_ERROR)

            dlg.ShowModal()
            dlg.Destroy()
            return False

        logger.info("Mac.mount_device(): Success! Waiting for user to finish with "
                    "it and prompt to unmount it...")

        return True

    @classmethod
    def unmount_output_file(cls, devicename):
        """
        Unmounts the given device. Can be used for output files as well, but needs
        to be given the device associated with them.

        Args:
            devicename (str).               The device to unmount.

        Returns:
            Boolean.
                True - Success
                False - Failed
        """

        #TODO handle APFS. Done now?
        #Always detach the image's device file.
        #FIXME will error out if it was never attached.
        logger.debug("Mac.unmount_output_file(): Detaching the device that "
                     "represents the image...")

        cmd = "hdiutil detach "+devicename

        #Ignore when devices don't exist - can happen if already unmounted.
        if not os.path.exists(devicename):
            return True

        if CoreTools.start_process(cmd=cmd, return_output=False, privileged=True) == 0:
            logger.info("Mac.unmount_output_file(): Successfully pulled down "
                        "loop device...")

            return True

        else:
            logger.info("Mac.unmount_output_file(): Failed to pull down the "
                        "loop device! Warning user...")

            dlg = wx.MessageDialog(None, "Couldn't finish unmounting your output file! "
                                   "Please close all applications that could be using it and "
                                   "try again.", "DDRescue-GUI - Warning",
                                   style=wx.OK | wx.ICON_INFORMATION)

            dlg.ShowModal()
            dlg.Destroy()
            return False

    @classmethod
    def get_device_name(cls, output):
        """
        Get the device name of an output file,
        given output from hdiutil attach -plist.

        Args:
            output (string).                Output from "hdiutil attach -plist",
                                            the command used to mount the output file.

        Returns:
            tuple(<inconsistent types>).

                1st element:        The device name of the output file eg
                                    "/dev/disk5", or None if unable to determine it.

                2nd element:        True (boolean) if successful in determining
                                    device name and mount point. Otherwise, a
                                    string describing the error eg "UnicodeError".
        """

        #Parse the plist (Property List).
        hdiutil_output = plistlib.readPlistFromString(output.encode())

        #Find the disk and get the mountpoint.
        try:
            if len(hdiutil_output["system-entities"]) > 1:
                mounted_disk = hdiutil_output["system-entities"][1]

            else:
                mounted_disk = hdiutil_output["system-entities"][0]

        except IndexError:
            return None, "IndexError"

        return mounted_disk["dev-entry"], True

    @classmethod
    def run_hdiutil(cls, options):
        """
        Runs hdiutil on behalf of the rest of the program when called.
        Tries to handle and fix hdiutil errors (e.g. 'Resource Temporarily
        Unavailable') if they occur.

        Args:
            options (string).               All of the options to pass to hdiutil.

        Returns:
            tuple(int, string).

                1st element:                The return value from hdiutil.

                2nd element:                The output from hdiutil.
        """

        retval, output = CoreTools.start_process(cmd="hdiutil "+options, return_output=True,
                                                 privileged=True)

        #Handle this common error - image in use.
        if "Resource temporarily unavailable" in output or retval != 0:
            logger.warning("Mac.run_hdiutil(): Attempting to fix hdiutil resource error...")
            #Fix by detaching all disks - certain disks eg system disk will fail, but it should fix
            #our problem. On OS X >= 10.11 can check for "(disk image)", but cos we support 10.9 &
            #10.10, we have to just detach all possible disks and ignore failures.

            #TODO Consider dropping support for macOS 10.9 and 10.10 to improve reliability.
            #Or could detect version and behave differently on newer versions.
            #This bug doesn't seem to be a big deal anyway.
            for line in CoreTools.start_process(cmd="diskutil list",
                                                return_output=True)[1].split("\n"):
                try:
                    if line.split()[0].split("/")[1] == "dev":
                        #This is a line with a device name on it.
                        logger.warning("Mac.run_hdiutil(): Attempting to detach "
                                       + line.split()[0]+"...")

                        CoreTools.start_process(cmd="hdiutil detach "+line.split()[0],
                                                privileged=True)

                except IndexError:
                    pass

            #Try again.
            retval, output = CoreTools.start_process(cmd="hdiutil "+options, return_output=True,
                                                     privileged=True)

        return retval, output
