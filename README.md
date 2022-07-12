# DDRescue-GUI

This repository holds DDRescue-GUI, which is available under the GNU GPLv3+.

NOTE: Source code for GNU ddrescue is available via https://www.gnu.org/software/ddrescue/

NOTE: Source code for terminal-notifier is available via https://github.com/julienXX/terminal-notifier

Description of Package
======================
A simple GUI frontend to make GNU ddrescue easier to use.

[![pipeline status](https://gitlab.com/hamishmb/ddrescue-gui/badges/master/pipeline.svg)](https://gitlab.com/hamishmb/ddrescue-gui/-/commits/master)

Packages
========

You can find these at https://www.hamishmb.com/html/ddrescue-gui.php.

Documentation
=============
This can be found at https://www.hamishmb.com/support/ddrescue-gui.php.

NOTE: To generate documentation, the directory containing the files in this repo must be called "ddrescue_gui".

Running The Tests
=================

As of v2.1.0, these no longer have to be run as the superuser.

The process for running these is the same on Linux, macOS, and Cygwin.

Without Coverage Reporting
--------------------------
Run:

"python3 ./tests.py"

With Coverage Reporting
-----------------------
Make sure you have installed Coverage.py using pip or your package manager.

Run:

"python3 -m coverage run --rcfile=./.coveragerc ./tests.py"

To run the tests. Then run:

"python3 -m coverage html"

To see the report.
