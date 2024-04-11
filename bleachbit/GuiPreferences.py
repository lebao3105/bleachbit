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
        self.dialog = wx.Dialog(parent, title=_("Preferences"))
        self.dialog.SetSize(300, 200)

        # Construct a notebook widget
        # It must be made as a class variable for place other widgets
        # inside the notebook (and sets the notebook as their 'parent' as well)
        self.notebook = wx.Notebook()
        self.notebook.AddPage(self.__general_page(), _("General"), True)
        self.notebook.AddPage(self.__locations_page(LOCATIONS_CUSTOM), _("Custom"))
        self.notebook.AddPage(self.__drives_page(), _("Drives"))
        if 'posix' == os.name:
            self.notebook.AddPage(self.__languages_page(), _("Languages"))
        self.notebook.AddPage(self.__locations_page(LOCATIONS_WHITELIST), _("Whitelist"))

        self.refresh_operations = False

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
            vbox.Add(cb_updates, flag=wx.ALL | wx.EXPAND)

            updates_box = wx.BoxSizer(wx.VERTICAL)

            self.cb_beta = wx.CheckBox(panel, label=_("Check for new beta releases"))
            self.cb_beta.SetValue(options.get('check_beta'))
            self.cb_beta.SetCanFocus(options.get('check_online_updates'))
            self.cb_beta.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('check_beta'))
            updates_box.Add(self.cb_beta, flag=wx.ALL | wx.EXPAND)

            if 'nt' == os.name:
                self.cb_winapp2 = wx.CheckBox(panel, label=_("Download and update cleaners from community (winapp2.ini)"))
                self.cb_winapp2.SetValue(options.get('update_winapp2'))
                self.cb_winapp2.SetCanFocus(options.get('check_online_updates'))
                self.cb_winapp2.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('update_winapp2'))
                updates_box.Add(self.cb_winapp2, flag=wx.ALL | wx.EXPAND)

            vbox.Add(updates_box, flag=wx.ALL | wx.EXPAND)

        # TRANSLATORS: This means to hide cleaners which would do
        # nothing.  For example, if Firefox were never used on
        # this system, this option would hide Firefox to simplify
        # the list of cleaners.
        cb_auto_hide = wx.CheckBox(panel, label=_("Hide irrelevant cleaners"))
        cb_auto_hide.SetValue(options.get('auto_hide'))
        cb_auto_hide.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('auto_hide'))
        vbox.Add(cb_auto_hide, flag=wx.ALL | wx.EXPAND)

        # TRANSLATORS: Overwriting is the same as shredding.  It is a way
        # to prevent recovery of the data. You could also translate
        # 'Shred files to prevent recovery.'
        cb_shred = wx.CheckBox(panel, label=_("Overwrite contents of files to prevent recovery"))
        cb_shred.SetValue(options.get('shred'))
        cb_shred.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('shred'))
        cb_shred.SetToolTip(wx.ToolTip(
            _("Overwriting is ineffective on some file systems and with certain BleachBit operations.  Overwriting is significantly slower.")))
        vbox.Add(cb_shred, flag=wx.ALL | wx.EXPAND)

        # Close the application after cleaning is complete.
        cb_exit = wx.CheckBox(panel, label=_("Exit after cleaning"))
        cb_exit.SetValue(options.get('exit_done'))
        cb_exit.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('exit_done'))
        vbox.Add(cb_exit, flag=wx.ALL | wx.EXPAND)

        # Disable delete confirmation message.
        cb_popup = wx.CheckBox(panel, label=_("Confirm before delete"))
        cb_popup.SetValue(options.get('delete_confirmation'))
        cb_popup.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('delete_confirmation'))
        vbox.Add(cb_popup, flag=wx.ALL | wx.EXPAND)

        # Use base 1000 over 1024?
        cb_units_iec = wx.CheckBox(panel, 
            label=_("Use IEC sizes (1 KiB = 1024 bytes) instead of SI (1 kB = 1000 bytes)"))
        cb_units_iec.SetValue(options.get("units_iec"))
        cb_units_iec.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('units_iec'))
        vbox.Add(cb_units_iec, flag=wx.ALL | wx.EXPAND)

        # Remember window geometry (position and size)
        self.cb_geom = wx.CheckBox(panel, label=_("Remember window geometry"))
        self.cb_geom.SetValue(options.get("remember_geometry"))
        self.cb_geom.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('remember_geometry'))
        vbox.Add(self.cb_geom, flag=wx.ALL | wx.EXPAND)

        # Debug logging
        cb_debug = wx.CheckBox(panel, label=_("Show debug messages"))
        cb_debug.SetValue(options.get("debug"))
        cb_debug.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('debug'))
        vbox.Add(cb_debug, flag=wx.ALL | wx.EXPAND)

        # KDE context menu shred option
        cb_kde_shred_menu_option = wx.CheckBox(panel, label=_("Add shred context menu option (KDE Plasma specific)"))
        cb_kde_shred_menu_option.SetValue(options.get("kde_shred_menu_option"))
        cb_kde_shred_menu_option.Bind(wx.EVT_CHECKBOX, lambda evt: self.__toggle_callback('kde_shred_menu_option'))
        vbox.Add(cb_kde_shred_menu_option, flag=wx.ALL | wx.EXPAND)

        return vbox

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
        notice = wx.StaticText(self.dialog, label=_(
            "Choose a writable folder for each drive for which to overwrite free space."))
        vbox.Add(notice, flag=wx.ALL | wx.EXPAND)

        pathnames = options.get_list('shred_drives')
        # Changes from the old GTK version: wxListBox has wxLB_SORT flag which will sort
        # the list for us, so no need to run sorted() anymore

        liststore = wx.ListBox(self.notebook, choices=pathnames,
                               style=wx.LB_SINGLE | wx.LB_HSCROLL | wx.LB_NEEDED_SB | wx.LB_SORT)

        vbox.Add(liststore, flag=wx.ALL | wx.EXPAND)

        # TRANSLATORS: In the preferences dialog, this button adds a path to
        # the list of paths
        button_add = wx.StaticText(panel, label=_p('button', 'Add'))
        button_add.Bind(wx.EVT_BUTTON, add_drive_cb)
        # TRANSLATORS: In the preferences dialog, this button removes a path
        # from the list of paths
        button_remove = wx.StaticText(panel, label=_p('button', 'Remove'))
        button_remove.Bind(wx.EVT_BUTTON, remove_drive_cb)

        button_box = wx.BoxSizer()
        button_box.Add(button_add, flag=wx.ALL | wx.EXPAND)
        button_box.Add(button_remove, flag=wx.ALL | wx.EXPAND)
        vbox.Add(button_box, flag=wx.ALL | wx.EXPAND)
        
        panel.SetSizer(vbox)

        return panel

    def __languages_page(self):
        """Return widget containing the languages page"""

        def preserve_toggled_cb(cell, path, liststore):
            """Callback for toggling the 'preserve' column"""
            __iter = liststore.get_iter_from_string(path)
            value = not liststore.get_value(__iter, 0)
            liststore.set(__iter, 0, value)
            langid = liststore[path][1]
            options.set_language(langid, value)

        vbox = wx.BoxSizer(wx.VERTICAL)
        notice = wx.StaticText(panel, label=_("All languages will be deleted except those checked."))
        vbox.Add(notice,  flag=wx.ALL | wx.EXPAND)

        # populate data
        liststore = Gtk.ListStore('gboolean', str, str)
        for lang, native in sorted(Unix.Locales.native_locale_names.items()):
            liststore.append([(options.get_language(lang)), lang, native])

        # create treeview
        treeview = Gtk.TreeView.new_with_model(liststore)

        # create column views
        self.renderer0 = Gtk.CellRendererToggle()
        self.renderer0.set_property('activatable', True)
        self.renderer0.Bind(wx.EVT_CHECKBOX, preserve_toggled_cb, liststore)
        self.column0 = Gtk.TreeViewColumn(
            _("Preserve"), self.renderer0, active=0)
        treeview.append_column(self.column0)

        self.renderer1 = Gtk.CellRendererText()
        self.column1 = Gtk.TreeViewColumn(_("Code"), self.renderer1, text=1)
        treeview.append_column(self.column1)

        self.renderer2 = Gtk.CellRendererText()
        self.column2 = Gtk.TreeViewColumn(_("Name"), self.renderer2, text=2)
        treeview.append_column(self.column2)
        treeview.set_search_column(2)

        # finish
        swindow = Gtk.ScrolledWindow()
        swindow.set_overlay_scrolling(False)
        swindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        swindow.set_size_request(300, 200)
        swindow.add(treeview)
        vbox.Add(swindow, flag=wx.ALL | wx.EXPAND)
        return vbox

    def __locations_page(self, page_type):
        """Return a widget containing a list of files and folders"""

        def add_whitelist_file_cb(button):
            """Callback for adding a file"""
            title = _("Choose a file")
            pathname = GuiBasic.browse_file(self.parent, title)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        logger.warning(
                            "'%s' already exists in whitelist", pathname)
                        return
                liststore.append([_('File'), pathname])
                pathnames.append(['file', pathname])
                options.set_whitelist_paths(pathnames)

        def add_whitelist_folder_cb(button):
            """Callback for adding a folder"""
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(self.parent, title,
                                              multiple=False, stock_button=Gtk.STOCK_ADD)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        logger.warning(
                            "'%s' already exists in whitelist", pathname)
                        return
                liststore.append([_('Folder'), pathname])
                pathnames.append(['folder', pathname])
                options.set_whitelist_paths(pathnames)

        def remove_whitelist_path_cb(button):
            """Callback for removing a path"""
            treeselection = treeview.get_selection()
            (model, _iter) = treeselection.get_selected()
            if None == _iter:
                # nothing selected
                return
            pathname = model[_iter][1]
            liststore.remove(_iter)
            for this_pathname in pathnames:
                if this_pathname[1] == pathname:
                    pathnames.remove(this_pathname)
                    options.set_whitelist_paths(pathnames)

        def add_custom_file_cb(button):
            """Callback for adding a file"""
            title = _("Choose a file")
            pathname = GuiBasic.browse_file(self.parent, title)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        logger.warning(
                            "'%s' already exists in whitelist", pathname)
                        return
                liststore.append([_('File'), pathname])
                pathnames.append(['file', pathname])
                options.set_custom_paths(pathnames)

        def add_custom_folder_cb(button):
            """Callback for adding a folder"""
            title = _("Choose a folder")
            pathname = GuiBasic.browse_folder(self.parent, title,
                                              multiple=False, stock_button=Gtk.STOCK_ADD)
            if pathname:
                for this_pathname in pathnames:
                    if pathname == this_pathname[1]:
                        logger.warning(
                            "'%s' already exists in whitelist", pathname)
                        return
                liststore.append([_('Folder'), pathname])
                pathnames.append(['folder', pathname])
                options.set_custom_paths(pathnames)

        def remove_custom_path_cb(button):
            """Callback for removing a path"""
            treeselection = treeview.get_selection()
            (model, _iter) = treeselection.get_selected()
            if None == _iter:
                # nothing selected
                return
            pathname = model[_iter][1]
            liststore.remove(_iter)
            for this_pathname in pathnames:
                if this_pathname[1] == pathname:
                    pathnames.remove(this_pathname)
                    options.set_custom_paths(pathnames)

        panel = wx.Panel(self.notebook)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # load data
        if LOCATIONS_WHITELIST == page_type:
            pathnames = options.get_whitelist_paths()
        elif LOCATIONS_CUSTOM == page_type:
            pathnames = options.get_custom_paths()
        liststore = Gtk.ListStore(str, str)
        for paths in pathnames:
            type_code = paths[0]
            type_str = None
            if type_code == 'file':
                type_str = _('File')
            elif type_code == 'folder':
                type_str = _('Folder')
            else:
                raise RuntimeError("Invalid type code: '%s'" % type_code)
            path = paths[1]
            liststore.append([type_str, path])

        if LOCATIONS_WHITELIST == page_type:
            # TRANSLATORS: "Paths" is used generically to refer to both files
            # and folders
            notice = wx.StaticText(panel, label=_("These paths will not be deleted or modified."))
        elif LOCATIONS_CUSTOM == page_type:
            notice = wx.StaticText(panel, label=_("These locations can be selected for deletion."))
        vbox.Add(notice,  flag=wx.ALL | wx.EXPAND)

        # create treeview
        treeview = Gtk.TreeView.new_with_model(liststore)

        # create column views
        self.renderer0 = Gtk.CellRendererText()
        self.column0 = Gtk.TreeViewColumn(_("Type"), self.renderer0, text=0)
        treeview.append_column(self.column0)

        self.renderer1 = Gtk.CellRendererText()
        # TRANSLATORS: In the tree view "Path" is used generically to refer to a
        # file, a folder, or a pattern describing either
        self.column1 = Gtk.TreeViewColumn(_("Path"), self.renderer1, text=1)
        treeview.append_column(self.column1)
        treeview.set_search_column(1)

        # finish tree view
        swindow = Gtk.ScrolledWindow()
        swindow.set_overlay_scrolling(False)
        swindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        swindow.set_size_request(300, 200)
        swindow.add(treeview)

        vbox.Add(swindow, flag=wx.ALL | wx.EXPAND)

        # buttons that modify the list
        button_add_file = wx.StaticText(panel, 
            label=_p('button', 'Add file'))
        if LOCATIONS_WHITELIST == page_type:
            button_add_file.Bind(wx.EVT_BUTTON, add_whitelist_file_cb)
        elif LOCATIONS_CUSTOM == page_type:
            button_add_file.Bind(wx.EVT_BUTTON, add_custom_file_cb)

        button_add_folder = wx.StaticText(panel, 
            label=_p('button', 'Add folder'))
        if LOCATIONS_WHITELIST == page_type:
            button_add_folder.Bind(wx.EVT_BUTTON, add_whitelist_folder_cb)
        elif LOCATIONS_CUSTOM == page_type:
            button_add_folder.Bind(wx.EVT_BUTTON, add_custom_folder_cb)

        button_remove = wx.StaticText(panel, label=_p('button', 'Remove'))
        if LOCATIONS_WHITELIST == page_type:
            button_remove.Bind(wx.EVT_BUTTON, remove_whitelist_path_cb)
        elif LOCATIONS_CUSTOM == page_type:
            button_remove.Bind(wx.EVT_BUTTON, remove_custom_path_cb)

        button_box = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.START)
        button_box.Add(button_add_file, flag=wx.ALL | wx.EXPAND)
        button_box.Add(button_add_folder, flag=wx.ALL | wx.EXPAND)
        button_box.Add(button_remove, flag=wx.ALL | wx.EXPAND)
        vbox.Add(button_box, flag=wx.ALL | wx.EXPAND)

        # return page
        panel.SetSizer(vbox)
        return panel

    def run(self):
        """Run the dialog"""
        return self.dialog.ShowModal()