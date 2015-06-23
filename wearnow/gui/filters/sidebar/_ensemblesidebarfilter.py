#
# WearNow - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
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
# Python modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# gtk
#
#-------------------------------------------------------------------------
from gi.repository import Gtk

#-------------------------------------------------------------------------
#
# WearNow modules
#
#-------------------------------------------------------------------------
from ... import widgets
from wearnow.tex.lib import Ensemble
from .. import build_filter_model
from . import SidebarFilter
from wearnow.tex.filters import GenericFilterFactory, rules
from wearnow.tex.filters.rules.ensemble import (RegExpIdOf, RegExpChildName, 
                                             HasTag, 
                                             HasNoteRegexp, MatchesFilter)

GenericEnsembleFilter = GenericFilterFactory('Ensemble')
#-------------------------------------------------------------------------
#
# EnsembleSidebarFilter class
#
#-------------------------------------------------------------------------
class EnsembleSidebarFilter(SidebarFilter):

    def __init__(self, dbstate, uistate, clicked):
        self.clicked_func = clicked
        self.filter_id = widgets.BasicEntry()
        self.filter_child = widgets.BasicEntry()

        self.ensemble_stub = Ensemble()
                
        self.filter_note = widgets.BasicEntry()

        self.filter_regex = Gtk.CheckButton(label=_('Use regular expressions'))

        self.tag = Gtk.ComboBox()
        self.generic = Gtk.ComboBox()

        SidebarFilter.__init__(self, dbstate, uistate, "Ensemble")

    def create_widget(self):
        cell = Gtk.CellRendererText()
        cell.set_property('width', self._FILTER_WIDTH)
        cell.set_property('ellipsize', self._FILTER_ELLIPSIZE)
        self.generic.pack_start(cell, True)
        self.generic.add_attribute(cell, 'text', 0)
        self.on_filters_changed('Ensemble')

        cell = Gtk.CellRendererText()
        cell.set_property('width', self._FILTER_WIDTH)
        cell.set_property('ellipsize', self._FILTER_ELLIPSIZE)
        self.tag.pack_start(cell, True)
        self.tag.add_attribute(cell, 'text', 0)

        self.add_text_entry(_('ID'), self.filter_id)
        self.add_text_entry(_('Child'), self.filter_child)
        self.add_text_entry(_('Ensemble Note'), self.filter_note)
        self.add_entry(_('Tag'), self.tag)
        self.add_filter_entry(_('Custom filter'), self.generic)
        self.add_regex_entry(self.filter_regex)

    def clear(self, obj):
        self.filter_id.set_text('')
        self.filter_child.set_text('')
        self.filter_note.set_text('')
        self.tag.set_active(0)
        self.generic.set_active(0)

    def get_filter(self):
        gid = str(self.filter_id.get_text()).strip()
        child = str(self.filter_child.get_text()).strip()
        note = str(self.filter_note.get_text()).strip()
        regex = self.filter_regex.get_active()
        tag = self.tag.get_active() > 0
        generic = self.generic.get_active() > 0

        empty = not (gid or child or note or regex or tag or generic)
        if empty:
            generic_filter = None
        else:
            generic_filter = GenericEnsembleFilter()
            if gid:
                rule = RegExpIdOf([gid], use_regex=regex)
                generic_filter.add_rule(rule)

            if child:
                rule = RegExpChildName([child], use_regex=regex)
                generic_filter.add_rule(rule)

            if note:
                rule = HasNoteRegexp([note], use_regex=regex)
                generic_filter.add_rule(rule)

            # check the Tag
            if tag:
                model = self.tag.get_model()
                node = self.tag.get_active_iter()
                attr = model.get_value(node, 0)
                rule = HasTag([attr])
                generic_filter.add_rule(rule)

        if self.generic.get_active() != 0:
            model = self.generic.get_model()
            node = self.generic.get_active_iter()
            obj = str(model.get_value(node, 0))
            rule = MatchesFilter([obj])
            generic_filter.add_rule(rule)

        return generic_filter

    def on_filters_changed(self, name_space):
        if name_space == 'Ensemble':
            all_filter = GenericEnsembleFilter()
            all_filter.set_name(_("None"))
            all_filter.add_rule(rules.ensemble.AllFamilies([]))
            self.generic.set_model(build_filter_model('Ensemble', [all_filter]))
            self.generic.set_active(0)

    def on_tags_changed(self, tag_list):
        """
        Update the list of tags in the tag filter.
        """
        model = Gtk.ListStore(str)
        model.append(('',))
        for tag_name in tag_list:
            model.append((tag_name,))
        self.tag.set_model(model)
        self.tag.set_active(0)
