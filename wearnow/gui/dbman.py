#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2009       Brian G. Matherly
# Copyright (C) 2009       Gary Burton
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
Provide the management of databases. This includes opening, renaming,
creating, and deleting of databases.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os
import time
import copy
import shutil
import subprocess
from urllib.parse import urlparse

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".DbManager")

from wearnow.tex.constfunc import win, conv_to_unicode
if win():
    _RCS_FOUND = os.system("rcs -V >nul 2>nul") == 0
    if _RCS_FOUND and "TZ" not in os.environ:
        # RCS requires the "TZ" variable be set.
        os.environ["TZ"] = str(time.timezone)
else:
    _RCS_FOUND = os.system("rcs -V >/dev/null 2>/dev/null") == 0

from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext

DEFAULT_TITLE = _("Collections")
NAME_FILE     = "name.txt"
META_NAME     = "meta_data.db"

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from gi.repository import Gdk
from gi.repository import Gtk
from gi.repository import Pango

#-------------------------------------------------------------------------
#
# wearnow modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import URL_HOMEPAGE
from .user import User
from .dialog import ErrorDialog, QuestionDialog, QuestionDialog2
from .pluginmanager import GuiPluginManager
from .ddtargets import DdTargets
from wearnow.tex.recentfiles import rename_filename, remove_filename
from .glade import Glade
from wearnow.tex.db.exceptions import DbException
from wearnow.tex.config import config

_RETURN = Gdk.keyval_from_name("Return")
_KP_ENTER = Gdk.keyval_from_name("KP_Enter")


#-------------------------------------------------------------------------
#
# constants
#
#-------------------------------------------------------------------------

ARCHIVE       = "rev.wearnow"
ARCHIVE_V     = "rev.wearnow,v"


def _errordialog(title, errormessage):
    """
    Show the error. A title for the error and an errormessage
    """
    print(_('ERROR: %(title)s \n       %(message)s') % {
                'title': title,
                'message': errormessage})
    sys.exit()

