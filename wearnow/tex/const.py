#
# WearNow - a GTK+ based Desktop App for wear comfort
#
# Copyright (C) 2015       Benny Malengier (UGent)
# Copyright (C) 2015       Mahmood Ahmed   (UGent)
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#


"""
Provides constants for other modules
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os
import sys
import uuid


#-------------------------------------------------------------------------
#
# modules
#
#-------------------------------------------------------------------------
from .git_revision import get_git_revision
from .constfunc import get_env_var, conv_to_unicode

#-------------------------------------------------------------------------
#
# WearNow Version
#
#-------------------------------------------------------------------------
PROGRAM_NAME   = "WearNow"
from wearnow.version import VERSION, VERSION_TUPLE, major_version

#-------------------------------------------------------------------------
#
# Standard WearNow Websites
#
#-------------------------------------------------------------------------
URL_HOMEPAGE    = "http://www.ugent.be/ea/textiles"

#-------------------------------------------------------------------------
#
# Mime Types
#
#-------------------------------------------------------------------------
APP_WEARNOW      = "application/x-wearnow"

#-------------------------------------------------------------------------
#
# Determine the home directory. 
#
#-------------------------------------------------------------------------
if 'WEARNOWHOME' in os.environ:
    USER_HOME = get_env_var('WEARNOWHOME') 
    HOME_DIR = os.path.join(USER_HOME, 'wearnow')
elif 'USERPROFILE' in os.environ:  # WINDOWS
    USER_HOME = get_env_var('USERPROFILE') 
    if 'APPDATA' in os.environ:
        HOME_DIR = os.path.join(get_env_var('APPDATA'), 'wearnow')
    else:
        HOME_DIR = os.path.join(USER_HOME, 'wearnow')
else:
    USER_HOME = get_env_var('HOME') 
    HOME_DIR = os.path.join(USER_HOME, '.wearnow')


VERSION_DIR    = os.path.join(
    HOME_DIR, "wearnow%s%s" % (VERSION_TUPLE[0], VERSION_TUPLE[1]))

ENV_DIR        = os.path.join(HOME_DIR, "env")
TEMP_DIR       = os.path.join(HOME_DIR, "temp")
THUMB_DIR      = os.path.join(HOME_DIR, "thumb")
THUMB_NORMAL   = os.path.join(THUMB_DIR, "normal")
THUMB_LARGE    = os.path.join(THUMB_DIR, "large")

# dirs checked/made for each session
USER_DIRLIST = (USER_HOME, HOME_DIR, VERSION_DIR, ENV_DIR, TEMP_DIR, THUMB_DIR,
                THUMB_NORMAL, THUMB_LARGE)


#-------------------------------------------------------------------------
#
# Paths to python modules - assumes that the root directory is one level 
# above this one, and that the plugins directory is below the root directory.
#
#-------------------------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(
    conv_to_unicode(__file__)), os.pardir))

sys.path.insert(0, ROOT_DIR)
git_revision = get_git_revision(ROOT_DIR)
if sys.platform == 'win32' and git_revision == "":
    git_revision = get_git_revision(os.path.split(ROOT_DIR)[1])
VERSION += git_revision


#
# Glade files
#
GLADE_DIR      = os.path.join(ROOT_DIR, "gui", "glade")
GLADE_FILE     = os.path.join(GLADE_DIR, "wearnow.glade")

PLUGINS_DIR        = os.path.join(ROOT_DIR, "plugins")

if sys.platform == 'win32':
    USE_THUMBNAILER = False
else:
    USE_THUMBNAILER = True

#-------------------------------------------------------------------------
#
# Paths to data files.
#
#-------------------------------------------------------------------------
from wearnow.tex.utils.resourcepath import ResourcePath
_resources = ResourcePath()
DATA_DIR = _resources.data_dir
IMAGE_DIR = _resources.image_dir

ICON = os.path.join(IMAGE_DIR, "wearnow.png")
LOGO = os.path.join(IMAGE_DIR, "logo.png")
SPLASH = os.path.join(IMAGE_DIR, "splash.jpg")

LICENSE_FILE = os.path.join(_resources.doc_dir, 'COPYING')

#-------------------------------------------------------------------------
#
# Init Localization
#
#-------------------------------------------------------------------------
from wearnow.tex.utils.wearnowlocale import WearNowLocale
WEARNOW_LOCALE = WearNowLocale(localedir=_resources.locale_dir)
_ = WEARNOW_LOCALE.translation.sgettext
GTK_GETTEXT_DOMAIN = 'gtk30'

#-------------------------------------------------------------------------
#
# About box information
#
#-------------------------------------------------------------------------
COPYRIGHT_MSG  = "© 2015-2016 Benny Malengier (UGENT)\n"
COMMENTS       = _("WearNow\n (Comfort related assistance to what you should wear."
                   "\n")
AUTHORS        = [
    "Benny Malengier", 
    "Mahmood Ahmed",
    ]

AUTHORS_FILE = os.path.join(DATA_DIR, "authors.xml")
DOCUMENTERS    = [ 
    ]
#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
THUMBSCALE       = 96.0
THUMBSCALE_LARGE = 180.0

WEARNOW_UUID =  uuid.UUID('43615387-3622-467f-b061-c04a378317b0')
