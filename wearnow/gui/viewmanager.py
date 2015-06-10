#
# WearNow - a GTK+ based Desktop App for wear comfort
#
# Copyright (C) 2015       Benny Malengier (UGent)
# Copyright (C) 2005-2007  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2009       Benny Malengier
# Copyright (C) 2010       Nick Hall
# Copyright (C) 2010       Jakim Friant
# Copyright (C) 2012       Gary Burton
# Copyright (C) 2012       Doug Blank <doug.blank@gmail.com>
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

from __future__ import print_function

"""
Manages the main window and the pluggable views
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os,sys
import time

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".")

#-------------------------------------------------------------------------
#
# GNOME modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk

#-------------------------------------------------------------------------
#
# modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.sgettext
from .user import User
from .displaystate import DisplayState, RecentDocsMenu
from wearnow.tex.const import (HOME_DIR, ICON, URL_HOMEPAGE, PLUGINS_DIR, USER_PLUGINS)
from wearnow.tex.db.dbconst import DBBACKEND
from wearnow.tex.errors import DbError
from wearnow.tex.dbstate import DbState
from wearnow.tex.db.exceptions import (DbUpgradeRequiredError, 
                                      DbVersionError, 
                                      PythonUpgradeRequiredError,
                                      PythonDowngradeError)
from wearnow.tex.plug import BasePluginManager
from wearnow.tex.constfunc import is_quartz, conv_to_unicode
from wearnow.tex.config import config
from wearnow.tex.errors import WindowActiveError
from wearnow.tex.recentfiles import recent_files
from .dialog import ErrorDialog, WarningDialog, QuestionDialog2, InfoDialog
from .widgets import Statusbar
from .display import display_help, display_url
from .configure import WearNowPreferences
from .aboutdialog import WearNowAboutDialog
from .actiongroup import ActionGroup

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
if is_quartz():
    try:
        from gi.repository import GtkosxApplication as QuartzApp
        _GTKOSXAPPLICATION = True
    except:
        print ("Failed to import gtk_osxapplication")
        _GTKOSXAPPLICATION = False
else:
    _GTKOSXAPPLICATION = False

_UNSUPPORTED = ("Unsupported", _("Unsupported"))

UIDEFAULT = '''<ui>
<menubar name="MenuBar">
  <menu action="FileMenu">
    <menuitem action="Open"/>
    <menu action="OpenRecent">
    </menu>
    <separator/>
    <menuitem action="Import"/>
    <menuitem action="Export"/>
    <placeholder name="LocalExport"/>
    <menuitem action="Backup"/>
    <separator/>
    <menuitem action="Abandon"/>
    <menuitem action="Quit"/>
  </menu>
  <menu action="EditMenu">
    <menuitem action="Undo"/>
    <menuitem action="Redo"/>
    <separator/>
    <placeholder name="CommonEdit"/>
    <separator/>
    <menuitem action="Preferences"/>
  </menu>
  <menu action="ViewMenu">
    <menuitem action="ConfigView"/>
    <menuitem action="Navigator"/>
    <menuitem action="Toolbar"/>
    <placeholder name="Bars"/>
    <menuitem action="Fullscreen"/>
    <separator/>
  </menu>
  <menu action="WindowsMenu">
    <placeholder name="WinMenu"/>
  </menu>
  <menu action="HelpMenu">
    <menuitem action="HomePage"/>
    <separator/>
    <menuitem action="About"/>
  </menu>
</menubar>
<toolbar name="ToolBar">
  <placeholder name="CommonNavigation"/>
  <separator/>
  <placeholder name="CommonEdit"/>
  <separator/>
  <toolitem action="ConfigView"/>
</toolbar>
<accelerator action="F2"/>
<accelerator action="F3"/>
<accelerator action="F4"/>
<accelerator action="F5"/>
<accelerator action="F6"/>
<accelerator action="F7"/>
<accelerator action="F8"/>
<accelerator action="F9"/>
<accelerator action="F11"/>
<accelerator action="F12"/>
<accelerator action="<PRIMARY>1"/>
<accelerator action="<PRIMARY>2"/>
<accelerator action="<PRIMARY>3"/>
<accelerator action="<PRIMARY>4"/>
<accelerator action="<PRIMARY>5"/>
<accelerator action="<PRIMARY>6"/>
<accelerator action="<PRIMARY>7"/>
<accelerator action="<PRIMARY>8"/>
<accelerator action="<PRIMARY>9"/>
<accelerator action="<PRIMARY>0"/>
<accelerator action="<PRIMARY>BackSpace"/>
<accelerator action="<PRIMARY>J"/>
<accelerator action="<PRIMARY>N"/>
<accelerator action="<PRIMARY>P"/>
</ui>
'''


#-------------------------------------------------------------------------
#
# CLI DbLoader class
#
#-------------------------------------------------------------------------
class CLIDbLoader(object):
    """
    Base class for Db loading action inside a :class:`.DbState`. Only the
    minimum is present needed for CLI handling
    """
    def __init__(self, dbstate):
        self.dbstate = dbstate
    
    def _warn(self, title, warnmessage):
        """
        Issue a warning message. Inherit for GUI action
        """
        print(_('WARNING: %s') % warnmessage, file=sys.stderr)
    
    def _errordialog(self, title, errormessage):
        """
        Show the error. A title for the error and an errormessage
        Inherit for GUI action
        """
        print(_('ERROR: %s') % errormessage, file=sys.stderr)
        sys.exit(1)
    
    def _dberrordialog(self, msg):
        """
        Show a database error. 
        :param msg: an error message
        :type msg : string
        .. note:: Inherit for GUI action
        """
        self._errordialog( '', _("Low level database corruption detected") 
            + '\n' +
            _("WearNow has detected a problem in the underlying "
              "Collection. This can be repaired from "
              "the Collection Manager. Select the collection and "
              'click on the Repair button') + '\n\n' + str(msg))
    
    def _begin_progress(self):
        """
        Convenience method to allow to show a progress bar if wanted on load
        actions. Inherit if needed
        """
        pass
    
    def _pulse_progress(self, value):
        """
        Convenience method to allow to show a progress bar if wanted on load
        actions. Inherit if needed
        """
        pass

    def _end_progress(self):
        """
        Convenience method to allow to hide the progress bar if wanted at
        end of load actions. Inherit if needed
        """
        pass

    def read_file(self, filename):
        """
        This method takes care of changing database, and loading the data.
        In 3.0 we only allow reading of real databases of filetype 
        'x-directory/normal'
        
        This method should only return on success.
        Returning on failure makes no sense, because we cannot recover,
        since database has already been changed.
        Therefore, any errors should raise exceptions.
        On success, return with the disabled signals. The post-load routine
        should enable signals, as well as finish up with other UI goodies.
        """

        if os.path.exists(filename):
            if not os.access(filename, os.W_OK):
                mode = "r"
                self._warn(_('Read only database'), 
                                             _('You do not have write access '
                                               'to the selected file.'))
            else:
                mode = "w"
        else:
            mode = 'w'

        dbid_path = os.path.join(filename, DBBACKEND)
        if os.path.isfile(dbid_path):
            with open(dbid_path) as fp:
                dbid = fp.read().strip()
        else:
            dbid = "bsddb"

        db = self.dbstate.make_database(dbid)
        
        self.dbstate.change_database(db)
        self.dbstate.db.disable_signals()

        self._begin_progress()
        
        try:
            self.dbstate.db.load(filename, self._pulse_progress, mode)
            self.dbstate.db.set_save_path(filename)
        except DbUpgradeRequiredError as msg:
            self.dbstate.no_database()
            self._errordialog( _("Cannot open database"), str(msg))
        except PythonDowngradeError as msg:
            self.dbstate.no_database()
            self._errordialog( _("Cannot open database"), str(msg))
        except PythonUpgradeRequiredError as msg:
            self.dbstate.no_database()
            self._errordialog( _("Cannot open database"), str(msg))
        except DbVersionError as msg:
            self.dbstate.no_database()
            self._errordialog( _("Cannot open database"), str(msg))
        except OSError as msg:
            self.dbstate.no_database()
            self._errordialog(
                _("Could not open file: %s") % filename, str(msg))
        except DbError as msg:
            self.dbstate.no_database()
            self._dberrordialog(msg)
        except Exception:
            self.dbstate.no_database()
            LOG.error("Failed to open database.", exc_info=True)
        return True


#-------------------------------------------------------------------------
#
# CLIManager class
#
#-------------------------------------------------------------------------

class CLIManager(object):
    """
    Sessionmanager for WearNow. This is in effect a reduced :class:`.ViewManager` 
    instance (see gui/viewmanager), suitable for CLI actions. 
    Aim is to manage a dbstate on which to work (load, unload), and interact
    with the plugin session
    """
    def __init__(self, dbstate, setloader, user):
        self.dbstate = dbstate
        if setloader:
            self.db_loader = CLIDbLoader(self.dbstate)
        else:
            self.db_loader = None
        self.file_loaded = False
        self._pmgr = BasePluginManager.get_instance()
        self.user = user

    def open_activate(self, path):
        """
        Open and make a family tree active
        """
        self._read_recent_file(path)
    
    def _errordialog(self, title, errormessage):
        """
        Show the error. A title for the error and an errormessage
        """
        print(_('ERROR: %s') % errormessage, file=sys.stderr)
        sys.exit(1)
        
    def _read_recent_file(self, filename):
        """
        Called when a file needs to be loaded
        """
        # A recent database should already have a directory If not, do nothing,
        #  just return. This can be handled better if family tree delete/rename
        #  also updated the recent file menu info in displaystate.py
        if not  os.path.isdir(filename):
            self._errordialog(
                    _("Could not load a recent Textile Collection."), 
                    _("Textile Collection does not exist, as it has been deleted."))
            return

        if os.path.isfile(os.path.join(filename, "lock")):
            self._errordialog(
                    _("The collection is locked."),
                    _("Use the --force-unlock option if you are sure "
                      "that the database is not in use."))
            return

        if self.db_loader.read_file(filename):
            # Attempt to figure out the database title
            path = os.path.join(filename, "name.txt")
            try:
                ifile = open(path)
                title = ifile.readline().strip()
                ifile.close()
            except:
                title = filename

            self._post_load_newdb(filename, 'x-directory/normal', title)
    
    def _post_load_newdb(self, filename, filetype, title=None):
        """
        The method called after load of a new database. 
        Here only CLI stuff is done, inherit this method to add extra stuff
        """
        self._post_load_newdb_nongui(filename, title)
    
    def _post_load_newdb_nongui(self, filename, title=None):
        """
        Called after a new database is loaded.
        """
        if not filename:
            return
        
        if filename[-1] == os.path.sep:
            filename = filename[:-1]
        name = os.path.basename(filename)
        self.dbstate.db.db_name = title
        if title:
            name = title

        # This method is for UI stuff when the database has changed.
        # Window title, recent files, etc related to new file.

        self.dbstate.db.set_save_path(filename)
        
        # apply preferred researcher if loaded file has none
        res = self.dbstate.db.get_researcher()
        owner = get_researcher()
        # If the DB Owner Info is empty and
        # [default] Researcher is not empty and
        # database is empty, then copy default researcher to DB owner
        if res.is_empty() and not owner.is_empty() and self.dbstate.db.is_empty():
            self.dbstate.db.set_researcher(owner)

        self.dbstate.db.enable_signals()
        self.dbstate.signal_change()

        config.set('paths.recent-file', filename)

        recent_files(filename, name)
        self.file_loaded = True

    def do_reg_plugins(self, dbstate, uistate):
        """
        Register the plugins at initialization time.
        """
        self._pmgr.reg_plugins(PLUGINS_DIR, dbstate, uistate)
        self._pmgr.reg_plugins(USER_PLUGINS, dbstate, uistate, load_on_reg=True)
#-------------------------------------------------------------------------
#
# ViewManager
#
#-------------------------------------------------------------------------
class ViewManager(CLIManager):
    """
    **Overview**

    The ViewManager is the session manager of the program.
    Specifically, it manages the main window of the program. It is closely tied
    into the Gtk.UIManager to control all menus and actions.

    The ViewManager controls the various Views within the programs.
    Views are organised in categories. The categories can be accessed via
    a sidebar. Within a category, the different views are accesible via the
    toolbar of view menu.

    A View is a particular way of looking at information in the main
    window. Each view is separate from the others, and has no knowledge of
    the others.

    The View Manager does not have to know the number of views, the type of
    views, or any other details about the views. It simply provides the
    method of containing each view, and has methods for creating, deleting and
    switching between the views.

    """

    def __init__(self, dbstate, view_category_order, user = None):
        """
        The viewmanager is initialised with a dbstate on which wearnow is
        working, and a fixed view_category_order, which is the order in which
        the view categories are accessible in the sidebar.
        """
        CLIManager.__init__(self, dbstate, setloader=False, user=user)
        if _GTKOSXAPPLICATION:
            self.macapp = QuartzApp.Application()

        self.view_category_order = view_category_order

        self.merge_ids = []
        self.toolactions = None
        self.tool_menu_ui_id = None
        self.reportactions = None
        self.report_menu_ui_id = None

        self.active_page = None
        self.pages = []
        self.page_lookup = {}
        self.views = None
        self.current_views = [] # The current view in each category
        self.view_changing = False

        self.show_navigator = config.get('interface.view')
        self.show_toolbar = config.get('interface.toolbar-on')
        self.fullscreen = config.get('interface.fullscreen')

        self.__build_main_window() # sets self.uistate
        if self.user is None:
            self.user = User(error=ErrorDialog,
                    callback=self.uistate.pulse_progressbar,
                    uistate=self.uistate)
        self.__connect_signals()
        if _GTKOSXAPPLICATION:
            self.macapp.ready()

    def _errordialog(self, title, errormessage):
        """
        Show the error.
        In the GUI, the error is shown, and a return happens
        """
        ErrorDialog(title, errormessage)
        return 1

    def __build_main_window(self):
        """
        Builds the GTK interface
        """
        width = config.get('interface.width')
        height = config.get('interface.height')

        self.window = Gtk.Window()
        self.window.set_icon_from_file(ICON)
        self.window.set_has_resize_grip(True)
        self.window.set_default_size(width, height)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(vbox)
        hpane = Gtk.Paned()
        self.ebox = Gtk.EventBox()

        self.navigator = Navigator(self)
        self.ebox.add(self.navigator.get_top())
        hpane.add1(self.ebox)
        hpane.show()

        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.set_show_tabs(False)
        self.notebook.show()
        self.__init_lists()
        self.__build_ui_manager()

        hpane.add2(self.notebook)
        self.menubar = self.uimanager.get_widget('/MenuBar')
        self.toolbar = self.uimanager.get_widget('/ToolBar')
        self.__attach_menubar(vbox)
        vbox.pack_start(self.toolbar, False, True, 0)
        vbox.pack_start(hpane, True, True, 0)
        self.statusbar = Statusbar()
        self.statusbar.show()
        vbox.pack_end(self.statusbar, False, True, 0)
        vbox.show()

        self.uistate = DisplayState(self.window, self.statusbar,
                                    self.uimanager, self)

        self.sidebar_menu = self.uimanager.get_widget(
            '/MenuBar/ViewMenu/Sidebar/')

        # handle OPEN button, insert it into the toolbar. Unfortunately,
        # UIManager has no built in support for and Open Recent button

        openbtn = self.__build_open_button()
        self.uistate.set_open_widget(openbtn)
        self.toolbar.insert(openbtn, 0)

        self.recent_manager = RecentDocsMenu(
            self.uistate, self.dbstate, self._read_recent_file)
        self.recent_manager.build()

        self.__setup_navigator()

        if self.show_toolbar:
            self.toolbar.show()
        else:
            self.toolbar.hide()

        if self.fullscreen:
            self.window.fullscreen()

        # Showing the main window is deferred so that
        # ArgHandler can work without it always shown
        # But we need to realize it here to have Gdk.window handy
        self.window.realize()

    def __setup_navigator(self):
        """
        If we have enabled te sidebar, show it, and turn off the tabs. If
        disabled, hide the sidebar and turn on the tabs.
        """
        if self.show_navigator:
            self.ebox.show()
        else:
            self.ebox.hide()

    def __build_open_button(self):
        """
        Build the OPEN button. Since GTK's UIManager does not have support for
        the Open Recent button, we must build in on our own.
        """
        openbtn = Gtk.MenuToolButton()
        openbtn.set_icon_name('wearnow')
        openbtn.connect('clicked', self.__open_activate)
        openbtn.set_sensitive(False)
        openbtn.set_tooltip_text(_("Open a recent clothes collection"))
        openbtn.show()
        return openbtn

    def __connect_signals(self):
        """
        Connects the signals needed
        """
        self.window.connect('delete-event', self.quit)
        self.notebook.connect('switch-page', self.view_changed)
        if _GTKOSXAPPLICATION:
            self.macapp.connect('NSApplicationWillTerminate', self.quit)

    def __init_lists(self):
        """
        Initialize the actions lists for the UIManager
        """
        self._file_action_list = [
            ('FileMenu', None, _('_Family Trees')),
            ('Open', 'wearnow-db', _('_Manage Collections...'), "<PRIMARY>o",
             _("Manage collections"), self.__open_activate),
            ('OpenRecent', None, _('Open _Recent'), None,
             _("Open an existing collection")),
            ('Quit', 'application-exit', _('_Quit'), "<PRIMARY>q", None,
             self.quit),
            ('ViewMenu', None, _('_View')),
            ('EditMenu', None, _('_Edit')),
            ('Preferences', 'preferences-system', _('_Preferences...'), None,
             None, self.preferences_activate),
            ('HelpMenu', None, _('_Help')),
            ('HomePage', None, _('WearNow _Home Page'), None, None,
             home_page_activate),
            ('ReportBug', None, _('_Report a Bug'), None, None,
             report_bug_activate),
            ('About', 'help-about', _('_About'), None, None,
             self.display_about_box),
            ('KeyBindings', None, _('_Key Bindings'), None, None, key_bindings),
            ]

        self._readonly_action_list = [
            ('Export', 'wearnow-export', _('_Export...'), "<PRIMARY>e", None,
             self.export_data),
            ('Backup', None, _("Make Backup..."), None,
             _("Make a backup of the collection"), self.quick_backup),
            ('WindowsMenu', None, _('_Windows')),
            ('F2', None, 'F2', "F2", None, self.__keypress),
            ('F3', None, 'F3', "F3", None, self.__keypress),
            ('F4', None, 'F4', "F4", None, self.__keypress),
            ('F5', None, 'F5', "F5", None, self.__keypress),
            ('F6', None, 'F6', "F6", None, self.__keypress),
            ('F7', None, 'F7', "F7", None, self.__keypress),
            ('F8', None, 'F9', "F8", None, self.__keypress),
            ('F9', None, 'F9', "F9", None, self.__keypress),
            ('F11', None, 'F11', "F11", None, self.__keypress),
            ('<PRIMARY>1', None, '<PRIMARY>1', "<PRIMARY>1", None, self.__gocat),
            ('<PRIMARY>2', None, '<PRIMARY>2', "<PRIMARY>2", None, self.__gocat),
            ('<PRIMARY>3', None, '<PRIMARY>3', "<PRIMARY>3", None, self.__gocat),
            ('<PRIMARY>4', None, '<PRIMARY>4', "<PRIMARY>4", None, self.__gocat),
            ('<PRIMARY>5', None, '<PRIMARY>5', "<PRIMARY>5", None, self.__gocat),
            ('<PRIMARY>6', None, '<PRIMARY>6', "<PRIMARY>6", None, self.__gocat),
            ('<PRIMARY>7', None, '<PRIMARY>7', "<PRIMARY>7", None, self.__gocat),
            ('<PRIMARY>8', None, '<PRIMARY>8', "<PRIMARY>8", None, self.__gocat),
            ('<PRIMARY>9', None, '<PRIMARY>9', "<PRIMARY>9", None, self.__gocat),
            ('<PRIMARY>0', None, '<PRIMARY>0', "<PRIMARY>0", None, self.__gocat),
            # NOTE: CTRL+ALT+NUMBER is set in src/plugins/sidebar/cat...py
            ('<PRIMARY>BackSpace', None, '<PRIMARY>BackSpace',
             "<PRIMARY>BackSpace", None, self.__keypress),
            ('<PRIMARY>Delete', None, '<PRIMARY>Delete',
             "<PRIMARY>Delete", None, self.__keypress),
            ('<PRIMARY>Insert', None, '<PRIMARY>Insert',
             "<PRIMARY>Insert", None, self.__keypress),
            ('F12', None, 'F12', "F12", None, self.__keypress),
            ('<PRIMARY>J', None, '<PRIMARY>J',
             "<PRIMARY>J", None, self.__keypress),
            ('<PRIMARY>N', None, '<PRIMARY>N', "<PRIMARY>N", None,
             self.__next_view),
            ('<PRIMARY>P', None, '<PRIMARY>P', "<PRIMARY>P", None,
             self.__prev_view),
            ]

        self._action_action_list = [
            ('Import', 'wearnow-import', _('_Import...'), "<PRIMARY>i", None,
             self.import_data),
            ('ConfigView', 'wearnow-config', _('_Configure...'),
             '<shift><PRIMARY>c', _('Configure the active view'),
             self.config_view),
            ]

        self._file_toggle_action_list = [
            ('Navigator', None, _('_Navigator'), "<PRIMARY>m", None,
             self.navigator_toggle, self.show_navigator ),
            ('Toolbar', None, _('_Toolbar'), None, None, self.toolbar_toggle,
             self.show_toolbar ),
            ('Fullscreen', None, _('F_ull Screen'), "F11", None,
             self.fullscreen_toggle, self.fullscreen),
            ]

        self._undo_action_list = [
            ('Undo', 'edit-undo', _('_Undo'), '<PRIMARY>z', None,
             self.undo),
            ]

        self._redo_action_list = [
            ('Redo', 'edit-redo', _('_Redo'), '<shift><PRIMARY>z', None,
             self.redo),
            ]

    def __keypress(self, action):
        """
        Callback that is called on a keypress. It works by extracting the
        name of the associated action, and passes that to the active page
        (current view) so that it can take the associated action.
        """
        name = action.get_name()
        try:
            self.active_page.call_function(name)
        except Exception:
            self.uistate.push_message(self.dbstate,
                                      _("Key %s is not bound") % name)

    def __gocat(self, action):
        """
        Callback that is called on ctrl+number press. It moves to the 
        requested category like __next_view/__prev_view. 0 is 10
        """
        cat = int(action.get_name()[-1])
        if cat == 0:
            cat = 10
        cat -= 1
        if cat >= len(self.current_views):
            #this view is not present
            return False
        self.goto_page(cat, None)

    def __next_view(self, action):
        """
        Callback that is called when the next category action is selected.
        It selects the next category as the active category. If we reach the end, 
        we wrap around to the first.
        """
        curpage = self.notebook.get_current_page()
        #find cat and view of the current page
        for key in self.page_lookup:
            if self.page_lookup[key] == curpage:
                cat_num, view_num = key
                break
        #now go to next category
        if cat_num >= len(self.current_views)-1:
            self.goto_page(0, None)
        else:
            self.goto_page(cat_num+1, None)

    def __prev_view(self, action):
        """
        Callback that is called when the previous category action is selected.
        It selects the previous category as the active category. If we reach the
        beginning of the list, we wrap around to the last.
        """
        curpage = self.notebook.get_current_page()
        #find cat and view of the current page
        for key in self.page_lookup:
            if self.page_lookup[key] == curpage:
                cat_num, view_num = key
                break
        #now go to next category
        if cat_num > 0:
            self.goto_page(cat_num-1, None)
        else:
            self.goto_page(len(self.current_views)-1, None)

    def init_interface(self):
        """
        Initialize the interface.
        """
        self.views = get_available_views()
        defaults = views_to_show(self.views,
                                 config.get('preferences.use-last-view'))
        self.current_views = defaults[2]

        self.navigator.load_plugins(self.dbstate, self.uistate)

        self.goto_page(defaults[0], defaults[1])

        if not self.file_loaded:
            self.actiongroup.set_visible(False)
            self.readonlygroup.set_visible(False)
            self.undoactions.set_visible(False)
            self.redoactions.set_visible(False)
            self.undohistoryactions.set_visible(False)
            
        self.uistate.widget.set_sensitive(True)
        config.connect("interface.statusbar", self.__statusbar_key_update)

    def __statusbar_key_update(self, client, cnxn_id, entry, data):
        """
        Callback function for statusbar key update
        """
        self.uistate.modify_statusbar(self.dbstate)

    def post_init_interface(self, show_manager=True):
        """
        Showing the main window is deferred so that
        ArgHandler can work without it always shown
        """
        self.window.show()
        if not self.dbstate.db.is_open() and show_manager:
            self.__open_activate(None)

    def quit(self, *obj):
        """
        Closes out the program, backing up data
        """
        # mark interface insenstitive to prevent unexpected events
        self.uistate.set_sensitive(False)

        # backup data, and close the database
        self.__backup()
        self.dbstate.db.close()

        # have each page save anything, if they need to:
        self.__delete_pages()

        # save the current window size
        (width, height) = self.window.get_size()
        config.set('interface.width', width)
        config.set('interface.height', height)
        config.save()
        Gtk.main_quit()

    def __backup(self):
        """
        Backup the current file as a backup file.
        """
        if self.dbstate.db.has_changed:
            self.uistate.set_busy_cursor(True)
            self.uistate.progress.show()
            self.uistate.push_message(self.dbstate, _("Autobackup..."))
            try:
                self.dbstate.db.backup()
            except DbException as msg:
                ErrorDialog(_("Error saving backup data"), msg)
            self.uistate.set_busy_cursor(False)
            self.uistate.progress.hide()

    def abort(self, obj=None):
        """
        Abandon changes and quit.
        """
        if self.dbstate.db.abort_possible:

            dialog = QuestionDialog2(
                _("Abort changes?"),
                _("Aborting changes will return the database to the state "
                  "it was before you started this editing session."),
                _("Abort changes"),
                _("Cancel"))

            if dialog.run():
                self.dbstate.db.disable_signals()
                while self.dbstate.db.undo():
                    pass
                self.quit()
        else:
            WarningDialog(
                _("Cannot abandon session's changes"),
                _('Changes cannot be completely abandoned because the '
                  'number of changes made in the session exceeded the '
                  'limit.'))

    def __init_action_group(self, name, actions, sensitive=True, toggles=None):
        """
        Initialize an action group for the UIManager
        """
        new_group = ActionGroup(name=name)
        new_group.add_actions(actions)
        if toggles:
            new_group.add_toggle_actions(toggles)
        new_group.set_sensitive(sensitive)
        self.uimanager.insert_action_group(new_group, 1)
        return new_group

    def __build_ui_manager(self):
        """
        Builds the UIManager, and the associated action groups
        """
        self.uimanager = Gtk.UIManager()

        accelgroup = self.uimanager.get_accel_group()

        self.actiongroup = self.__init_action_group(
            'MainWindow', self._action_action_list)
        self.readonlygroup = self.__init_action_group(
            'AllMainWindow', self._readonly_action_list)
        self.undohistoryactions = self.__init_action_group(
            'UndoHistory', self._undo_history_action_list)
        self.fileactions = self.__init_action_group(
            'FileWindow', self._file_action_list,
            toggles=self._file_toggle_action_list)
        self.undoactions = self.__init_action_group(
            'Undo', self._undo_action_list, sensitive=False)
        self.redoactions = self.__init_action_group(
            'Redo', self._redo_action_list, sensitive=False)
        self.window.add_accel_group(accelgroup)

        self.uimanager.add_ui_from_string(UIDEFAULT)
        self.uimanager.ensure_update()

    def __attach_menubar(self, vbox):
        vbox.pack_start(self.menubar, False, True, 0)
        if _GTKOSXAPPLICATION:
            self.menubar.hide()
            quit_item = self.uimanager.get_widget("/MenuBar/FileMenu/Quit")
            about_item = self.uimanager.get_widget("/MenuBar/HelpMenu/About")
            prefs_item = self.uimanager.get_widget("/MenuBar/EditMenu/Preferences")
            self.macapp.set_menu_bar(self.menubar)
            self.macapp.insert_app_menu_item(about_item, 0)
            self.macapp.insert_app_menu_item(prefs_item, 1)

    def preferences_activate(self, obj):
        """
        Open the preferences dialog.
        """
        try:
            WearNowPreferences(self.uistate, self.dbstate)
        except WindowActiveError:
            return

    def navigator_toggle(self, obj, data=None):
        """
        Set the sidebar based on the value of the toggle button. Save the
        results in the configuration settings
        """
        if obj.get_active():
            self.ebox.show()
            config.set('interface.view', True)
            self.show_navigator = True
        else:
            self.ebox.hide()
            config.set('interface.view', False)
            self.show_navigator = False
        config.save()

    def toolbar_toggle(self, obj, data=None):
        """
        Set the toolbar based on the value of the toggle button. Save the
        results in the configuration settings
        """
        if obj.get_active():
            self.toolbar.show()
            config.set('interface.toolbar-on', True)
        else:
            self.toolbar.hide()
            config.set('interface.toolbar-on', False)
        config.save()

    def fullscreen_toggle(self, obj, data=None):
        """
        Set the main Granps window fullscreen based on the value of the
        toggle button. Save the setting in the config file.
        """
        if obj.get_active():
            self.window.fullscreen()
            config.set('interface.fullscreen', True)
        else:
            self.window.unfullscreen()
            config.set('interface.fullscreen', False)
        config.save()

    def get_views(self):
        """
        Return the view definitions.
        """
        return self.views

    def goto_page(self, cat_num, view_num):
        """
        Create the page if it doesn't exist and make it the current page.
        """
        if view_num is None:
            view_num = self.current_views[cat_num]
        else:
            self.current_views[cat_num] = view_num

        page_num = self.page_lookup.get((cat_num, view_num))
        if page_num is None:
            page_def = self.views[cat_num][view_num]
            page_num = self.notebook.get_n_pages()
            self.page_lookup[(cat_num, view_num)] = page_num
            self.__create_page(page_def[0], page_def[1])

        self.notebook.set_current_page(page_num)
        return self.pages[page_num]

    def get_category(self, cat_name):
        """
        Return the category number from the given category name.
        """
        for cat_num, cat_views in enumerate(self.views):
            if cat_name == cat_views[0][0].category[1]:
                return cat_num
        return None

    def __create_dummy_page(self, pdata, error):
        from .views.pageview import DummyPage
        return DummyPage(pdata.name, pdata, self.dbstate, self.uistate,
                    _("View failed to load. Check error output."), error)
    
    def __create_page(self, pdata, page_def):
        """
        Create a new page and set it as the current page.
        """
        try:
            page = page_def(pdata, self.dbstate, self.uistate)
        except:
            import traceback
            LOG.warn("View '%s' failed to load." % pdata.id)
            traceback.print_exc()
            page = self.__create_dummy_page(pdata, traceback.format_exc())

        try:
            page_display = page.get_display()
        except:
            import traceback
            print("ERROR: '%s' failed to create view" % pdata.name)
            traceback.print_exc()
            page = self.__create_dummy_page(pdata, traceback.format_exc())
            page_display = page.get_display()

        page.define_actions()
        page.post()

        self.pages.append(page)

        # create icon/label for notebook tab (useful for debugging)
        hbox = Gtk.Box()
        image = Gtk.Image()
        image.set_from_icon_name(page.get_stock(), Gtk.IconSize.MENU)
        hbox.pack_start(image, False, True, 0)
        hbox.add(Gtk.Label(label=pdata.name))
        hbox.show_all()
        page_num = self.notebook.append_page(page.get_display(), hbox)
        return page

    def view_changed(self, notebook, page, page_num):
        """
        Called when the notebook page is changed.
        """
        if self.view_changing:
            return
        self.view_changing = True

        cat_num = view_num = None
        for key in self.page_lookup:
            if self.page_lookup[key] == page_num:
                cat_num, view_num = key
                break

        # Save last view in configuration
        view_id = self.views[cat_num][view_num][0].id
        config.set('preferences.last-view', view_id)
        last_views = config.get('preferences.last-views')
        if len(last_views) != len(self.views):
            # If the number of categories has changed then reset the defaults
            last_views = [''] * len(self.views)
        last_views[cat_num] = view_id
        config.set('preferences.last-views', last_views)
        config.save()

        self.navigator.view_changed(cat_num, view_num)
        self.__change_page(page_num)
        self.view_changing = False

    def __change_page(self, page_num):
        """
        Perform necessary actions when a page is changed.
        """
        if not self.dbstate.open:
            return

        self.__disconnect_previous_page()

        self.active_page = self.pages[page_num]
        self.active_page.set_active()
        self.__connect_active_page(page_num)

        self.uimanager.ensure_update()
        if _GTKOSXAPPLICATION:
            self.macapp.sync_menubar()

        while Gtk.events_pending():
            Gtk.main_iteration()

        self.active_page.change_page()

    def __delete_pages(self):
        """
        Calls on_delete() for each view
        """
        for page in self.pages:
            page.on_delete()

    def __disconnect_previous_page(self):
        """
        Disconnects the previous page, removing the old action groups
        and removes the old UI components.
        """
        list(map(self.uimanager.remove_ui, self.merge_ids))

        if self.active_page:
            self.active_page.set_inactive()
            groups = self.active_page.get_actions()
            for grp in groups:
                if grp in self.uimanager.get_action_groups():
                    self.uimanager.remove_action_group(grp)

    def __connect_active_page(self, page_num):
        """
        Inserts the action groups associated with the current page
        into the UIManager
        """
        for grp in self.active_page.get_actions():
            self.uimanager.insert_action_group(grp, 1)

        uidef = self.active_page.ui_definition()
        self.merge_ids = [self.uimanager.add_ui_from_string(uidef)]

        for uidef in self.active_page.additional_ui_definitions():
            mergeid = self.uimanager.add_ui_from_string(uidef)
            self.merge_ids.append(mergeid)

        configaction = self.actiongroup.get_action('ConfigView')
        if self.active_page.can_configure():
            configaction.set_sensitive(True)
        else:
            configaction.set_sensitive(False)

    def import_data(self, obj):
        """
        Imports a file
        """
        if self.dbstate.db.is_open():
            self.db_loader.import_file()
            infotxt = self.db_loader.import_info_text()
            if infotxt:
                InfoDialog(_('Import Statistics'), infotxt, self.window)
            self.__post_load()

    def __open_activate(self, obj):
        """
        Called when the Open button is clicked, opens the DbManager
        """
        from .dbman import DbManager
        dialog = DbManager(self.dbstate, self.window)
        value = dialog.run()
        if value:
            (filename, title) = value
            filename = conv_to_unicode(filename)
            self.db_loader.read_file(filename)
            self._post_load_newdb(filename, 'x-directory/normal', title)

    def __post_load(self):
        """
        This method is for the common UI post_load, both new files
        and added data like imports.
        """
        self.dbstate.db.undo_callback = self.__change_undo_label
        self.dbstate.db.redo_callback = self.__change_redo_label
        self.__change_undo_label(None)
        self.__change_redo_label(None)
        self.dbstate.db.undo_history_callback = self.undo_history_update
        self.undo_history_close()

    def _post_load_newdb(self, filename, filetype, title=None):
        """
        The method called after load of a new database.
        Inherit CLI method to add GUI part
        """
        self._post_load_newdb_nongui(filename, title)
        self._post_load_newdb_gui(filename, filetype, title)

    def _post_load_newdb_gui(self, filename, filetype, title=None):
        """
        Called after a new database is loaded to do GUI stuff
        """
        # GUI related post load db stuff
        # Update window title
        if filename[-1] == os.path.sep:
            filename = filename[:-1]
        name = os.path.basename(filename)
        if title:
            name = title

        if self.dbstate.db.readonly:
            msg =  "%s (%s) - WearNow" % (name, _('Read Only'))
            self.uistate.window.set_title(msg)
            self.actiongroup.set_sensitive(False)
        else:
            msg = "%s - WearNow" % name
            self.uistate.window.set_title(msg)
            self.actiongroup.set_sensitive(True)

        self.__change_page(self.notebook.get_current_page())
        self.actiongroup.set_visible(True)
        self.readonlygroup.set_visible(True)
        self.undoactions.set_visible(True)
        self.redoactions.set_visible(True)
        self.undohistoryactions.set_visible(True)

        self.recent_manager.build()

        # Call common __post_load method for GUI update after a change
        self.__post_load()

    def __change_undo_label(self, label):
        """
        Change the UNDO label
        """
        self.uimanager.remove_action_group(self.undoactions)
        self.undoactions = Gtk.ActionGroup(name='Undo')
        if label:
            self.undoactions.add_actions([
                ('Undo', 'edit-undo', label, '<PRIMARY>z', None, self.undo)])
        else:
            self.undoactions.add_actions([
                ('Undo', 'edit-undo', _('_Undo'),
                 '<PRIMARY>z', None, self.undo)])
            self.undoactions.set_sensitive(False)
        self.uimanager.insert_action_group(self.undoactions, 1)

    def __change_redo_label(self, label):
        """
        Change the REDO label
        """
        self.uimanager.remove_action_group(self.redoactions)
        self.redoactions = Gtk.ActionGroup(name='Redo')
        if label:
            self.redoactions.add_actions([
                ('Redo', 'edit-redo', label, '<shift><PRIMARY>z',
                 None, self.redo)])
        else:
            self.redoactions.add_actions([
                ('Redo', 'edit-undo', _('_Redo'),
                 '<shift><PRIMARY>z', None, self.redo)])
            self.redoactions.set_sensitive(False)
        self.uimanager.insert_action_group(self.redoactions, 1)

    def undo_history_update(self):
        """
        This function is called to update both the state of
        the Undo History menu item (enable/disable) and
        the contents of the Undo History window.
        """
        try:
            # Try updating undo history window if it exists
            self.undo_history_window.update()
        except AttributeError:
            # Let it go: history window does not exist
            return

    def undo_history_close(self):
        """
        Closes the undo history
        """
        try:
            # Try closing undo history window if it exists
            if self.undo_history_window.opened:
                self.undo_history_window.close()
        except AttributeError:
            # Let it go: history window does not exist
            return

    def quick_backup(self, obj):
        """
        Make a quick XML back with or without media.
        """
        from .dialog import QuestionDialog2
        window = Gtk.Dialog(_("WearNow Backup"),
                            self.uistate.window,
                            Gtk.DialogFlags.DESTROY_WITH_PARENT, None)
        window.set_size_request(400, -1)
        ok_button = window.add_button(_('_OK'),
                                      Gtk.ResponseType.APPLY)
        close_button = window.add_button(_('_Close'),
                                         Gtk.ResponseType.CLOSE)
        vbox = window.get_content_area()
        hbox = Gtk.Box()
        label = Gtk.Label(label=_("Path:"))
        label.set_justify(Gtk.Justification.LEFT)
        label.set_size_request(90, -1)
        label.set_halign(Gtk.Align.START)
        hbox.pack_start(label, False, True, 0)
        path_entry = Gtk.Entry()
        text = config.get('paths.quick-backup-directory')
        path_entry.set_text(text)
        hbox.pack_start(path_entry, True, True, 0)
        file_entry = Gtk.Entry()
        button = Gtk.Button()
        button.connect("clicked",
                       lambda widget: self.select_backup_path(widget, path_entry))
        image = Gtk.Image()
        image.set_from_icon_name('document-open', Gtk.IconSize.BUTTON)
        image.show()
        button.add(image)
        hbox.pack_end(button, False, True, 0)
        vbox.pack_start(hbox, False, True, 0)
        hbox = Gtk.Box()
        label = Gtk.Label(label=_("File:"))
        label.set_justify(Gtk.Justification.LEFT)
        label.set_size_request(90, -1)
        label.set_halign(Gtk.Align.START)
        hbox.pack_start(label, False, True, 0)
        struct_time = time.localtime()
        file_entry.set_text(config.get('paths.quick-backup-filename') %
                            {"filename": self.dbstate.db.get_dbname(),
                             "year": struct_time.tm_year,
                             "month": struct_time.tm_mon,
                             "day": struct_time.tm_mday,
                             "hour": struct_time.tm_hour,
                             "minutes": struct_time.tm_min,
                             "seconds": struct_time.tm_sec,
                             "extension": "wpkg",
                             })
        hbox.pack_end(file_entry, True, True, 0)
        vbox.pack_start(hbox, False, True, 0)
        
        window.show_all()
        d = window.run()
        window.hide()
        if d == Gtk.ResponseType.APPLY:
            # if file exists, ask if overwrite; else abort
            basefile = conv_to_unicode(file_entry.get_text())
            basefile = basefile.replace("/", r"-")
            filename = os.path.join(conv_to_unicode(path_entry.get_text()),
                                    basefile)
            if os.path.exists(filename):
                question = QuestionDialog2(
                        _("Backup file already exists! Overwrite?"),
                        _("The file '%s' exists.") % filename,
                        _("Proceed and overwrite"),
                        _("Cancel the backup"),
                        parent=self.window)
                yes_no = question.run()
                if not yes_no:
                    return
            self.uistate.set_busy_cursor(True)
            self.uistate.pulse_progressbar(0)
            self.uistate.progress.show()
            self.uistate.push_message(self.dbstate, _("Making backup..."))
            from wearnow.plugins.export.exportxml import XmlWriter
            writer = XmlWriter(self.dbstate.db, self.user,
                               strip_photos=0, compress=1)
            writer.write(filename)
            self.uistate.set_busy_cursor(False)
            self.uistate.progress.hide()
            self.uistate.push_message(self.dbstate, _("Backup saved to '%s'") % filename)
            config.set('paths.quick-backup-directory', path_entry.get_text())
        else:
            self.uistate.push_message(self.dbstate, _("Backup aborted"))
        window.destroy()

    def select_backup_path(self, widget, path_entry):
        """
        Choose a backup folder. Make sure there is one highlighted in
        right pane, otherwise FileChooserDialog will hang.
        """
        f = Gtk.FileChooserDialog(
            title=_("Select backup directory"),
            parent=self.window,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            buttons=(_('_Cancel'),
                     Gtk.ResponseType.CANCEL,
                     _('_Apply'),
                     Gtk.ResponseType.OK))
        mpath = path_entry.get_text()
        if not mpath:
            mpath = HOME_DIR
        f.set_current_folder(os.path.dirname(mpath))
        f.set_filename(os.path.join(mpath, "."))
        status = f.run()
        if status == Gtk.ResponseType.OK:
            filename = f.get_filename()
            if filename:
                path_entry.set_text(filename)
        f.destroy()
        return True

    def config_view(self, obj):
        """
        Displays the configuration dialog for the active view
        """
        self.active_page.configure()

    def undo(self, obj):
        """
        Calls the undo function on the database
        """
        self.uistate.set_busy_cursor(True)
        self.dbstate.db.undo()
        self.uistate.set_busy_cursor(False)

    def redo(self, obj):
        """
        Calls the redo function on the database
        """
        self.uistate.set_busy_cursor(True)
        self.dbstate.db.redo()
        self.uistate.set_busy_cursor(False)

    def undo_history(self, obj):
        """
        Displays the Undo history window
        """
        try:
            self.undo_history_window = UndoHistory(self.dbstate, self.uistate)
        except WindowActiveError:
            return

    def export_data(self, obj):
        """
        Calls the ExportAssistant to export data
        """
        if self.dbstate.db.db_is_open:
            from .plug.export import ExportAssistant
            try:
                ExportAssistant(self.dbstate, self.uistate)
            except WindowActiveError:
                return

    def display_about_box(self, obj):
        """Display the About box."""
        about = WearNowAboutDialog(self.uistate.window)
        about.run()
        about.destroy()

def key_bindings(obj):
    """
    Display key bindings
    """
    display_help(webpage=URL_HOMEPAGE)

def manual_activate(obj):
    """
    Display the wearnow manual
    """
    display_help(webpage=URL_HOMEPAGE)

def report_bug_activate(obj):
    """
    Display the bug tracker web site
    """
    display_url(URL_HOMEPAGE)

def home_page_activate(obj):
    """
    Display the wearnow home page
    """
    display_url(URL_HOMEPAGE)
