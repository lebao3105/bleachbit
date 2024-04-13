# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-


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
Preferences dialog
"""

from bleachbit import _, _p, online_update_notification_enabled
from bleachbit.Options import options
from bleachbit import GuiBasic

import wx
import logging
import os

if 'nt' == os.name:
    from bleachbit import Windows
if 'posix' == os.name:
    from bleachbit import Unix

logger = logging.getLogger(__name__)

LOCATIONS_WHITELIST = 1
LOCATIONS_CUSTOM = 2


class PreferencesDialog:

    """Present the preferences dialog and save changes"""

    def __init__(self, parent, cb_refresh_operations):
        self.cb_refresh_operations = cb_refresh_operations

        self.parent = parent
        self.dialog = wx.Dialog(parent, style=wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX, title=_("Preferences"))
        self.dialog.SetMinSize((600, 400))
        sz = wx.BoxSizer(wx.VERTICAL)

        # Construct a notebook widget
        # It must be made as a class variable for place other widgets
        # inside the notebook (and sets the notebook as their 'parent' as well)
        self.notebook = wx.Notebook(self.dialog)
        self.notebook.AddPage(self.__general_page(), _("General"), True)
        self.notebook.AddPage(self.__locations_page(LOCATIONS_CUSTOM), _("Custom"))
        self.notebook.AddPage(self.__drives_page(), _("Drives"))
        if 'posix' == os.name:
            self.notebook.AddPage(self.__languages_page(), _("Languages"))
        self.notebook.AddPage(self.__locations_page(LOCATIONS_WHITELIST), _("Whitelist"))
        sz.Add(self.notebook, 1, wx.EXPAND|wx.ALL, 5)

        self.refresh_operations = False

        dlgBox = wx.StdDialogButtonSizer()
        dlgBox.AddButton(wx.Button(self.dialog, wx.ID_CLOSE))
        dlgBox.Realize()
        sz.Add(dlgBox, 0, wx.EXPAND, 5)

        self.dialog.SetSizer(sz)
        self.dialog.Layout()

    def __del__(self):
        """Destructor called when the dialog is closing"""
        if self.refresh_operations:
            # refresh the list of cleaners
            self.cb_refresh_operations()

    def __toggle_callback(self, path):
        """Callback function to toggle option"""
        options.toggle(path)
        if online_update_notification_enabled:
            self.cb_beta.SetCanFocus(options.get('check_online_updates'))
            if 'nt' == os.name: self.cb_winapp2.SetCanFocus( options.get('check_online_updates'))

        if 'auto_hide' == path:
            self.refresh_operations = True

        if 'debug' == path:
            from bleachbit.Log import set_root_log_level
            set_root_log_level(options.get('debug'))

        if 'kde_shred_menu_option' == path:
            from bleachbit.DesktopMenuOptions import install_kde_service_menu_file
            install_kde_service_menu_file()

    def __general_page(self):
        """Return a widget containing the general page"""

        panel = wx.Panel(self.notebook)
        vbox = wx.BoxSizer(wx.VERTICAL)

        if online_update_notification_enabled:
            cb_updates = wx.CheckBox(panel, label= _("Check periodically for software updates via the Internet"))
            cb_updates.SetValue(options.get('check_online_updates'))
            cb_updates.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('check_online_updates'))
            cb_updates.SetToolTip(wx.ToolTip(
                _("If an update is found, you will be given the option to view information about it.  Then, you may manually download and install the update.")))
            vbox.Add(cb_updates, 0, wx.ALL, 5)

            updates_box = wx.BoxSizer(wx.VERTICAL)

            self.cb_beta = wx.CheckBox(panel, label=_("Check for new beta releases"))
            self.cb_beta.SetValue(options.get('check_beta'))
            self.cb_beta.SetCanFocus(options.get('check_online_updates'))
            self.cb_beta.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('check_beta'))
            updates_box.Add(self.cb_beta, 0, wx.ALL, 5)

            if 'nt' == os.name:
                self.cb_winapp2 = wx.CheckBox(panel, label=_("Download and update cleaners from community (winapp2.ini)"))
                self.cb_winapp2.SetValue(options.get('update_winapp2'))
                self.cb_winapp2.SetCanFocus(options.get('check_online_updates'))
                self.cb_winapp2.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('update_winapp2'))
                updates_box.Add(self.cb_winapp2, 0, wx.ALL, 5)

            vbox.Add(updates_box, 0, wx.ALL, 5)

        # TRANSLATORS: This means to hide cleaners which would do
        # nothing.  For example, if Firefox were never used on
        # this system, this option would hide Firefox to simplify
        # the list of cleaners.
        cb_auto_hide = wx.CheckBox(panel, label=_("Hide irrelevant cleaners"))
        cb_auto_hide.SetValue(options.get('auto_hide'))
        cb_auto_hide.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('auto_hide'))
        vbox.Add(cb_auto_hide, 0, wx.ALL, 5)

        # TRANSLATORS: Overwriting is the same as shredding.  It is a way
        # to prevent recovery of the data. You could also translate
        # 'Shred files to prevent recovery.'
        cb_shred = wx.CheckBox(panel, label=_("Overwrite contents of files to prevent recovery"))
        cb_shred.SetValue(options.get('shred'))
        cb_shred.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('shred'))
        cb_shred.SetToolTip(wx.ToolTip(
            _("Overwriting is ineffective on some file systems and with certain BleachBit operations.  Overwriting is significantly slower.")))
        vbox.Add(cb_shred, 0, wx.ALL, 5)

        # Close the application after cleaning is complete.
        cb_exit = wx.CheckBox(panel, label=_("Exit after cleaning"))
        cb_exit.SetValue(options.get('exit_done'))
        cb_exit.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('exit_done'))
        vbox.Add(cb_exit, 0, wx.ALL, 5)

        # Disable delete confirmation message.
        cb_popup = wx.CheckBox(panel, label=_("Confirm before delete"))
        cb_popup.SetValue(options.get('delete_confirmation'))
        cb_popup.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('delete_confirmation'))
        vbox.Add(cb_popup, 0, wx.ALL, 5)

        # Use base 1000 over 1024?
        cb_units_iec = wx.CheckBox(panel, 
            label=_("Use IEC sizes (1 KiB = 1024 bytes) instead of SI (1 kB = 1000 bytes)"))
        cb_units_iec.SetValue(options.get("units_iec"))
        cb_units_iec.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('units_iec'))
        vbox.Add(cb_units_iec, 0, wx.ALL, 5)

        # Remember window geometry (position and size)
        self.cb_geom = wx.CheckBox(panel, label=_("Remember window geometry"))
        self.cb_geom.SetValue(options.get("remember_geometry"))
        self.cb_geom.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('remember_geometry'))
        vbox.Add(self.cb_geom, 0, wx.ALL, 5)

        # Debug logging
        cb_debug = wx.CheckBox(panel, label=_("Show debug messages"))
        cb_debug.SetValue(options.get("debug"))
        cb_debug.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('debug'))
        vbox.Add(cb_debug, 0, wx.ALL, 5)

        # KDE context menu shred option
        cb_kde_shred_menu_option = wx.CheckBox(panel, label=_("Add shred context menu option (KDE Plasma specific)"))
        cb_kde_shred_menu_option.SetValue(options.get("kde_shred_menu_option"))
        cb_kde_shred_menu_option.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('kde_shred_menu_option'))
        vbox.Add(cb_kde_shred_menu_option, 0, wx.ALL, 5)

        panel.SetSizer(vbox)
        panel.Layout()
        panel.Center()
    
        return panel

    def __drives_page(self):
        """Return widget containing the drives page"""

        panel = wx.Panel(self.notebook)

        def add_drive_cb(evt):
            """Callback for adding a drive"""
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(self.parent, title, multiple=False)
            if pathname:
                liststore.AppendItems([pathname])
                pathnames.append(pathname)
                options.set_list('shred_drives', pathnames)

        def remove_drive_cb(evt):
            """Callback for removing a drive"""
            selection = liststore.GetStringSelection()
            if not selection: return
            liststore.Delete(pathnames.index(selection))
            pathnames.remove(selection)
            options.set_list('shred_drives', pathnames)

        vbox = wx.BoxSizer(wx.VERTICAL)

        # TRANSLATORS: 'free' means 'unallocated'
        notice = wx.StaticText(panel, label=_(
            "Choose a writable folder for each drive for which to overwrite free space."))
        vbox.Add(notice, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)

        pathnames = options.get_list('shred_drives')
        # Changes from the old GTK version: wxListBox has wxLB_SORT flag which will sort
        # the list for us, so no need to run sorted() anymore

        liststore = wx.ListBox(panel, choices=pathnames,
                               style=wx.LB_SINGLE | wx.LB_HSCROLL | wx.LB_NEEDED_SB | wx.LB_SORT)

        vbox.Add(liststore, 1, wx.ALL|wx.EXPAND, 5)

        # Add page buttons
        button_add = wx.Button(panel, wx.ID_ADD)
        button_add.Bind(wx.EVT_BUTTON, add_drive_cb)

        button_remove = wx.Button(panel, wx.ID_REMOVE)
        button_remove.Bind(wx.EVT_BUTTON, remove_drive_cb)

        button_box = wx.BoxSizer()
        button_box.Add(button_add, flag=wx.ALL | wx.EXPAND)
        button_box.Add(button_remove, flag=wx.ALL | wx.EXPAND)
        vbox.Add(button_box, flag=wx.ALL | wx.EXPAND)
        
        panel.SetSizer(vbox)
        panel.Layout()
        panel.Center()

        return panel

    def __languages_page(self):
        """Return widget containing the languages page"""

        def preserve_toggled_cb(evt):
            """Callback for toggling the 'preserve' column"""
            item = liststore.GetItem(evt.index)
            options.set_language(liststore.GetItemText(item), liststore.IsItemChecked(item))

        panel = wx.Panel(self.notebook)
        vbox = wx.BoxSizer(wx.VERTICAL)

        notice = wx.StaticText(panel, label=_("All languages will be deleted except those checked."))
        vbox.Add(notice, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)

        liststore = wx.ListCtrl(panel)
        liststore.EnableCheckBoxes(True)
        liststore.Bind(wx.EVT_LIST_ITEM_CHECKED, preserve_toggled_cb)
        liststore.Bind(wx.EVT_LIST_ITEM_UNCHECKED, preserve_toggled_cb)

        # create column views and populate items
        liststore.InsertColumn(0, _("Code"))
        liststore.InsertColumn(1, _("Name"))

        for lang, native in sorted(Unix.locales.native_locale_names.items()):
            index = liststore.InsertItem(liststore.GetItemCount(), lang)
            liststore.SetItem(index, 1, native)
            liststore.CheckItem(index, options.get_language(lang))

        vbox.Add(liststore, 1, wx.ALL|wx.EXPAND, 5)

        # finish
        panel.SetSizer(vbox)
        panel.Layout()
        panel.Center()
        return panel

    def __locations_page(self, page_type):
        """Return a widget containing a list of files and folders"""

        def add_file_cb(evt):
            """Callback for adding a file"""
            title = _("Choose a file")
            pathname = GuiBasic.browse_file(self.parent, title)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        logger.warning(
                            "'%s' already exists in whitelist", pathname)
                        return
                liststore.SetItem(liststore.InsertItem(liststore.GetItemCount(), _("File")), 1, pathname)
                pathnames.append(['file', pathname])
                options.set_whitelist_paths(pathnames)

        def add_folder_cb(evt):
            """Callback for adding a folder"""
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(self.parent, title, multiple=False)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        logger.warning(
                            "'%s' already exists in whitelist", pathname)
                        return
                liststore.SetItem(liststore.InsertItem(liststore.GetItemCount(), _("Folder")), 1, pathname)
                pathnames.append(['folder', pathname])
                options.set_whitelist_paths(pathnames)

        def remove_path_cb(evt):
            """Callback for removing a path"""
            selection = liststore.GetItem(evt.index)
            for this_pathname in pathnames:
                if this_pathname[1] == liststore.GetItemText(selection):
                    pathnames.remove(this_pathname)
                    options.set_whitelist_paths(pathnames)
                    liststore.DeleteItem(selection)

        # def add_custom_file_cb(evt):
        #     """Callback for adding a file"""
        #     pathname = GuiBasic.browse_file(self.parent, _("Choose a file"))
        #     if pathname:
        #         for this_pathname in pathnames:
        #             if pathname == this_pathname[1]:
        #                 logger.warning(
        #                     "'%s' already exists in whitelist", pathname)
        #                 return
        #         liststore.SetItem(liststore.InsertItem(liststore.GetItemCount(), _("File")), 1, pathname)
        #         pathnames.append(['file', pathname])
        #         options.set_custom_paths(pathnames)

        # def add_custom_folder_cb(button):
        #     """Callback for adding a folder"""
        #     title = _("Choose a folder")
        #     pathname = GuiBasic.browse_folder(self.parent, title,
        #                                       multiple=False, stock_button=Gtk.STOCK_ADD)
        #     if pathname:
        #         for this_pathname in pathnames:
        #             if pathname == this_pathname[1]:
        #                 logger.warning(
        #                     "'%s' already exists in whitelist", pathname)
        #                 return
        #         liststore.append([_('Folder'), pathname])
        #         pathnames.append(['folder', pathname])
        #         options.set_custom_paths(pathnames)

        # def remove_custom_path_cb(button):
        #     """Callback for removing a path"""
        #     treeselection = treeview.get_selection()
        #     (model, _iter) = treeselection.get_selected()
        #     if None == _iter:
        #         # nothing selected
        #         return
        #     pathname = model[_iter][1]
        #     liststore.remove(_iter)
        #     for this_pathname in pathnames:
        #         if this_pathname[1] == pathname:
        #             pathnames.remove(this_pathname)
        #             options.set_custom_paths(pathnames)

        panel = wx.Panel(self.notebook)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # load data
        if LOCATIONS_WHITELIST == page_type:
            pathnames = options.get_whitelist_paths()
        elif LOCATIONS_CUSTOM == page_type:
            pathnames = options.get_custom_paths()

        liststore = wx.ListCtrl(panel)

        # create column views
        liststore.InsertColumn(0, _("Type"))
        liststore.InsertColumn(1, _("Path"))

        # populate datas
        for paths in pathnames:
            type_code: str = paths[0]
            type_str = None
            
            if not type_code in ['file', 'folder']:
                raise RuntimeError("Invalid type code: '%s'" % type_code)
            else:
                type_str = _(type_code.capitalize())

            path = paths[1]
            idx = liststore.InsertItem(liststore.GetItemCount(), type_str)
            liststore.SetItem(idx, 1, path)

        if LOCATIONS_WHITELIST == page_type:
            # TRANSLATORS: "Paths" is used generically to refer to both files
            # and folders
            notice = wx.StaticText(panel, label=_("These paths will not be deleted or modified."))
        elif LOCATIONS_CUSTOM == page_type:
            notice = wx.StaticText(panel, label=_("These locations can be selected for deletion."))

        vbox.Add(notice, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)
        vbox.Add(liststore, 1, wx.ALL|wx.EXPAND, 5)

        # buttons that modify the list
        button_add_file = wx.Button(panel, label=_p('button', 'Add file'))
        button_add_file.Bind(wx.EVT_BUTTON, add_file_cb)

        button_add_folder = wx.Button(panel, label=_p('button', 'Add folder'))
        button_add_folder.Bind(wx.EVT_BUTTON, add_folder_cb)

        button_remove = wx.Button(panel, label=_p('button', 'Remove'))
        button_remove.Bind(wx.EVT_BUTTON, remove_path_cb)

        button_box = wx.BoxSizer()
        button_box.Add(button_add_file, 0, wx.ALL, 5)
        button_box.Add(button_add_folder, 0, wx.ALL, 5)
        button_box.Add(button_remove, 0, wx.ALL, 5)
        vbox.Add(button_box, 0, wx.ALL | wx.EXPAND, 5)

        # return page
        panel.SetSizer(vbox)
        panel.Layout()
        panel.Center()
        return panel

    def run(self):
        """Run the dialog"""
        return self.dialog.Show()