#-------------------------------------------------------------------------
#
# CLIDbManager
#
#-------------------------------------------------------------------------
class CLIDbManager(object):
    """
    Database manager without GTK functionality, allows users to create and
    open databases
    """
    IND_NAME = 0
    IND_PATH = 1
    IND_PATH_NAMEFILE = 2
    IND_TVAL_STR = 3
    IND_TVAL = 4
    IND_USE_ICON_BOOL = 5
    IND_STOCK_ID =6
    
    ICON_NONE     = 0
    ICON_RECOVERY = 1
    ICON_LOCK     = 2
    ICON_OPEN     = 3
    
    ICON_MAP = {
                ICON_NONE : None,
                ICON_RECOVERY : None,
                ICON_LOCK : None,
                ICON_OPEN : None,
               }
    
    ERROR = _errordialog
    def __init__(self, dbstate):
        self.dbstate = dbstate
        self.msg = None
        
        if dbstate:
            self.active  = dbstate.db.get_save_path()
        else:
            self.active = None
        
        self.current_names = []
        if dbstate:
            self._populate_cli()

    def empty(self, val):
        """
        Callback that does nothing
        """
        pass

    def get_dbdir_summary(self, dirpath, name):
        """
        dirpath: full path to database
        name: proper name of family tree

        Returns dictionary of summary item.
        Should include at least, if possible:

        _("Path")
        _("Family Tree")
        _("Last accessed")
        _("Database backend")
        _("Locked?")

        and these details:

        _("Number of people")
        _("Version")
        _("Schema version")
        """
        dbid = "bsddb"
        dbid_path = os.path.join(dirpath, "database.txt")
        if os.path.isfile(dbid_path):
            dbid = open(dbid_path).read().strip()
        try:
            database = self.dbstate.make_database(dbid)
            database.load(dirpath, None)
            retval = database.get_summary()
        except Exception as msg:
            retval = {"Unavailable": str(msg)[:74] + "..."}
        retval.update({
            _("Family Tree"): name,
            _("Path"): dirpath,
            _("Database backend"): dbid,
            _("Last accessed"): time_val(dirpath)[1],
            _("Locked?"): self.is_locked(dirpath),
        })
        return retval

    def family_tree_summary(self):
        """
        Return a list of dictionaries of the known family trees.
        """
        # make the default directory if it does not exist
        summary_list = []
        for item in self.current_names:
            (name, dirpath, path_name, last, 
             tval, enable, stock_id) = item
            retval = self.get_dbdir_summary(dirpath, name)
            summary_list.append( retval )
        return summary_list

    def _populate_cli(self):
        """
        Get the list of current names in the database dir
        """
        # make the default directory if it does not exist
        dbdir = os.path.expanduser(config.get('behavior.database-path'))
        db_ok = make_dbdir(dbdir)

        self.current_names = []
        if db_ok:
            for dpath in os.listdir(dbdir):
                dirpath = os.path.join(dbdir, dpath)
                path_name = os.path.join(dirpath, NAME_FILE)
                if os.path.isfile(path_name):
                    file = io.open(path_name, 'r', encoding='utf8')
                    name = file.readline().strip()
                    file.close()

                    (tval, last) = time_val(dirpath)
                    (enable, stock_id) = self.icon_values(dirpath, self.active, 
                                                     self.dbstate.db.is_open())

                    if (stock_id == 'wearnow-lock'):
                        last = find_locker_name(dirpath)

                    self.current_names.append(
                        (name, os.path.join(dbdir, dpath), path_name,
                         last, tval, enable, stock_id))

        self.current_names.sort()

    def get_family_tree_path(self, name):
        """
        Given a name, return None if name not existing or the path to the
        database if it is a known database name.
        """
        for data in self.current_names:
            if data[0] == name:
                return data[1]
        return None

    def family_tree_list(self):
        """
        Return a list of name, dirname of the known family trees
        """
        lst = [(x[0], x[1]) for x in self.current_names]
        return lst

    def __start_cursor(self, msg):
        """
        Do needed things to start import visually, eg busy cursor
        """
        print(_('Starting Import, %s') % msg)

    def __end_cursor(self):
        """
        Set end of a busy cursor
        """
        print(_('Import finished...'))

    def create_new_db_cli(self, title=None, create_db=True, dbid=None):
        """
        Create a new database.
        """
        new_path = find_next_db_dir()

        os.mkdir(new_path)
        path_name = os.path.join(new_path, NAME_FILE)

        if title is None:
            name_list = [ name[0] for name in self.current_names ]
            title = find_next_db_name(name_list)

        name_file = io.open(path_name, "w", encoding='utf8')
        name_file.write(title)
        name_file.close()

        if create_db:
            # write the version number into metadata
            if dbid is None:
                dbid = "bsddb"
            newdb = self.dbstate.make_database(dbid)
            newdb.write_version(new_path)

        (tval, last) = time_val(new_path)
        
        self.current_names.append((title, new_path, path_name,
                                   last, tval, False, ""))
        return new_path, title

    def _create_new_db(self, title=None, dbid=None):
        """
        Create a new database, do extra stuff needed
        """
        return self.create_new_db_cli(title, dbid=dbid)

    def import_new_db(self, filename, user):
        """
        Attempt to import the provided file into a new database.
        A new database will only be created if an appropriate importer was 
        found.

        :param filename: a fully-qualified path, filename, and
                         extension to open.

        :param user: a :class:`.cli.user.User` or :class:`.gui.user.User`
                     instance for managing user interaction.
        
        :returns: A tuple of (new_path, name) for the new database
                  or (None, None) if no import was performed.
        """
        pmgr = BasePluginManager.get_instance()
        # check to see if it isn't a filename directly:
        if not os.path.isfile(filename):
            # Allow URL names here; make temp file if necessary
            url = urlparse(filename)
            if url.scheme != "":
                if url.scheme == "file":
                    filename = url2pathname(filename[7:])
                else:
                    url_fp = urlopen(filename) # open URL
                    # make a temp local file:
                    ext = os.path.splitext(url.path)[1]
                    fd, filename = tempfile.mkstemp(suffix=ext)
                    temp_fp = os.fdopen(fd, "w")
                    # read from URL:
                    data = url_fp.read()
                    # write locally:
                    temp_fp.write(data)
                    url_fp.close()
                    from  gen.db.dbconst import BDBVERSFN
                    versionpath = os.path.join(name, BDBVERSFN)
                    _LOG.debug("Write bsddb version %s" % str(dbase.version()))
                    with open(versionpath, "w") as version_file:
                        version_file.write(str(dbase.version()))
                    temp_fp.close()

        (name, ext) = os.path.splitext(os.path.basename(filename))
        format = ext[1:].lower()

        for plugin in pmgr.get_import_plugins():
            if format == plugin.get_extension():

                new_path, name = self._create_new_db(name)
    
                # Create a new database
                self.__start_cursor(_("Importing data..."))

                dbase = self.dbstate.make_database("bsddb")
                dbase.load(new_path, user.callback)
    
                import_function = plugin.get_import_function()
                import_function(dbase, filename, user)
    
                # finish up
                self.__end_cursor()
                dbase.close()
                
                return new_path, name
        return None, None

    def is_locked(self, dbpath):
        """
        Returns True if there is a lock file in the dirpath
        """
        if os.path.isfile(os.path.join(dbpath,"lock")):
            return True
        return False

    def needs_recovery(self, dbpath):
        """
        Returns True if the database in dirpath needs recovery
        """
        if os.path.isfile(os.path.join(dbpath,"need_recover")):
            return True
        return False

    def rename_database(self, filepath, new_text):
        """
        Renames the database by writing the new value to the name.txt file
        Returns old_name, new_name if success, None, None if no success
        """
        try:
            filepath = conv_to_unicode(filepath, 'utf8')
            new_text = conv_to_unicode(new_text, 'utf8')
            name_file = io.open(filepath, "r", encoding='utf8')
            old_text=name_file.read()
            name_file.close()
            name_file = io.open(filepath, "w", encoding='utf8')
            name_file.write(new_text)
            name_file.close()
        except (OSError, IOError) as msg:
            CLIDbManager.ERROR(_("Could not rename Family Tree"),
                  str(msg))
            return None, None
        return old_text, new_text

    def break_lock(self, dbpath):
        """
        Breaks the lock on a database
        """
        if os.path.exists(os.path.join(dbpath, "lock")):
            os.unlink(os.path.join(dbpath, "lock"))
    
    def icon_values(self, dirpath, active, is_open):
        """
        If the directory path is the active path, then return values
        that indicate to use the icon, and which icon to use.
        """
        if os.path.isfile(os.path.join(dirpath,"need_recover")):
            return (True, self.ICON_MAP[self.ICON_RECOVERY])
        elif dirpath == active and is_open:
            return (True, self.ICON_MAP[self.ICON_OPEN])
        elif os.path.isfile(os.path.join(dirpath,"lock")):
            return (True, self.ICON_MAP[self.ICON_LOCK])
        else:
            return (False, self.ICON_MAP[self.ICON_NONE])


