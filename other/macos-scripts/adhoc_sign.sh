#!/bin/bash
#Sign with Ad-Hoc signature (just a checksum).
codesign -dvf --deep -s - ../../dist/DDRescue_GUI.app/
