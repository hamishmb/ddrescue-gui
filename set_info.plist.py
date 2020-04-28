#!/usr/bin/env python3
import plistlib

fd = open("dist/DDRescue_GUI.app/Contents/Info.plist", "rb")
data = plistlib.load(fd)
fd.close()

data["CFBundleDisplayName"] = "DDRescue-GUI"
data["CFBundleName"] = "DDRescue-GUI"
data["CFBundleIdentifier"] = "org.pythonmac.unspecified.DDRescue-GUI"
data["CFBundleVersion"] = "2.1.1"
data["CFBundleShortVersionString"] = "2.1.1"
data["NSHumanReadableCopyright"] = "Copyright (C) 2013-2020 Hamish McIntyre-Bhatty"

fd = open("dist/DDRescue_GUI.app/Contents/Info.plist", "wb")
plistlib.dump(data, fd)
fd.close()
