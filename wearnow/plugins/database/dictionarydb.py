# WearNow - a GTK+/GNOME based  program
#
# Copyright (C) 2012         Douglas S. Blank <doug.blank@gmail.com>
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

""" Implements a Db interface as a Dictionary """

#------------------------------------------------------------------------
#
# Python Modules
#
#------------------------------------------------------------------------
import pickle
import re
import os
import logging

#------------------------------------------------------------------------
#
# WearNow Modules
#
#------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext
from wearnow.tex.db.base import DbReadBase, DbWriteBase
from wearnow.tex.db.txn import DbTxn
from wearnow.tex.db.dbconst import KEY_TO_NAME_MAP, KEY_TO_CLASS_MAP
from wearnow.tex.db.undoredo import DbUndo
from wearnow.tex.db.dbconst import *
from wearnow.tex.utils.callback import Callback
from wearnow.tex.updatecallback import UpdateCallback
from wearnow.tex.db import (TEXTILE_KEY,
                            ENSEMBLE_KEY,
                            MEDIA_KEY,
                            NOTE_KEY,
                            TAG_KEY)

from wearnow.tex.utils.id import create_id
from wearnow.tex.lib.researcher import Researcher
from wearnow.tex.lib.mediaobj import MediaObject
from wearnow.tex.lib.textile import Textile
from wearnow.tex.lib.ensemble import Ensemble
from wearnow.tex.lib.note import Note
from wearnow.tex.lib.tag import Tag

_LOG = logging.getLogger(DBLOGNAME)

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    ## After http://stackoverflow.com/questions/1158076/implement-touch-using-python
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd else fname,
                 dir_fd=None if os.supports_fd else dir_fd, **kwargs)

class Environment(object):
    """
    Implements the Environment API.
    """
    def __init__(self, db):
        self.db = db

    def txn_begin(self):
        return DictionaryTxn("DictionaryDb Transaction", self.db)

class Table(object):
    """
    Implements Table interface.
    """
    def __init__(self, funcs):
        self.funcs = funcs

    def cursor(self):
        """
        Returns a Cursor for this Table.
        """
        return self.funcs["cursor_func"]()

    def put(self, key, data, txn=None):
        self.funcs["add_func"](data, txn)

