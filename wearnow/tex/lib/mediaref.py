#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2010       Michiel D. Nauta
# Copyright (C) 2011       Tim G L Lyons
# Copyright (C) 2013       Doug Blank <doug.blank@gmail.com>
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
Media Reference class for Gramps.
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from .secondaryobj import SecondaryObject
from .privacybase import PrivacyBase
from .refbase import RefBase
from .const import IDENTICAL, EQUAL, DIFFERENT
from .handle import Handle

#-------------------------------------------------------------------------
#
# MediaObject References for Person/Place/Source
#
#-------------------------------------------------------------------------
class MediaRef(SecondaryObject, PrivacyBase, RefBase):
    """Media reference class."""
    def __init__(self, source=None):
        PrivacyBase.__init__(self, source)
        RefBase.__init__(self, source)

        if source:
            self.rect = source.rect
        else:
            self.rect = None

    def serialize(self):
        """
        Convert the object to a serialized tuple of data.
        """
        return (PrivacyBase.serialize(self),
                RefBase.serialize(self),
                self.rect)

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
        return {"_class": "MediaRef",
                "private": PrivacyBase.serialize(self),
                "ref": Handle("Media", self.ref),
                "rect": self.rect if self.rect != (0,0,0,0) else None}

    @classmethod
    def from_struct(cls, struct):
        """
        Given a struct data representation, return a serialized object.

        :returns: Returns a serialized object
        """
        default = MediaRef()
        return (PrivacyBase.from_struct(struct.get("private", default.private)),
                RefBase.from_struct(struct.get("ref", default.ref)),
                struct.get("rect", default.rect))

    def unserialize(self, data):
        """
        Convert a serialized tuple of data to an object.
        """
        (privacy,ref,self.rect) = data
        PrivacyBase.unserialize(self, privacy)
        RefBase.unserialize(self, ref)
        return self

    def get_text_data_child_list(self):
        """
        Return the list of child objects that may carry textual data.

        :returns: Returns the list of child objects that may carry textual data.
        :rtype: list
        """
        return []

    def get_note_child_list(self):
        """
        Return the list of child secondary objects that may refer notes.

        :returns: Returns the list of child secondary child objects that may 
                  refer notes.
        :rtype: list
        """
        return []

    def get_referenced_handles(self):
        """
        Return the list of (classname, handle) tuples for all directly
        referenced primary objects.
        
        :returns: List of (classname, handle) tuples for referenced objects.
        :rtype: list
        """
        ret = []
        if self.ref:
            ret += [('MediaObject', self.ref)]
        return ret

    def get_handle_referents(self):
        """
        Return the list of child objects which may, directly or through
        their children, reference primary objects.
        
        :returns: Returns the list of objects referencing primary objects.
        :rtype: list
        """
        return []

    def is_equivalent(self, other):
        """
        Return if this object reference is equivalent, that is agrees in
        reference and region, to other.

        :param other: The object reference to compare this one to.
        :type other: MediaRef
        :returns: Constant indicating degree of equivalence.
        :rtype: int
        """
        if self.ref != other.ref or self.rect != other.rect:
            return DIFFERENT
        else:
            if self.is_equal(other):
                return IDENTICAL
            else:
                return EQUAL

    def merge(self, acquisition):
        """
        Merge the content of acquisition into this object reference.

        Lost: hlink and region or acquisition.

        :param acquisition: The object reference to merge with the present one.
        :type acquisition: MediaRef
        """
        self._merge_privacy(acquisition)

    def set_rectangle(self, coord):
        """Set subsection of an image."""
        self.rect = coord

    def get_rectangle(self):
        """Return the subsection of an image."""
        return self.rect
