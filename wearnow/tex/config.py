# -*- coding: utf-8 -*-
#
#
# WearNow - a GTK+ based Desktop App for wear comfort
#
# Copyright (C) 2015       Benny Malengier (UgGent)
# Copyright (C) 2005-2007  Donald N. Allingham
# Copyright (C) 2008-2009  Gary Burton 
# Copyright (C) 2009-2012  Doug Blank <doug.blank@gmail.com>
# Copyright (C) 2011       Tim G L Lyons
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
This package implements access to WEARNOW configuration.
"""

#---------------------------------------------------------------
#
# imports
#
#---------------------------------------------------------------
import os, sys
import logging

#---------------------------------------------------------------
#
# imports
#
#---------------------------------------------------------------
from .const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext
from .const import HOME_DIR, USER_HOME, VERSION_DIR
from .utils.configmanager import ConfigManager

#---------------------------------------------------------------
#
# Constants
#
#---------------------------------------------------------------
INIFILE = os.path.join(VERSION_DIR, "wearnow.ini")

#---------------------------------------------------------------
#
# Module functions
#
#---------------------------------------------------------------
def register(key, value):
    """ Module shortcut to register key, value """
    return CONFIGMAN.register(key, value)

def get(key):
    """ Module shortcut to get value from key """
    return CONFIGMAN.get(key)

def get_default(key):
    """ Module shortcut to get default from key """
    return CONFIGMAN.get_default(key)

def has_default(key):
    """ Module shortcut to get see if there is a default for key """
    return CONFIGMAN.has_default(key)

def get_sections():
    """ Module shortcut to get all section names of settings """
    return CONFIGMAN.get_sections()

def get_section_settings(section):
    """ Module shortcut to get all settings of a section """
    return CONFIGMAN.get_section_settings(section)

def set(key, value):
    """ Module shortcut to set value from key """
    return CONFIGMAN.set(key, value)

def is_set(key):
    """ Module shortcut to set value from key """
    return CONFIGMAN.is_set(key)

def save(filename=None):
    """ Module shortcut to save config file """
    return CONFIGMAN.save(filename)

def connect(key, func):
    """ 
    Module shortcut to connect a key to a callback func.
    Returns a unique callback ID number.
    """
    return CONFIGMAN.connect(key, func)

def disconnect(callback_id):
    """ Module shortcut to remove callback by ID number """
    return CONFIGMAN.disconnect(callback_id)

def reset(key=None):
    """ Module shortcut to reset some or all config data """
    return CONFIGMAN.reset(key)

def load(filename=None, oldstyle=False):
    """ Module shortcut to load an INI file into config data """
    return CONFIGMAN.load(filename, oldstyle)

def emit(key):
    """ Module shortcut to call all callbacks associated with key """
    return CONFIGMAN.emit(key)

#---------------------------------------------------------------
#
# Register the system-wide settings in a singleton config manager
#
#---------------------------------------------------------------

CONFIGMAN = ConfigManager(INIFILE, "plugins")

register('behavior.betawarn', True)
register('behavior.check-for-updates', 0)
register('behavior.last-check-for-updates', "1970/01/01")
register('behavior.previously-seen-updates', [])
register('behavior.do-not-show-previously-seen-updates', True)
register('behavior.database-path', os.path.join( HOME_DIR, 'wearnowdb'))
register('behavior.database-backend', 'dictionarydb')
register('behavior.welcome', 100)
register('behavior.web-search-url', 'http://google.com/#&q=%(text)s')

register('interface.fullscreen', False)
register('interface.height', 500)
register('interface.statusbar', 1)
register('interface.toolbar-on', True)
register('interface.width', 775)
register('interface.view', True)
register('interface.view-categories',
         ["Textile", "WearNow", "Ensemble", "Media", "Notes"])

register('paths.recent-export-dir', '')
register('paths.recent-file', '')
register('paths.recent-import-dir', '')
register('paths.report-directory', USER_HOME)
register('paths.website-directory', USER_HOME)
register('paths.quick-backup-directory', USER_HOME)
register('paths.quick-backup-filename', 
         "%(filename)s_%(year)d-%(month)02d-%(day)02d.%(extension)s")

register('preferences.use-last-view', False)
register('preferences.last-view', '')
register('preferences.iprefix', 'I%04d')
register('preferences.eprefix', 'E%04d')
register('preferences.oprefix', 'O%04d')
register('preferences.nprefix', 'N%04d')

register('owner.owner-addr', '')
register('owner.owner-locality', '')
register('owner.owner-city', '')
register('owner.owner-country', '')
register('owner.owner-email', '')
register('owner.owner-name', '')
register('owner.owner-phone', '')
register('owner.owner-postal', '')
register('owner.owner-state', '')

register('plugin.hiddenplugins', [])
register('plugin.addonplugins', [])

#---------------------------------------------------------------
#
# Upgrade Conversions go here.
#
#---------------------------------------------------------------

# If we have not already upgraded to this version,
# we can tell by seeing if there is a key file for this version:
if not os.path.exists(CONFIGMAN.filename):
    # If not, let's read old if there:
    if os.path.exists(os.path.join(HOME_DIR, "keys.ini")):
        # read it in old style:
        logging.warning("Importing old key file 'keys.ini'...")
        CONFIGMAN.load(os.path.join(HOME_DIR, "keys.ini"),
                            oldstyle=True)
        logging.warning("Done importing old key file 'keys.ini'")
    # other version upgrades here...

#---------------------------------------------------------------
#
# Now, load the settings from the config file, if one
#
#---------------------------------------------------------------
CONFIGMAN.load()

config = CONFIGMAN
