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
Basic GUI code
"""

from bleachbit import _, ModuleNotFoundError

import os

try:
    import wx
    import wx.xrc
except ModuleNotFoundError as e:
    print('*'*60)
    print('Please install wxPython')
    print('May require additional build tools + GUI toolkit!')
    print('*'*60)
    raise e

if os.name == 'nt':
    from bleachbit import Windows


def browse_folder(parent, title, multiple, stock_button):
    """Ask the user to select a folder.  Return the full path or None."""

    # if os.name == 'nt' and not os.getenv('BB_NATIVE'):
    #     ret = Windows.browse_folder(parent, title)
    #     return [ret] if multiple and not ret is None else ret

    chooser = wx.DirDialog(parent, title,
                           style=(wx.DD_DEFAULT_STYLE if not multiple
                                else wx.DD_MULTIPLE) | wx.DD_DIR_MUST_EXIST)
    
    ret: list
    
    if chooser.ShowModal() == wx.ID_OK:
        if multiple: ret = chooser.GetPaths(ret)
        else: ret = [chooser.GetPath()]
    else:
        ret = None
        
    return ret


def browse_file(parent, title, multiple: bool = False):
    """Prompt user to select a single file"""

    chooser = wx.FileDialog(parent, title, os.path.expanduser('~'),
                            style=(wx.FD_MULTIPLE if multiple
                                   else wx.FD_DEFAULT_STYLE) | wx.FD_FILE_MUST_EXIST)
    
    if chooser.ShowModal() == wx.ID_OK:
        if multiple: return chooser.GetPaths()
        else: return chooser.GetPath()
    else:
        return None


def browse_files(parent, title):
    """Prompt user to select multiple files to delete"""

    return browse_file(parent, title, True)


def delete_confirmation_dialog(parent, mention_preview, shred_settings=False):
    """Return boolean whether OK to delete files."""

    if shred_settings:
        notice_text = _(
            "This function deletes all BleachBit settings and then quits the application. "
            "Use this to hide your use of BleachBit or to reset its settings. "
            "The next time you start BleachBit, the settings will initialize to default values.")

    if mention_preview:
        question_text = _(
            "Are you sure you want to permanently delete files according to the selected operations? "
            "The actual files that will be deleted may have changed since you ran the preview.")
    else:
        question_text = _(
            "Are you sure you want to permanently delete these files?")
        
    ret = wx.MessageBox(notice_text, _("Delete confirmation"), wx.YES_NO | wx.ICON_WARNING, parent)
    
    return ret == wx.ID_YES


def message_dialog(parent, msg, mtype=wx.ICON_ERROR, buttons=wx.OK_DEFAULT, title=None):
    """Convenience wrapper for wx.MessageDialog"""
    
    dialog = wx.MessageDialog(
        parent, msg, title="" if not title else title,
        style = buttons | mtype
    )
    
    resp = dialog.ShowModal()

    return resp


def open_url(url, parent_window=None, prompt=True):
    """Open an HTTP URL.  Try to run as non-root."""
    
    # drop privileges so the web browser is running as a normal process
    if os.name == 'posix' and os.getuid() == 0:
        msg = _(
            "Because you are running as root, please manually open this link in a web browser:\n%s") % url
        message_dialog(None, msg, wx.ICON_INFORMATION)
        return
    
    if prompt:
        # find hostname
        import re
        ret = re.search('^http(s)?://([a-z.]+)', url)
        if not ret:
            host = url
        else:
            host = ret.group(2)
            
        # TRANSLATORS: %s expands to www.bleachbit.org or similar
        msg = _("Open web browser to %s?") % host
        resp = message_dialog(parent_window,
                              msg,
                              wx.ICON_QUESTION,
                              wx.YES_NO,
                              _('Confirm'))
        
        if resp != wx.ID_YES:
            return
        
    # open web browser
    import webbrowser
    webbrowser.open(url)

# Taken from lebao3105's libtextworker
# Used to load XRC code - which holds GUI designs
class XRCLoader:
    
    def __init__(self, parent: wx.Window | None, file: str):
        self.parent = parent
        
        # Setup translation
        # Credit: https://wiki.wxpython.org/XRCAndI18N
        
        with open(file, encoding="utf-8") as f:
            xrc_data = f.read()
        
        import re
        
        def txtLocalize(match_obj: re.Match[str]):
            return _(match_obj.group(1))
        
        ## Replace texts with translated ones
        xrc_data = re.sub("_(['\"](.*?)['\"])", txtLocalize, xrc_data)
        xrc_data = xrc_data.encode("utf8")

        # Call out the resource file, with translated strings
        self.Res = wx.xrc.XmlResource()
        self.Res.LoadFromBuffer(xrc_data)
    
    def loadObject(self, objname, objtype):
        """
        Load a XRC object.
        Mainly used for calling the top-level widget (e.g wxFrame),
            and not all widgets will work with this.
        If this function is not usable, use children-communicate functions such as
            GetSizer, GetChildren, wx.FindWindowBy*; or use wx.xrc.XRCCTRL.
        """
        return self.Res.LoadObject(self.parent, objname, objtype)