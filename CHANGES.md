DDRescue-GUI (2.1.1):

  * Changes since v2.1.0:
  *
  * Drop support and workarounds for Python 2.
  * Make DDRescue-GUI compatible with wxPython 4.1.0.
  * Various fixes for Cygwin, including fixing a potential memory leak.
  * Make developer docs more mobile friendly.
  * Fix unmounting output files on certain versions of macOS.
  * Add the .desktop file to the repository.

DDRescue-GUI (2.1.0):
  * Changes since v2.0.2:
  *
  * Drop support for wxPython 2.8.11, Ubuntu 14.04, and Python 2.7.6.
  * Fix logging in submodules.
  * Improve in-code documentation.
  * Fix using output and log files with spaces in the names.
  * Add tooltips for macOS about the overwrite notices.
  * Clarify when to enable direct disk access in the settings window.
  * Large rewrite and various fixes in output file mounting code.
  * Fix mounting CD images on Linux and macOS.
  * Fix LP #1852598 Reusing DDRescue-GUI after aborting results in an aborted message upon completion
  * Fix LP #1852596 Choosing previously selected file causes DDRescue-GUI to hang
  * General cleanup and fixed several hangs.
  * Use ddrescue's time remaining estimates when available, fixes LP#1731640
  * Add APFS mounting support for macOS 10.12 and higher.
  * Add LVM mounting support for Linux.
  * Add explicit support for ddrescue 1.25 and add ddrescue 1.25 binary for macOS.
  * Add an "Open File Viewer" button on the finished window.
  * Provide a text entry dialog so users on macOS can now select arbitrary devices.
  * Don't present users with choices during mounting when unneccessary.
  * Various other smaller fixes and improvements.

DDRescue-GUI (2.0.2):

  * Changes since v2.0.1:
  *
  * Update files so compatibility with ddrescue 1.24 is recognised.
  * Catch more errors when running getdevinfo, preventing crashes in certain situations.