NAME_COL  = 0
PATH_COL  = 1
FILE_COL  = 2
DATE_COL  = 3
DSORT_COL = 4
OPEN_COL  = 5
ICON_COL = 6

RCS_BUTTON = { True : _('_Extract'), False : _('_Archive') }

class DbManager(CLIDbManager):
    """
    Database Manager. Opens a database manager window that allows users to
    create, rename, delete and open databases.
    """
    ICON_MAP = {
                CLIDbManager.ICON_NONE : None,
                CLIDbManager.ICON_RECOVERY : 'dialog-error',
                CLIDbManager.ICON_LOCK : 'wearnow-lock',
                CLIDbManager.ICON_OPEN : 'document-open',
               }

    ERROR = ErrorDialog
        
    def __init__(self, dbstate, parent=None):
        """
        Create the top level window from the glade description, and extracts
        the GTK widgets that are needed.
        """
        CLIDbManager.__init__(self, dbstate)
        self.glade = Glade(toplevel='dbmanager')
        self.top = self.glade.toplevel

        if parent:
            self.top.set_transient_for(parent)

        for attr in ['connect', 'cancel', 'new', 'remove', 'copy',
                     'dblist', 'rename', 'repair', 'rcs', 'msg']:
            setattr(self, attr, self.glade.get_object(attr))

        self.model = None
        self.column  = None
        self.lock_file = None
        self.data_to_delete = None

        self.selection = self.dblist.get_selection()

        self.__connect_signals()
        self.__build_interface()
        self._populate_model()

    def __connect_signals(self):
        """
        Connects the signals to the buttons on the interface. 
        """
        ddtarget = DdTargets.URI_LIST
        self.top.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        tglist = Gtk.TargetList.new([])
        tglist.add(ddtarget.atom_drag_type, ddtarget.target_flags,
                   ddtarget.app_id)
        self.top.drag_dest_set_target_list(tglist)

        self.remove.connect('clicked', self.__remove_db)
        self.new.connect('clicked', self.__new_db)
        self.rename.connect('clicked', self.__rename_db)
        self.copy.connect('clicked', self.__copy_db)
        self.repair.connect('clicked', self.__repair_db)
        self.selection.connect('changed', self.__selection_changed)
        self.dblist.connect('button-press-event', self.__button_press)
        self.dblist.connect('key-press-event', self.__key_press)
        self.top.connect('drag_data_received', self.__drag_data_received)
        self.top.connect('drag_motion', drag_motion)
        self.top.connect('drag_drop', drop_cb)

        if _RCS_FOUND:
            self.rcs.connect('clicked', self.__rcs)

    def __button_press(self, obj, event):
        """
        Checks for a double click event. In the tree view, we want to 
        treat a double click as if it was OK button press. However, we have
        to make sure that an item was selected first.
        """
        if event.type == Gdk.EventType._2BUTTON_PRESS and event.button == 1:
            if self.connect.get_property('sensitive'):
                self.top.response(Gtk.ResponseType.OK)
                return True
        return False

    def __key_press(self, obj, event):
        """
        Grab ENTER so it does not start editing the cell, but behaves
        like double click instead
        """
        if event.keyval in (_RETURN, _KP_ENTER):
            if self.connect.get_property('sensitive'):
                self.top.response(Gtk.ResponseType.OK)
                return True
        return False

    def __selection_changed(self, selection):
        """
        Called when the selection is changed in the TreeView. 
        """
        self.__update_buttons(selection)

    def __update_buttons(self, selection):
        """
        What we are trying to detect is the selection or unselection of a row.
        When a row is unselected, the Open, Rename, and Remove buttons
        are set insensitive. If a row is selected, the rename and remove
        buttons are disabled, and the Open button is disabled if the
        row represents a open database.
        """
            
        # Get the current selection
        store, node = selection.get_selected()

        # if nothing is selected
        if not node:
            self.connect.set_sensitive(False)
            self.rename.set_sensitive(False)
            self.copy.set_sensitive(False)
            self.rcs.set_sensitive(False)
            self.repair.set_sensitive(False)
            self.remove.set_sensitive(False)
            return
        
        path = self.model.get_path(node)
        if path is None:
            return

        is_rev = len(path.get_indices()) > 1
        self.rcs.set_label(RCS_BUTTON[is_rev])

        if store.get_value(node, ICON_COL) == 'document-open':
            self.connect.set_sensitive(False)
            if _RCS_FOUND:
                self.rcs.set_sensitive(True)
        else:
            self.connect.set_sensitive(not is_rev)
            if _RCS_FOUND and is_rev:
                self.rcs.set_sensitive(True)
            else:
                self.rcs.set_sensitive(False)

        if store.get_value(node, ICON_COL) == 'dialog-error':
            path = conv_to_unicode(store.get_value(node, PATH_COL), 'utf8')
            backup = os.path.join(path, "person.gbkp")
            self.repair.set_sensitive(os.path.isfile(backup))
        else:
            self.repair.set_sensitive(False)
            
        self.rename.set_sensitive(True)
        self.copy.set_sensitive(True)
        self.remove.set_sensitive(True)
        self.new.set_sensitive(True)

    def __build_interface(self):
        """
        Builds the columns for the TreeView. The columns are:

        Icon, Database Name, Last Modified

        The Icon column gets its data from column 6 of the database model.
        It is expecting either None, or a GTK stock icon name

        The Database Name column is an editable column. We connect to the
        'edited' signal, so that we can change the name when the user changes
        the column.

        The last accessed column simply displays the last time famtree was 
        opened.
        """

        # build the database name column
        render = Gtk.CellRendererText()
        render.set_property('ellipsize', Pango.EllipsizeMode.END)
        render.connect('edited', self.__change_name)
        render.connect('editing-canceled', self.__stop_edit)
        render.connect('editing-started', self.__start_edit)
        self.column = Gtk.TreeViewColumn(_('Family Tree name'), render, 
                                         text=NAME_COL)
        self.column.set_sort_column_id(NAME_COL)
        self.column.set_sort_indicator(True)
        self.column.set_resizable(True)
        self.column.set_min_width(275)
        self.dblist.append_column(self.column)
        self.name_renderer = render

        # build the icon column
        render = Gtk.CellRendererPixbuf()
        #icon_column = Gtk.TreeViewColumn(_('Status'), render, 
                                         #icon_name=ICON_COL)
        icon_column = Gtk.TreeViewColumn(_('Status'), render)
        icon_column.set_cell_data_func(render, bug_fix)
        self.dblist.append_column(icon_column)

        # build the last accessed column
        render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_('Last accessed'), render, text=DATE_COL)
        column.set_sort_column_id(DSORT_COL)
        self.dblist.append_column(column)

    def __populate(self):
        """
        Builds the data and the display model.
        """
        self._populate_cli()
        self._populate_model()
        
    def _populate_model(self):
        """
        Builds the display model.
        """
        self.model = Gtk.TreeStore(str, str, str, str, int, bool, str)

        #use current names to set up the model
        for items in self.current_names:
            data = list(items[:7])
            node = self.model.append(None, data)
            for rdata in find_revisions(os.path.join(items[1], ARCHIVE_V)):
                data = [ rdata[2], rdata[0], items[1], rdata[1], 0, False, "" ]
                self.model.append(node, data)
        self.model.set_sort_column_id(NAME_COL, Gtk.SortType.ASCENDING)
        self.dblist.set_model(self.model)

    def existing_name(self, name, skippath=None):
        """
        Return true if a name is present in the model already.
        If skippath given, the name of skippath is not considered
        """
        iter = self.model.get_iter_first()
        while (iter):
            path = self.model.get_path(iter)
            if path == skippath:
                pass
            else:
                itername = self.model.get_value(iter, NAME_COL)
                if itername.strip() == name.strip():
                    return True
            iter = self.model.iter_next(iter)
        return False

    def run(self):
        """
        Runs the dialog, returning None if nothing has been chosen,
        or the path and name if something has been selected
        """
        while True:
            value = self.top.run()
            if value == Gtk.ResponseType.OK:
                store, node = self.selection.get_selected()
                # don't open a locked file
                if store.get_value(node, ICON_COL) == 'wearnow-lock':
                    self.__ask_to_break_lock(store, node)
                    continue 
                # don't open a version
                if len(store.get_path(node).get_indices()) > 1:
                    continue
                if node:
                    self.top.destroy()
                    del self.selection
                    del self.name_renderer
                    path = conv_to_unicode(store.get_value(node, PATH_COL), 'utf8')
                    return (path, store.get_value(node, NAME_COL))
            else:
                self.top.destroy()
                del self.selection
                del self.name_renderer
                return None

    def __ask_to_break_lock(self, store, node):
        """
        Prompts the user for permission to break the lock file that another
        process has set on the file.
        """
        path = store.get_path(node)
        self.lock_file = store[path][PATH_COL]

        QuestionDialog(
            _("Break the lock on the '%s' database?") % store[path][0],
            _("WearNow believes that someone else is actively editing "
              "this database. You cannot edit this database while it "
              "is locked. If no one is editing the database you may "
              "safely break the lock. However, if someone else is editing "
              "the database and you break the lock, you may corrupt the "
              "database."),
            _("Break lock"),
            self.__really_break_lock, self.top)

    def __really_break_lock(self):
        """
        Deletes the lock file associated with the selected database, then updates
        the display appropriately.
        """
        try:
            self.break_lock(self.lock_file)
            store, node = self.selection.get_selected()
            dbpath = conv_to_unicode(store.get_value(node, PATH_COL), 'utf8')
            (tval, last) = time_val(dbpath)
            store.set_value(node, OPEN_COL, 0)
            store.set_value(node, ICON_COL, "")
            store.set_value(node, DATE_COL, last)
            store.set_value(node, DSORT_COL, tval)
        except IOError:
            return

    def __stop_edit(self, *args):
        self.name_renderer.set_property('editable', False)
        self.__update_buttons(self.selection)

    def __start_edit(self, *args):
        """
        Do not allow to click Load while changing name, to force users to finish
        the action of renaming. Hack around the fact that clicking button
        sends a 'editing-canceled' signal loosing the new name
        """
        self.connect.set_sensitive(False)
        self.rename.set_sensitive(False)
        self.copy.set_sensitive(False)
        self.rcs.set_sensitive(False)
        self.repair.set_sensitive(False)
        self.remove.set_sensitive(False)
        self.new.set_sensitive(False)

    def __change_name(self, renderer_sel, path, new_text):
        """
        Change the name of the database. This is a callback from the
        column, which has been marked as editable. 

        If the new string is empty, do nothing. Otherwise, renaming the	
        database is simply changing the contents of the name file.
        """
        #path is a string, convert to TreePath first
        path = Gtk.TreePath(path=path)
        if len(new_text) > 0:
            new_text = conv_to_unicode(new_text, 'utf8')
            node = self.model.get_iter(path)
            old_text = self.model.get_value(node, NAME_COL)
            if not old_text.strip() == new_text.strip():
                if len(path.get_indices()) > 1 :
                    self.__rename_revision(path, new_text)
                else:
                    self.__rename_database(path, new_text)
        
        self.name_renderer.set_property('editable', False)
        self.__update_buttons(self.selection)

    def __rename_revision(self, path, new_text):
        """
        Renames the RCS revision using the rcs command. The rcs command 
        is in the format of:

           rcs -mREV:NEW_NAME archive

        """
        node = self.model.get_iter(path)
        db_dir = self.model.get_value(node, FILE_COL)
        rev = self.model.get_value(node, PATH_COL)
        archive = os.path.join(db_dir, ARCHIVE_V)

        cmd = [ "rcs", "-x,v", "-m%s:%s" % (rev, new_text), archive ]

        proc = subprocess.Popen(cmd, stderr = subprocess.PIPE)
        status = proc.wait()
        message = "\n".join(proc.stderr.readlines())
        proc.stderr.close()
        del proc

        if status != 0:
            DbManager.ERROR(
                _("Rename failed"),
                _("An attempt to rename a version failed "
                  "with the following message:\n\n%s") % message
                )
        else:
            self.model.set_value(node, NAME_COL, new_text)
            #scroll to new position
            store, node = self.selection.get_selected()
            tree_path = store.get_path(node)
            self.dblist.scroll_to_cell(tree_path, None, False, 0.5, 0.5)

    def __rename_database(self, path, new_text):
        """
        Renames the database by writing the new value to the name.txt file
        """
        new_text = new_text.strip()
        node = self.model.get_iter(path)
        filename = self.model.get_value(node, FILE_COL)
        if self.existing_name(new_text, skippath=path):
            DbManager.ERROR(_("Could not rename the Family Tree."), 
                  _("Family Tree already exists, choose a unique name."))
            return
        old_text, new_text = self.rename_database(filename, new_text)
        if not (old_text is None):
            rename_filename(old_text, new_text)
            self.model.set_value(node, NAME_COL, new_text)
        #scroll to new position
        store, node = self.selection.get_selected()
        tree_path = store.get_path(node)
        self.dblist.scroll_to_cell(tree_path, None, False, 0.5, 0.5)

    def __rcs(self, obj):
        """
        Callback for the RCS button. If the tree path is > 1, then we are
        on an RCS revision, in which case we can check out. If not, then
        we can only check in.
        """
        store, node = self.selection.get_selected()
        tree_path = store.get_path(node)
        if len(tree_path.get_indices()) > 1:
            parent_node = store.get_iter((tree_path[0],))
            parent_name = store.get_value(parent_node, NAME_COL)
            name = store.get_value(node, NAME_COL)
            revision = store.get_value(node, PATH_COL)
            db_path = store.get_value(node, FILE_COL)

            self.__checkout_copy(parent_name, name, revision, db_path)
        else:
            base_path = self.dbstate.db.get_save_path()
            archive = os.path.join(base_path, ARCHIVE) 
            check_in(self.dbstate.db, archive, User(), self.__start_cursor)
            self.__end_cursor()

        self.__populate()
        
    def __checkout_copy(self, parent_name, name, revision, db_path):
        """
        Create a new database, then extracts a revision from RCS and
        imports it into the db
        """
        new_path, newname = self._create_new_db("%s : %s" % (parent_name, name))
        
        self.__start_cursor(_("Extracting archive..."))

        dbase = self.dbstate.make_database("bsddb")
        dbase.load(new_path, None)
        
        self.__start_cursor(_("Importing archive..."))
        check_out(dbase, revision, db_path, User())
        self.__end_cursor()
        dbase.close()

    def __remove_db(self, obj):
        """
        Callback associated with the Remove button. Get the selected
        row and data, then call the verification dialog.
        """
        store, node = self.selection.get_selected()
        path = store.get_path(node)
        self.data_to_delete = store[path]

        if len(path.get_indices()) == 1:
            QuestionDialog(
                _("Remove the '%s' Family Tree?") % self.data_to_delete[0],
                _("Removing this Family Tree will permanently destroy the data."),
                _("Remove Family Tree"),
                self.__really_delete_db, parent=self.top)
        else:
            rev = self.data_to_delete[0]
            parent = store[(path[0],)][0]
            QuestionDialog(
                _("Remove the '%(revision)s' version of '%(database)s'") % {
                    'revision' : rev, 
                    'database' : parent
                    },
                _("Removing this version will prevent you from "
                  "extracting it in the future."),
                _("Remove version"),
                self.__really_delete_version, parent=self.top)

    def __really_delete_db(self):
        """
        Delete the selected database. If the database is open, close it first.
        Then scan the database directory, deleting the files, and finally
        removing the directory.
        """

        # close the database if the user has requested to delete the
        # active database
        if self.data_to_delete[PATH_COL] == self.active:
            self.dbstate.no_database()
            
        store, node = self.selection.get_selected()
        path = store.get_path(node)
        node = self.model.get_iter(path)
        filename = conv_to_unicode(self.model.get_value(node, FILE_COL), 'utf8')
        try:
            name_file = open(filename, "r")
            file_name_to_delete=name_file.read()
            name_file.close()
            remove_filename(file_name_to_delete)
            directory = conv_to_unicode(self.data_to_delete[1], 'utf8')
            for (top, dirs, files) in os.walk(directory):
                for filename in files:
                    os.unlink(os.path.join(top, filename))
            os.rmdir(directory)
        except (IOError, OSError) as msg:
            DbManager.ERROR(_("Could not delete Family Tree"),
                            str(msg))
        # rebuild the display
        self.__populate()
            
    def __really_delete_version(self):
        """
        Delete the selected database. If the database is open, close it first.
        Then scan the database directory, deleting the files, and finally
        removing the directory.
        """
        db_dir = self.data_to_delete[FILE_COL]
        rev = self.data_to_delete[PATH_COL]
        archive = os.path.join(db_dir, ARCHIVE_V)

        cmd = [ "rcs", "-x,v", "-o%s" % rev, "-q", archive ]

        proc = subprocess.Popen(cmd, stderr = subprocess.PIPE)
        status = proc.wait()
        message = "\n".join(proc.stderr.readlines())
        proc.stderr.close()
        del proc

        if status != 0:
            DbManager.ERROR(
                _("Deletion failed"),
                _("An attempt to delete a version failed "
                  "with the following message:\n\n%s") % message
                )

        # rebuild the display
        self.__populate()
            
    def __rename_db(self, obj):
        """
        Start the rename process by calling the start_editing option on 
        the line with the cursor.
        """
        store, node = self.selection.get_selected()
        path = self.model.get_path(node)
        self.name_renderer.set_property('editable', True)
        self.dblist.set_cursor(path, self.column, True)

    def __copy_db(self, obj):
        """
        Copy the database through low-level file copies.
        """
        # First, get the selected tree:
        store, node = self.selection.get_selected()
        # New title:
        date_string = time.strftime("%d %b %Y %H:%M:%S", time.gmtime())
        title = _("%(new_DB_name)s (copied %(date_string)s)") % {
                      'new_DB_name' : store[node][NAME_COL],
                      'date_string' : date_string }
        # Create the row and directory, awaits user edit of title:
        (new_dir, title) = self._create_new_db(title, create_db=False)
        # Copy the files:
        name_file = conv_to_unicode(store[node][FILE_COL], 'utf8')
        old_dir = os.path.dirname(name_file)
        for filename in os.listdir(old_dir):
            if filename == "name.txt":
                continue
            old_file = os.path.abspath(os.path.join(old_dir, filename))
            shutil.copy2(old_file, new_dir)

    def __repair_db(self, obj):
        """
        Start the repair process by calling the start_editing option on 
        the line with the cursor.
        """
        store, node = self.selection.get_selected()
        dirname = store[node][1]
        
        #First ask user if he is really sure :-)
        yes_no = QuestionDialog2(
            _("Repair Family Tree?"),
            _(
              "If you click %(bold_start)sProceed%(bold_end)s, WearNow will "
              "attempt to recover your Family Tree from the last good "
              "backup. There are several ways this can cause unwanted "
              "effects, so %(bold_start)sbackup%(bold_end)s the "
              "Family Tree first.\nThe Family Tree you have selected "
              "is stored in %(dirname)s.\n\n"
              "Before doing a repair, verify that the Family Tree can "
              "really no longer be opened, as the database back-end can "
              "recover from some errors automatically.\n\n"
              "%(bold_start)sDetails:%(bold_end)s Repairing a Family Tree "
              "actually uses the last backup of the Family Tree, which "
              "WearNow stored on last use. If you have worked for "
              "several hours/days without closing WearNow, then all "
              "this information will be lost! If the repair fails, then "
              "the original Family Tree will be lost forever, hence "
              "a backup is needed. If the repair fails, or too much "
              "information is lost, you can fix the original "
              "Family Tree manually. For details, see the webpage\n"
              "%(wearnow_wiki_recover_url)s\n"
              "Before doing a repair, try to open the Family Tree "
              "in the normal manner. Several errors that trigger the "
              "repair button can be fixed automatically. "
              "If this is the case, you can disable the repair button "
              "by removing the file %(recover_file)s in the "
              "Family Tree directory."
             ) % { 'bold_start'   : '<b>' ,
                   'bold_end'     : '</b>' ,
                   'recover_file' : '<i>need_recover</i>' ,
                   'wearnow_wiki_recover_url' :
                       URL_HOMEPAGE + 'Recover_corrupted_family_tree',
                   'dirname'      : dirname },
            _("Proceed, I have taken a backup"),
            _("Stop"))
        prompt = yes_no.run()
        if not prompt:
            return
        
        opened = store[node][OPEN_COL]
        if opened:
            self.dbstate.no_database()
        
        # delete files that are not backup files or the .txt file
        for filename in os.listdir(dirname):
            if os.path.splitext(filename)[1] not in (".gbkp", ".txt"):
                fname = os.path.join(dirname, filename)
                os.unlink(fname)

        newdb = self.dbstate.make_database("bsddb")
        newdb.write_version(dirname)

        dbase = self.dbstate.make_database("bsddb")
        dbase.set_save_path(dirname)
        dbase.load(dirname, None)

        self.__start_cursor(_("Rebuilding database from backup files"))
        
        try:
            dbase.restore()
        except DbException as msg:
            DbManager.ERROR(_("Error restoring backup data"), msg)

        self.__end_cursor()

        dbase.close()
        self.dbstate.no_database()
        self.__populate()

    def __start_cursor(self, msg):
        """
        Set the cursor to the busy state, and displays the associated
        message
        """
        self.msg.set_label(msg)
        self.top.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.WATCH))
        while (Gtk.events_pending()):
            Gtk.main_iteration()

    def __end_cursor(self):
        """
        Set the cursor back to normal and clears the message
        """
        self.top.get_window().set_cursor(None)
        self.msg.set_label("")

    def __new_db(self, obj):
        """
        Callback wrapper around the actual routine that creates the
        new database. Catch OSError and IOError and display a warning 
        message.
        """
        self.new.set_sensitive(False)
        dbid = config.get('behavior.database-backend')
        if dbid:
            try:
                self._create_new_db(dbid=dbid)
            except (OSError, IOError) as msg:
                DbManager.ERROR(_("Could not create Family Tree"),
                                str(msg))
        self.new.set_sensitive(True)

    def _create_new_db(self, title=None, create_db=True, dbid=None):
        """
        Create a new database, append to model
        """
        new_path, title = self.create_new_db_cli(conv_to_unicode(title, 'utf8'),
                                                 create_db, dbid)
        path_name = os.path.join(new_path, NAME_FILE)
        (tval, last) = time_val(new_path)
        node = self.model.append(None, [title, new_path, path_name, 
                                        last, tval, False, ''])
        self.selection.select_iter(node)
        path = self.model.get_path(node)
        self.name_renderer.set_property('editable', True)
        self.dblist.set_cursor(path, self.column, True)
        return new_path, title

    def __drag_data_received(self, widget, context, xpos, ypos, selection, 
                             info, rtime):
        """
        Handle the reception of drag data
        """
        drag_value = selection.get_data()
        fname = None
        type = None
        title = None
        # Allow any type of URL ("file://", "http://", etc):
        if drag_value and urlparse(drag_value).scheme != "":
            fname, title = [], []
            for treename in [v.strip() for v in drag_value.split("\n") if v.strip() != '']:
                f, t = self.import_new_db(treename, User())
                fname.append(f)
                title.append(t)
        return fname, title

