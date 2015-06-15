#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2010       Michiel D. Nauta
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
Ensemble object for WearNow.
"""

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".ensemble")

#-------------------------------------------------------------------------
#
# modules
#
#-------------------------------------------------------------------------
from .primaryobj import PrimaryObject
from .notebase import NoteBase
from .mediabase import MediaBase
from .tagbase import TagBase
from .childref import ChildRef
from .const import IDENTICAL, EQUAL, DIFFERENT
from .handle import Handle

#-------------------------------------------------------------------------
#
# Ensemble class
#
#-------------------------------------------------------------------------
class Ensemble(NoteBase, MediaBase, PrimaryObject):
    """
    The Ensemble record is the WearNow in-memory representation of the
    relationships between people. It contains all the information
    related to the relationship.
    
    Ensemble objects are usually created in one of two ways.

    1. Creating a new Ensemble object, which is then initialized and
       added to the database.
    2. Retrieving an object from the database using the records
       handle.

    Once a Ensemble object has been modified, it must be committed
    to the database using the database object's commit_ensemble function,
    or the changes will be lost.
    """

    def __init__(self):
        """
        Create a new Ensemble instance. 
        
        After initialization, most data items have empty or null values, 
        including the database handle.
        """
        PrimaryObject.__init__(self)
        NoteBase.__init__(self)
        MediaBase.__init__(self)
        self.child_ref_list = []
        self.complete = 0

    def serialize(self):
        """
        Convert the data held in the event to a Python tuple that
        represents all the data elements. 
        
        This method is used to convert the object into a form that can easily 
        be saved to a database.

        These elements may be primitive Python types (string, integers),
        complex Python types (lists or tuples, or Python objects. If the
        target database cannot handle complex types (such as objects or
        lists), the database is responsible for converting the data into
        a form that it can use.

        :returns: Returns a python tuple containing the data that should
                  be considered persistent.
        :rtype: tuple
        """
        return (self.handle, self.wearnow_id, 
                [cr.serialize() for cr in self.child_ref_list],
                MediaBase.serialize(self),
                NoteBase.serialize(self),
                self.change, TagBase.serialize(self), self.private)

    def to_struct(self):
        """
        Convert the data held in this object to a structure (eg,
        struct) that represents all the data elements.
        
        This method is used to recursively convert the object into a
        self-documenting form that can easily be used for various
        purposes, including diffs and queries.

        These structures may be primitive Python types (string,
        integer, boolean, etc.) or complex Python types (lists,
        tuples, or dicts). If the return type is a dict, then the keys
        of the dict match the fieldname of the object. If the return
        struct (or value of a dict key) is a list, then it is a list
        of structs. Otherwise, the struct is just the value of the
        attribute.

        :returns: Returns a struct containing the data of the object.
        :rtype: dict
        """
        return {"_class": "Ensemble",
                "handle": Handle("Ensemble", self.handle), 
                "wearnow_id": self.wearnow_id, 
                "child_ref_list": [cr.to_struct() for cr in self.child_ref_list],
                "media_list": MediaBase.to_struct(self),
                "note_list": NoteBase.to_struct(self),
                "change": self.change, 
                "tag_list": TagBase.to_struct(self), 
                "private": self.private}

    @classmethod
    def from_struct(cls, struct):
        """
        Given a struct data representation, return a serialized object.

        :returns: Returns a serialized object
        """
        default = Ensemble()
        return (Handle.from_struct(struct.get("handle", default.handle)),
                struct.get("wearnow_id", default.wearnow_id),
                [ChildRef.from_struct(cr) for cr in struct.get("child_ref_list", default.child_ref_list)],
                MediaBase.from_struct(struct.get("media_list", default.media_list)),
                NoteBase.from_struct(struct.get("note_list", default.note_list)),
                struct.get("change", default.change), 
                TagBase.from_struct(struct.get("tag_list", default.tag_list)), 
                struct.get("private", default.private))

    def unserialize(self, data):
        """
        Convert the data held in a tuple created by the serialize method
        back into the data in a Ensemble structure.
        """
        (self.handle, self.wearnow_id, child_ref_list, media_list,
          note_list, self.change, tag_list, self.private) = data

        self.child_ref_list = [ChildRef().unserialize(cr)
                               for cr in child_ref_list]
        MediaBase.unserialize(self, media_list)
        NoteBase.unserialize(self, note_list)
        TagBase.unserialize(self, tag_list)
        return self

    def _has_handle_reference(self, classname, handle):
        """
        Return True if the object has reference to a given handle of given 
        primary object type.
        
        :param classname: The name of the primary object class.
        :type classname: str
        :param handle: The handle to be checked.
        :type handle: str
        :returns: Returns whether the object has reference to this handle of 
                  this object type.
        :rtype: bool
        """
        if classname == 'Textile':
            return handle in ([ref.ref for ref in self.child_ref_list])
        return False

    def _remove_handle_references(self, classname, handle_list):
        """
        Remove all references in this object to object handles in the list.

        :param classname: The name of the primary object class.
        :type classname: str
        :param handle_list: The list of handles to be removed.
        :type handle_list: str
        """
        if classname == 'Textile':
            new_list = [ref for ref in self.child_ref_list
                            if ref.ref not in handle_list]
            self.child_ref_list = new_list

    def _replace_handle_reference(self, classname, old_handle, new_handle):
        """
        Replace all references to old handle with those to the new handle.

        :param classname: The name of the primary object class.
        :type classname: str
        :param old_handle: The handle to be replaced.
        :type old_handle: str
        :param new_handle: The handle to replace the old one with.
        :type new_handle: str
        """
        if classname == 'Textile':
            refs_list = [ ref.ref for ref in self.child_ref_list ]
            new_ref = None
            if new_handle in refs_list:
                new_ref = self.child_ref_list[refs_list.index(new_handle)]
            n_replace = refs_list.count(old_handle)
            for ix_replace in range(n_replace):
                idx = refs_list.index(old_handle)
                self.child_ref_list[idx].ref = new_handle
                refs_list[idx] = new_handle
                if new_ref:
                    child_ref = self.child_ref_list[idx]
                    equi = new_ref.is_equivalent(child_ref)
                    if equi != DIFFERENT:
                        if equi == EQUAL:
                            new_ref.merge(child_ref)
                        self.child_ref_list.pop(idx)
                        refs_list.pop(idx)

    def get_text_data_list(self):
        """
        Return the list of all textual attributes of the object.

        :returns: Returns the list of all textual attributes of the object.
        :rtype: list
        """
        return [self.wearnow_id]

    def get_text_data_child_list(self):
        """
        Return the list of child objects that may carry textual data.

        :returns: Returns the list of child objects that may carry textual data.
        :rtype: list
        """
        return self.media_list

    def get_note_child_list(self):
        """
        Return the list of child secondary objects that may refer notes.

        :returns: Returns the list of child secondary child objects that may 
                  refer notes.
        :rtype: list
        """
        check_list = self.media_list + self.attribute_list + \
            self.child_ref_list
        return check_list

    def get_referenced_handles(self):
        """
        Return the list of (classname, handle) tuples for all directly
        referenced primary objects.
        
        :returns: List of (classname, handle) tuples for referenced objects.
        :rtype: list
        """
        ret = self.get_referenced_note_handles() 
        ret += [('Textile', handle) for handle
                in ([ref.ref for ref in self.child_ref_list])
                if handle]
        ret += self.get_referenced_tag_handles()
        return ret

    def get_handle_referents(self):
        """
        Return the list of child objects which may, directly or through their 
        children, reference primary objects..
        
        :returns: Returns the list of objects referencing primary objects.
        :rtype: list
        """
        return self.media_list + self.child_ref_list

    def merge(self, acquisition):
        """
        Merge the content of acquisition into this Ensemble.

        Lost: handle, id, relation, father, mother of acquisition.

        :param acquisition: The Ensemble to merge with the present Ensemble.
        :type acquisition: Ensemble
        """
        self._merge_privacy(acquisition)
        self._merge_media_list(acquisition)
        self._merge_child_ref_list(acquisition)
        self._merge_note_list(acquisition)
        self._merge_tag_list(acquisition)

    def add_child_ref(self, child_ref):
        """
        Add the database handle for :class:`~.textile.Textile` to the Ensemble's
        list of children.

        :param child_ref: Child Reference instance
        :type  child_ref: ChildRef
        """
        if not isinstance(child_ref, ChildRef):
            raise ValueError("expecting ChildRef instance")
        self.child_ref_list.append(child_ref)
            
    def remove_child_ref(self, child_ref):
        """
        Remove the database handle for :class:`~.textile.Textile` to the Ensemble's
        list of children if the :class:`~.textile.Textile` is already in the list.

        :param child_ref: Child Reference instance
        :type child_ref: ChildRef
        :returns: True if the handle was removed, False if it was not
                  in the list.
        :rtype: bool
        """
        if not isinstance(child_ref, ChildRef):
            raise ValueError("expecting ChildRef instance")
        new_list = [ref for ref in self.child_ref_list
                    if ref.ref != child_ref.ref ]
        self.child_ref_list = new_list

    def remove_child_handle(self, child_handle):
        """
        Remove the database handle for :class:`~.textile.Textile` to the Ensemble's
        list of children if the :class:`~.textile.Textile` is already in the list.

        :param child_handle: :class:`~.textile.Textile` database handle
        :type  child_handle: str
        :returns: True if the handle was removed, False if it was not
                  in the list.
        :rtype: bool
        """
        new_list = [ref for ref in self.child_ref_list
                    if ref.ref != child_handle ]
        self.child_ref_list = new_list

    def get_child_ref_list(self):
        """
        Return the list of :class:`~.childref.ChildRef` handles identifying the
        children of the Ensemble.

        :returns: Returns the list of :class:`~.childref.ChildRef` handles
                  associated with the Ensemble.
        :rtype: list
        """
        return self.child_ref_list

    def set_child_ref_list(self, child_ref_list):
        """
        Assign the passed list to the Ensemble's list children.

        :param child_ref_list: List of Child Reference instances to be
                               associated as the Ensemble's list of children.
        :type child_ref_list: list of :class:`~.childref.ChildRef` instances
        """
        self.child_ref_list = child_ref_list

    def _merge_child_ref_list(self, acquisition):
        """
        Merge the list of child references from acquisition with our own.

        :param acquisition: the childref list of this Ensemble will be merged
                            with the current childref list.
        :type acquisition: Ensemble
        """
        childref_list = self.child_ref_list[:]
        for addendum in acquisition.get_child_ref_list():
            for childref in childref_list:
                equi = childref.is_equivalent(addendum)
                if equi == IDENTICAL:
                    break
                elif equi == EQUAL:
                    childref.merge(addendum)
                    break
            else:
                self.child_ref_list.append(addendum)
