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
GUI for making chaff
"""

from bleachbit import _
from bleachbit.Chaff import download_models, generate_emails, generate_2600, have_models
from bleachbit.GuiBasic import XRCLoader, message_dialog

import logging
import os
import wx

logger = logging.getLogger(__name__)


def make_files_thread(file_count, inspiration, output_folder, delete_when_finished, on_progress):
    if inspiration == 0:
        generated_file_names = generate_2600(
            file_count, output_folder, on_progress=on_progress)
    elif inspiration == 1:
        generated_file_names = generate_emails(
            file_count, output_folder, on_progress=on_progress)
    if delete_when_finished:
        on_progress(0, msg=_('Deleting files'))
        for i in range(0, file_count):
            os.unlink(generated_file_names[i])
            on_progress(1.0 * (i+1)/file_count)
    on_progress(1.0, is_done=True)


class ChaffDialog(XRCLoader):

    """Present the dialog to make chaff"""

    def __init__(self, parent):
        
        # TRANSLATORS: BleachBit creates digital chaff like that is like the
        # physical chaff airplanes use to protect themselves from radar-guided
        # missiles. For more explanation, see the online documentation.
        super().__init__(parent, app_makechaff_filename)
        
        self.dialog: wx.Dialog = self.loadObject("ChaffDlg", "wxDialog")
        childs = self.dialog.GetChildren()
        self.inspiration_combo: wx.Choice = childs[2]
        self.file_count: wx.SpinCtrl = childs[4]
        self.choose_folder_button: wx.DirPickerCtrl = childs[6]
        self.when_finished_combo: wx.Choice = childs[8]
        self.progressbar: wx.Gauge = childs[9]
        self.make_button: wx.Button = childs[10]
        
        import tempfile
        self.choose_folder_button.SetPath(tempfile.gettempdir())

    def download_models_gui(self):
        """Download models and return whether successful as boolean"""
        def on_download_error(msg, msg2):
            return message_dialog(self.dialog, msg2, buttons=wx.CANCEL | wx.OK, title=msg)
        return download_models(on_error=on_download_error)

    def download_models_dialog(self):
        """Download models"""
        response = message_dialog(self.dialog, "", wx.ICON_QUESTION, wx.OK | wx.CANCEL,
                                  _("Download data needed for chaff generator?"))
        ret = None
        if response == wx.ID_OK:
            # User wants to download
            ret = self.download_models_gui()  # True if successful
        elif response == wx.ID_CANCEL:
            ret = False
        dialog.destroy()
        return ret

    def on_make_files(self, widget):
        """Callback for make files button"""
        file_count = self.file_count.get_value_as_int()
        output_dir = self.choose_folder_button.get_filename()
        delete_when_finished = self.when_finished_combo.get_active() == 0
        inspiration = self.inspiration_combo.get_active()
        if not output_dir:
            message_dialog(self.dialog, _("Select destination folder"),
                           buttons=wx.CANCEL)
            return

        if not have_models():
            if not self.download_models_dialog():
                return

        def _on_progress(fraction, msg, is_done):
            """Update progress bar from GLib main loop"""
            if msg:
                self.progressbar.set_text(msg)
            self.progressbar.set_fraction(fraction)
            if is_done:
                self.progressbar.hide()
                self.make_button.set_sensitive(True)

        def on_progress(fraction, msg=None, is_done=False):
            """Callback for progress bar"""
            # Use idle_add() because threads cannot make GDK calls.
            GLib.idle_add(_on_progress, fraction, msg, is_done)

        msg = _('Generating files')
        logger.info(msg)
        self.progressbar.show()
        self.progressbar.set_text(msg)
        self.progressbar.set_show_text(True)
        self.progressbar.set_fraction(0.0)
        self.make_button.set_sensitive(False)
        import threading
        args = (file_count, inspiration, output_dir,
                delete_when_finished, on_progress)
        t = threading.Thread(target=make_files_thread, args=args)
        t.start()

    def run(self):
        """Run the dialog"""
        self.show_all()