def drag_motion(wid, context, xpos, ypos, time_stamp):
    """
    DND callback that is called on a DND drag motion begin
    """
    Gdk.drag_status(context, Gdk.DragAction.COPY, time_stamp)
    return True

def drop_cb(wid, context, xpos, ypos, time_stamp):
    """
    DND callback that finishes the DND operation
    """
    Gtk.drag_finish(context, True, False, time_stamp)
    return True

def find_revisions(name):
    """
    Finds all the revisions of the specified RCS archive.
    """
    import re

    rev  = re.compile("\s*revision\s+([\d\.]+)")
    date = re.compile("date:\s+(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d)[-+]\d\d;")

    if not os.path.isfile(name) or not _RCS_FOUND:
        return []

    rlog = [ "rlog", "-x,v", "-zLT" , name ]

    proc = subprocess.Popen(rlog, stdout = subprocess.PIPE)
    proc.wait()

    revlist = []
    date_str = ""
    rev_str = ""
    com_str = ""
    
    get_next = False
    if os.path.isfile(name):
        for line in proc.stdout:
            if not isinstance(line, str):
                # we assume utf-8 ...
                line = line.decode('utf-8')
            match = rev.match(line)
            if match:
                rev_str = copy.copy(match.groups()[0])
                continue
            match = date.match(line)
            if match:
                date_str = time.strftime('%x %X',
                        time.strptime(match.groups()[0], '%Y-%m-%d %H:%M:%S'))
                
                get_next = True
                continue
            if get_next:
                get_next = False
                com_str = line.strip()
                revlist.append((rev_str, date_str, com_str))
    proc.stdout.close()
    del proc
    return revlist



