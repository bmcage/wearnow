#
# wearnow - a GTK+/GNOME based program
#
# Copyright (C) 2007       Brian G. Matherly
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
Proxy class for the WEARNOW databases. Filter out all data marked private.
"""

#-------------------------------------------------------------------------
#
# Python libraries
#
#-------------------------------------------------------------------------
from ..const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext
import logging
LOG = logging.getLogger(".citation")

#-------------------------------------------------------------------------
#
# WEARNOW libraries
#
#-------------------------------------------------------------------------
from ..lib import (MediaRef, Attribute,
                   Textile, MediaObject,
                   Ensemble, ChildRef, Note, Tag)
from .proxybase import ProxyDbBase

class PrivateProxyDb(ProxyDbBase):
    """
    A proxy to a WEARNOW database. This proxy will act like a WEARNOW database,
    but all data marked private will be hidden from the user.
    """

    def __init__(self, db):
        """
        Create a new PrivateProxyDb instance. 
        """
        ProxyDbBase.__init__(self, db)

    def get_textile_from_handle(self, handle):
        """
        Finds a Textile in the database from the passed WEARNOW ID.
        If no such Textile exists, None is returned.
        """
        textile = self.db.get_textile_from_handle(handle)
        if textile and not textile.get_privacy():
            return sanitize_textile(self.db, textile)
        return None

    def get_object_from_handle(self, handle):
        """
        Finds an Object in the database from the passed WEARNOW ID.
        If no such Object exists, None is returned.
        """
        media = self.db.get_object_from_handle(handle)
        if media and not media.get_privacy():
            return sanitize_media(self.db, media)
        return None

    def get_ensemble_from_handle(self, handle):
        """
        Finds a Ensemble in the database from the passed WEARNOW ID.
        If no such Ensemble exists, None is returned.
        """
        ensemble = self.db.get_ensemble_from_handle(handle)
        if ensemble and not ensemble.get_privacy():
            return sanitize_ensemble(self.db, ensemble)
        return None

    def get_note_from_handle(self, handle):
        """
        Finds a Note in the database from the passed WEARNOW ID.
        If no such Note exists, None is returned.
        """
        note = self.db.get_note_from_handle(handle)
        if note and not note.get_privacy():
            return note
        return None

    def get_textile_from_wearnow_id(self, val):
        """
        Finds a Textile in the database from the passed wearnow ID.
        If no such Textile exists, None is returned.
        """
        textile = self.db.get_textile_from_wearnow_id(val)
        if textile and not textile.get_privacy():
            return sanitize_textile(self.db, textile)
        return None

    def get_ensemble_from_wearnow_id(self, val):
        """
        Finds a Ensemble in the database from the passed wearnow ID.
        If no such Ensemble exists, None is returned.
        """
        ensemble = self.db.get_ensemble_from_wearnow_id(val)
        if ensemble and not ensemble.get_privacy():
            return sanitize_ensemble(self.db, ensemble)
        return None

    def get_object_from_wearnow_id(self, val):
        """
        Finds a MediaObject in the database from the passed wearnow ID.
        If no such MediaObject exists, None is returned.
        """
        obj = self.db.get_object_from_wearnow_id(val)
        if obj and not obj.get_privacy():
            return sanitize_media(self.db, obj)
        return None

    def get_note_from_wearnow_id(self, val):
        """
        Finds a Note in the database from the passed wearnow ID.
        If no such Note exists, None is returned.
        """
        note = self.db.get_note_from_wearnow_id(val)
        if note and not note.get_privacy():
            return note
        return None

    # Define predicate functions for use by default iterator methods
    
    def include_textile(self, handle):
        """
        Predicate returning True if object is to be included, else False
        """
        obj = self.get_unfiltered_textile(handle)
        return obj and not obj.get_privacy()
    
    def include_ensemble(self, handle):
        """
        Predicate returning True if object is to be included, else False
        """        
        obj = self.get_unfiltered_ensemble(handle)
        return obj and not obj.get_privacy()
    
    def include_media_object(self, handle):
        """
        Predicate returning True if object is to be included, else False
        """
        obj = self.get_unfiltered_object(handle)
        return obj and not obj.get_privacy()
    
    def include_note(self, handle):
        """
        Predicate returning True if object is to be included, else False
        """        
        obj = self.get_unfiltered_note(handle)
        return obj and not obj.get_privacy()

    def get_default_textile(self):
        """returns the default Textile of the database"""
        textile = self.db.get_default_textile()
        if textile and not textile.get_privacy():
            return sanitize_textile(self.db, textile)
        return None

    def get_default_handle(self):
        """returns the default Textile of the database"""
        handle = self.db.get_default_handle()
        textile = self.db.get_textile_from_handle(handle)
        if textile and not textile.get_privacy():
            return handle
        return None
    
    def has_textile_handle(self, handle):
        """
        returns True if the handle exists in the current Textile database.
        """
        textile = self.db.get_textile_from_handle(handle)
        if textile and not textile.get_privacy():
            return True
        return False

    def has_ensemble_handle(self, handle):            
        """
        Return True if the handle exists in the current Ensemble database.
        """
        ensemble = self.db.get_ensemble_from_handle(handle)
        if ensemble and not ensemble.get_privacy():
            return True
        return False

    def has_object_handle(self, handle):
        """
        Return True if the handle exists in the current MediaObjectdatabase.
        """
        object = self.db.get_object_from_handle(handle)
        if object and not object.get_privacy():
            return True
        return False

    def has_note_handle(self, handle):
        """
        Return True if the handle exists in the current Note database.
        """
        note = self.db.get_note_from_handle(handle)
        if note and not note.get_privacy():
            return True
        return False

    def find_backlink_handles(self, handle, include_classes=None):
        """
        Find all objects that hold a reference to the object handle.
        Returns an iterator over a list of (class_name, handle) tuples.

        :param handle: handle of the object to search for.
        :type handle: database handle
        :param include_classes: list of class names to include in the results.
                                Default: None means include all classes.
        :type include_classes: list of class names
        
        This default implementation does a sequential scan through all
        the primary object databases and is very slow. Backends can
        override this method to provide much faster implementations that
        make use of additional capabilities of the backend.

        Note that this is a generator function, it returns a iterator for
        use in loops. If you want a list of the results use::

        >    result_list = list(find_backlink_handles(handle))
        """
        
        # This isn't done yet because it doesn't check if references are
        # private (like a MediaRef). It only checks if the 
        # referenced object is private.

        objects = {
            'Textile'        : self.db.get_textile_from_handle,
            'Ensemble'        : self.db.get_ensemble_from_handle,
            'MediaObject'   : self.db.get_object_from_handle,
            'Note'          : self.db.get_note_from_handle,
            }

        handle_itr = self.db.find_backlink_handles(handle, include_classes)
        for (class_name, handle) in handle_itr:
            if class_name in objects:
                obj = objects[class_name](handle)
                if obj and not obj.get_privacy():
                    yield (class_name, handle)
            else:
                raise NotImplementedError                
        return

def copy_media_ref_list(db, original_obj, clean_obj):
    """
    Copies media references from one object to another - excluding private 
    references and references to private objects.

    :param db: wearnow database to which the references belongs
    :type db: DbBase
    :param original_obj: Object that may have private references
    :type original_obj: MediaBase
    :param clean_obj: Object that will have only non-private references
    :type original_obj: MediaBase
    :returns: Nothing
    """
    for media_ref in original_obj.get_media_list():
        if media_ref and not media_ref.get_privacy():
            handle = media_ref.get_reference_handle()
            media_object = db.get_object_from_handle(handle)
            if media_object and not media_object.get_privacy():
                clean_obj.add_media_reference(sanitize_media_ref(db, media_ref))

def copy_notes(db, original_obj, clean_obj):
    """
    Copies notes from one object to another - excluding references to private
    notes.

    :param db: wearnow database to which the references belongs
    :type db: DbBase
    :param original_obj: Object that may have private references
    :type original_obj: NoteBase
    :param clean_obj: Object that will have only non-private references
    :type original_obj: NoteBase
    :returns: Nothing
    """     
    for note_handle in original_obj.get_note_list():
        note = db.get_note_from_handle(note_handle)
        if note and not note.get_privacy():
            clean_obj.add_note(note_handle)

def copy_attributes(db, original_obj, clean_obj):
    """
    Copies attributes from one object to another - excluding references to 
    private attributes.

    :param db: wearnow database to which the references belongs
    :type db: DbBase
    :param original_obj: Object that may have private references
    :type original_obj: AttributeBase
    :param clean_obj: Object that will have only non-private references
    :type original_obj: AttributeBase
    :returns: Nothing
    """   
    for attribute in original_obj.get_attribute_list():
        if attribute and not attribute.get_privacy():
            new_attribute = Attribute()
            new_attribute.set_type(attribute.get_type())
            new_attribute.set_value(attribute.get_value())
            copy_notes(db, attribute, new_attribute)
            copy_citation_ref_list(db, attribute, new_attribute)
            clean_obj.add_attribute(new_attribute)

def copy_urls(db, original_obj, clean_obj):
    """
    Copies urls from one object to another - excluding references to 
    private urls.

    :param db: wearnow database to which the references belongs
    :type db: DbBase
    :param original_obj: Object that may have urls
    :type original_obj: UrlBase
    :param clean_obj: Object that will have only non-private urls
    :type original_obj: UrlBase
    :returns: Nothing
    """         
    for url in original_obj.get_url_list():
        if url and not url.get_privacy():
            clean_obj.add_url(url)
        
def sanitize_media_ref(db, media_ref):
    """
    Create a new MediaRef instance based off the passed MediaRef
    instance. The returned instance has all private records
    removed from it.
    
    :param db: wearnow database to which the MediaRef object belongs
    :type db: DbBase
    :param source_ref: source MediaRef object that will be copied with
                       privacy records removed
    :type source_ref: MediaRef
    :returns: 'cleansed' MediaRef object
    :rtype: MediaRef
    """
    new_ref = MediaRef()
    new_ref.set_rectangle(media_ref.get_rectangle())
    
    new_ref.set_reference_handle(media_ref.get_reference_handle())
    
    return new_ref

def sanitize_textile(db, textile):
    """
    Create a new Textile instance based off the passed Textile
    instance. The returned instance has all private records
    removed from it.
    
    :param db: wearnow database to which the Textile object belongs
    :type db: DbBase
    :param textile: source Textile object that will be copied with
                   privacy records removed
    :type textile: Textile
    :returns: 'cleansed' Textile object
    :rtype: Textile
    """
    new_textile = Textile()

    # copy gender
    new_textile.set_wearnow_id(textile.get_wearnow_id())
    new_textile.set_handle(textile.get_handle())
    new_textile.set_change_time(textile.get_change_time())
    new_textile.set_tag_list(textile.get_tag_list())
    
    copy_attributes(db, textile, new_textile)
    copy_urls(db, textile, new_textile)
    copy_media_ref_list(db, textile, new_textile)
    copy_notes(db, textile, new_textile)
    
    return new_textile

def sanitize_media(db, media):
    """
    Create a new MediaObject instance based off the passed Media
    instance. The returned instance has all private records
    removed from it.
    
    :param db: wearnow database to which the Textile object belongs
    :type db: DbBase
    :param media: source Media object that will be copied with
                  privacy records removed
    :type media: MediaObject
    :returns: 'cleansed' Media object
    :rtype: MediaObject
    """
    new_media = MediaObject()
    
    new_media.set_mime_type(media.get_mime_type())
    new_media.set_path(media.get_path())
    new_media.set_description(media.get_description())
    new_media.set_wearnow_id(media.get_wearnow_id())
    new_media.set_handle(media.get_handle())
    new_media.set_change_time(media.get_change_time())
    new_media.set_tag_list(media.get_tag_list())

    return new_media

def sanitize_ensemble(db, ensemble):
    """
    Create a new Ensemble instance based off the passed Ensemble
    instance. The returned instance has all private records
    removed from it.
    
    :param db: wearnow database to which the Textile object belongs
    :type db: DbBase
    :param ensemble: source Ensemble object that will be copied with
                   privacy records removed
    :type ensemble: Ensemble
    :returns: 'cleansed' Ensemble object
    :rtype: Ensemble
    """
    new_ensemble = Ensemble()
    
    new_ensemble.set_wearnow_id(ensemble.get_wearnow_id())
    new_ensemble.set_handle(ensemble.get_handle())
    new_ensemble.set_change_time(ensemble.get_change_time())
    new_ensemble.set_tag_list(ensemble.get_tag_list())
    
    # Copy child references.
    for child_ref in ensemble.get_child_ref_list():
        if child_ref and child_ref.get_privacy():
            continue
        child_handle = child_ref.get_reference_handle()
        child = db.get_textile_from_handle(child_handle)
        if child and child.get_privacy():
            continue
        # Copy this reference
        new_ref = ChildRef()
        new_ref.set_reference_handle(child_ref.get_reference_handle())
        new_ensemble.add_child_ref(new_ref)
        
    copy_media_ref_list(db, ensemble, new_ensemble)
    
    return new_ensemble
