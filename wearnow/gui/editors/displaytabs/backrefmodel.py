#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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

#-------------------------------------------------------------------------
#
# GTK libraries
#
#-------------------------------------------------------------------------
from gi.repository import Gtk
from gi.repository import GLib

from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# WEARNOW classes
#
#-------------------------------------------------------------------------
#-------------------------------------------------------------------------
#
# BackRefModel
#
#-------------------------------------------------------------------------
class BackRefModel(Gtk.ListStore):
    
    dispstr = _('%(part1)s - %(part2)s')

    def __init__(self, sref_list, db):
        Gtk.ListStore.__init__(self, str, str, str, str, str)
        self.db = db
        self.sref_list = sref_list
        self.count = 0
        self.loading = False
        self.idle = GLib.idle_add(self.load_model().__next__)

    def destroy(self):
        if self.loading:
            GLib.source_remove(self.idle)

    def load_model(self):
        """
        Objects can have very large backreferences. To avoid blocking the 
        interface up to the moment that the model is created, this method is 
        called via GLib.idle_add.
        WARNING: a consequence of above is that loading can still be happening
            while the GUI using this model is no longer used. Disconnect any
            methods before closing the GUI.
        """
        self.loading = True
        self.count = 0
        for ref in self.sref_list:
            self.count += 1
            dtype = ref[0]
            if dtype == 'Textile':
                p = self.db.get_textile_from_handle(ref[1])
                if not p:
                    continue
                gid = p.gramps_id
                handle = p.handle
                name = p.name
            elif dtype == 'Ensemble':
                p = self.db.get_family_from_handle(ref[1])
                if not p:
                    continue
                gid = p.gramps_id
                handle = p.handle
                name = p.name
            else:
                p = self.db.get_object_from_handle(ref[1])
                if not p:
                    continue
                name = p.get_description()
                gid = p.gramps_id
                handle = p.handle

            # dtype is the class name, i.e. is English
            # We need to use localized string in the model.
            # we also need to keep class names to get the object type,
            # but we don't need to show that in the view.
            self.append(row=[_(dtype), gid, name, handle, dtype])
            yield True
        self.loading = False
        yield False