def check_out(dbase, rev, path, user):
    """
    Checks out the revision from rcs, and loads the resulting XML file
    into the database.
    """
    co_cmd   = [ "co", "-x,v", "-q%s" % rev] + [ os.path.join(path, ARCHIVE),
                                                 os.path.join(path, ARCHIVE_V)]

    proc = subprocess.Popen(co_cmd, stderr = subprocess.PIPE)
    status = proc.wait()
    message = "\n".join(proc.stderr.readlines())
    proc.stderr.close()
    del proc

    if status != 0:
        user.notify_error(
            _("Retrieve failed"),
            _("An attempt to retrieve the data failed "
              "with the following message:\n\n%s") % message
            )
        return 

    pmgr = GuiPluginManager.get_instance()
    for plugin in pmgr.get_import_plugins():
        if plugin.get_extension() == "wearnow":
            rdr = plugin.get_import_function()

    xml_file = os.path.join(path, ARCHIVE)
    rdr(dbase, xml_file, user)
    os.unlink(xml_file)

def check_in(dbase, filename, user, cursor_func = None):
    """
    Checks in the specified file into RCS
    """
    init   = [ "rcs", '-x,v', '-i', '-U', '-q', '-t-"WearNow database"' ]
    ci_cmd = [ "ci", '-x,v', "-q", "-f" ]
    archive_name = filename + ",v"
    
    glade = Glade(toplevel='comment')
    top = glade.toplevel
    text = glade.get_object('description')
    top.run()
    comment = text.get_text()
    top.destroy()

    if not os.path.isfile(archive_name):
        cmd = init + [archive_name]
        proc = subprocess.Popen(cmd,
                                stderr = subprocess.PIPE)
        status = proc.wait()
        message = "\n".join(proc.stderr.readlines())
        proc.stderr.close()
        del proc
        
        if status != 0:
            ErrorDialog(
                _("Archiving failed"),
                _("An attempt to create the archive failed "
                  "with the following message:\n\n%s") % message
                )

    if cursor_func:
        cursor_func(_("Creating data to be archived..."))
        
    plugin_manager = GuiPluginManager.get_instance()
    for plugin in plugin_manager.get_export_plugins():
        if plugin.get_extension() == "wearnow":
            export_function = plugin.get_export_function()
            export_function(dbase, filename, user)

    if cursor_func:
        cursor_func(_("Saving archive..."))
        
    cmd = ci_cmd + ['-m%s' % comment, filename, archive_name ]
    proc = subprocess.Popen(cmd, 
                            stderr = subprocess.PIPE)

    status = proc.wait()
    message = "\n".join(proc.stderr.readlines())
    proc.stderr.close()
    del proc

    if status != 0:
        ErrorDialog(
            _("Archiving failed"),
            _("An attempt to archive the data failed "
              "with the following message:\n\n%s") % message
            )

