#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2010       Nick Hall
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
# python modules
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".")

#-------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk

#-------------------------------------------------------------------------
#
# WearNow modules
#
#-------------------------------------------------------------------------
from wearnow.tex.datehandler import format_time
from .flatbasemodel import FlatBaseModel
from wearnow.tex.config import config
from wearnow.tex.const import WEARNOW_LOCALE as glocale

#-------------------------------------------------------------------------
#
# EnsembleModel
#
#-------------------------------------------------------------------------
class EnsembleModel(FlatBaseModel):

    def __init__(self, db, scol=0, order=Gtk.SortType.ASCENDING, search=None, 
                 skip=set(), sort_map=None):
        self.gen_cursor = db.get_ensemble_cursor
        self.map = db.get_raw_ensemble_data
        self.fmap = [
            self.column_id,
            self.column_private,
            self.column_tags,
            self.column_change, 
            self.column_tag_color,
            ]
        self.smap = [
            self.column_id, 
            self.column_private,
            self.column_tags,
            self.sort_change, 
            self.column_tag_color,
            ]
        FlatBaseModel.__init__(self, db, scol, order, search=search, skip=skip,
                               sort_map=sort_map)

    def destroy(self):
        """
        Unset all elements that can prevent garbage collection
        """
        self.db = None
        self.gen_cursor = None
        self.map = None
        self.fmap = None
        self.smap = None
        FlatBaseModel.destroy(self)

    def color_column(self):
        """
        Return the color column.
        """
        return 4

    def on_get_n_columns(self):
        return len(self.fmap)+1

    def column_id(self, data):
        return str(data[1])

    def column_private(self, data):
        if data[7]:
            return 'wearnow-lock'
        else:
            # There is a problem returning None here.
            return ''

    def sort_change(self, data):
        return "%012x" % data[5]
    
    def column_change(self, data):
        return format_time(data[5])

    def get_tag_name(self, tag_handle):
        """
        Return the tag name from the given tag handle.
        """
        return self.db.get_tag_from_handle(tag_handle).get_name()
        
    def column_tag_color(self, data):
        """
        Return the tag color.
        """
        tag_color = "#000000000000"
        tag_priority = None
        for handle in data[6]:
            tag = self.db.get_tag_from_handle(handle)
            this_priority = tag.get_priority()
            if tag_priority is None or this_priority < tag_priority:
                tag_color = tag.get_color()
                tag_priority = this_priority
        return tag_color

    def column_tags(self, data):
        """
        Return the sorted list of tags.
        """
        tag_list = list(map(self.get_tag_name, data[13]))
        return ', '.join(sorted(tag_list, key=glocale.sort_key))
