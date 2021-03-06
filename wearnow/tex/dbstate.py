#
# WearNow - a GTK+/GNOME based  program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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
Provide the database state class
"""
import sys
import os
import io

from .db.base import DbReadBase
#from .proxy.proxybase import ProxyDbBase
from .utils.callback import Callback
from .config import config

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".dbstate")

class DbState(Callback):
    """
    Provide a class to encapsulate the state of the database.
    """

    __signals__ = {
        'database-changed' : ((DbReadBase, ), ),
        'no-database' :  None, 
        }

    def __init__(self):
        """
        Initalize the state with an empty (and useless) DbBsddbRead. This is
        just a place holder until a real DB is assigned.
        """
        Callback.__init__(self)
        self.db      = self.make_database("dictionarydb")
        self.open    = False
        self.stack = []

    def change_database(self, database):
        """
        Closes the existing db, and opens a new one.
        Retained for backward compatibility.
        """
        if database:
            self.emit('no-database', ())
            self.db.close()
            self.change_database_noclose(database)

    def change_database_noclose(self, database):
        """
        Change the current database. and resets the configuration prefixes.
        """
        self.db = database
        self.db.set_prefixes(
            config.get('preferences.iprefix'),
            config.get('preferences.oprefix'),
            config.get('preferences.eprefix'),
            config.get('preferences.nprefix') )
        self.open = True
        self.signal_change()

    def signal_change(self):
        """
        Emits the database-changed signal with the new database
        """
        self.emit('database-changed', (self.db, ))

    def no_database(self):
        """
        Closes the database without a new database
        """
        self.emit('no-database', ())
        self.db.close()
        self.db = self.make_database("dictionarydb")
        self.db.db_is_open = False
        self.open = False
        self.emit('database-changed', (self.db, ))
        
    def get_database(self):
        """
        Get a reference to the current database.
        """
        return self.db

    def make_database(self, id):
        """
        Make a database, given a plugin id.
        """
        from .plug import BasePluginManager
        from .const import PLUGINS_DIR

        pmgr = BasePluginManager.get_instance()
        pdata = pmgr.get_plugin(id)
        
        if not pdata:
            # This might happen if using gramps from outside, and
            # we haven't loaded plugins yet
            pmgr.reg_plugins(PLUGINS_DIR, self, None)
            #pmgr.reg_plugins(USER_PLUGINS, self, None, load_on_reg=True)
            pdata = pmgr.get_plugin(id)

        if pdata:
            if pdata.reset_system:
                if self.modules_is_set():
                    self.reset_modules()
                else:
                    self.save_modules()
            mod = pmgr.load_plugin(pdata)
            database = getattr(mod, pdata.databaseclass)
            return database()
        else:
            raise ValueError("No Plugin to import database of type " + str(id) + \
                        '. Is there an import plugin?')

    def open_database(self, dbname, force_unlock=False, callback=None):
        """
        Open a database by name and return the database.
        """
        data = self.lookup_family_tree(dbname)
        database = None
        if data:
            dbpath, locked, locked_by, backend = data
            if (not locked) or (locked and force_unlock):
                database = self.make_database(backend)
                database.load(dbpath, callback=callback)
        return database

    def lookup_collection(self, dbname):
        """
        Find a Collection given its name, and return properties.
        """
        dbdir = os.path.expanduser(config.get('behavior.database-path'))
        for dpath in os.listdir(dbdir):
            dirpath = os.path.join(dbdir, dpath)
            path_name = os.path.join(dirpath, "name.txt")
            if os.path.isfile(path_name):
                file = io.open(path_name, 'r', encoding='utf8')
                name = file.readline().strip()
                file.close()
                if dbname == name:
                    locked = False
                    locked_by = None
                    backend = None
                    fname = os.path.join(dirpath, "database.txt")
                    if os.path.isfile(fname):
                        ifile = io.open(fname, 'r', encoding='utf8')
                        backend = ifile.read().strip()
                        ifile.close()
                    else:
                        backend = "dictionarydb"
                    try:
                        fname = os.path.join(dirpath, "lock")
                        ifile = io.open(fname, 'r', encoding='utf8')
                        locked_by = ifile.read().strip()
                        locked = True
                        ifile.close()
                    except (OSError, IOError):
                        pass
                    return (dirpath, locked, locked_by, backend)
        return None

    def import_from_filename(self, db, filename, user=None):
        """
        Import the filename into the db.
        """
        from .plug import BasePluginManager
        from .const import PLUGINS_DIR
        from gramps.cli.user import User
        pmgr = BasePluginManager.get_instance()
        if user is None:
            user = User()
        (name, ext) = os.path.splitext(os.path.basename(filename))
        format = ext[1:].lower()
        import_list = pmgr.get_reg_importers()
        if import_list == []:
            # This might happen if using gramps from outside, and
            # we haven't loaded plugins yet
            pmgr.reg_plugins(PLUGINS_DIR, self, None)
            #pmgr.reg_plugins(USER_PLUGINS, self, None, load_on_reg=True)
            import_list = pmgr.get_reg_importers()
        for pdata in import_list:
            if format == pdata.extension:
                mod = pmgr.load_plugin(pdata)
                if not mod:
                    for item in pmgr.get_fail_list():
                        name, error_tuple, pdata = item
                        # (filename, (exception-type, exception, traceback), pdata)
                        etype, exception, traceback = error_tuple
                        print("ERROR:", name, exception)
                    return False
                import_function = getattr(mod, pdata.import_function)
                results = import_function(db, filename, user)
                return True
        return False

    ## Work-around for databases that need sys refresh (django):
    def modules_is_set(self):
        LOG.info("modules_is_set?")
        if hasattr(self, "_modules"):
            return self._modules != None
        else:
            self._modules = None
            return False

    def reset_modules(self):
        LOG.info("reset_modules!")
        # First, clear out old modules:
        for key in list(sys.modules.keys()):
            del(sys.modules[key])
        # Next, restore previous:
        for key in self._modules:
            sys.modules[key] = self._modules[key]

    def save_modules(self):
        LOG.info("save_modules!")
        self._modules = sys.modules.copy()