class Map(dict):
    """
    Implements the map API for textile_map, etc.
    
    Takes a Table() as argument.
    """
    def __init__(self, tbl, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = tbl

class MetaCursor(object):
    def __init__(self):
        pass
    def __enter__(self):
        return self
    def __iter__(self):
        return self.__next__()
    def __next__(self):
        yield None
    def __exit__(self, *args, **kwargs):
        pass
    def iter(self):
        yield None
    def first(self):
        self._iter = self.__iter__()
        return self.next()
    def next(self):
        try:
            return next(self._iter)
        except:
            return None
    def close(self):
        pass

class Cursor(object):
    def __init__(self, map):
        self.map = map
        self._iter = self.__iter__()
    def __enter__(self):
        return self
    def __iter__(self):
        for item in self.map.keys():
            yield (bytes(item, "utf-8"), self.map[item])
    def __next__(self):
        try:
            return self._iter.__next__()
        except StopIteration:
            return None
    def __exit__(self, *args, **kwargs):
        pass
    def iter(self):
        for item in self.map.keys():
            yield (bytes(item, "utf-8"), self.map[item])
    def first(self):
        self._iter = self.__iter__()
        try:
            return next(self._iter)
        except:
            return
    def next(self):
        try:
            return next(self._iter)
        except:
            return
    def close(self):
        pass

class Bookmarks(object):
    def __init__(self):
        self.handles = []
    def get(self):
        return self.handles
    def append(self, handle):
        self.handles.append(handle)

class DictionaryTxn(DbTxn):
    def __init__(self, message, db, batch=False):
        DbTxn.__init__(self, message, db, batch)

    def get(self, key, default=None, txn=None, **kwargs):
        """
        Returns the data object associated with key
        """
        if txn and key in txn:
            return txn[key]
        else:
            return None

    def put(self, handle, new_data, txn):
        """
        """
        txn[handle] = new_data

class DictionaryDb(DbWriteBase, DbReadBase, UpdateCallback, Callback):
    """
    A WearNow Database Backend. This replicates the wearnowdb functions.
    """
    __signals__ = dict((obj+'-'+op, signal)
                       for obj in
                       ['textile', 'ensemble', 'media', 'note', 'tag']
                       for op, signal in zip(
                               ['add',   'update', 'delete', 'rebuild'],
                               [(list,), (list,),  (list,),   None]
                       )
                   )
    
    # 2. Signals for long operations
    __signals__.update(('long-op-'+op, signal) for op, signal in zip(
        ['start',  'heartbeat', 'end'],
        [(object,), None,       None]
        ))

    # 3. Special signal for change in home textile
    __signals__['home-textile-changed'] = None


    __callback_map = {}

    def __init__(self, directory=None):
        DbReadBase.__init__(self)
        DbWriteBase.__init__(self)
        Callback.__init__(self)
        self._tables['Textile'].update(
            {
                "handle_func": self.get_textile_from_handle, 
                "wearnow_id_func": self.get_textile_from_wearnow_id,
                "class_func": Textile,
                "cursor_func": self.get_textile_cursor,
                "handles_func": self.get_textile_handles,
                "add_func": self.add_textile,
                "commit_func": self.commit_textile,
                "iter_func": self.iter_textiles,
            })
        self._tables['Ensemble'].update(
            {
                "handle_func": self.get_ensemble_from_handle, 
                "wearnow_id_func": self.get_ensemble_from_wearnow_id,
                "class_func": Ensemble,
                "cursor_func": self.get_ensemble_cursor,
                "handles_func": self.get_ensemble_handles,
                "add_func": self.add_ensemble,
                "commit_func": self.commit_ensemble,
                "iter_func": self.iter_ensembles,
            })
        self._tables['Media'].update(
            {
                "handle_func": self.get_object_from_handle, 
                "wearnow_id_func": self.get_object_from_wearnow_id,
                "class_func": MediaObject,
                "cursor_func": self.get_media_cursor,
                "handles_func": self.get_media_object_handles,
                "add_func": self.add_object,
                "commit_func": self.commit_media_object,
                "iter_func": self.iter_media_objects,
            })
        self._tables['MediaObject'] = self._tables['Media']
        self._tables['Note'].update(
            {
                "handle_func": self.get_note_from_handle, 
                "wearnow_id_func": self.get_note_from_wearnow_id,
                "class_func": Note,
                "cursor_func": self.get_note_cursor,
                "handles_func": self.get_note_handles,
                "add_func": self.add_note,
                "commit_func": self.commit_note,
                "iter_func": self.iter_notes,
            })
        self._tables['Tag'].update(
            {
                "handle_func": self.get_tag_from_handle, 
                "wearnow_id_func": None,
                "class_func": Tag,
                "cursor_func": self.get_tag_cursor,
                "handles_func": self.get_tag_handles,
                "add_func": self.add_tag,
                "commit_func": self.commit_tag,
                "iter_func": self.iter_tags,
            })
        # skip GEDCOM cross-ref check for now:
        self.set_feature("skip-check-xref", True)
        self.set_feature("skip-import-additions", True)
        self.readonly = False
        self.db_is_open = True
        self.name_formats = []
        self.bookmarks = Bookmarks()
        self.ensemble_bookmarks = Bookmarks()
        self.media_bookmarks = Bookmarks()
        self.note_bookmarks = Bookmarks()
        self.set_textile_id_prefix('I%04d')
        self.set_object_id_prefix('O%04d')
        self.set_ensemble_id_prefix('F%04d')
        self.set_note_id_prefix('N%04d')
        # ----------------------------------
        self.id_trans  = DictionaryTxn("ID Transaction", self)
        self.fid_trans = DictionaryTxn("FID Transaction", self)
        self.pid_trans = DictionaryTxn("PID Transaction", self)
        self.oid_trans = DictionaryTxn("OID Transaction", self)
        self.nid_trans = DictionaryTxn("NID Transaction", self)
        self.pmap_index = 0
        self.fmap_index = 0
        self.omap_index = 0
        self.nmap_index = 0
        self.env = Environment(self)
        self.textile_map = Map(Table(self._tables["Textile"]))
        self.textile_id_map = {}
        self.ensemble_map = Map(Table(self._tables["Ensemble"]))
        self.ensemble_id_map = {}
        self.note_map = Map(Table(self._tables["Note"]))
        self.note_id_map = {}
        self.media_map  = Map(Table(self._tables["Media"]))
        self.media_id_map = {}
        self.tag_map  = Map(Table(self._tables["Tag"]))
        self.metadata   = Map(Table({"cursor_func": lambda: MetaCursor()}))
        self.undo_callback = None
        self.redo_callback = None
        self.undo_history_callback = None
        self.modified   = 0
        self.txn = DictionaryTxn("DbDictionary Transaction", self)
        self.transaction = None
        self.undodb = DbUndo(self)
        self.abort_possible = False
        self._bm_changes = 0
        self._directory = directory
        self.full_name = None
        self.path = None
        self.brief_name = None
        self.owner = Researcher()
        if directory:
            self.load(directory)

    def version_supported(self):
        """Return True when the file has a supported version."""
        return True

    def get_table_names(self):
        """Return a list of valid table names."""
        return list(self._tables.keys())

    def get_table_metadata(self, table_name):
        """Return the metadata for a valid table name."""
        if table_name in self._tables:
            return self._tables[table_name]
        return None

    def transaction_commit(self, txn):
        ## FIXME
        pass

    def get_undodb(self):
        ## FIXME
        return None

    def transaction_abort(self, txn):
        ## FIXME
        pass

    @staticmethod
    def _validated_id_prefix(val, default):
        if isinstance(val, str) and val:
            try:
                str_ = val % 1
            except TypeError:           # missing conversion specifier
                prefix_var = val + "%d"
            except ValueError:          # incomplete format
                prefix_var = default+"%04d"
            else:
                prefix_var = val        # OK as given
        else:
            prefix_var = default+"%04d" # not a string or empty string
        return prefix_var

    @staticmethod
    def __id2user_format(id_pattern):
        """
        Return a method that accepts a WearNow ID and adjusts it to the users
        format.
        """
        pattern_match = re.match(r"(.*)%[0 ](\d+)[diu]$", id_pattern)
        if pattern_match:
            str_prefix = pattern_match.group(1)
            nr_width = int(pattern_match.group(2))
            def closure_func(wearnow_id):
                if wearnow_id and wearnow_id.startswith(str_prefix):
                    id_number = wearnow_id[len(str_prefix):]
                    if id_number.isdigit():
                        id_value = int(id_number, 10)
                        #if len(str(id_value)) > nr_width:
                        #    # The ID to be imported is too large to fit in the
                        #    # users format. For now just create a new ID,
                        #    # because that is also what happens with IDs that
                        #    # are identical to IDs already in the database. If
                        #    # the problem of colliding import and already
                        #    # present IDs is solved the code here also needs
                        #    # some solution.
                        #    wearnow_id = id_pattern % 1
                        #else:
                        wearnow_id = id_pattern % id_value
                return wearnow_id
        else:
            def closure_func(wearnow_id):
                return wearnow_id
        return closure_func

    def set_textile_id_prefix(self, val):
        """
        Set the naming template for GRAMPS textile ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as I%d or I%04d.
        """
        self.textile_prefix = self._validated_id_prefix(val, "I")
        self.id2user_format = self.__id2user_format(self.textile_prefix)

    def set_object_id_prefix(self, val):
        """
        Set the naming template for GRAMPS MediaObject ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as O%d or O%04d.
        """
        self.mediaobject_prefix = self._validated_id_prefix(val, "O")
        self.oid2user_format = self.__id2user_format(self.mediaobject_prefix)

    def set_ensemble_id_prefix(self, val):
        """
        Set the naming template for GRAMPS ensemble ID values. The string is
        expected to be in the form of a simple text string, or in a format
        that contains a C/Python style format string using %d, such as F%d
        or F%04d.
        """
        self.ensemble_prefix = self._validated_id_prefix(val, "F")
        self.fid2user_format = self.__id2user_format(self.ensemble_prefix)

    def set_note_id_prefix(self, val):
        """
        Set the naming template for GRAMPS Note ID values. 
        
        The string is expected to be in the form of a simple text string, or 
        in a format that contains a C/Python style format string using %d, 
        such as N%d or N%04d.
        """
        self.note_prefix = self._validated_id_prefix(val, "N")
        self.nid2user_format = self.__id2user_format(self.note_prefix)

    def __find_next_wearnow_id(self, prefix, map_index, trans):
        """
        Helper function for find_next_<object>_wearnow_id methods
        """
        index = prefix % map_index
        while trans.get(str(index)) is not None:
            map_index += 1
            index = prefix % map_index
        map_index += 1
        return (map_index, index)
        
    def find_next_textile_wearnow_id(self):
        """
        Return the next available GRAMPS' ID for a textile object based off the 
        textile ID prefix.
        """
        if self.pmap_index == 0: 
            #determine a good start value
            self.pmap_index = len(self.textile_id_map.keys())
        self.pmap_index, gid = self.__find_next_wearnow_id(self.textile_prefix,
                                          self.pmap_index, self.textile_id_map)
        return gid

    def find_next_object_wearnow_id(self):
        """
        Return the next available GRAMPS' ID for a MediaObject object based
        off the media object ID prefix.
        """
        if self.omap_index == 0: 
            #determine a good start value
            self.omap_index = len(self.media_id_map.keys())
        self.omap_index, gid = self.__find_next_wearnow_id(self.mediaobject_prefix,
                                          self.omap_index, self.media_id_map)
        return gid

    def find_next_ensemble_wearnow_id(self):
        """
        Return the next available GRAMPS' ID for a ensemble object based off the 
        ensemble ID prefix.
        """
        if self.fmap_index == 0: 
            #determine a good start value
            self.fmap_index = len(self.ensemble_id_map.keys())
        self.fmap_index, gid = self.__find_next_wearnow_id(self.ensemble_prefix,
                                          self.fmap_index, self.ensemble_id_map)
        return gid

    def find_next_note_wearnow_id(self):
        """
        Return the next available GRAMPS' ID for a Note object based off the 
        note ID prefix.
        """
        if self.nmap_index == 0: 
            #determine a good start value
            self.nmap_index = len(self.note_id_map.keys())
        self.nmap_index, gid = self.__find_next_wearnow_id(self.note_prefix,
                                          self.nmap_index, self.note_id_map)
        return gid

    def get_mediapath(self):
        return None

    def get_textile_handles(self, sort_handles=False):
        ## Fixme: implement sort
        return self.textile_map.keys()

    def get_ensemble_handles(self, sort_handles=False):
        ## Fixme: implement sort
        return self.ensemble_map.keys()

    def get_media_object_handles(self, sort_handles=False):
        ## Fixme: implement sort
        return self.media_map.keys()

    def get_note_handles(self, sort_handles=False):
        ## Fixme: implement sort
        return self.note_map.keys()

    def get_tag_handles(self, sort_handles=False):
        # FIXME: implement sort
        return self.tag_map.keys()

    def get_ensemble_from_handle(self, handle): 
        if isinstance(handle, bytes):
            handle = str(handle, "utf-8")
        ensemble = None
        if handle in self.ensemble_map:
            ensemble = Ensemble.create(self.ensemble_map[handle])
        return ensemble

    def get_textile_from_handle(self, handle):
        if isinstance(handle, bytes):
            handle = str(handle, "utf-8")
        textile = None
        if handle in self.textile_map:
            textile = Textile.create(self.textile_map[handle])
        return textile

    def get_note_from_handle(self, handle):
        if isinstance(handle, bytes):
            handle = str(handle, "utf-8")
        note = None
        if handle in self.note_map:
            note = Note.create(self.note_map[handle])
        return note

    def get_object_from_handle(self, handle):
        if isinstance(handle, bytes):
            handle = str(handle, "utf-8")
        media = None
        if handle in self.media_map:
            media = MediaObject.create(self.media_map[handle])
        return media

    def get_tag_from_handle(self, handle):
        if isinstance(handle, bytes):
            handle = str(handle, "utf-8")
        tag = None
        if handle in self.tag_map:
            tag = Tag.create(self.tag_map[handle])
        return tag

    def get_default_textile(self):
        handle = self.get_default_handle()
        if handle:
            return self.get_textile_from_handle(handle)
        else:
            return None

    def iter_textiles(self):
        return (Textile.create(textile) for textile in self.textile_map.values())

    def iter_textile_handles(self):
        return (handle for handle in self.textile_map.keys())

    def iter_ensembles(self):
        return (Ensemble.create(ensemble) for ensemble in self.ensemble_map.values())

    def iter_ensemble_handles(self):
        return (handle for handle in self.ensemble_map.keys())

    def get_tag_from_name(self, name):
        ## Slow, but typically not too many tags:
        for data in self.tag_map.values():
            tag = Tag.create(data)
            if tag.name == name:
                return tag
        return None

    def get_textile_from_wearnow_id(self, wearnow_id):
        if wearnow_id in self.textile_id_map:
            return Textile.create(self.textile_id_map[wearnow_id])
        return None

    def get_ensemble_from_wearnow_id(self, wearnow_id):
        if wearnow_id in self.ensemble_id_map:
            return Ensemble.create(self.ensemble_id_map[wearnow_id])
        return None

    def get_object_from_wearnow_id(self, wearnow_id):
        if wearnow_id in self.media_id_map:
            return MediaObject.create(self.media_id_map[wearnow_id])
        return None

    def get_note_from_wearnow_id(self, wearnow_id):
        if wearnow_id in self.note_id_map:
            return Note.create(self.note_id_map[wearnow_id])
        return None

    def get_number_of_textiles(self):
        return len(self.textile_map)

    def get_number_of_tags(self):
        return len(self.tag_map)

    def get_number_of_ensembles(self):
        return len(self.ensemble_map)

    def get_number_of_notes(self):
        return len(self.note_map)

    def get_number_of_media_objects(self):
        return len(self.media_map)

    def get_textile_cursor(self):
        return Cursor(self.textile_map)

    def get_ensemble_cursor(self):
        return Cursor(self.ensemble_map)

    def get_note_cursor(self):
        return Cursor(self.note_map)

    def get_tag_cursor(self):
        return Cursor(self.tag_map)

    def get_media_cursor(self):
        return Cursor(self.media_map)

    def has_wearnow_id(self, obj_key, wearnow_id):
        key2table = {
            TEXTILE_KEY:     self.textile_id_map, 
            ENSEMBLE_KEY:     self.ensemble_id_map,
            MEDIA_KEY:      self.media_id_map,
            NOTE_KEY:       self.note_id_map,
            }
        return wearnow_id in key2table[obj_key]

    def has_textile_handle(self, handle):
        return handle in self.textile_map

    def has_ensemble_handle(self, handle):
        return handle in self.ensemble_map

    def has_note_handle(self, handle):
        return handle in self.note_map

    def has_tag_handle(self, handle):
        return handle in self.tag_map

    def has_object_handle(self, handle):
        return handle in self.media_map

    def set_default_textile_handle(self, handle):
        ## FIXME
        pass

    def set_mediapath(self, mediapath):
        ## FIXME
        pass

    def get_raw_textile_data(self, handle):
        if handle in self.textile_map:
            return self.textile_map[handle]
        return None

    def get_raw_ensemble_data(self, handle):
        if handle in self.ensemble_map:
            return self.ensemble_map[handle]
        return None

    def get_raw_note_data(self, handle):
        if handle in self.note_map:
            return self.note_map[handle]
        return None

    def get_raw_object_data(self, handle):
        if handle in self.media_map:
            return self.media_map[handle]
        return None

    def get_raw_tag_data(self, handle):
        if handle in self.tag_map:
            return self.tag_map[handle]
        return None

    def add_textile(self, textile, trans, set_gid=True):
        if not textile.handle:
            textile.handle = create_id()
        if not textile.wearnow_id and set_gid:
            textile.wearnow_id = self.find_next_textile_wearnow_id()
        self.commit_textile(textile, trans)
        return textile.handle

    def add_ensemble(self, ensemble, trans, set_gid=True):
        if not ensemble.handle:
            ensemble.handle = create_id()
        if not ensemble.wearnow_id and set_gid:
            ensemble.wearnow_id = self.find_next_ensemble_wearnow_id()
        self.commit_ensemble(ensemble, trans)
        return ensemble.handle

    def add_note(self, note, trans, set_gid=True):
        if not note.handle:
            note.handle = create_id()
        if not note.wearnow_id and set_gid:
            note.wearnow_id = self.find_next_note_wearnow_id()
        self.commit_note(note, trans)
        return note.handle

    def add_tag(self, tag, trans):
        if not tag.handle:
            tag.handle = create_id()
        self.commit_tag(tag, trans)
        return tag.handle

    def add_object(self, obj, transaction, set_gid=True):
        """
        Add a MediaObject to the database, assigning internal IDs if they have
        not already been defined.
        
        If not set_gid, then wearnow_id is not set.
        """
        if not obj.handle:
            obj.handle = create_id()
        if not obj.wearnow_id and set_gid:
            obj.wearnow_id = self.find_next_object_wearnow_id()
        self.commit_media_object(obj, transaction)
        return obj.handle

    def commit_textile(self, textile, trans, change_time=None):
        emit = None
        oldid = False
        if textile.handle in self.textile_map:
            oldid = self.textile_map[textile.handle][1]
            if not trans.batch:
                emit = "textile-update"
        else:
            if not trans.batch:
                emit = "textile-add"
        self.textile_map[textile.handle] = textile.serialize()
        if not (oldid is False):
            del self.textile_id_map[oldid]
        self.textile_id_map[textile.wearnow_id] = self.textile_map[textile.handle]
        # Emit after added:
        if emit:
            self.emit(emit, ([textile.handle],))

    def commit_ensemble(self, ensemble, trans, change_time=None):
        emit = None
        oldid = False
        if ensemble.handle in self.ensemble_map:
            oldid = self.ensemble_map[ensemble.handle][1]
            if not trans.batch:
                emit = "ensemble-update"
        else:
            if not trans.batch:
                    emit = "ensemble-add"
        self.ensemble_map[ensemble.handle] = ensemble.serialize()
        if not (oldid is False):
            del self.ensemble_id_map[oldid]
        self.ensemble_id_map[ensemble.wearnow_id] = self.ensemble_map[ensemble.handle]
        # Emit after added:
        if emit:
            self.emit(emit, ([ensemble.handle],))

    def commit_note(self, note, trans, change_time=None):
        emit = None
        oldid = False
        if note.handle in self.note_map:
            oldid = self.note_map[note.handle][1]
            if not trans.batch:
                emit = "note-update"
        else:
            if not trans.batch:
                emit = "note-add"
        self.note_map[note.handle] = note.serialize()
        if not (oldid is False):
            del self.note_id_map[oldid]
        self.note_id_map[note.wearnow_id] = self.note_map[note.handle]
        # Emit after added:
        if emit:
            self.emit(emit, ([note.handle],))

    def commit_tag(self, tag, trans, change_time=None):
        emit = None
        if not trans.batch:
            if tag.handle in self.tag_map:
                emit = "tag-update"
            else:
                emit = "tag-add"
        self.tag_map[tag.handle] = tag.serialize()
        # Emit after added:
        if emit:
            self.emit(emit, ([tag.handle],))

    def commit_media_object(self, media, trans, change_time=None):
        emit = None
        oldid = False
        if media.handle in self.media_map:
            oldid = self.media_map[media.handle][1]
            if not trans.batch:
                emit = "media-update"
        else:
            if not trans.batch:
                emit = "media-add"
        self.media_map[media.handle] = media.serialize()
        if not (oldid is False):
            del self.media_id_map[oldid]
        self.media_id_map[media.wearnow_id] = self.media_map[media.handle]
        # Emit after added:
        if emit:
            self.emit(emit, ([media.handle],))

    def get_wearnow_ids(self, obj_key):
        key2table = {
            TEXTILE_KEY:    self.textile_id_map,
            ENSEMBLE_KEY:   self.ensemble_id_map,
            MEDIA_KEY:      self.media_id_map,
            NOTE_KEY:       self.note_id_map,
            }
        return list(key2table[obj_key].keys())

    def transaction_begin(self, transaction):
        ## FIXME
        return 

    def set_owner(self, owner):
        self.owner.set_from(owner)

    def get_owner(self):
        return self.owner

    def request_rebuild(self):
        self.emit('textile-rebuild')
        self.emit('ensemble-rebuild')
        self.emit('media-rebuild')
        self.emit('note-rebuild')
        self.emit('tag-rebuild')

    def copy_from_db(self, db):
        """
        A (possibily) implementation-specific method to get data from
        db into this database.
        """
        for key in db._tables.keys():
            cursor = db._tables[key]["cursor_func"]
            class_ = db._tables[key]["class_func"]
            for (handle, data) in cursor():
                map = getattr(self, "%s_map" % key.lower())
                map[handle] = class_.create(data)

    def get_transaction_class(self):
        """
        Get the transaction class associated with this database backend.
        """
        return DictionaryTxn

    def get_from_name_and_handle(self, table_name, handle):
        """
        Returns a gen.lib object (or None) given table_name and
        handle.

        Examples:

        >>> self.get_from_name_and_handle("Textile", "a7ad62365bc652387008")
        >>> self.get_from_name_and_handle("Media", "c3434653675bcd736f23")
        """
        if table_name in self._tables:
            return self._tables[table_name]["handle_func"](handle)
        return None

    def get_from_name_and_wearnow_id(self, table_name, wearnow_id):
        """
        Returns a gen.lib object (or None) given table_name and
        WearNow ID.

        Examples:

        >>> self.get_from_name_and_wearnow_id("Textile", "I00002")
        >>> self.get_from_name_and_wearnow_id("Ensemble", "F056")
        >>> self.get_from_name_and_wearnow_id("Media", "M00012")
        """
        if table_name in self._tables:
            return self._tables[table_name]["wearnow_id_func"](wearnow_id)
        return None

    def remove_textile(self, handle, transaction):
        """
        Remove the textile specified by the database handle from the database, 
        preserving the change in the passed transaction. 
        """

        if self.readonly or not handle:
            return
        if handle in self.textile_map:
            textile = Textile.create(self.textile_map[handle])
            del self.textile_map[handle]
            del self.textile_id_map[textile.wearnow_id]
            self.emit("textile-delete", ([handle],))

    def remove_object(self, handle, transaction):
        """
        Remove the MediaObject specified by the database handle from the
        database, preserving the change in the passed transaction. 
        """
        self.__do_remove(handle, transaction, self.media_map, 
                         self.media_id_map, MEDIA_KEY)

    def remove_ensemble(self, handle, transaction):
        """
        Remove the Ensemble specified by the database handle from the
        database, preserving the change in the passed transaction. 
        """
        self.__do_remove(handle, transaction, self.ensemble_map, 
                         self.ensemble_id_map, ENSEMBLE_KEY)

    def remove_note(self, handle, transaction):
        """
        Remove the Note specified by the database handle from the
        database, preserving the change in the passed transaction. 
        """
        self.__do_remove(handle, transaction, self.note_map, 
                         self.note_id_map, NOTE_KEY)

    def remove_tag(self, handle, transaction):
        """
        Remove the Tag specified by the database handle from the
        database, preserving the change in the passed transaction. 
        """
        self.__do_remove(handle, transaction, self.tag_map, 
                         None, TAG_KEY)

    def is_empty(self):
        """
        Return true if there are no [primary] records in the database
        """
        for table in self._tables:
            if len(self._tables[table]["handles_func"]()) > 0:
                return False
        return True

    def __do_remove(self, handle, transaction, data_map, data_id_map, key):
        if self.readonly or not handle:
            return
        if handle in data_map:
            obj = self._tables[KEY_TO_CLASS_MAP[key]]["class_func"].create(data_map[handle])
            del data_map[handle]
            if data_id_map:
                del data_id_map[obj.wearnow_id]
            self.emit(KEY_TO_NAME_MAP[key] + "-delete", ([handle],))

    def delete_primary_from_reference_map(self, handle, transaction, txn=None):
        """
        Remove all references to the primary object from the reference_map.
        handle should be utf-8
        """
        primary_cur = self.get_reference_map_primary_cursor()

        try:
            ret = primary_cur.set(handle)
        except:
            ret = None
        
        remove_list = set()
        while (ret is not None):
            (key, data) = ret
            
            # data values are of the form:
            #   ((primary_object_class_name, primary_object_handle),
            #    (referenced_object_class_name, referenced_object_handle))
            
            # so we need the second tuple give us a reference that we can
            # combine with the primary_handle to get the main key.
            main_key = (handle.decode('utf-8'), pickle.loads(data)[1][1])
            
            # The trick is not to remove while inside the cursor,
            # but collect them all and remove after the cursor is closed
            remove_list.add(main_key)

            ret = primary_cur.next_dup()

        primary_cur.close()

        # Now that the cursor is closed, we can remove things
        for main_key in remove_list:
            self.__remove_reference(main_key, transaction, txn)

    def __remove_reference(self, key, transaction, txn):
        """
        Remove the reference specified by the key, preserving the change in 
        the passed transaction.
        """
        if isinstance(key, tuple):
            #create a byte string key, first validity check in python 3!
            for val in key:
                if isinstance(val, bytes):
                    raise DbError(_('An attempt is made to save a reference key '
                        'which is partly bytecode, this is not allowed.\n'
                        'Key is %s') % str(key))
            key = str(key)
        if isinstance(key, str):
            key = key.encode('utf-8')
        if not self.readonly:
            if not transaction.batch:
                old_data = self.reference_map.get(key, txn=txn)
                transaction.add(REFERENCE_KEY, TXNDEL, key, old_data, None)
                #transaction.reference_del.append(str(key))
            self.reference_map.delete(key, txn=txn)

    ## Missing:

    def backup(self):
        ## FIXME
        pass

    def close(self):
        if self._directory:
            from wearnow.plugins.export.exportxml import XmlWriter
            from wearnow.gui.user import User 
            writer = XmlWriter(self, User(), strip_photos=0, compress=1)
            filename = os.path.join(self._directory, "data.wearnow")
            writer.write(filename)
            filename = os.path.join(self._directory, "meta_data.db")
            touch(filename)

    def find_backlink_handles(self, handle, include_classes=None):
        ## FIXME
        return []

    def find_initial_textile(self):
        items = self.textile_map.keys()
        if len(items) > 0:
            return self.get_textile_from_handle(list(items)[0])
        return None

    def get_bookmarks(self):
        return self.bookmarks

    def get_cursor(self, table, txn=None, update=False, commit=False):
        ## FIXME
        ## called from a complete find_back_ref
        pass

    # cursors for lookups in the reference_map for back reference
    # lookups. The reference_map has three indexes:
    # the main index: a tuple of (primary_handle, referenced_handle)
    # the primary_handle index: the primary_handle
    # the referenced_handle index: the referenced_handle
    # the main index is unique, the others allow duplicate entries.

    def get_default_handle(self):
        items = self.textile_map.keys()
        if len(items) > 0:
            return list(items)[0]
        return None

    def get_ensemble_attribute_types(self):
        ## FIXME
        return []

    def get_ensemble_bookmarks(self):
        return self.ensemble_bookmarks

    def get_media_attribute_types(self):
        ## FIXME
        return []

    def get_media_bookmarks(self):
        return self.media_bookmarks

    def get_note_bookmarks(self):
        return self.note_bookmarks

    def get_note_types(self):
        ## FIXME
        return []

    def get_textile_attribute_types(self):
        ## FIXME
        return []

    def get_save_path(self):
        return self._directory

    def has_changed(self):
        ## FIXME
        return True

    def is_open(self):
        return self._directory is not None

    def iter_media_objects(self):
        return (MediaObject.create(key) for key in self.media_map.values())

    def iter_note_handles(self):
        return (key for key in self.note_map.keys())

    def iter_notes(self):
        return (Note.create(key) for key in self.note_map.values())

    def iter_tag_handles(self):
        return (key for key in self.tag_map.keys())

    def iter_tags(self):
        return (Tag.create(key) for key in self.tag_map.values())

    def load(self, directory, callback=None, mode=None, 
             force_schema_upgrade=False, 
             force_bsddb_upgrade=False, 
             force_bsddb_downgrade=False, 
             force_python_upgrade=False):
        from wearnow.plugins.importer.importxml import importData
        from wearnow.gui.user import User 
        self._directory = directory
        self.full_name = os.path.abspath(self._directory)
        self.path = self.full_name
        self.brief_name = os.path.basename(self._directory)
        filename = os.path.join(directory, "data.wearnow")
        if os.path.isfile(filename):
            importData(self, filename, User())

    def redo(self, update_history=True):
        ## FIXME
        pass

    def restore(self):
        ## FIXME
        pass

    def set_prefixes(self, textile, media, ensemble, note):
        ## FIXME
        pass

    def set_save_path(self, directory):
        self._directory = directory
        self.full_name = os.path.abspath(self._directory)
        self.path = self.full_name
        self.brief_name = os.path.basename(self._directory)

    def undo(self, update_history=True):
        ## FIXME
        pass

    def write_version(self, directory):
        """Write files for a newly created DB."""
        versionpath = os.path.join(directory, str(DBBACKEND))
        _LOG.debug("Write database backend file to 'dictionarydb'")
        with open(versionpath, "w") as version_file:
            version_file.write("dictionarydb")

    def report_bm_change(self):
        """
        Add 1 to the number of bookmark changes during this session.
        """
        self._bm_changes += 1

    def db_has_bm_changes(self):
        """
        Return whethere there were bookmark changes during the session.
        """
        return self._bm_changes > 0

    def get_summary(self):
        """
        Returns dictionary of summary item.
        Should include, if possible:

        _("Number of textiles")
        _("Version")
        _("Schema version")
        """
        return {
            _("Number of textiles"): self.get_number_of_textiles(),
        }

    def get_dbname(self):
        """
        In DictionaryDb, the database is in a text file at the path
        """
        filepath = os.path.join(self._directory, "name.txt")
        try:
            name_file = open(filepath, "r")
            name = name_file.readline().strip()
            name_file.close()
        except (OSError, IOError) as msg:
            _LOG.error(str(msg))
            name = None
        return name

    def reindex_reference_map(self):
        ## FIXME
        pass

    def rebuild_secondary(self, update):
        ## FIXME
        pass

    def prepare_import(self):
        """
        Initialization before imports
        """
        pass

    def commit_import(self):
        """
        Post process after imports
        """
        pass

