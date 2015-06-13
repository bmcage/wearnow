#
#
# WearNow - a GTK+ based Desktop App for wear comfort
#
# Copyright (C) 2015       Benny Malengier (UGent)
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2009 Benny Malengier
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

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import sys
import os
import logging
LOG = logging.getLogger(".wearnow_gui")

#-------------------------------------------------------------------------
#
# Modules
#
#-------------------------------------------------------------------------
from wearnow.tex.config import config
from wearnow.tex.const import DATA_DIR, IMAGE_DIR, GTK_GETTEXT_DOMAIN
from wearnow.tex.constfunc import has_display, win, lin
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext

from .logger import RotateHandler
from .logger import GtkHandler
#-------------------------------------------------------------------------
#
# Miscellaneous initialization
#
#-------------------------------------------------------------------------

MIN_PYGOBJECT_VERSION = (3, 3, 2)
PYGOBJ_ERR = False

try:
    #import gnome introspection, part of pygobject
    import gi
    giversion = gi.require_version
except:
    print(_("Your version of gi (gnome-introspection) seems to be too old. "
            "You need a version which has the function 'require_version' "
            "to start WearNow"))
    sys.exit(0)
            
if not PYGOBJ_ERR:
    try:
        from gi.repository import GObject, GLib
        if not GObject.pygobject_version >= MIN_PYGOBJECT_VERSION :
            PYGOBJ_ERR = True
    except:
        PYGOBJ_ERR = True

if PYGOBJ_ERR:
    print((_("Your pygobject version does not meet the requirements.\n"
             "At least pygobject %(major)d.%(feature)d.%(minor)d "
             "is needed to start WearNow with a GUI.\n\n"
             "WearNow will terminate now.") % 
            {'major':MIN_PYGOBJECT_VERSION[0], 
            'feature':MIN_PYGOBJECT_VERSION[1],
            'minor':MIN_PYGOBJECT_VERSION[2]}))
    sys.exit(0)

try:
    gi.require_version('Pango', '1.0')
    gi.require_version('PangoCairo', '1.0')
    gi.require_version('Gtk', '3.0')
    #It is important to import Pango before Gtk, or some things start to go
    #wrong in GTK3 !
    from gi.repository import Pango, PangoCairo
    from gi.repository import Gtk, Gdk
except (ImportError, ValueError):
    print((_("Gdk, Gtk, Pango or PangoCairo typelib not installed.\n"
             "Install Gnome Introspection, and "
             "pygobject version 3.3.2 or later.\n"
             "Then install introspection data for Gdk, Gtk, Pango and "
             "PangoCairo\n\n"
             "WearNow will terminate now.")))
    sys.exit(0)

try:
    import cairo
except ImportError:
    print((_("\ncairo python support not installed. Install cairo for your "
             "version of python (eg package python3-cairo)\n\n"
             "WearNow will terminate now.")))
    sys.exit(0)

#-------------------------------------------------------------------------
#
# Functions
#
#-------------------------------------------------------------------------

def _display_welcome_message():
    """
    Display a welcome message to the user.
    """
    if not config.get('behavior.betawarn'):
        from .dialog import WarningDialog
        WarningDialog(
            _('Danger: This is unstable code!'),
            _("This is a development release. "
              "This version is not meant for normal usage. Use "
              "at your own risk.\n"
              "\n"
              "This version may:\n"
              "1) Work differently than you expect.\n"
              "2) Fail to run at all.\n"
              "3) Crash often.\n"
              "4) Corrupt your data.\n"
              "5) Save data in a format that is incompatible with the "
              "official release.\n"
              "\n"
              "%(bold_start)sBACKUP%(bold_end)s "
              "your existing data before opening.")
                  % { 'bold_start' : '<b>',
                      'bold_end'   : '</b>' } )
        config.set('behavior.autoload', False)
        config.set('behavior.betawarn', True)
        config.set('behavior.betawarn', config.get('behavior.betawarn'))

