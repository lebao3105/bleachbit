#!/usr/bin/python3
# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2023 Andrew Ziem
# https://www.bleachbit.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
wxPython graphical user interface
"""

from bleachbit import GuiBasic
from bleachbit import Cleaner, FileUtilities
from bleachbit import _, APP_NAME, appicon_path, portable_mode
from bleachbit.Options import options, init_configuration

# Now that the configuration is loaded, honor the debug preference there.
from bleachbit.Log import set_root_log_level
set_root_log_level(options.get('debug'))

from bleachbit.GuiPreferences import PreferencesDialog
from bleachbit.Cleaner import backends, register_cleaners
import bleachbit

import glob
import logging
import os
import sys
import threading
import time

import wx
import wx.adv
import wx.dataview
import wx.html
import wx.xrc

from libtextworker.interface.wx.miscs import XMLBuilder

if os.name == 'nt':
    from bleachbit import Windows

logger = logging.getLogger(__name__)


def threaded(func):
    """Decoration to create a threaded function"""
    def wrapper(*args):
        thread = threading.Thread(target=func, args=args)
        thread.start()
    return wrapper


def notify(msg):
    """Show a popup-notification"""
    return wx.adv.NotificationMessage(
        title=APP_NAME,
        message=msg,
        parent=None
    ).Show(10000)


class Bleachbit(wx.App, XMLBuilder):
    mainFrame = None # Replaces _window
    guilog = None # Replaces gtklog
    _shred_paths = None
    _auto_exit = False

    def __init__(self, uac=True, shred_paths=None, auto_exit=False):

        wx.App.__init__(self)
        XMLBuilder.__init__(self, None, bleachbit.app_window_filename)
        self.SetClassName(APP_NAME)
        
        # This is used for automated testing of whether the GUI can start.
        # It is called from assert_execute_console() in windows/setup_py2exe.py
        self._auto_exit = auto_exit      

        self._shred_paths = shred_paths

        if os.name == 'nt':
            # clean up nonce files https://github.com/bleachbit/bleachbit/issues/858
            import atexit
            atexit.register(Windows.cleanup_nonce)

        # Do some startup checks
        from bleachbit.General import startup_check
        startup_check()
        
        # Setup logging (redirect output to a window)
        from bleachbit.Log import GUILoggerHandler, DelayLog
        self.guilog = GUILoggerHandler(self.append_text)
        logging.getLogger('bleachbit').addHandler(self.guilog)
        
        if isinstance(sys.stderr, DelayLog):
            for msg in sys.stderr.read():
                self.append_text(msg)
            # if stderr was redirected - keep that
            sys.stderr = self.guilog
        
        # Reset options if they are corrupted
        if options.is_corrupt():
            logger.error(
                _('Resetting the configuration file because it is corrupt: %s'),
                bleachbit.options_file)
            init_configuration()
        
        wx.CallAfter(self.cb_refresh_operations)
        
    def WindInit(self):
        self.mainFrame: wx.Frame = self.loadObject('MainFrame', 'wxFrame')
        
        screen = wx.DisplaySize()
        self.mainFrame.SetSize(width=min(screen[0], 800),
                               height=min(screen[1], 600))
        
        if os.path.exists(appicon_path):
            self.mainFrame.SetIcon(wx.Icon(appicon_path))
        
        opts_menu = self.mainFrame.GetMenuBar().GetMenu(0)
        help_menu = self.mainFrame.GetMenuBar().GetMenu(1)
        self.tree = self.mainFrame.GetChildren()[0]
        self.textbuffer = self.mainFrame.GetChildren()[1]
        
        actions = [(self.cb_shred_file, 0), (self.cb_shred_folder, 1), (self.cb_shred_clipboard, 2),
                   (self.cb_wipe_free_space, 3), (self.cb_make_chaff, 4), (self.cb_shred_quit, 5),
                   (self.quit, 7), (self.cb_preferences_dialog, 10), (self.get_system_information_dialog, 12),
                   (self.cb_help, 13), (self.get_about_dialog, 14)]
        
        for callback, pos in actions:
            if pos < 10:
                self.mainFrame.Bind(wx.EVT_MENU, callback, opts_menu.FindItemByPosition(pos))
            else:
                self.mainFrame.Bind(wx.EVT_MENU, callback, help_menu.FindItemByPosition(pos - 10))
        
        if os.name == 'nt': Windows.check_dll_hijacking(self.mainFrame)
        
        self.ShowSplashScreen()
        self.SetTopWindow(self.mainFrame)
        self.mainFrame.Centre()
        self.mainFrame.Show()
        
        wx.CallAfter(self.cb_refresh_operations)

    def ShowSplashScreen(self):
        """
        Shows a splash screen on Windows.
        """
        if os.name != 'nt': return # Probably we should use PNG on all platforms (splash screen now uses .ico)
        bleachbit.SplashScreen(self.mainFrame).Show()

    def shred_paths(self, paths, shred_settings=False):
        """
        Shred files or folders
        When shred_settings=True: returns the user opition as a boolean.
        """
        # create a temporary cleaner object
        backends['_gui'] = Cleaner.create_simple_cleaner(paths)

        # preview and confirm
        operations = {'_gui': ['files']}
        self.preview_or_run_operations(False, operations)

        if self._confirm_delete(False, shred_settings):
            # delete
            self.preview_or_run_operations(True, operations)
            if shred_settings:
                return True

        if self._auto_exit:
            wx.CallAfter(self.quit)

        # user aborted
        return False
    
    def append_text(self, text, tag=None, __iter=None, scroll=True):
        """Add some text to the main log"""
        if self.textbuffer is None:
            # textbuffer was destroyed.
            return
        if not __iter:
            __iter = self.textbuffer.get_end_iter()
        if tag:
            self.textbuffer.insert_with_tags_by_name(__iter, text, tag)
        else:
            self.textbuffer.insert(__iter, text)
        # Scroll to end.  If the command is run directly instead of
        # through the idle loop, it may only scroll most of the way
        # as seen on Ubuntu 9.04 with Italian and Spanish.
        if scroll:
            wx.CallAfter(lambda: self.textbuffer is not None and
                          self.textview.scroll_mark_onscreen(
                              self.textbuffer.get_insert()))
    
    def update_log_level(self):
        """Is the log level changed via the preferences."""
        self.guilog.update_log_level()
    
    """
    Event callbacks
    """
    
    def cb_refresh_operations(self):
        """Callback to refresh the list of cleaners"""
        # Is this the first time in this session?
        if not hasattr(self, 'recognized_cleanerml') and not self._auto_exit:
            from bleachbit import RecognizeCleanerML
            RecognizeCleanerML.RecognizeCleanerML()
            self.recognized_cleanerml = True
        # reload cleaners from disk
        # self.view.expand_all()
        # self.progressbar.show()
        # rc = register_cleaners(self.update_progress_bar,
        #                        self.cb_register_cleaners_done)
        # wx.CallAfter(rc.__next__)
        # return False

    def cb_help(self, event):
        """Callback for help"""
        GuiBasic.open_url(bleachbit.help_contents_url, self.mainFrame)

    def cb_make_chaff(self, event):
        """Callback to make chaff"""
        from bleachbit.GuiChaff import ChaffDialog
        cd = ChaffDialog(self.mainFrame)
        cd.run()

    def cb_shred_file(self, event):
        """Callback for shredding a file"""

        # get list of files
        paths = GuiBasic.browse_files(self.mainFrame, _('Choose files to shred'))
        if not paths:
            return
        self.shred_paths(self.mainFrame, paths)

    def cb_shred_folder(self, event):
        """Callback for shredding a folder"""

        paths = GuiBasic.browse_folder(self.mainFrame,
                                       _('Choose folder to shred'),
                                       multiple=True,
                                       stock_button=_('_Delete'))
        if not paths:
            return
        self.shred_paths(self.mainFrame, paths)

    def cb_shred_clipboard(self, event):
        """Callback for menu option: shred paths from clipboard"""
        text_data = wx.TextDataObject()
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(text_data)
            wx.TheClipboard.Close()
        if success:
            return self.cb_clipboard_uri_received(text_data.GetText())

    def cb_clipboard_uri_received(self, clipboard: str):
        """Callback for when URIs are received from clipboard"""
        # Needs a test
        shred_paths = FileUtilities.uris_to_paths(clipboard)
        if shred_paths:
            self.shred_paths(self.mainFrame, shred_paths)
        else:
            logger.warning(_('No paths found in clipboard.'))

    def cb_shred_quit(self, event):
        """Shred settings (for privacy reasons) and quit"""
        # build a list of paths to delete
        paths = []
        if os.name == 'nt' and portable_mode:
            # in portable mode on Windows, the options directory includes
            # executables
            paths.append(bleachbit.options_file)
            if os.path.isdir(bleachbit.personal_cleaners_dir):
                paths.append(bleachbit.personal_cleaners_dir)
            for f in glob.glob(os.path.join(bleachbit.options_dir, "*.bz2")):
                paths.append(f)
        else:
            paths.append(bleachbit.options_dir)

        # prompt the user to confirm
        if not self.shred_paths(paths, True):
            logger.debug('user aborted shred')
            # aborted
            return

        # Quit the application through the idle loop to allow the worker
        # to delete the files.  Use the lowest priority because the worker
        # uses the standard priority. Otherwise, this will quit before
        # the files are deleted.
        #
        # Rebuild a minimal bleachbit.ini when quitting
        # GLib.idle_add(self.quit, None, None, True,
        #               priority=GObject.PRIORITY_LOW)

    def cb_wipe_free_space(self, event):
        """callback to wipe free space in arbitrary folder"""
        path = GuiBasic.browse_folder(self.mainFrame,
                                      _("Choose a folder"),
                                      multiple=False, stock_button=_('_OK'))
        if not path:
            # user cancelled
            return

        backends['_gui'] = Cleaner.create_wipe_cleaner(path)

        # execute
        operations = {'_gui': ['free_disk_space']}
        self.mainFrame.preview_or_run_operations(True, operations)

    def cb_preferences_dialog(self, event):
        """Callback for preferences dialog"""
        pref = PreferencesDialog(self.mainFrame, self.cb_refresh_operations)
        pref.run()

        # In case the user changed the log level...
        self.update_log_level()

    def get_about_dialog(self, event):
        info = wx.adv.AboutDialogInfo()
        info.SetName(APP_NAME)
        info.SetVersion(bleachbit.APP_VERSION)
        info.SetDescription(_("Program to clean unnecessary files"))
        info.SetCopyright('Copyright (C) 2008-2023 Andrew Ziem')
        info.SetWebSite(bleachbit.APP_URL)
        
        try:
            with open(bleachbit.license_filename) as f_license:
                info.SetLicense(f_license.read())
        except (IOError, TypeError):
            info.SetLicense(
                _("GNU General Public License version 3 or later.\nSee https://www.gnu.org/licenses/gpl-3.0.txt"))
            
        # dialog.set_name(APP_NAME)
        # TRANSLATORS: Maintain the names of translators here.
        # Launchpad does this automatically for translations
        # typed in Launchpad. This is a special string shown
        # in the 'About' box.
        # dialog.set_translator_credits(_("translator-credits"))
        if appicon_path and os.path.exists(appicon_path):
            icon = wx.Icon(appicon_path)
            info.SetIcon(icon)
        
        return wx.adv.AboutBox(info, self.mainFrame)

    def quit(self, evt=None, init_settings=False):
        if init_settings: init_configuration()
        self.mainFrame.Destroy()

    def get_system_information_dialog(self, event):
        """Show system information dialog"""
        from bleachbit import SystemInformation
        dialog = wx.Dialog(self.mainFrame,
                           title=_("System infomation"),
                           size=(600, 400))
        
        sizer = wx.BoxSizer()
        txt = SystemInformation.get_system_information()
        textview = wx.TextCtrl(dialog, value=txt, style=wx.TE_MULTILINE | wx.TE_READONLY)
        
        bottombar = wx.StdDialogButtonSizer()
        copybtn = wx.Button(dialog, wx.ID_COPY)
        
        def copyText(evt):
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(txt))
                wx.TheClipboard.Close()
                
        copybtn.Bind(wx.EVT_BUTTON, copyText)
        
        bottombar.AddButton(copybtn)
        bottombar.Realize()
        
        sizer.Add(textview, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(bottombar, 0, wx.EXPAND, 5)
        
        dialog.SetSizer(sizer)
        dialog.Layout()
        dialog.Centre()
        
        return dialog.ShowModal()
