#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Uses getdevinfo to gather device information when requested for DDRescue-GUI
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
This is used to run getdevinfo to obtain device information.
"""

#Must be run as root to work (at least on Linux)!
import sys

import getdevinfo #pylint: disable=import-error

sys.stdout.write(str(getdevinfo.getdevinfo.get_info()))
sys.exit(0)