DDRescue-GUI (2.0.1):

  * Changes since v2.0.0:
  *
  * Replace wx.Yield() with wx.GetApp().Yield() (deprecation warning).
  * Don't automatically add file extensions for files under /dev (bug).
  * macOS - Remove the all files wildcard to prevent weird behaviour
  * Note in about box that Python and wxPython are bundled with macOS too - more clarity.
  * Add GetDevInfo version to about box.
  * Fix an issue when selecting map files.
  * Move version and release date info to the left a bit in the statusbar - looks better on some platforms.
  * Don't catch the general exception class when running getdevinfo.
  * Code clean up with pylint.
  * Fix aborting the recovery on some newer version of Linux (workaround for psmisc/killall issue #13 in gitlab).

DDRescue-GUI (2.0.0):
  * Changes since v1.7.2:
  *
  * NB: This list is a fairly exhaustive list of changes. It shows all the progress I've made since January.
  * See the corresponding blog post on my website for a concise summary in English.
  *
  * NB: In case you're wondering, there was lots of toing-and-froing on the auth mechanisms because I was still deciding the implementation, so I was trying lots of prototype things.
  *
  * Update release info and version.
  * Update to use the new GetDevInfo module.
  * Remove old "GetDevInfo" folder.
  * Don't use old IsPartition() method of GetDevInfo any more.
  * Use pylint to tidy up and fix some errors.
  * Transition fixes for GetDevInfo module integration.
  * Rename modules to be in keeping with the python style guide.
  * Remove old tests for GetDevInfo package.
  * Move IsPartition() function from old GetDevInfo into tools.py.
  * Make the tools module more independent.
  * Use pylint to further clean up the source code.
  * ^ Also follow the style guide more closely.
  * getdevinfo fix for macOS.
  * Add some Py3 support code from GetDevInfo.
  * Fix style issues on the auth dialog.
  * Enable the about and disk info menu options while recovering data.
  * Fix disk size calculations on macOS.
  * Test with lots of versions of GNU ddrescue.
  * Fix an issue with the ddrescue tools decorator.
  * Fix for ddrescue v1.18.1 - better version detection.
  * Test w/ ddrescue 1.23~rc1 and add config to support it better,
  * Find new notification backend - terminal-notifier.
  * Send sigint when stopping ddrescue instead of sigterm - less likely to cause issues.
  * Determine ddrescue version in new function & warn about prerelease versions.
  * More workarounds for ddrescue 1.23.
  * Don't ever present an empty list of choices when mounting partitions.
  * Check if it will be possible to support wxPython 4 & Py 3 combo - preliminary hacky way - it is.
  * Lots of fixes for Python 3 support.
  * The files are now compatible with both py3 and py2.
  * Test with Python 3 on various platforms.
  * Change over to new branding.
  * Show more program info in about dialog.
  * Remove old 32-bit macOS setup crud - builds are now 64-bit only for macOS 10.9+.
  * Various Py3 fixes for macOS.
  * Make better use of global menus on macOS - can do because of wxPython 4.
  * macOS: Set window focus to most recently clicked preset - better usability.
  * Unit tests: stop asking for disk names over and over again.
  * Add terminal-notifier to source tree, and use it instead of CocoaDialog (breaks macOS < 10.9 support).
  * Remove CocoaDialog from source tree.
  * Fix hdiutil resource unavailable errors on old versions of macOS.
  * Fix display bug on Fedora & GNOME 3 w/ Py3.
  * Ignore minor version differences in ddrescue.
  * Compare ddrescue versions a smarter way to avoid breaking when run with newer ddrescue versions even if there's no reason it won't work.
  * Create some tools to run privileged processes as root and get them working on Linux.
  * Write a polkit policy for Linux.
  * Make separate files for each type of program so we can have separate pkexec rules.
  * Redirect output carefully to silence error messages from pkexec.
  * Remove Linux xhost hack for Wayland - no longer needed.
  * Move auth dialog to Tools/runasroot_mac.py & modify for this purpose.
  * Stop the sudo password prompt from getting to stdout on macOS.
  * Update setup.py for py2app macOS builds.
  * Use user home directory as default file picker location - usability improvements.
  * Mount output files read-only on Linux.
  * Label the presets on settings window for extra clarity.
  * Hide the auth dialog when desired on macos.
  * Don't block the GUI thread when opening the browser.
  * Put progress %age before program name in title bar - easier to see on some platforms.
  * Clarify privacy policy.
  * Improve security by not using shell=True when running subprocesses.
  * Test changes on macOS & get deployment builds working.
  * Refactoring & fix some pylint issues.
  * Lots of improvements to documentation.
  * macOS: Don't remove cached credentials.
  * macOS: Streamline auth dialog.
  * Test on macOS with APM disks (works fine).
  * Test on macOS with APFS disks (will fix soon).
  * Fix various issues with the auth dialog on macOS.
  * New terminology: call ddrescue's log files "map files" in accordance with newer versions of ddrescue.
  * Check that hybrid MBR disks can be mounted - they can.
  * Update bundled ddrescue binary to v1.23.
  * Fix many more issues with the auth dialog.
  * Beta testing.
  * Fix very long line in about box.
  * Remove cancel button from mac auth dialog.
  * Fix macOS packaging.
  * Fix potential display glitch.
  * Fix macOS getdevinfo issues -py2app has poor support for python subprocesses.
  * macOS: Activate window on startup to stop it opening in the background.
  * Tighten & adjust polkit policy.
  * Use lsblk's JSON output for extra reliability on supported platforms (!= Ubuntu 14.04).
  * Add read() method for output parsing from WxFixBoot - fixes potential deadlock getting device info.
  * Do initial developer docs (more coming in a later release).
  * Keep asking for auth until we get it on Linux.
  * Fix some JSON parsing issues with lsblk.
  * Add check for update feature.
  * Sort partitions to mount alphabetically.
  * Re-add old code for mounting output files for Ubuntu 14.04 (no JSON output from lsblk. Sigh.).
  * Use wget to make update checker work on Ubuntu 14.04 (Python too old to support proper TLS. Sigh.).
  * Delay update checker on startup by 10 seconds.
  * Add release info details to the update checker.
  * Rename some files to make them more importable.
  * Catch generic exceptions from AST and JSON, preventing crashes.
  * Pre-authenticate before running ddresuce on macOS.
  * macOS: don't depend on being in /Applications.

DDRescue-GUI(1.7.2):
  * Changes since v1.7.1:

  * Add support for running on ddrescue 1.23.

DDRescue-GUI (1.7.1)
  * Changes since v1.7:

  * Fix a low-priority issue when running on ddrescue v1.22.

DDRescue-GUI (v1.7):
  * Changes since v1.6.1:

  * Pull in new GetDevInfo from WxFixBoot.
  * Prevent user from starting 2+ instances at once (AuthWindow fix).
  * Prevent user from accidentally overwriting the recovery log file.
  * Show how much data was recovered on FinishedWindow.
  * Improve unexpected error handling.
  * Create emergency exit function (allows easy saving of log file in situations when the GUI would otherwise hae crashed).
  * Make a algorithm for creating unique dictionary keys.
  * Use this feature for all 3 file choices.
  * Attempt to veto system shutdowns.
  * Shutdown the logging system when the system is shutting down.
  * Attempt to handle UTF-8 input from programs.
  * Start to refactor choice box handlers.
  * Fix bugs in FileChoiceHandler().
  * Auto-add file extension to logs if needed.
  * Fix Unicode char handling.
  * Move Output Box functions into custom class.
  * Update the copyright info for 2017.
  * General maintenance.
  * Report errors better in FinishedWindow().UnmountOutputFile().
  * Refactoring + Performance improvements + better error handling in FinishedWindow.MountDiskOSX/Linux().
  * Fix errors in MountDiskOSX().
  * Handle hdiutil "Resource temporarily unavailable" errors.
  * Fix some silly errors in MacRunHdiutil().
  * Fix some more bugs in MountDiskOSX().
  * Create BackendTools().SendNotification().
  * Make MainWindow wider by default.
  * Create unit test package and files.
  * Create some tests for etDevInfo.IsPartition().
  * Test unittest framework on both platforms.
  * Make unit test for GetDevInfo.GetVendor().
  * Finish basic Linux DevInfoTools tests.
  * Make unit test for GetVendor on Mac.
  * Write some OS X tests.
  * Fix OS X bug in GetDescription.
  * Make Linux LVM test (finished DevInfoTools test).
  * Put test data in separate files.
  * Make Tests.py accept options to pick test suite.
  * Start work on BackendTools tests.
  * Create 1st BackendTools test.
  * Create test for CreateUniqueKey().
  * Make notification test.
  * Make hdiutil test.
  * Make IsMounted test.
  * Make GetMountPointOf test.
  * Make basic tests for MountPartition.
  * Make tests more automated.
  * Refactor some stuff.
  * Make separate file with some functions for BackendToolsTests.
  * Don't run tests when not root.
  * Adapt GetDevInfo.GetBlockSize() so we can make a test for it.
  * Write a test for it.
  * Finish BackendTools tests.
  * Fix multiple errors in the tests.
  * Fix OS X bug in IsMounted.
  * Fix various bugs in BackendTools and fix more OS X tests.
  * Add "-d, --debug" options to enable full debug log messages in tests.
  * Re-enable StartProcess() tests. (Disabled because they're slow and were impacting dev speed).
  * Make OS X disk mounting more reliable.
  * Bump version to 1.7.
  * Merge MountDiskOSX and MountDiskLinux.
  * Fix MountDisk on Linux.
  * Fix minor bug in FileChoiceHandler.
  * Create DetermineOutputFileType().
  * Create MacGetDevAndMountPoint().
  * Update FinishedWindow panel before showing mount success dialog to fix layout glitch.
  * Refactoring in MountDisk().
  * Fix silly errors in MountDisk().
  * Test MountDisk().
  * Fix some bugs in UnmountOutputFile().
  * Improve reliability with unsupported versions of ddrescue.
  * Organise ddrescue output-grabbing functions in separate files (see commit history for more details).
  * Check ddrescue version on startup and warn user if unsupported.
  * Test this stuff on MacOS.
  * Get ddrescue functions organiser working.
  * Fix the race condition causing the "can't get initial status" error.
  * Refactoring in ProcessLine.
  * Add support for ddrescue v1.22.
  * Set time remaining to 0 when recovery is finished.
  * Fix a bug cancelling quitting from FinishedWindow.
  * Test on all ddrescue versions.
  * Check options are compatible with ddrescue 1.22.
  * Select best ddrescue tools if on an unsupported version.
  * Compile ddrescue 1.22 on OS X 10.6 and add to repo to make maintaining easier.
  * Handle Hdiutuil errors in MacRunHdiutil.
  * Link to my website instead of launchpad.
  * Add new dependencies to the OS X build scripts.
  * OS X packaging test.
  * OS X: Fix the ddrescue binary's permissions.
  * Change the "RescourcePath" variable to "ResourcePath" so it's spelt right.
  * Fix hdiutil resource temporarily unavailable error (OS X El Cap or higher, fix for older versions coming in next release).
  * Create option on DDRescue-GUI.py to run the tests, so you can do it in the OS X image too.
  * Basic tests on all OS X versions.
  * Make windows 20px wider to look better on old OS X versions.
  * Amend the privacy policy to note that the version of ddrescue is now gathered as well.
  * Fix a bug when closing from FinishedWindow.
  * Fix typo in abort code.
  * Fix a few small typos.

DDRescue-GUI 1.6.1:
  * Changes since v1.6:
  * OS X - Fix bugs preventing the use of a normal (non device) file as the input file.

DDRescue-GUI (1.6):
  * Changes since v1.5.1:

  * Fix time elapsed counter.
  * Test (again) with ddrescue v1.20.
  * Add support for ddrescue v1.21.
  * Always call wx.Panels "self.Panel".
  * Use new GetDevInfo module.
  * Use dictionaries.
  * Fix some misc bugs.
  * Don't create duplicate device entries when a device in the choice box list is manually selected by the user.
  * Fix Authentication dialog text on Fedora.
  * Don't try to unmount normal files when starting a recovery.
  * Linux: Get rid of IDE HDDD file selection filter.
  * Linux: Fix partition numbers in partition to mount choice dialog.
  * Refactoring & general maintenance.
  * Remove dependency on Parted.
  * Fix another few bugs when mounting output file on Linux.
  * Fix LVM partition descriptions.
  * Fix display glitch on Fedora 23.
  * Fixes for ddrescue 1.21.
  * OS X: Fix many misc bugs.
  * Linux: Fix a bug with unmounting output files.

DDRescue-GUI (1.5.1):

  * Changes since v1.5:
  * Fix a bug in the authentication dialog where it may fail to start DDRescue-GUI when a non-English locale is being used.

DDRescue-GUI (1.5):
  * Changes since v1.4:
  *
  * Use Cocoa Dialog (http://mstratman.github.io/cocoadialog/#) to add notifications on OS X, because it works from 10.4 onwards.
  * Add LC_ALL=C when calling lshw (GetDevInfo package), so make it work when the system language isn't English.
  * Always call parted with the "-s" flag so it never waits for user input in weird situations, making mounting output files more robust.
  * Use a thread to keep track of elapsed time because the wx.Timer seems unreliable on OS X.
  * Enable the log file option on OS X (for some reason it's just working now!).
  * Rewrite the OS X portion of the GetDevInfo package to use plists (Property Lists) because it's faster, easier and more reliable.
  * Get direct disk access working on Parted Magic (get physical block size instead of logical block size in GetDevInfo package).
  * Fix relatively unimportant GUI formatting issues when using ddrescue v1.20.
  * Enable Reverse option on OS X (give ddrescue disk size cos it can't calculate it).
  * Detach images when mounting fails on OS X, allowing the user to try again in some circumstances.
  * Fix crash when resizing main window during recovery (wxpython 3.x, Linux only).
  * Get \r (carriage return) and \x1b[a (up one line) working in the output box, so ddrescue's output is now displayed exactly the same as when run from a terminal.
  * Fix high CPU Usage on OS X.
  * Fix memory leak on OS X.
  * Fix big delay before first GUI update on OS X.
  * Build ddrescue v1.20 fat binary (32-bit and 64-bit) for OS X.
  * Get Reverse and Preallocate working again on OS X.
  * Make output box work like a terminal on OS X.
  * Fix detecting of complete recovery with all data on OS X.
  * Make SettingsWindow remember settings if the user navigates back to it later.
  * Stop the user from changing the insertion point in the output box and messing up the formatting by accident.
  * If ddrescue won't exit, prompt user to wait or try again rather than waiting indefinitely until it stops.
  * Don't let the user save outputfile, logfile to /root on Parted Magic because the lack of space will cause the recovery to stop quickly.
  * Fix elapsed time counter.
  * Make sure to destroy dialogs after using them to free up memory.
  * Fix a few last-minute bugs with the settings window.

DDRescue-GUI (1.4):

  * Changes since 1.3:
  * Credit Minnie McIntyre-Bhatty for the idea for the splash screen, and for GUI design in this new version.
  * Credit Holly McIntyre-Bhatty for logo and splash screen design in the about box as well as the release page.
  * Update code (remove dependency on wx.lib.pubsub.Publisher()).
  * Update about box.
  * Use sizers with the Device Information Window.
  * Redesign the Preferences Window, and also switch to using sizers.
  * Redesign the Device Info Window.
  * Integrate the new device detection method into DDRescue-GUI (imported from Wine Autostart 2.0~rc1) (MainWindow, and DeviceInfoWindow)
  * Rewrite the finished window with sizers.
  * Write logging information in, and add support for logging to /var/log/ddrescue-gui.log
  * Do some future-proofing for python 3, including:
  * Using the new absolute import statement,
  * Using the new print function,
  * Use only unicode strings and literals, internally dropping all ASCII strings.
  * Update file choice wildcards for easier use.
  * Use one button for both starting and aborting recovery.
  * Get the Device Information Window to display properly on OS X (call self.DevInfoPanel.Layout(), and I now do this for every panel).
  * Use docstrings at the start of functions and methods, instead of comments.
  * Make the new device detection system work on OS X.
  * Make the file choices more intelligent.
  * Write logging stuff into the new device detection system.
  * Redesign the main window.
  * Remove all dependence on listdevices.sh and getblocksize.sh
  * Get detailed recovery info working in the ListCtrl.
  * Fully integrate the icon into the GUI.
  * Remove the log file when exiting rather than when starting.
  * Redesign the arrows on MainWindow.
  * Make the wx.ListCtrls resize automatically.
  * Make the main listctrl and the outputbox look nice in the GUI, and work together in a better way.
  * Fix an important UI bug that occurs only when running a wxPython version newer than 2.8.12.1 (Only affects 1.4~rc1 active development, but not v1.3)
  * Fix another UI bug with the throbber for Ubuntu 14.10 and 15.04 (Only affects 1.4~rc1 active development, but not v1.3).
  * Unmount devices before attempting to recover any data.
  * Disable the new settings button during a recovery.
  * Enable experimental support for direct disk access (not yet tested on OS X)
  * Fix a variety of bugs, and make the dialog messages more simple and clear-cut.
  * Get the output box working fully.
  * Compile new ddrescue (1.19) for OS X.
  * Test the internal tools module on OS X.
  * Design a plan for the new OS X authentication Dialog.
  * Add OS X support in the new backend.
  * Remove the old backend code.
  * Remove startddrescue.sh
  * Get the elapsed time counter working.
  * Improve Linux mount support.
  * Remove the separate Partition view Window, replacing it with a wx.SingleChoiceDialog() (I didn't know this existed at the time).
  * Get rid of the temporary directory (no longer needed).
  * Implement support for direct disk access for both Linux and OS X.
  * Make an image for the DMG installer for OS X, simplifying installation.
  * Create and semi-finalize the new authentication dialog.
  * Remove a dependency on the "platform" module, instead using wx.PlatformInfo, and saving some RAM.
  * Fix a number of OS X specific GUI bugs, and make the GUI more intuitive for Mac users.
  * Add support for mounting finished (or semi-finished) images on OS X (Like on Linux in v1.3).
  * Write the privacy policy.
  * Update the image for the DMG installer.

DDRescue-GUI (1.3):

  * Option to mount a completed image (Linux only).
  * Implement not allowing quiting the program during recovery.
  * Implement restart when ddrescue doesn't start.
  * Full testing on Mac version.
  * Complete Mac version.
  * Implement graphical sudo for Mac (requires admin permissions).

DDRescue-GUI (1.3~rc2):

  * A lot of bug fixes.
  * OS X disk size calculation (ddrescue cannot determine size, but stops at the right time)
  * Compiled ddrescue on OS X Mavericks.
  * Detect which OS is being used (Mac or Linux), and execute certain parts of script accordingly.
  * Modify splash to work on Mac.
  * New Device Information dialog (looks the same as the old one, but works on mac, no longer requiring zenity), also including refresh button.
  * Fixed indentation errors.
  * Include devices in output file choice (with warning).
  * Fix close button not triggering exit method.
  * Exit method now includes "are you sure?" dlg.
  * Option to recover another image when finished.
  * Policy Kit now supported, dumped gksudo.
  * Busy cursor during recovery.
  * 1st mac packaging test.
  * Have a "Stopping ddrescue..." label when aborting recovery.
  * No longer use shell=True in subprocess module, where possible.

DDRescue-GUI (1.3~rc1):

  * Fixed many bugs.
  * OS detection is now functional (Linux or Mac)
  * New cross-mpatible device info dialog, no longer needing zenity
  * Devices included in output choice (with warning)
  * Recovering another image before exit is now supported (UNTESTED)
  * Are you sure dlg on exit
  * Partial compatibility with OS X Mavericks (with precompiled ddrescue)

DDRescue-GUI (1.2):

  * Fixed many bugs.
  * Layout problems fixed.
  * Added presets to preferences dialog.
  * Lower CPU and RAM usage.
  * Support for viewing terminal output.
  * new about dialog.
  * Reorganized preferences dialog.
  * Now uses notifications.

DDRescue-GUI (1.1):

  * Fixed several bugs.
  * First version to work with Parted Magic.

DDRescue-GUI (1.0):

  * Initial stable release

DDRescue-GUI (0.9):

  * Initial development release