def bug_fix(column, renderer, model, iter_, data):
    """
    Cell data function to set the status column.
    
    There is a bug in pygobject which prevents us from setting a value to
    None using the TreeModel set_value method.  Instead we set it to an empty
    string and convert it to None here.
    """
    icon_name = model.get_value(iter_, ICON_COL)
    if icon_name == '':
        icon_name = None
    renderer.set_property('icon-name', icon_name)

def make_dbdir(dbdir):
    """
    Create the default database directory, as defined by dbdir
    """
    try:
        if not os.path.isdir(dbdir):
            os.makedirs(dbdir)
    except (IOError, OSError) as msg:
        LOG.error(_("\nERROR: Wrong database path in Edit Menu->Preferences.\n"
                    "Open preferences and set correct database path.\n\n"
                    "Details: Could not make database directory:\n    %s\n\n") % msg)
        return False
    return True

def find_next_db_name(name_list):
    """
    Scan the name list, looking for names that do not yet exist.
    Use the DEFAULT_TITLE as the basis for the database name.
    """
    i = 1
    while True:
        title = "%s %d" % (DEFAULT_TITLE, i)
        if title not in name_list:
            return conv_to_unicode(title)
        i += 1

def find_next_db_dir():
    """
    Searches the default directory for the first available default
    database name. Base the name off the current time. In all actuality,
    the first should be valid.
    """
    while True:
        base = "%x" % int(time.time())
        dbdir = os.path.expanduser(config.get('behavior.database-path'))
        new_path = os.path.join(dbdir, base)
        if not os.path.isdir(new_path):
            break
    return new_path

