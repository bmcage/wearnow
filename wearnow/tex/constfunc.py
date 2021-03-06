#
# WearNow - a GTK+ based Desktop App for wear comfort
#
# Copyright (C) 2015       Benny Malengier (UGent)
# Copyright (C) 2015       Mahmood Ahmed   (UGent)
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2009       Brian G. Matherly
# Copyright (C) 2009       Peter G. Landgren
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

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
import platform
import sys
import os

#-------------------------------------------------------------------------
#
# Platforms
# Never test on LINUX, handle Linux in the else statement as default
#
#-------------------------------------------------------------------------
LINUX = ["Linux", "linux", "linux2"]
MACOS = ["Darwin", "darwin"]
WINDOWS = ["Windows", "win32"]

#-------------------------------------------------------------------------
#
# Public Functions
#
#-------------------------------------------------------------------------
def conv_to_unicode(x, y='utf8'):
    return x if x is None or isinstance(x, str) else str(x, y) if y else str(x)

#-------------------------------------------------------------------------
#
# Platform determination functions
#
#-------------------------------------------------------------------------

def lin():
    """
    Return True if a linux system
    Note: Normally do as linux in else statement of a check !
    """
    if platform.system() in LINUX:
        return True
    return False
    
def mac():
    """
    Return True if a Macintosh system
    """
    if platform.system() in MACOS:
        return True
    return False

def win():
    """
    Return True if a windows system
    """
    if platform.system() in WINDOWS:
        return True
    return False

## The following functions do import gtk, but only when called. They
## should only be called after translation system has been
## initialized!

def is_quartz():
    """
    Tests to see if Python is currently running with gtk and 
    windowing system is Mac OS-X's "quartz".
    """
    if mac():
        try:
            from gi.repository import Gtk
            from gi.repository import Gdk
        except:
            return False
        return Gdk.Display.get_default().__class__.__name__.endswith("QuartzDisplay")
    return False

def has_display():
    """
    Tests to see if Python is currently running with gtk 
    """
    # FIXME: currently, Gtk.init_check() requires all strings
    # in argv, and we might have unicode.
    temp, sys.argv = sys.argv, sys.argv[:1]
    try:
        from gi.repository import Gtk
        from gi.repository import Gdk
    except:
        return False

    try:
        test = Gtk.init_check(temp) and \
            Gdk.Display.get_default()
        sys.argv = temp
        return bool(test)
    except:
        sys.argv = temp
        return False

# A couple of places add menu accelerators using <alt>, which doesn't
# work with Gtk-quartz. <Meta> is the usually correct replacement, but
# in one case the key is a number, and <meta>number is used by Spaces
# (a mac feature), so we'll use control instead.

def mod_key():
    """
    Returns a string to pass to an accelerator map.
    """

    if is_quartz():
        return "<ctrl>"

    return "<alt>"

# Python2 on Windows munges environment variables to match the system
# code page. This breaks all manner of things and the workaround
# though a bit ugly, is encapsulated here. Use this to retrieve
# environment variables if there's any chance they might contain
# Unicode, and especially for paths.

# Shamelessly lifted from http://stackoverflow.com/questions/2608200/problems-with-umlauts-in-python-appdata-environvent-variable, answer 1.


def get_env_var(name, default=None):
    '''
    Python2 on Windows can't directly read unicode values from
    environment variables. This routine does so using the native C
    wide-character function.
    '''
    if not name or not name in os.environ:
        return default

    return os.environ[name]

def get_curr_dir():
    '''
    In Python2 on Windows, os.getcwd() returns a string encoded with
    the current code page, which may not be able to correctly handle
    an arbitrary unicode character in a path. This function uses the
    native GetCurrentDirectory function to return a unicode cwd.
    '''
    return os.getcwd()
