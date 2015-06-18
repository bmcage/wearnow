#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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
Utilities for getting information from the database.
"""
#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".gui.utils.db")

#-------------------------------------------------------------------------
#
# modules
#
#-------------------------------------------------------------------------
from ..const import WEARNOW_LOCALE as glocale
_ = glocale.translation.sgettext

#-------------------------------------------------------------------------
#
# Fallback functions
#
#-------------------------------------------------------------------------


#-------------------------------------------------------------------------
#
# Function to return a label to display the active object in the status bar
# and to describe bookmarked objects.
#
#-------------------------------------------------------------------------
def navigation_label(db, nav_type, handle):

    label = None
    obj = None
    if nav_type == 'Textile':
        obj = db.get_textile_from_handle(handle)
        if obj:
            label = obj.description
    elif nav_type == 'Ensemble':
        obj = db.get_ensemble_from_handle(handle)
        if obj:
            label = "Ensemble "
    elif nav_type == 'Event':
        obj = db.get_event_from_handle(handle)
        if obj:
            desc = obj.get_description()
            label = obj.get_type()
            if desc:
                label = '%s - %s' % (label, desc)
    elif nav_type == 'Media' or nav_type == 'MediaObject':
        obj = db.get_object_from_handle(handle)
        if obj:
            label = obj.get_description()
    elif nav_type == 'Note':
        obj = db.get_note_from_handle(handle)
        if obj:
            label = obj.get()
            # When strings are cut, make sure they are unicode
            #otherwise you may end of with cutting within an utf-8 sequence
            label = str(label)
            label = " ".join(label.split())
            if len(label) > 40:
                label = label[:40] + "..."

    if label and obj:
        label = '[%s] %s' % (obj.get_wearnow_id(), label)

    return (label, obj)

#-------------------------------------------------------------------------
#
# Referents functions
#
#-------------------------------------------------------------------------
def get_referents(handle, db, primary_objects):
    """ Find objects that refer to an object.

    This function is the base for other get_<object>_referents functions.

    """
    # Use one pass through the reference map to grab all the references
    object_list = list(db.find_backlink_handles(handle))

    # Then form the object-specific lists
    the_lists = ()

    for primary in primary_objects:
        primary_list = [item[1] for item in object_list if item[0] == primary]
        the_lists = the_lists + (primary_list, )
    return the_lists

def get_media_referents(media_handle, db):
    """ Find objects that refer the media object.

    This function finds all primary objects that refer
    to a given media handle in a given database.

    """
    _primaries = ('Textile', 'Ensemble')

    return (get_referents(media_handle, db, _primaries))

def get_note_referents(note_handle, db):
    """ Find objects that refer a note object.

    This function finds all primary objects that refer
    to a given note handle in a given database.

    """
    _primaries = ('Textile', )

    return (get_referents(note_handle, db, _primaries))
