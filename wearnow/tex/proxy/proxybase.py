#
# WEARNOW - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007       Brian G. Matherly
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
Proxy class for the WEARNOW databases. Filter out all data marked private.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import types

#-------------------------------------------------------------------------
#
# WEARNOW libraries
#
#-------------------------------------------------------------------------
from ..db.base import DbReadBase, DbWriteBase

class ProxyCursor(object):
    """
    A cursor for moving through proxied data.
    """
    def __init__(self, get_raw, get_handles):
        self.get_raw = get_raw
        self.get_handles = get_handles

    def __enter__(self):
        """
        Context manager enter method
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
        
    def __iter__(self):
        for handle in self.get_handles():
            yield handle, self.get_raw(handle)

class ProxyMap(object):
    """
    A dictionary-like object for accessing "raw" proxied data. Of
    course, proxied data may have been changed by the proxy.
    """
    def __init__(self, db, get_raw, get_keys):
        self.get_raw = get_raw
        self.get_keys = get_keys
        self.db = db

    def __getitem__(self, handle):
        return self.get_raw(handle)

    def keys(self):
        return self.get_keys()

class ProxyDbBase(DbReadBase):
    """
    ProxyDbBase is a base class for building a proxy to a WEARNOW database. 
    This class attempts to implement functions that are likely to be common 
    among proxy classes. Functions that are not likely to be common raise a 
    NotImplementedError to remind the developer to implement those functions.

    Real database proxy classes can inherit from this class to make sure the
    database interface is properly implemented.
    """

    def __init__(self, db):
        """
        Create a new ProxyDb instance. 
        """
        self.db = self.basedb = db
        while isinstance(self.basedb, ProxyDbBase):
            self.basedb = self.basedb.db
        self.bookmarks = db.bookmarks
        self.ensemble_bookmarks = db.ensemble_bookmarks
        self.media_bookmarks = db.media_bookmarks
        self.note_bookmarks = db.note_bookmarks

        self.textile_map = ProxyMap(self, self.get_raw_textile_data, 
                                 self.get_textile_handles)
        self.ensemble_map = ProxyMap(self, self.get_raw_ensemble_data, 
                                 self.get_ensemble_handles)
        self.media_map = ProxyMap(self, self.get_raw_object_data, 
                                 self.get_media_object_handles)
        self.note_map = ProxyMap(self, self.get_raw_note_data, 
                                 self.get_note_handles)

    def is_open(self):
        """
        Return 1 if the database has been opened.
        """
        return self.db.is_open
        
    def get_owner(self):
        """returns the Researcher instance, providing information about
        the owner of the database"""
        return self.db.get_owner()        
        
    def include_something(self, handle, obj=None):
        """
        Model predicate. Returns True if object referred to by handle is to be
        included, otherwise returns False.
        """
        if obj is None:
            obj = self.get_unfiltered_something(handle)

        # Call function to determine if object should be included or not
        return obj.include()
        
    # Define default predicates for each object type
    
    include_textile = \
    include_ensemble = \
    include_media_object = \
    include_note = \
    include_tag = \
        None
        
    def get_textile_cursor(self):
        return ProxyCursor(self.get_raw_textile_data, 
                           self.get_textile_handles)

    def get_ensemble_cursor(self):
        return ProxyCursor(self.get_raw_ensemble_data,
                           self.get_ensemble_handles)

    def get_media_cursor(self):
        return ProxyCursor(self.get_raw_object_data,
                           self.get_media_object_handles)

    def get_note_cursor(self):
        return ProxyCursor(self.get_raw_note_data,
                           self.get_note_handles)

    def get_tag_cursor(self):
        return ProxyCursor(self.get_raw_tag_data,
                           self.get_tag_handles)

    def get_textile_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each Textile in
        the database. 
        """
        if self.db.is_open:
            return list(self.iter_textile_handles())
        else:
            return []
        
    def get_ensemble_handles(self, sort_handles=True):
        """
        Return a list of database handles, one handle for each Ensemble in
        the database. 
        """
        if self.db.is_open:
            return list(self.iter_ensemble_handles())
        else:
            return []
        
    def get_media_object_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each MediaObject in
        the database. 
        """
        if self.db.is_open:
            return list(self.iter_media_object_handles())
        else:
            return []

    def get_note_handles(self, sort_handles=True):
        """
        Return a list of database handles, one handle for each Note in
        the database. 
        """
        if self.db.is_open:
            return list(self.iter_note_handles())
        else:
            return []

    def get_tag_handles(self, sort_handles=False):
        """
        Return a list of database handles, one handle for each Tag in
        the database. 
        """
        if self.db.is_open:
            return list(self.iter_tag_handles())
        else:
            return []

    def get_default_textile(self):
        """returns the default Textile of the database"""
        return self.db.get_default_textile()

    def get_default_handle(self):
        """returns the default Textile of the database"""
        return self.db.get_default_handle()            
            
    def iter_textile_handles(self):
        """
        Return an iterator over database handles, one handle for each Textile in
        the database.
        """
        return filter(self.include_textile, self.db.iter_textile_handles())
        
    def iter_ensemble_handles(self):
        """
        Return an iterator over database handles, one handle for each Ensemble in
        the database.
        """
        return filter(self.include_ensemble, self.db.iter_ensemble_handles())

    def iter_media_object_handles(self):
        """
        Return an iterator over database handles, one handle for each Media
        Object in the database.
        """
        return filter(self.include_media_object, self.db.iter_media_object_handles())

    def iter_note_handles(self):
        """
        Return an iterator over database handles, one handle for each Note in
        the database.
        """
        return filter(self.include_note, self.db.iter_note_handles())

    def iter_tag_handles(self):
        """
        Return an iterator over database handles, one handle for each Tag in
        the database.
        """
        return filter(self.include_tag, self.db.iter_tag_handles())

    @staticmethod
    def __iter_object(selector, method):
        """ Helper function to return an iterator over an object class """
        return filter(lambda obj: ((selector is None) or selector(obj.handle)),
                       method())

    def iter_textiles(self):
        """
        Return an iterator over Textile objects in the database
        """
        return self.__iter_object(self.include_textile, self.db.iter_textiles)
        
    def iter_ensembles(self):
        """
        Return an iterator over Ensemble objects in the database
        """
        return self.__iter_object(self.include_ensemble, self.db.iter_ensembles)    
  
    def iter_media_objects(self):
        """
        Return an iterator over Media objects in the database
        """
        return self.__iter_object(self.include_media_object,
                                  self.db.iter_media_objects)      
        
    def iter_notes(self):
        """
        Return an iterator over Note objects in the database
        """
        return self.__iter_object(self.include_note, self.db.iter_notes)       
        
    def iter_tags(self):
        """
        Return an iterator over Tag objects in the database
        """
        return self.__iter_object(self.include_tag, self.db.iter_tags)       
        
    @staticmethod
    def gfilter(predicate, obj):
        """
        Returns obj if predicate is True or not callable, else returns None
        """
        if predicate is not None and obj is not None:
            return obj if predicate(obj.handle) else None
        return obj

    def __getattr__(self, name):
        """ Handle unknown attribute lookups """
        if name == "readonly":
            return True
        sname = name.split('_')
        if sname[:2] == ['get', 'unfiltered']:
            """
            Handle get_unfiltered calls.  Return the name of the access
            method for the base database object.  Call setattr before
            returning so that the lookup happens at most once for a given
            method call and a given object.
            """
            attr = getattr(self.basedb, 'get_' + sname[2] + '_from_handle')
            setattr(self, name, attr)
            return attr

        # if a write-method:
        if (name in DbWriteBase.__dict__ and
            not name.startswith("__") and 
            type(DbWriteBase.__dict__[name]) is types.FunctionType):
            raise AttributeError
        # Default behaviour: lookup attribute in parent object
        return getattr(self.db, name)

    def get_textile_from_handle(self, handle):
        """
        Finds a Textile in the database from the passed wearnow handle.
        If no such Textile exists, None is returned.
        """
        return self.gfilter(self.include_textile,
                            self.db.get_textile_from_handle(handle))

    def get_ensemble_from_handle(self, handle):
        """
        Finds a Ensemble in the database from the passed wearnow handle.
        If no such Ensemble exists, None is returned.
        """
        return self.gfilter(self.include_ensemble,
                            self.db.get_ensemble_from_handle(handle)) 

    def get_object_from_handle(self, handle):
        """
        Finds an Object in the database from the passed wearnow handle.
        If no such Object exists, None is returned.
        """
        return self.gfilter(self.include_media_object,
                    self.db.get_object_from_handle(handle))

    def get_note_from_handle(self, handle):
        """
        Finds a Note in the database from the passed wearnow handle.
        If no such Note exists, None is returned.
        """
        return self.gfilter(self.include_note,
                            self.db.get_note_from_handle(handle))
        
    def get_tag_from_handle(self, handle):
        """
        Finds a Tag in the database from the passed wearnow handle.
        If no such Tag exists, None is returned.
        """
        return self.gfilter(self.include_tag,
                            self.db.get_tag_from_handle(handle))
        
    def get_textile_from_wearnow_id(self, val):
        """
        Finds a Textile in the database from the passed WEARNOW ID.
        If no such Textile exists, None is returned.
        """
        return self.gfilter(self.include_textile,
                self.db.get_textile_from_wearnow_id(val))

    def get_ensemble_from_wearnow_id(self, val):
        """
        Finds a Ensemble in the database from the passed WEARNOW ID.
        If no such Ensemble exists, None is returned.
        """
        return self.gfilter(self.include_ensemble,
                self.db.get_ensemble_from_wearnow_id(val))

    def get_object_from_wearnow_id(self, val):
        """
        Finds a MediaObject in the database from the passed wearnow' ID.
        If no such MediaObject exists, None is returned.
        """
        return self.gfilter(self.include_media_object,
                self.db.get_object_from_wearnow_id(val))

    def get_note_from_wearnow_id(self, val):
        """
        Finds a Note in the database from the passed wearnow' ID.
        If no such Note exists, None is returned.
        """
        return self.gfilter(self.include_note,
                self.db.get_note_from_wearnow_id(val))

    def get_tag_from_name(self, val):
        """
        Finds a Tag in the database from the passed tag name.
        If no such Tag exists, None is returned.
        """
        return self.gfilter(self.include_tag,
                self.db.get_tag_from_name(val))

    def get_number_of_textiles(self):
        """
        Return the number of textiles currently in the database.
        """
        return len(self.get_textile_handles())

    def get_number_of_ensembles(self):
        """
        Return the number of ensembles currently in the database.
        """
        return len(self.get_ensemble_handles())

    def get_number_of_media_objects(self):
        """
        Return the number of media objects currently in the database.
        """
        return len(self.get_media_object_handles())

    def get_number_of_repositories(self):
        """
        Return the number of source repositories currently in the database.
        """
        return len(self.get_repository_handles())

    def get_number_of_tags(self):
        """
        Return the number of tags currently in the database.
        """
        return len(self.get_tag_handles())

    def get_save_path(self):
        """returns the save path of the file, or "" if one does not exist"""
        return self.db.get_save_path()

    def get_textile_attribute_types(self):
        """returns a list of all Attribute types associated with Textile
        instances in the database"""
        return self.db.get_textile_attribute_types()

    def get_note_types(self):
        """returns a list of all custom note types associated with
        Note instances in the database"""
        return self.db.get_note_types()

    def get_url_types(self):
        """returns a list of all custom names types associated with Url
        instances in the database"""
        return self.db.get_url_types()

    def get_raw_textile_data(self, handle):
        return self.get_textile_from_handle(handle).serialize()

    def get_raw_ensemble_data(self, handle):
        return self.get_ensemble_from_handle(handle).serialize()

    def get_raw_object_data(self, handle):
        return self.get_object_from_handle(handle).serialize()

    def get_raw_note_data(self, handle):
        return self.get_note_from_handle(handle).serialize()

    def get_raw_tag_data(self, handle):
        return self.get_tag_from_handle(handle).serialize()

    def has_textile_handle(self, handle):
        """
        Returns True if the handle exists in the current Textile database.
        """
        return self.gfilter(self.include_textile,
                self.db.get_textile_from_handle(handle)) is not None

    def has_ensemble_handle(self, handle):
        """
        Returns True if the handle exists in the current Ensemble database.
        """
        return self.gfilter(self.include_ensemble,
                self.db.get_ensemble_from_handle(handle)) is not None

    def has_object_handle(self, handle):
        """
        returns True if the handle exists in the current MediaObjectdatabase.
        """
        return self.gfilter(self.include_media_object,
                self.db.get_object_from_handle(handle)) is not None

    def has_note_handle(self, handle):
        """
        returns True if the handle exists in the current Note database.
        """
        return self.gfilter(self.include_note,
                self.db.get_note_from_handle(handle)) is not None
        
    def has_tag_handle(self, handle):
        """
        returns True if the handle exists in the current Tag database.
        """
        return self.gfilter(self.include_tag,
                self.db.get_tag_from_handle(handle)) is not None
        
    def get_mediapath(self):
        """returns the default media path of the database"""
        return self.db.get_mediapath()

    def get_wearnow_ids(self, obj_key):
        return self.db.get_wearnow_ids(obj_key)

    def has_wearnow_id(self, obj_key, wearnow_id):
        return self.db.has_wearnow_id(obj_key, wearnow_id)

    def get_bookmarks(self):
        """returns the list of Textile handles in the bookmarks"""
        return self.bookmarks

    def get_ensemble_bookmarks(self):
        """returns the list of Ensemble handles in the bookmarks"""
        return self.ensemble_bookmarks

    def get_media_bookmarks(self):
        """returns the list of Media handles in the bookmarks"""
        return self.media_bookmarks

    def get_note_bookmarks(self):
        """returns the list of Note handles in the bookmarks"""
        return self.note_bookmarks

    def close(self):
        """
        Close on a proxy closes real database.
        """
        self.basedb.close()

    def find_initial_textile(self):
        """
        Find an initial textile, given that they might not be
        available.
        """
        textile = self.basedb.find_initial_textile()
        if textile and self.has_textile_handle(textile.handle):
            return textile
        else:
            return None

    def get_dbid(self):
        """
        Return the database ID.
        """
        return self.basedb.get_dbid()
