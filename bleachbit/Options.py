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
Store and retrieve user preferences
"""

from typing import Iterable
import bleachbit
from bleachbit import General
from bleachbit import _

import logging
import os
import re

from libtextworker.get_config import GetConfig

logger = logging.getLogger(__name__)

if 'nt' == os.name:
    from win32file import GetLongPathName




def path_to_option(pathname):
    """Change a pathname to a .ini option name (a key)"""
    # On Windows change to lowercase and use backwards slashes.
    pathname = os.path.normcase(pathname)
    # On Windows expand DOS-8.3-style pathnames.
    if 'nt' == os.name and os.path.exists(pathname):
        pathname = GetLongPathName(pathname)
    if ':' == pathname[1]:
        # ConfigParser treats colons in a special way
        pathname = pathname[0] + pathname[2:]
    return pathname


def init_configuration():
    """Initialize an empty configuration, if necessary"""

    if not os.path.exists(bleachbit.options_dir):
        General.makedirs(bleachbit.options_dir)

    elif os.path.lexists(bleachbit.options_file):
        logger.debug(f'Deleting configuration file: {bleachbit.options_file}')
        os.remove(bleachbit.options_file)

    # Is this neccessary? I think no.

    # with open(bleachbit.options_file, 'w', encoding='utf-8-sig') as f_ini:
    #     f_ini.write('[bleachbit]\n')
    #     if os.name == 'nt' and bleachbit.portable_mode:
    #         f_ini.write('[Portable]\n')

    # for section in options.sections():
    #     options.remove_section(section)

    # options.restore()

# Default settings
defaults: dict[str, object] = {
    "auto_hide": True,
    "check_beta": False,
    "check_online_updates": True,
    "dark_mode": True,
    "debug": False,
    "delete_confirmation": True,
    "exit_done": False,
    "remember_geometry": True,
    "shred": False,
    "units_iec": False,
    "window_maximized": False
}

if os.name != 'nt':
    defaults["kde_shred_menu_option"] = False
else:
    defaults["update_winapp2"] = False

boolean_keys = defaults.keys() # works for NOW
int_keys = ['window_x', 'window_y', 'window_width', 'window_height']

class Options(GetConfig):

    """Store and retrieve user preferences"""

    purged: bool = False

    def __init__(self):
        super().__init__(defaults, bleachbit.options_file, True, 'utf-8-sig')

        self.optionxform = str  # make keys case sensitive for hashpath purging
        
        self.yes_values.append('t')
        self.no_values.append('f')

        self.restore()

    def Update_And_Write(self):
        if not self.purged:
            self.__purge()

        if not os.path.isdir(bleachbit.options_dir):
            General.makedirs(bleachbit.options_dir)

        notExists = not os.path.isfile(bleachbit.options_file)

        try:
            super().Update_And_Write()
        except IOError as e:
            from errno import ENOSPC
            if e.errno == ENOSPC:
                    logger.error(
                         _("Disk was full when writing configuration to file ") + bleachbit.options_file)
            else:
                raise
        
        if notExists and General.sudo_mode():
            General.chownself(bleachbit.options_file)

    def __purge(self):
        """Clear out obsolete data"""
        self.purged = True

        if not self.has_section('hashpath'):
            return
        
        for option in self.options('hashpath'):
            pathname = option
            if 'nt' == os.name and re.search('^[a-z]\\\\', option):
                # restore colon lost because ConfigParser treats colon special
                # in keys
                pathname = pathname[0] + ':' + pathname[1:]
            exists = False
            try:
                exists = os.path.lexists(pathname)
            except:
                # this deals with corrupt keys
                # https://www.bleachbit.org/forum/bleachbit-wont-launch-error-startup
                logger.error(_("Error checking whether path exists: ") + pathname)

            if not exists:
                # the file does not on exist, so forget it
                self.remove_option('hashpath', option)

    def is_corrupt(self):
        """Perform a self-check for corruption of the configuration"""
        # no boolean key must raise an exception
        for boolean_key in boolean_keys:
            try:
                if self.has_option('bleachbit', boolean_key):
                    self.getboolean('bleachbit', boolean_key)
            except ValueError:
                return True
        # no int key must raise an exception
        for int_key in int_keys:
            try:
                if self.has_option('bleachbit', int_key):
                    self.getint('bleachbit', int_key)
            except ValueError:
                return True
        return False
    
    # FIXME:
    # Should all settings below become @property-s?
    # For some like language, the setter will accept iterable object for language ID and whatever value it is.
    # Some are properties now.

    #region Getters

    def Get(self, option, section = 'bleachbit', raw = False, find_everywhere = False,
            write_to_self = False, noraise = True, convertTo: type | None = bool):
        if not 'nt' == os.name and 'update_winapp2' == option:
            return False
        
        if section == 'bleachbit' and option == 'debug':
            from bleachbit.Log import is_debugging_enabled_via_cli
            if is_debugging_enabled_via_cli():
                # command line overrides stored configuration
                return True
            
        if section == 'hashpath' and option[1] == ':':
            option = option[0] + option[2:]
        
        return super().Get(section, option, raw, find_everywhere, write_to_self, noraise,
                           int if option in int_keys else bool if option in boolean_keys else convertTo)

    def get_hashpath(self, pathname):
        """Recall the hash for a file"""
        return self.get(path_to_option(pathname), 'hashpath')

    def get_language(self, langid):
        """Retrieve value for whether to preserve the language"""
        if not self.has_option('preserve_languages', langid):
            return False
        
        return self.getboolean('preserve_languages', langid)

    def get_languages(self):
        """Return a list of all selected languages"""
        if not self.has_section('preserve_languages'):
            return None
        
        return self.options('preserve_languages')

    def get_list(self, option):
        """Return an option which is a list data type"""
        section = f"list/{option}"
        if not self.has_section(section):
            return None
        values = [
            self.get(section, option)
            for option in sorted(self.options(section))
        ]
        return values

    def get_paths(self, section) -> dict[str, list[str]]:
        """Abstracts get_whitelist_paths and get_custom_paths"""
        if not self.has_section(section):
            return {}
        
        myoptions = []
        for option in sorted(self.options(section)):
            pos = option.find('_')
            if -1 == pos:
                continue
            myoptions.append(option[0:pos])

        values = {
            'files': [],
            'folders': []
        }
        for option in set(myoptions):
            p_type = self.get(section, f'{option}_type')
            p_path = self.get(section, f'{option}_path')
            values[f"{p_type}s"].append(p_path)

        return values
    
    @property
    def whitelist_paths(self) -> dict[str, list[str]]:
        """Return the whitelist of paths"""
        return self.get_paths("whitelist/paths")
    
    @property
    def custom_paths(self) -> dict[str, list[str]]:
        """Return list of custom paths"""
        return self.get_paths("custom/paths")

    def get_tree(self, parent, child):
        """Retrieve an option for the tree view.  The child may be None."""
        option = parent
        if child is not None:
            option += "." + child
        if not self.has_option('tree', option):
            return False
        try:
            return self.getboolean('tree', option)
        except:
            # in case of corrupt configuration (Launchpad #799130)
            logger.exception('Error in get_tree()')
            return False

    #endregion

    #region Setters

    def restore(self):
        """
        Restore saved options from disk.
        This is usually called after the class initialization.
        """

        if not self.has_section("bleachbit"):
            self.add_section("bleachbit")

        if not self.has_section("hashpath"):
            self.add_section("hashpath")

        if not self.has_section("list/shred_drives"):
            from bleachbit.FileUtilities import guess_overwrite_paths
            try:
                self.set_list('shred_drives', guess_overwrite_paths())
            except:
                logger.exception(
                    _("Error when setting the default drives to shred."))

        if not self.has_section('preserve_languages'):
            lang = bleachbit.user_locale
            pos = lang.find('_')
            if -1 != pos:
                lang = lang[0: pos]
            for _lang in set([lang, 'en']):
                logger.info(_("Automatically preserving language %s."), _lang)
                self.set_language(_lang, True)

        # BleachBit upgrade or first start ever
        if not self.has_option('bleachbit', 'version') or \
                self.get('version') != bleachbit.APP_VERSION:
            self.set('bleachbit', 'first_start', 'true')

        # set version
        self.set('bleachbit', "version", bleachbit.APP_VERSION)

    def set_hashpath(self, pathname, hashvalue):
        """Remember the hash of a path"""
        self.set(path_to_option(pathname), hashvalue, 'hashpath')

    def set_list(self, key, values):
        """Set a value which is a list data type"""
        section = f"list/{key}"
        if self.has_section(section):
            self.remove_section(section)

        self.add_section(section)

        for counter, value in enumerate(values):
            self.set(section, str(counter), value)
            
        self.Update_And_Write()

    @whitelist_paths.setter
    def whitelist_paths(self, values: dict[str, list[str]]):
        """Save the whitelist"""
        section = "whitelist/paths"
        
        if self.has_section(section):
            self.remove_section(section)

        self.add_section(section)
        for kind in values:
            for counter in range(len(values[kind])):
                self.set(section, str(counter) + '_type', kind)
                self.set(section, str(counter) + '_path', values[kind][counter])
        
        self.Update_And_Write()

    @custom_paths.setter
    def custom_paths(self, values: dict[str, list[str]]):
        """Save the customlist"""
        section = "custom/paths"
        
        if self.has_section(section):
            self.remove_section(section)

        self.add_section(section)
        for kind in values:
            for counter in range(len(values[kind])):
                self.set(section, str(counter) + '_type', kind)
                self.set(section, str(counter) + '_path', values[kind][counter])
        
        self.Update_And_Write()

    def set_language(self, langid, value):
        """Set the value for a locale (whether to preserve it)"""
        if not self.has_section('preserve_languages'):
            self.add_section('preserve_languages')
        if self.has_option('preserve_languages', langid) and not value:
            self.remove_option('preserve_languages', langid)
        else:
            self.set('preserve_languages', langid, str(value))
        self.Update_And_Write()

    def set_tree(self, parent, child, value):
        """Set an option for the tree view.  The child may be None."""
        if not self.has_section("tree"):
            self.add_section("tree")

        option = parent

        if child is not None:
            option = option + "." + child
        
        if self.has_option('tree', option) and not value:
            self.remove_option('tree', option)
        else:
            self.set('tree', option, str(value))
        
        self.Update_And_Write()

    def toggle(self, key):
        """Toggle a boolean key"""
        self.set(key, not self.get(key))

    #endregion


options = Options()
