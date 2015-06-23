#
# wearnow - a GTK+/GNOME based program
#
# Copyright (C) 2003-2006  Donald N. Allingham
#               2009       Gary Burton
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
# internationalization
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# wearnow modules
#
#-------------------------------------------------------------------------
from ..views.treemodels import TextileListModel
from .baseselector import BaseSelector

#-------------------------------------------------------------------------
#
# SelectEvent
#
#-------------------------------------------------------------------------
class SelectTextile(BaseSelector):

    def __init__(self, dbstate, uistate, track=[], title=None, filter=None,
                 skip=set(), show_search_bar=False, default=None):

        # SelectTextile may have a title passed to it which should be used
        # instead of the default defined for get_window_title()
        if title is not None:
            self.title = title

        BaseSelector.__init__(self, dbstate, uistate, track, filter,
                              skip, show_search_bar, default)

    def _local_init(self):
        """
        Perform local initialisation for this class
        """
        self.width_key = 'interface.textile-sel-width'
        self.height_key = 'interface.textile-sel-height'
#        self.tree.connect('key-press-event', self._key_press)

    def get_window_title(self):
        return _("Select Textile")
        
    def get_model_class(self):
        return TextileListModel

    def get_column_titles(self):
        return [
            (_('Description'),         250, BaseSelector.TEXT,   0),
            (_('ID'),            75, BaseSelector.TEXT,   1),
            (_('Last Change'),  150, BaseSelector.TEXT,   14)
            ]

    def get_from_handle_func(self):
        return self.db.get_textile_from_handle
        
#    def exact_search(self):
#        """
#        Returns a tuple indicating columns requiring an exact search
#        """
#        return (,) 

#    def _on_row_activated(self, treeview, path, view_col):
#        store, paths = self.selection.get_selected_rows()
#        if paths and len(paths[0].get_indices()) == 2 :
#            self.window.response(Gtk.ResponseType.OK)
#
#    def _key_press(self, obj, event):
#        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
#            store, paths = self.selection.get_selected_rows()
#            if paths and len(paths[0].get_indices()) == 1 :
#                if self.tree.row_expanded(paths[0]):
#                    self.tree.collapse_row(paths[0])
#                else:
#                    self.tree.expand_row(paths[0], 0)
#                return True
#        return False