def time_val(dirpath):
    """
    Return the last modified time of the database. We do this by looking
    at the modification time of the meta db file. If this file does not 
    exist, we indicate that database as never modified.
    """
    meta = os.path.join(dirpath, META_NAME)
    if os.path.isfile(meta):
        tval = os.stat(meta)[9]
        # This gives creation date in Windows, but correct date in Linux
        if win():
            # Try to use last modified date instead in Windows
            # and check that it is later than the creation date.
            tval_mod = os.stat(meta)[8]
            if tval_mod > tval:
                tval = tval_mod
        last = time.strftime('%x %X', time.localtime(tval))
    else:
        tval = 0
        last = _("Never")
    return (tval, last)

def find_locker_name(dirpath):
    """
    Opens the lock file if it exists, reads the contexts which is "USERNAME"
    and returns the contents, with correct string before "USERNAME",
    so the message can be printed with correct locale.
    If a file is encountered with errors, we return 'Unknown'
    This data can eg be displayed in the time column of the manager
    """
    try:
        fname = os.path.join(dirpath, "lock")
        ifile = io.open(fname, 'r', encoding='utf8')
        username = ifile.read().strip()
        # feature request 2356: avoid genitive form
        last = _("Locked by %s") % username
        ifile.close()
    except (OSError, IOError, UnicodeDecodeError):
        last = _("Unknown")
    return last