#-------------------------------------------------------------------------
#
# Main WearNow class
#
#-------------------------------------------------------------------------
class WearNow(object):
    """
    Main class corresponding to a running wearnow process.

    There can be only one instance of this class per wearnow application
    process. It may spawn several windows and control several databases.
    """

    def __init__(self, args):
        from .dialog import WarningDialog
        import gettext

        _display_welcome_message()

        # Append image directory to the theme search path
        theme = Gtk.IconTheme.get_default()
        theme.append_search_path(IMAGE_DIR)

        if lin() and glocale.lang != 'C' and not gettext.find(GTK_GETTEXT_DOMAIN):
            LOG.warn("GTK translations missing, GUI will be broken, especially for RTL languages!")
            # Note: the warning dialog below will likely have wrong stock icons!
            # Translators: the current language will be the one you translate into.
            WarningDialog(
               _("WearNow detected an incomplete GTK installation"),
               _("GTK translations for the current language (%(language)s) "
                 "are missing.\n%(bold_start)sWearNow%(bold_end)s will "
                 "proceed nevertheless.\nThe GUI will likely be broken "
                 "as a result, especially for RTL languages!\n\n"
                 "See the WearNow README documentation for installation "
                 "prerequisites,\ntypically located in "
                 "/usr/share/doc/wearnow.\n") % {
                     'language'   : glocale.lang ,
                     'bold_start' : '<b>' ,
                     'bold_end'   : '</b>' } )

        from .viewmanager import ViewManager
        from wearnow.tex.dbstate import DbState
        
        dbstate = DbState()
        order_categories = ['Textile', 'WearNow', 'Ensemble', 'Media', 'Notes']
        self.vm = ViewManager(dbstate, order_categories)
        self.vm.init_interface()

        self.vm.post_init_interface()

    def argerrorfunc(self, string):
        from .dialog import ErrorDialog
        """ Show basic errors in argument handling in GUI fashion"""
        ErrorDialog(_("Error parsing arguments"), string)

#-------------------------------------------------------------------------
#
# Main startup functions
#
#-------------------------------------------------------------------------

def __startwearnow(errors, args):
    """
    Main startup function started via GObject.timeout_add
    First action inside the gtk loop
    """
    try:
        from .dialog import ErrorDialog
        #handle first existing errors in GUI fashion
        if errors:
            for error in errors:
                ErrorDialog(error[0], error[1])
            Gtk.main_quit()
            sys.exit(1)

        # add gui logger
        form = logging.Formatter(fmt="%(relativeCreated)d: %(levelname)s: "
                                    "%(filename)s: line %(lineno)d: %(message)s")
        # Create the log handlers
        rh = RotateHandler(capacity=20)
        rh.setFormatter(form)
        # Only error and critical log records should
        # trigger the GUI handler.
        gtkh = GtkHandler(rotate_handler=rh)
        gtkh.setFormatter(form)
        gtkh.setLevel(logging.ERROR)
        l = logging.getLogger()
        l.addHandler(rh)
        l.addHandler(gtkh)

    except:
        #make sure there is a clean exit if there is an error in above steps
        quit_now = True
        exit_code = 1
        LOG.error(_(
    "\nWearNow failed to start. Please report a bug about this.\n"
                   ), exc_info=True)
    
    # start WearNow, errors stop the gtk loop
    try:
        quit_now = False
        exit_code = 0
        if has_display():
            WearNow(args)
        else:
            print("WearNow terminated because of no DISPLAY")
            sys.exit(exit_code)

    except SystemExit as e:
        quit_now = True
        if e.code:
            exit_code = e.code
            LOG.error("WearNow terminated with exit code: %d." \
                      % e.code, exc_info=True)
    except OSError as e:
        quit_now = True
        exit_code = e.errno or 1
        try:
            fn = e.filename
        except AttributeError:
            fn = ""
        LOG.error("WearNow terminated because of OS Error\n" +
            "Error details: %s %s" % (repr(e), fn), exc_info=True)

    except:
        quit_now = True
        exit_code = 1
        LOG.error(_(
    "\nWearNow failed to start. Please report a bug about this.\n"
                   ), exc_info=True)

    if quit_now:
        #stop gtk loop and quit
        Gtk.main_quit()
        sys.exit(exit_code)

    #function finished, return False to stop the timeout_add function calls
    return False

def startgtkloop(errors, argparser):
    """ We start the gtk loop and run the function to start up WearNow
    """
    if GObject.pygobject_version < (3, 10, 2):
        GObject.threads_init()

    GLib.timeout_add(100, __startwearnow, errors, argparser, priority=100)
    if os.path.exists(os.path.join(DATA_DIR, "wearnow.accel")):
        Gtk.AccelMap.load(os.path.join(DATA_DIR, "wearnow.accel"))
    Gtk.main()
