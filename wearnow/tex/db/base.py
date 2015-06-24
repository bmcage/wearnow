#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2010       Nick Hall
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
Base class for the WearNow databases. All database interfaces should inherit
from this class.
"""

#-------------------------------------------------------------------------
#
# Python libraries
#
#-------------------------------------------------------------------------
from ..const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# WearNow libraries
#
#-------------------------------------------------------------------------
from .txn import DbTxn
from .exceptions import DbTransactionCancel

class DbReadBase(object):
    """
    WearNow database object. This object is a base class for all
    database interfaces.  All methods raise NotImplementedError
    and must be implemented in the derived class as required.
    """

    def __init__(self):
        """
        Create a new DbReadBase instance.

        A new DbReadBase class should never be directly created. Only classes
        derived from this class should be created.
        """
        self.basedb = self
        self.__feature = {} # {"feature": VALUE, ...}
        self._tables = {
            "Ensemble": {},
            "Media": {},
            "Note": {},
            "Textile": {},
            "Tag": {},
        }

    def get_feature(self, feature):
        """
        Databases can implement certain features or not. The default is
        None, unless otherwise explicitly stated.
        """
        return self.__feature.get(feature, None) # can also be explicitly None

    def set_feature(self, feature, value):
        """
        Databases can implement certain features.
        """
        self.__feature[feature] = value

    def all_handles(self, table):
        """
        Return all handles from the specified table as a list
        """
        raise NotImplementedError

    def close(self):
        """
        Close the specified database.
        """
        raise NotImplementedError

    def db_has_bm_changes(self):
        """
        Return whethere there were bookmark changes during the session.
        """
        raise NotImplementedError

    def find_backlink_handles(self, handle, include_classes=None):
        """
        Find all objects that hold a reference to the object handle.

        Returns an iterator over a list of (class_name, handle) tuples.

        :param handle: handle of the object to search for.
        :type handle: database handle
        :param include_classes: list of class names to include in the results.
            Default is None which includes all classes.
        :type include_classes: list of class names

        This default implementation does a sequential scan through all
        the primary object databases and is very slow. Backends can
        override this method to provide much faster implementations that
        make use of additional capabilities of the backend.

        Note that this is a generator function, it returns a iterator for
        use in loops. If you want a list of the results use::

            result_list = list(find_backlink_handles(handle))
        """
        raise NotImplementedError

    def find_initial_textile(self):
        """
        Returns first garment in the database
        """
        raise NotImplementedError

    def find_next_ensemble_wearnow_id(self):
        """
        Return the next available WearNow ID for a Ensemble object based off the
        Ensemble ID prefix.
        """
        raise NotImplementedError

    def find_next_note_wearnow_id(self):
        """
        Return the next available WearNow ID for a Note object based off the
        note ID prefix.
        """
        raise NotImplementedError

    def find_next_object_wearnow_id(self):
        """
        Return the next available WearNow ID for a MediaObject object based
        off the media object ID prefix.
        """
        raise NotImplementedError

    def find_next_textile_wearnow_id(self):
        """
        Return the next available WearNow ID for a Person object based off the
        textile ID prefix.
        """
        raise NotImplementedError

    def get_bookmarks(self):
        """
        Return the list of Person handles in the bookmarks.
        """
        raise NotImplementedError

    def get_default_handle(self):
        """
        Return the default Textile of the database.
        """
        raise NotImplementedError

    def get_default_textile(self):
        """
        Return the default Textile of the database.
        """
        raise NotImplementedError

    def get_event_bookmarks(self):
        """
        Return the list of Event handles in the bookmarks.
        """
        raise NotImplementedError

    def get_ensemble_bookmarks(self):
        """
        Return the list of ensemble handles in the bookmarks.
        """
        raise NotImplementedError

    def get_ensemble_cursor(self):
        """
        Return a reference to a cursor over ensemble objects
        """
        raise NotImplementedError

    def get_ensemble_from_wearnow_id(self, val):
        """
        Find a ensemble in the database from the passed WearNow ID.

        If no such ensemble exists, None is returned.
        Need to be overridden by the derived class.
        """
        raise NotImplementedError

    def get_ensemble_from_handle(self, handle):
        """
        Find a ensemble in the database from the passed WearNow ID.

        If no such ensemble exists, None is returned.
        """
        raise NotImplementedError

    def get_ensemble_handles(self):
        """
        Return a list of database handles, one handle for each ensemble in
        the database.
        """
        raise NotImplementedError


    def get_from_handle(self, handle, class_type, data_map):
        """
        Return unserialized data from database given handle and object class
        """
        raise NotImplementedError

    def get_wearnow_ids(self, obj_key):
        """
        Returns all the keys from a table given a table name
        """
        raise NotImplementedError

    def get_media_bookmarks(self):
        """
        Return the list of Media handles in the bookmarks.
        """
        raise NotImplementedError

    def get_media_cursor(self):
        """
        Return a reference to a cursor over Media objects
        """
        raise NotImplementedError

    def get_media_object_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each MediaObject in
        the database.

        If sort_handles is True, the list is sorted by title.
        """
        raise NotImplementedError

    def get_mediapath(self):
        """
        Return the default media path of the database.
        """
        raise NotImplementedError

    def get_note_bookmarks(self):
        """
        Return the list of Note handles in the bookmarks.
        """
        raise NotImplementedError

    def get_note_cursor(self):
        """
        Return a reference to a cursor over Note objects
        """
        raise NotImplementedError

    def get_note_from_wearnow_id(self, val):
        """
        Find a Note in the database from the passed WearNow ID.

        If no such Note exists, None is returned.
        Needs to be overridden by the derived classderri.
        """
        raise NotImplementedError

    def get_note_from_handle(self, handle):
        """
        Find a Note in the database from the passed WearNow ID.

        If no such Note exists, None is returned.
        """
        raise NotImplementedError

    def get_note_handles(self):
        """
        Return a list of database handles, one handle for each Note in the
        database.
        """
        raise NotImplementedError

    def get_note_types(self):
        """
        Return a list of all custom note types associated with Note instances
        in the database.
        """
        raise NotImplementedError

    def get_textile_types(self):
        """
        Return a list of all custom names types associated with Textile
        instances in the database.
        """
        raise NotImplementedError

    def get_number_of_ensembles(self):
        """
        Return the number of ensembles currently in the database.
        """
        raise NotImplementedError

    def get_number_of_media_objects(self):
        """
        Return the number of media objects currently in the database.
        """
        raise NotImplementedError

    def get_number_of_notes(self):
        """
        Return the number of notes currently in the database.
        """
        raise NotImplementedError

    def get_number_of_textiles(self):
        """
        Return the number of textile currently in the database.
        """
        raise NotImplementedError

    def get_number_of_tags(self):
        """
        Return the number of tags currently in the database.
        """
        raise NotImplementedError

    def get_object_from_wearnow_id(self, val):
        """
        Find a MediaObject in the database from the passed WearNow ID.

        If no such MediaObject exists, None is returned.
        Needs to be overridden by the derived class.
        """
        raise NotImplementedError

    def get_object_from_handle(self, handle):
        """
        Find an Object in the database from the passed WearNow ID.

        If no such Object exists, None is returned.
        """
        raise NotImplementedError

    def get_textile_attribute_types(self):
        """
        Return a list of all Attribute types associated with textile instances
        in the database.
        """
        raise NotImplementedError

    def get_textile_cursor(self):
        """
        Return a reference to a cursor over textile objects
        """
        raise NotImplementedError

    def get_textile_from_wearnow_id(self, val):
        """
        Find a textile in the database from the passed WearNow ID.

        If no such textile exists, None is returned.
        Needs to be overridden by the derived class.
        """
        raise NotImplementedError

    def get_textile_from_handle(self, handle):
        """
        Find a textile in the database from the passed WearNow ID.

        If no such textile exists, None is returned.
        """
        raise NotImplementedError

    def get_textile_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each textile in
        the database.

        If sort_handles is True, the list is sorted by name.
        """
        raise NotImplementedError

    def get_raw_ensemble_data(self, handle):
        """
        Return raw (serialized and pickled) Ensemble object from handle
        """
        raise NotImplementedError

    def get_raw_note_data(self, handle):
        """
        Return raw (serialized and pickled) Note object from handle
        """
        raise NotImplementedError

    def get_raw_object_data(self, handle):
        """
        Return raw (serialized and pickled) Ensemble object from handle
        """
        raise NotImplementedError

    def get_raw_textile_data(self, handle):
        """
        Return raw (serialized and pickled) Person object from handle
        """
        raise NotImplementedError

    def get_raw_tag_data(self, handle):
        """
        Return raw (serialized and pickled) Tag object from handle
        """
        raise NotImplementedError

    def get_reference_map_cursor(self):
        """
        Returns a reference to a cursor over the reference map
        """
        raise NotImplementedError

    def get_reference_map_primary_cursor(self):
        """
        Returns a reference to a cursor over the reference map primary map
        """
        raise NotImplementedError

    def get_reference_map_referenced_cursor(self):
        """
        Returns a reference to a cursor over the reference map referenced map
        """
        raise NotImplementedError

    def get_owner(self):
        """
        Return the owner instance, providing information about the owner
        of the database.
        """
        raise NotImplementedError

    def get_save_path(self):
        """
        Return the save path of the file, or "" if one does not exist.
        """
        raise NotImplementedError

    def get_tag_cursor(self):
        """
        Return a reference to a cursor over Tag objects
        """
        raise NotImplementedError

    def get_tag_from_handle(self, handle):
        """
        Find a Tag in the database from the passed handle.

        If no such Tag exists, None is returned.
        """
        raise NotImplementedError

    def get_tag_from_name(self, val):
        """
        Find a Tag in the database from the passed Tag name.

        If no such Tag exists, None is returned.
        Needs to be overridden by the derived class.
        """
        raise NotImplementedError

    def get_tag_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each Tag in
        the database.

        If sort_handles is True, the list is sorted by Tag name.
        """
        raise NotImplementedError

    def wearnow_upgrade(self):
        """
        Return True if database is upgraded
        """
        raise NotImplementedError

    def has_ensemble_handle(self, handle):
        """
        Return True if the handle exists in the current ensemble database.
        """
        raise NotImplementedError

    def has_wearnow_id(self, obj_key, wearnow_id):
        """
        Returns True if the key exists in table given a table name

        Not used in current codebase
        """
        raise NotImplementedError

    def has_note_handle(self, handle):
        """
        Return True if the handle exists in the current Note database.
        """
        raise NotImplementedError

    def has_object_handle(self, handle):
        """
        Return True if the handle exists in the current MediaObjectdatabase.
        """
        raise NotImplementedError

    def has_textile_handle(self, handle):
        """
        Return True if the handle exists in the current textile database.
        """
        raise NotImplementedError

    def has_tag_handle(self, handle):
        """
        Return True if the handle exists in the current Tag database.
        """
        raise NotImplementedError

    def is_open(self):
        """
        Return True if the database has been opened.
        """
        raise NotImplementedError

    def iter_ensembles(self):
        """
        Return an iterator over objects for ensembles in the database
        """
        raise NotImplementedError

    def iter_ensembles_handles(self):
        """
        Return an iterator over handles for ensembles in the database
        """
        raise NotImplementedError

    def iter_media_object_handles(self):
        """
        Return an iterator over handles for Media in the database
        """
        raise NotImplementedError

    def iter_media_objects(self):
        """
        Return an iterator over objects for MediaObjects in the database
        """
        raise NotImplementedError

    def iter_note_handles(self):
        """
        Return an iterator over handles for Notes in the database
        """
        raise NotImplementedError

    def iter_notes(self):
        """
        Return an iterator over objects for Notes in the database
        """
        raise NotImplementedError

    def iter_textiles(self):
        """
        Return an iterator over objects for textiles in the database
        """
        raise NotImplementedError

    def iter_textile_handles(self):
        """
        Return an iterator over handles for textile in the database
        """
        raise NotImplementedError

    def iter_tag_handles(self):
        """
        Return an iterator over handles for Tags in the database
        """
        raise NotImplementedError

    def iter_tags(self):
        """
        Return an iterator over objects for Tags in the database
        """
        raise NotImplementedError

    def load(self, name, callback, mode=None, force_schema_upgrade=False,
             force_bsddb_upgrade=False):
        """
        Open the specified database.
        """
        raise NotImplementedError

    def report_bm_change(self):
        """
        Add 1 to the number of bookmark changes during this session.
        """
        raise NotImplementedError

    def request_rebuild(self):
        """
        Notify clients that the data has changed significantly, and that all
        internal data dependent on the database should be rebuilt.
        Note that all rebuild signals on all objects are emitted at the same
        time. It is correct to assume that this is always the case.

        .. todo:: it might be better to replace these rebuild signals by one
                  single database-rebuild signal.
        """
        raise NotImplementedError

    def version_supported(self):
        """
        Return True when the file has a supported version.
        """
        raise NotImplementedError

    def set_ensemble_id_prefix(self, val):
        """
        Set the naming template for WearNow ensemble ID values. The string is
        expected to be in the form of a simple text string, or in a format
        that contains a C/Python style format string using %d, such as F%d
        or F%04d.
        """
        raise NotImplementedError

    def set_note_id_prefix(self, val):
        """
        Set the naming template for WearNow Note ID values.

        The string is expected to be in the form of a simple text string, or
        in a format that contains a C/Python style format string using %d,
        such as N%d or N%04d.
        """
        raise NotImplementedError

    def set_object_id_prefix(self, val):
        """
        Set the naming template for WearNow MediaObject ID values.

        The string is expected to be in the form of a simple text string, or
        in a format that contains a C/Python style format string using %d,
        such as O%d or O%04d.
        """
        raise NotImplementedError

    def set_textile_id_prefix(self, val):
        """
        Set the naming template for WearNow textile ID values.

        The string is expected to be in the form of a simple text string, or
        in a format that contains a C/Python style format string using %d,
        such as I%d or I%04d.
        """
        raise NotImplementedError

    def set_prefixes(self, textile, media, ensemble, note):
        """
        Set the prefixes for the wearnow ids for all wearnow objects
        """
        raise NotImplementedError

    def set_mediapath(self, path):
        """
        Set the default media path for database, path should be utf-8.
        """
        raise NotImplementedError

    def set_redo_callback(self, callback):
        """
        Define the callback function that is called whenever an redo operation
        is executed.

        The callback function receives a single argument that is a text string
        that defines the operation.
        """
        raise NotImplementedError

    def set_owner(self, owner):
        """
        Set the information about the owner of the database.
        """
        raise NotImplementedError

    def set_save_path(self, path):
        """
        Set the save path for the database.
        """
        raise NotImplementedError

    def set_undo_callback(self, callback):
        """
        Define the callback function that is called whenever an undo operation
        is executed.

        The callback function receives a single argument that is a text string
        that defines the operation.
        """
        raise NotImplementedError

    def get_dbid(self):
        """
        A unique ID for this database on this computer.
        """
        raise NotImplementedError

    def get_dbname(self):
        """
        A name for this database on this computer.
        """
        raise NotImplementedError

