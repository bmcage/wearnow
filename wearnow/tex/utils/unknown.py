#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2009       Gary Burton
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
Make an 'Unknown' primary object
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import time
import os

#-------------------------------------------------------------------------
#
# WearNow modules
#
#-------------------------------------------------------------------------
from ..lib import (Textile, Ensemble, MediaObject, Note, NoteType,
                   StyledText, StyledTextTag, StyledTextTagType, Tag,
                   ChildRef)
from .id import create_id
from ..const import IMAGE_DIR
from ..const import WEARNOW_LOCALE as glocale
_ = glocale.translation.sgettext

#-------------------------------------------------------------------------
#
# make_unknown
#
#-------------------------------------------------------------------------
def make_unknown(class_arg, explanation, class_func, commit_func, transaction,
                 **argv):
    """
    Make a primary object and set some property so that it qualifies as
    "Unknown".

    Some object types need extra parameters:
    Family: db, Event: type (optional),
    Citation: methods to create/store source.

    Some theoretical underpinning
    This function exploits the fact that all import methods basically do the
    same thing: Create an object of the right type, fill it with some
    attributes, store it in the database. This function does the same, so
    the observation is why not use the creation and storage methods that the 
    import routines use themselves, that makes nice reuse of code. To do this
    formally correct we would need to specify a interface (in the OOP sence)
    which the import methods would need to implement. For now, that is deemed
    too restrictive and here we just slip through because of the similarity in
    code of both GEDCOM and XML import methods.

    :param class_arg: The argument the class_func needs, typically a kind of id.
    :type class_arg: unspecified
    :param explanation: Handle of a note that explains the origin of primary obj
    :type explanation: str
    :param class_func: Method to create primary object.
    :type class_func: method
    :param commit_func: Method to store primary object in db.
    :type commit_func: method
    :param transactino: Database transaction handle
    :type transaction: str
    :param argv: Possible additional parameters
    :type param: unspecified
    :returns: List of newly created objects.
    :rtype: list
    """
    retval = []
    obj = class_func(class_arg)
    if isinstance(obj, Textile):
        pass # nothing to indicate unknown
    elif isinstance(obj, Ensemble):
        pass # nothing to indicate unknown
    elif isinstance(obj, MediaObject):
        obj.set_path(os.path.join(IMAGE_DIR, "image-missing.png"))
        obj.set_mime_type('image/png')
        obj.set_description(_('Unknown'))
    elif isinstance(obj, Note):
        obj.set_type(NoteType.UNKNOWN);
        text = _('Unknown, created to replace a missing note object.')
        link_start = text.index(',') + 2
        link_end = len(text) - 1
        tag = StyledTextTag(StyledTextTagType.LINK,
                'wearnow://Note/handle/%s' % explanation,
                [(link_start, link_end)])
        obj.set_styledtext(StyledText(text, [tag]))
    elif isinstance(obj, Tag):
        if not hasattr(make_unknown, 'count'):
            make_unknown.count = 1 #primitive static variable
        obj.set_name(_("Unknown, was missing %(time)s (%(count)d)") % {
                'time': time.strftime('%x %X', time.localtime()),
                'count': make_unknown.count})
        make_unknown.count += 1
    else:
        raise TypeError("Object if of unsupported type")

    if hasattr(obj, 'add_note'):
        obj.add_note(explanation)
    commit_func(obj, transaction, time.time())
    retval.append(obj)
    return retval

def create_explanation_note(dbase):
    """
    When creating objects to fill missing primary objects in imported files,
    those objects of type "Unknown" need a explanatory note. This funcion
    provides such a note for import methods.
    """
    note = Note( _('Objects referenced by this note '
                                    'were missing in a file imported on %s.') %
                                    time.strftime('%x %X', time.localtime()))
    note.set_handle(create_id())
    note.set_wearnow_id(dbase.find_next_note_wearnow_id())
    # Use defaults for privacy, format and type.
    return note
