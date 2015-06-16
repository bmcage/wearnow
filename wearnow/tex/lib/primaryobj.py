#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2000-2007 Donald N. Allingham
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
Basic Primary Object class for WearNow.
"""

#-------------------------------------------------------------------------
#
# WearNow modules
#
#-------------------------------------------------------------------------
from .tableobj import TableObject
from .privacybase import PrivacyBase
from .mediabase import MediaBase
from .tagbase import TagBase

#-------------------------------------------------------------------------
#
# Basic Primary Object class
#
#-------------------------------------------------------------------------
class BasicPrimaryObject(TableObject, PrivacyBase, TagBase):
    """
    The BasicPrimaryObject is the base class for :class:`~.note.Note` objects.
    
    It is also the base class for the :class:`PrimaryObject` class.    
    
    The :class:`PrimaryObject` is the base class for all other primary objects
    in the database. Primary objects are the core objects in the database.
    Each object has a database handle and a WearNow ID value. The database
    handle is used as the record number for the database, and the WearNow
    ID is the user visible version.
    """
    
    def __init__(self, source=None):
        """
        Initialize a PrimaryObject. 
        
        If source is None, both the ID and handle are assigned as empty 
        strings. If source is not None, then object is initialized from values 
        of the source object.

        :param source: Object used to initialize the new object
        :type source: PrimaryObject
        """
        TableObject.__init__(self, source)
        PrivacyBase.__init__(self, source)
        TagBase.__init__(self)
        if source:
            self.wearnow_id = source.wearnow_id
        else:
            self.wearnow_id = None

    def set_wearnow_id(self, wearnow_id):
        """
        Set the WearNow ID for the primary object.
        
        :param wearnow_id: WearNow ID
        :type wearnow_id: str
        """
        self.wearnow_id = wearnow_id

    def get_wearnow_id(self):
        """
        Return the WearNow ID for the primary object.

        :returns: WearNow ID associated with the object
        :rtype: str
        """
        return self.wearnow_id

    def has_handle_reference(self, classname, handle):
        """
        Return True if the object has reference to a given handle of given 
        primary object type.
        
        :param classname: The name of the primary object class.
        :type classname: str
        :param handle: The handle to be checked.
        :type handle: str

        :returns: 
          Returns whether the object has reference to this handle of 
          this object type.

        :rtype: bool
        """
        return False

    def remove_handle_references(self, classname, handle_list):
        """
        Remove all references in this object to object handles in the list.

        :param classname: The name of the primary object class.
        :type classname: str
        :param handle_list: The list of handles to be removed.
        :type handle_list: str
        """
        pass

    def replace_handle_reference(self, classname, old_handle, new_handle):
        """
        Replace all references to old handle with those to the new handle.

        :param classname: The name of the primary object class.
        :type classname: str
        :param old_handle: The handle to be replaced.
        :type old_handle: str
        :param new_handle: The handle to replace the old one with.
        :type new_handle: str
        """
        pass

    def has_media_reference(self, handle):
        """
        Indicate if the object has a media references. 
        
        In the base class, no such references exist. Derived classes should 
        override this if they provide media references.
        """
        return False

    def remove_media_references(self, handle_list):
        """
        Remove the specified media references from the object. 
        
        In the base class no such references exist. Derived classes should 
        override this if they provide media references.
        """
        pass

    def replace_media_references(self, old_handle, new_handle):
        pass

#-------------------------------------------------------------------------
#
# Primary Object class
#
#-------------------------------------------------------------------------
class PrimaryObject(BasicPrimaryObject):
    """
    The PrimaryObject is the base class for all primary objects in the
    database. 
    
    Primary objects are the core objects in the database.
    Each object has a database handle and a WearNow ID value. The database
    handle is used as the record number for the database, and the WearNow
    ID is the user visible version.
    """
    
    def __init__(self, source=None):
        """
        Initialize a PrimaryObject. 
        
        If source is None, both the ID and handle are assigned as empty 
        strings. If source is not None, then object is initialized from values 
        of the source object.

        :param source: Object used to initialize the new object
        :type source: PrimaryObject
        """
        BasicPrimaryObject.__init__(self, source)

    def has_handle_reference(self, classname, handle):
        """
        Return True if the object has reference to a given handle of given 
        primary object type.
        
        :param classname: The name of the primary object class.
        :type classname: str
        :param handle: The handle to be checked.
        :type handle: str
        :returns: Returns whether the object has reference to this handle 
                  of this object type.
        :rtype: bool
        """
        if classname == 'MediaObject' and isinstance(self, MediaBase):
            return self.has_media_reference(handle)
        else:
            return self._has_handle_reference(classname, handle)

    def remove_handle_references(self, classname, handle_list):
        """
        Remove all references in this object to object handles in the list.

        :param classname: The name of the primary object class.
        :type classname: str
        :param handle_list: The list of handles to be removed.
        :type handle_list: str
        """
        if classname == 'MediaObject' and isinstance(self, MediaBase):
            self.remove_media_references(handle_list)
        else:
            self._remove_handle_references(classname, handle_list)

    def replace_handle_reference(self, classname, old_handle, new_handle):
        """
        Replace all references to old handle with those to the new handle.

        :param classname: The name of the primary object class.
        :type classname: str
        :param old_handle: The handle to be replaced.
        :type old_handle: str
        :param new_handle: The handle to replace the old one with.
        :type new_handle: str
        """
        if classname == 'MediaObject' and isinstance(self, MediaBase):
            self.replace_media_references(old_handle, new_handle)
        else:
            self._replace_handle_reference(classname, old_handle, new_handle)

    def _has_handle_reference(self, classname, handle):
        """
        Return True if the handle is referenced by the object.
        """
        return False

    def _remove_handle_references(self, classname, handle_list):
        """
        Remove the handle references from the object.
        """
        pass

    def _replace_handle_reference(self, classname, old_handle, new_handle):
        """
        Replace the handle reference with the new reference.
        """
        pass
