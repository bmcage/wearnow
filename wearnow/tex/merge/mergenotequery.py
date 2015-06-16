#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2010  Michiel D. Nauta
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
Provide merge capabilities for notes.
"""

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from ..lib import (Textile, Ensemble, MediaObject)
from ..db.txn import DbTxn
from ..const import WEARNOW_LOCALE as glocale
_ = glocale.translation.sgettext
from ..errors import MergeError

#-------------------------------------------------------------------------
#
# MergeNoteQuery
#
#-------------------------------------------------------------------------
class MergeNoteQuery(object):
    """
    Create database query to merge two notes.
    """
    def __init__(self, dbstate, phoenix, titanic):
        self.database = dbstate.db
        self.phoenix = phoenix
        self.titanic = titanic

    def execute(self):
        """
        Merges two notes into a single note.
        """
        new_handle = self.phoenix.get_handle()
        old_handle = self.titanic.get_handle()
        self.phoenix.merge(self.titanic)
        with DbTxn(_("Merge Notes"), self.database) as trans:
            self.database.commit_note(self.phoenix, trans)
            for (class_name, handle) in self.database.find_backlink_handles(
                    old_handle):
                if class_name == Textile.__name__:
                    textile = self.database.get_textile_from_handle(handle)
                    assert(textile.has_note_reference(old_handle))
                    textile.replace_note_references(old_handle, new_handle)
                    self.database.commit_textile(textile, trans)
                elif class_name == Ensemble.__name__:
                    ensemble = self.database.get_ensemble_from_handle(handle)
                    assert(ensemble.has_note_reference(old_handle))
                    ensemble.replace_note_references(old_handle, new_handle)
                    self.database.commit_ensemble(ensemble, trans)
                elif class_name == MediaObject.__name__:
                    obj = self.database.get_object_from_handle(handle)
                    assert(obj.has_note_reference(old_handle))
                    obj.replace_note_references(old_handle, new_handle)
                    self.database.commit_media_object(obj, trans)
                else:
                    raise MergeError("Encounter object of type %s that has "
                            "a note reference." % class_name)
            self.database.remove_note(old_handle, trans)