class DbWriteBase(DbReadBase):
    """
    WearNow database object. This object is a base class for all
    database interfaces.  All methods raise NotImplementedError
    and must be implemented in the derived class as required.
    """

    def __init__(self):
        """
        Create a new DbWriteBase instance.

        A new DbWriteBase class should never be directly created. Only classes
        derived from this class should be created.
        """
        DbReadBase.__init__(self)

    def add_ensemble(self, ensemble, transaction, set_gid=True):
        """
        Add a ensemble to the database, assigning internal IDs if they have
        not already been defined.

        If not set_gid, then wearnow_id is not set.
        """
        raise NotImplementedError

    def add_note(self, obj, transaction, set_gid=True):
        """
        Add a Note to the database, assigning internal IDs if they have
        not already been defined.

        If not set_gid, then wearnow_id is not set.
        """
        raise NotImplementedError

    def add_object(self, obj, transaction, set_gid=True):
        """
        Add a MediaObject to the database, assigning internal IDs if they have
        not already been defined.

        If not set_gid, then wearnow_id is not set.
        """
        raise NotImplementedError

    def add_textile(self, textile, transaction, set_gid=True):
        """
        Add a textile to the database, assigning internal IDs if they have
        not already been defined.

        If not set_gid, then wearnow_id is not set.
        """
        raise NotImplementedError

    def add_tag(self, tag, transaction):
        """
        Add a Tag to the database, assigning a handle if it has not already
        been defined.
        """
        raise NotImplementedError

    def commit_base(self, obj, data_map, key, transaction, change_time):
        """
        Commit the specified object to the database, storing the changes as
        part of the transaction.
        """
        raise NotImplementedError

    def commit_ensemble(self, ensemble, transaction, change_time=None):
        """
        Commit the specified ensemble to the database, storing the changes as
        part of the transaction.
        """
        raise NotImplementedError

    def commit_media_object(self, obj, transaction, change_time=None):
        """
        Commit the specified MediaObject to the database, storing the changes
        as part of the transaction.
        """
        raise NotImplementedError

    def commit_note(self, note, transaction, change_time=None):
        """
        Commit the specified Note to the database, storing the changes as part
        of the transaction.
        """
        raise NotImplementedError

    def commit_textile(self, textile, transaction, change_time=None):
        """
        Commit the specified textile to the database, storing the changes as
        part of the transaction.
        """
        raise NotImplementedError

    def commit_tag(self, tag, transaction, change_time=None):
        """
        Commit the specified Tag to the database, storing the changes as
        part of the transaction.
        """
        raise NotImplementedError

    def delete_primary_from_reference_map(self, handle, transaction):
        """
        Called each time an object is removed from the database.

        This can be used by subclasses to update any additional index tables
        that might need to be changed.
        """
        raise NotImplementedError

    def get_undodb(self):
        """
        Return the database that keeps track of Undo/Redo operations.
        """
        raise NotImplementedError

    def need_schema_upgrade(self):
        """
        Return True if database needs to be upgraded
        """
        raise NotImplementedError

    def rebuild_secondary(self, callback):
        """
        Rebuild secondary indices
        """
        raise NotImplementedError

    def reindex_reference_map(self, callback):
        """
        Reindex all primary records in the database.
        """
        raise NotImplementedError

    def remove_ensemble(self, handle, transaction):
        """
        Remove the ensemble specified by the database handle from the
        database, preserving the change in the passed transaction.

        This method must be overridden in the derived class.
        """
        raise NotImplementedError

    def remove_note(self, handle, transaction):
        """
        Remove the Note specified by the database handle from the
        database, preserving the change in the passed transaction.

        This method must be overridden in the derived class.
        """
        raise NotImplementedError

    def remove_object(self, handle, transaction):
        """
        Remove the MediaObjectPerson specified by the database handle from the
        database, preserving the change in the passed transaction.

        This method must be overridden in the derived class.
        """
        raise NotImplementedError

    def remove_textile(self, handle, transaction):
        """
        Remove the textile specified by the database handle from the database,
        preserving the change in the passed transaction.

        This method must be overridden in the derived class.
        """
        raise NotImplementedError

    def remove_tag(self, handle, transaction):
        """
        Remove the Tag specified by the database handle from the
        database, preserving the change in the passed transaction.

        This method must be overridden in the derived class.
        """
        raise NotImplementedError

    def set_auto_remove(self):
        """
        BSDDB change log settings using new method with renamed attributes
        """
        raise NotImplementedError

    def set_default_textile_handle(self, handle):
        """
        Set the default textile to the passed instance.
        """
        raise NotImplementedError

    def transaction_begin(self, transaction):
        """
        Prepare the database for the start of a new transaction.

        Two modes should be provided: transaction.batch=False for ordinary
        database operations that will be encapsulated in database transactions
        to make them ACID and that are added to WearNow transactions so that
        they can be undone. And transaction.batch=True for lengthy database
        operations, that benefit from a speedup by making them none ACID, and
        that can't be undone. The user is warned and is asked for permission
        before the start of such database operations.

        :param transaction: WearNow transaction ...
        :type transaction: :py:class:`.DbTxn`
        :returns: Returns the WearNow transaction.
        :rtype: :py:class:`.DbTxn`
        """
        raise NotImplementedError

    def transaction_commit(self, transaction):
        """
        Make the changes to the database final and add the content of the
        transaction to the undo database.
        """
        raise NotImplementedError

    def transaction_abort(self, transaction):
        """
        Revert the changes made to the database so far during the transaction.
        """
        raise NotImplementedError

    def update_reference_map(self, obj, transaction):
        """
        Called each time an object is writen to the database.

        This can be used by subclasses to update any additional index tables
        that might need to be changed.
        """
        raise NotImplementedError

    def write_version(self, name):
        """
        Write version number for a newly created DB.
        """
        raise NotImplementedError

    def delete_textile_from_database(self, textile, trans):
        """
        Deletes a textile from the database, cleaning up all associated references.
        """

        # clear out the default textile if the textile is the default textile
        if self.get_default_textile() == textile:
            self.set_default_textile_handle(None)

        # loop through the ensemble list
#        for ensemble_handle in textile.get_ensemble_handle_list():
#            if not ensemble_handle:
#                continue
        for ensemble_handle in self.get_ensemble_cursor():
            ensemble = self.get_ensemble_from_handle(ensemble_handle)

            changed = ensemble.remove_textile(textile.get_handle())
            if changed:
                self.commit_ensemble(ensemble, trans)

        handle = textile.get_handle()
        self.remove_textile(handle, trans)

    def get_total(self):
        """
        Get the total of primary objects.
        """
        textile_len = self.get_number_of_textiles()
        ensemble_len = self.get_number_of_ensembles()
        obj_len = self.get_number_of_media_objects()

        return textile_len + ensemble_len  + obj_len
