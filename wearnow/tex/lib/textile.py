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
Textile object for WearNow.
"""

#-------------------------------------------------------------------------
#
# modules
#
#-------------------------------------------------------------------------
from .primaryobj import PrimaryObject
from .notebase import NoteBase
from .mediabase import MediaBase
from .attrbase import AttributeBase
from .urlbase import UrlBase
from .tagbase import TagBase
from .attrtype import AttributeType
from .attribute import Attribute
from .textiletype import TextileType
from .const import IDENTICAL, EQUAL, DIFFERENT
from ..const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext
from .handle import Handle

#-------------------------------------------------------------------------
#
# Textile class
#
#-------------------------------------------------------------------------
class Textile(NoteBase, AttributeBase, MediaBase, UrlBase, PrimaryObject):
    """
    The Textile record is the WearNow in-memory representation of an
    individual garment. It contains all the information related to
    an garment.
    
    Textile objects are usually created in one of two ways.

    1. Creating a new Textile object, which is then initialized and added to 
       the database.
    2. Retrieving an object from the database using the records handle.

    Once a Textile object has been modified, it must be committed
    to the database using the database object's commit_textile function, 
    or the changes will be lost.

    """
    
    def __init__(self, data=None):
        """
        Create a new Textile instance. 
        
        After initialization, most data items have empty or null values, 
        including the database handle.
        """
        PrimaryObject.__init__(self)
        NoteBase.__init__(self)
        MediaBase.__init__(self)
        AttributeBase.__init__(self)
        UrlBase.__init__(self)
        self.description = ""
        self.type = TextileType()
        if data:
            self.unserialize(data)

    def __eq__(self, other):
        return isinstance(other, Textile) and self.handle == other.handle

    def __ne__(self, other):
        return not self == other
        
    def serialize(self):
        """
        Convert the data held in the Textile to a Python tuple that
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
        return (
            self.handle,                                         #  0
            self.wearnow_id,                                     #  1
            self.description,
            MediaBase.serialize(self),                           # 10
            AttributeBase.serialize(self),                       # 12
            UrlBase.serialize(self),                             # 13
            NoteBase.serialize(self),                            # 16
            self.change,                                         # 17
            TagBase.serialize(self),                             # 18
            self.private,                                        # 19
            self.type.serialize(),
            )

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
        return {
            "_class": "Textile",
            "handle":  Handle("Textile", self.handle),            #  0
            "wearnow_id": self.wearnow_id,                         #  1
            "description": self.description,
            "media_list": MediaBase.to_struct(self),             # 10
            "attribute_list": AttributeBase.to_struct(self),     # 12
            "urls": UrlBase.to_struct(self),                     # 13
            "note_list": NoteBase.to_struct(self),               # 16
            "change": self.change,                               # 17
            "tag_list": TagBase.to_struct(self),                 # 18
            "private": self.private,                             # 19
            "type": self.type.to_struct(), 
            }

    @classmethod
    def from_struct(cls, struct):
        """
        Given a struct data representation, return a serialized object.

        :returns: Returns a serialized object
        """
        default = Textile()
        return (
            Handle.from_struct(struct.get("handle", default.handle)),
            struct.get("wearnow_id", default.wearnow_id),
            struct.get("description", default.description),
            MediaBase.from_struct(struct.get("media_list", default.media_list)),
            AttributeBase.from_struct(struct.get("attribute_list", default.attribute_list)),
            UrlBase.from_struct(struct.get("urls", default.urls)),
            NoteBase.from_struct(struct.get("note_list", default.note_list)),
            struct.get("change", default.change),
            TagBase.from_struct(struct.get("tag_list", default.tag_list)),
            struct.get("private", default.private),
            TextileType.from_struct(struct.get("type", {})), 
        )

    def unserialize(self, data):
        """
        Convert the data held in a tuple created by the serialize method
        back into the data in a Textile object.

        :param data: tuple containing the persistent data associated the
                     Textile object
        :type data: tuple
        """
        (self.handle,             #  0
         self.wearnow_id,          #  1
         self.description,
         media_list,              # 10
         attribute_list,          # 12
         urls,                    # 13
         note_list,               # 16
         self.change,             # 17
         tag_list,                # 18
         self.private,            # 19
         the_type,
         ) = data

        MediaBase.unserialize(self, media_list)
        AttributeBase.unserialize(self, attribute_list)
        UrlBase.unserialize(self, urls)
        NoteBase.unserialize(self, note_list)
        TagBase.unserialize(self, tag_list)
        self.type = TextileType()
        self.type.unserialize(the_type)
        return self
            
    def set_type(self, the_type):
        """Set descriptive type of the Note.
        
        :param the_type: descriptive type of the Note
        :type the_type: str
        """
        self.type.set(the_type)

    def get_type(self):
        """Get descriptive type of the Note.
        
        :returns: the descriptive type of the Note
        :rtype: str
        """
        return self.type

    def set_description(self, descr):
        self.description = descr
        
    def get_description(self):
        return self.description

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
        return False

    def _remove_handle_references(self, classname, handle_list):
        pass

    def _replace_handle_reference(self, classname, old_handle, new_handle):
        pass

    def get_text_data_list(self):
        """
        Return the list of all textual attributes of the object.

        :returns: Returns the list of all textual attributes of the object.
        :rtype: list
        """
        return [self.wearnow_id, self.description]

    def get_text_data_child_list(self):
        """
        Return the list of child objects that may carry textual data.

        :returns: Returns the list of child objects that may carry textual data.
        :rtype: list
        """
        return ([self.media_list +
                 self.attribute_list +
                 self.urls]
                ) 

    def get_note_child_list(self):
        """
        Return the list of child secondary objects that may refer notes.

        :returns: Returns the list of child secondary child objects that may 
                  refer notes.
        :rtype: list
        """
        return ( self.attribute_list
                )

    def get_referenced_handles(self):
        """
        Return the list of (classname, handle) tuples for all directly
        referenced primary objects.
        
        :returns: List of (classname, handle) tuples for referenced objects.
        :rtype: list
        """
        return  (
                 self.get_referenced_note_handles() +
                 self.get_referenced_tag_handles()
                )

    def get_handle_referents(self):
        """
        Return the list of child objects which may, directly or through
        their children, reference primary objects.
        
        :returns: Returns the list of objects referencing primary objects.
        :rtype: list
        """
        return ( self.media_list +
                 self.attribute_list
                )

    def merge(self, acquisition):
        """
        Merge the content of acquisition into this Textile.

        :param acquisition: The Textile to merge with the present Textile.
        :type acquisition: Textile
        """
        acquisition_id = acquisition.get_wearnow_id()
        if acquisition_id:
            attr = Attribute()
            attr.set_type(_("Merged WearNow ID"))
            attr.set_value(acquisition.get_wearnow_id())
            self.add_attribute(attr)

        self._merge_privacy(acquisition)
        self._merge_media_list(acquisition)
        self._merge_attribute_list(acquisition)
        self._merge_url_list(acquisition)
        self._merge_note_list(acquisition)
        self._merge_tag_list(acquisition)
