#
# WearNow - a GTK+/GNOME based genealogy program
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

"""
Custom Filter Editor tool.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
log = logging.getLogger(".filtereditor")

#-------------------------------------------------------------------------
#
# GTK/GNOME 
#
#-------------------------------------------------------------------------
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

#-------------------------------------------------------------------------
#
# WEARNOW modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.sgettext
from wearnow.tex.filters import (GenericFilterFactory, FilterList, 
                                reload_custom_filters)
from wearnow.tex.filters.rules._matchesfilterbase import MatchesFilterBase
from ..listmodel import ListModel
from ..managedwindow import ManagedWindow
from ..dialog import QuestionDialog
from wearnow.tex.const import RULE_GLADE, URL_HOMEPAGE
from ..display import display_help
from wearnow.tex.errors import WindowActiveError
from wearnow.tex.lib import (AttributeType, NoteType)
from wearnow.tex.filters import rules
from ..autocomp import StandardCustomSelector
from ..selectors import SelectorFactory

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = WIKI_HELP_PAGE = '%s_-_Filters' % URL_HOMEPAGE

# dictionary mapping FILTER_TYPE of views to Filter window name
_TITLES = {
            'Textile' : _("Textile Filters"),
            'Ensemble' : _('Ensemble Filters'),
            'Media' : _('Media Filters'),
            'Note' : _('Note Filters'),
}

_name2typeclass = {
    _('Textile attribute:') : AttributeType,
    _('Note type:')          : NoteType,
}

#-------------------------------------------------------------------------
#
# MyBoolean - check button with standard interface
#
#-------------------------------------------------------------------------
class MyBoolean(Gtk.CheckButton):

    def __init__(self, label=None):
        GObject.GObject.__init__(self)
        self.set_label(label)
        self.show()

    def get_text(self):
        """
        Return the text to save. 
        
        It should be the same no matter the present locale (English or numeric 
        types).
        This class sets this to get_display_text, but when localization
        is an issue (events/attr/etc types) then it has to be overridden.
        
        """
        return str(int(self.get_active()))

    def set_text(self, val):
        """
        Set the selector state to display the passed value.
        """
        is_active = bool(int(val))
        self.set_active(is_active)

#-------------------------------------------------------------------------
#
# MyInteger - spin button with standard interface
#
#-------------------------------------------------------------------------
class MyInteger(Gtk.SpinButton):

    def __init__(self, min, max):
        GObject.GObject.__init__(self)
        self.set_adjustment(Gtk.Adjustment(min, min, max, 1))
        self.show()

    def get_text(self):
        return str(self.get_value_as_int())

    def set_text(self, val):
        self.set_value(int(val))

#-------------------------------------------------------------------------
#
# MyFilters - Combo box with list of filters with a standard interface
#
#-------------------------------------------------------------------------
class MyFilters(Gtk.ComboBox):
    """
    Class to present a combobox of selectable filters.
    """
    def __init__(self, filters, filter_name=None):
        """
        Construct the combobox from the entries of the filters list.
        
        Filter_name is name of calling filter.
        If filter_name is given, it will be excluded from the dropdown box.
        
        """
        GObject.GObject.__init__(self)
        store = Gtk.ListStore(GObject.TYPE_STRING)
        self.set_model(store)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        #remove own name from the list if given.
        self.flist = sorted(f.get_name() for f in filters
            if filter_name is None or f.get_name() != filter_name
            )

        for fname in self.flist:
            store.append(row=[fname])
        self.set_active(0)
        self.show()
        
    def get_text(self):
        active = self.get_active()
        if active < 0:
            return ""
        return self.flist[active]

    def set_text(self, val):
        if val in self.flist:
            self.set_active(self.flist.index(val))

#-------------------------------------------------------------------------
#
# MyList - Combo box to allow entries
#
#-------------------------------------------------------------------------
class MyList(Gtk.ComboBox):
 
    def __init__(self, clist, clist_trans, default=0):
        GObject.GObject.__init__(self)
        store = Gtk.ListStore(GObject.TYPE_STRING)
        self.set_model(store)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        self.clist = clist
        for name in clist_trans:
            store.append(row=[name])
        self.set_active(default)
        self.show()
    
    def get_text(self):
        active = self.get_active()
        return self.clist[active]

    def set_text(self, val):
        if val in self.clist:
            self.set_active(self.clist.index(val))

#-------------------------------------------------------------------------
#
# MyLesserEqualGreater - Combo box to allow selection of "<", "=", or ">"
#
#-------------------------------------------------------------------------
class MyLesserEqualGreater(Gtk.ComboBox):

    def __init__(self, default=0):
        GObject.GObject.__init__(self)
        store = Gtk.ListStore(GObject.TYPE_STRING)
        self.set_model(store)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)
        self.clist = ['lesser than', 'equal to', 'greater than']
        self.clist_trans = [_('lesser than'), _('equal to'), _('greater than')]
        for name in self.clist_trans:
            store.append(row=[name])
        self.set_active(default)
        self.show()

    def get_text(self):
        active = self.get_active()
        if active < 0:
            return 'equal to'
        return self.clist[active]

    def set_text(self, val):
        if val in self.clist:
            self.set_active(self.clist.index(val))
        else:
            self.set_active(self.clist.index('equal to'))

#-------------------------------------------------------------------------
#
# MyID - Textile/WEARNOW ID selection box with a standard interface
#
#-------------------------------------------------------------------------
class MyID(Gtk.Box):
    _invalid_id_txt = _('Not a valid ID')
    _empty_id_txt  = _invalid_id_txt

    obj_name = {
        'Textile' : _('Textile'),
        'Ensemble' : _('Ensemble'),
        'Media'  : _('Media'),
        'Note'   : _('Note'),
        }
    
    def __init__(self, dbstate, uistate, track, namespace='Textile'):
        GObject.GObject.__init__(self)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_homogeneous(False)
        self.set_spacing(6)
        self.dbstate = dbstate
        self.db = dbstate.db
        self.uistate = uistate
        self.track = track
        
        self.namespace = namespace
        self.entry = Gtk.Entry()
        self.entry.show()
        self.button = Gtk.Button()
        self.button.set_label(_('Select...'))
        self.button.connect('clicked', self.button_press)
        self.button.show()
        self.pack_start(self.entry, True, True, 0)
        self.add(self.button)
        self.button.set_tooltip_text(_('Select %s from a list')
                              % self.obj_name[namespace])
        self.show()
        self.set_text('')

    def button_press(self, obj):
        obj_class = self.namespace
        selector = SelectorFactory(obj_class)
        inst = selector(self.dbstate, self.uistate, self.track)
        val = inst.run()
        if val is None:
            self.set_text('')
        else:
            self.set_text(val.get_wearnow_id())
        
    def get_text(self):
        return str(self.entry.get_text())

    def name_from_wearnow_id(self, wearnow_id):
        if self.namespace == 'Textile':
            textile = self.db.get_textile_from_wearnow_id(wearnow_id)
            name = textile.description
        elif self.namespace == 'Ensemble':
            ensemble = self.db.get_ensemble_from_wearnow_id(wearnow_id)
            name = ensemble.name
        elif self.namespace == 'Media':
            obj = self.db.get_object_from_wearnow_id(wearnow_id)
            name = obj.get_path()
        elif self.namespace == 'Note':
            note = self.db.get_note_from_wearnow_id(wearnow_id)
            name = note.get()
        return name

    def set_text(self, val):
        if not val:
            self.entry.set_tooltip_text(self._empty_id_txt)
        else:
            try:
                name = self.name_from_wearnow_id(val)
                self.entry.set_tooltip_text(name)
            except AttributeError:
                self.entry.set_tooltip_text(self._invalid_id_txt)
        self.entry.set_text(val)

#-------------------------------------------------------------------------
#
# MySelect
#
#-------------------------------------------------------------------------
class MySelect(Gtk.ComboBox):
    
    def __init__(self, type_class, additional):
        #we need to inherit and have an combobox with an entry
        Gtk.ComboBox.__init__(self, has_entry=True)
        self.type_class = type_class
        self.sel = StandardCustomSelector(type_class._I2SMAP, self,
                                          type_class._CUSTOM,
                                          type_class._DEFAULT,
                                          additional,
                                          type_class._MENU)
        self.show()
        
    def get_text(self):
        return self.type_class(self.sel.get_values()).xml_str()

    def set_text(self, val):
        tc = self.type_class()
        tc.set_from_xml_str(val)
        self.sel.set_values((int(tc), str(tc)))

#-------------------------------------------------------------------------
#
# MyEntry
#
#-------------------------------------------------------------------------
class MyEntry(Gtk.Entry):
    
    def __init__(self):
        GObject.GObject.__init__(self)
        self.show()
        
#-------------------------------------------------------------------------
#
# EditRule
#
#-------------------------------------------------------------------------
class EditRule(ManagedWindow):
    def __init__(self, namespace, dbstate, uistate, track, filterdb, val,
                 label, update, filter_name):
        ManagedWindow.__init__(self, uistate, track, EditRule)
        self.width_key = "interface.edit-rule-width"
        self.height_key = "interface.edit-rule-height"
        self.namespace = namespace
        self.dbstate = dbstate
        self.db = dbstate.db
        self.filterdb = filterdb
        self.update_rule = update
        self.filter_name = filter_name

        self.active_rule = val
        self.define_glade('rule_editor', RULE_GLADE)
        
        self.set_window(self.get_widget('rule_editor'),
                        self.get_widget('rule_editor_title'),label)
        self.window.hide()
        self.valuebox = self.get_widget('valuebox')
        self.rname = self.get_widget('ruletree')
        self.rule_name = self.get_widget('rulename')

        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(0)
        self.notebook.set_show_border(0)
        self.notebook.show()
        self.valuebox.pack_start(self.notebook, True, True, 0)
        self.page_num = 0
        self.page = []
        self.class2page = {}
        the_map = {}

        if self.namespace == 'Textile':
            class_list = rules.textile.editor_rule_list
        elif self.namespace == 'Ensemble':
            class_list = rules.ensemble.editor_rule_list
        elif self.namespace == 'Media':
            class_list = rules.media.editor_rule_list
        elif self.namespace == 'Note':
            class_list = rules.note.editor_rule_list
        
        for class_obj in class_list:
            arglist = class_obj.labels
            vallist = []
            tlist = []
            pos = 0
            l2 = Gtk.Label(label=class_obj.name, halign=Gtk.Align.START)
            l2.show()
            c = Gtk.TreeView()
            #c.set_data('d', pos)
            c.show()
            the_map[class_obj] = c
            grid = Gtk.Grid()
            grid.set_border_width(12)
            grid.set_column_spacing(6)
            grid.set_row_spacing(6)
            grid.show()
            for v in arglist:
                l = Gtk.Label(label=v, halign=Gtk.Align.END)
                l.show()
                if v in [_('Reference count:'),
                            _('Number of instances:')
                            ]:
                    t = MyInteger(0, 999)
                elif v == _('Reference count must be:'):
                    t = MyLesserEqualGreater()
                elif v == _('Number must be:'):
                    t = MyLesserEqualGreater(2)
                elif v == _('ID:'):
                    t = MyID(self.dbstate, self.uistate, self.track, 
                             self.namespace)
                elif v == _('Filter name:'):
                    t = MyFilters(self.filterdb.get_filters(self.namespace),
                                  self.filter_name)
                # filters of another namespace, name may be same as caller!
                elif v == _('Textile filter name:'):
                    t = MyFilters(self.filterdb.get_filters('Textile'))
                elif v in _name2typeclass:
                    additional = None
                    if v == _('Textile attribute:'):
                        additional = self.db.get_textile_attribute_types()
                    elif v == _('Note type:'):
                        additional = self.db.get_note_types()
                    t = MySelect(_name2typeclass[v], additional)
                elif v == _('Inclusive:'):
                    t = MyBoolean(_('Include original textile'))
                elif v == _('Case sensitive:'):
                    t = MyBoolean(_('Use exact case of letters'))
                elif v == _('Regular-Expression matching:'):
                    t = MyBoolean(_('Use regular expression'))
                elif v == _('Tag:'):
                    taglist = ['']
                    taglist = taglist + [tag.get_name() for tag in dbstate.db.iter_tags()]
                    t = MyList(taglist, taglist)
                else:                    
                    t = MyEntry()
                t.set_hexpand(True)
                tlist.append(t)
                grid.attach(l, 0, pos, 1, 1)
                grid.attach(t, 1, pos, 1, 1)
                pos += 1

            use_regex = None
            if class_obj.allow_regex:
                use_regex = Gtk.CheckButton(label=_('Use regular expressions'))
                tip = _('Interpret the contents of string fields as regular '
                        'expressions.\n'
                        'A decimal point will match any character. '
                        'A question mark will match zero or one occurences '
                        'of the previous character or group. '
                        'An asterisk will match zero or more occurences. '
                        'A plus sign will match one or more occurences. '
                        'Use parentheses to group expressions. '
                        'Specify alternatives using a vertical bar. '
                        'A caret will match the start of a line. '
                        'A dollar sign will match the end of a line.')
                use_regex.set_tooltip_text(tip)
                grid.attach(use_regex, 1, pos, 1, 1)

            self.page.append((class_obj, vallist, tlist, use_regex))

            # put the grid into a scrollable area:
            scrolled_win = Gtk.ScrolledWindow()
            scrolled_win.add(grid)
            scrolled_win.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled_win.show()
            self.notebook.append_page(scrolled_win, Gtk.Label(label=class_obj.name))
            self.class2page[class_obj] = self.page_num
            self.page_num = self.page_num + 1
        self.page_num = 0
        self.store = Gtk.TreeStore(GObject.TYPE_STRING, GObject.TYPE_PYOBJECT)
        self.selection = self.rname.get_selection()
        col = Gtk.TreeViewColumn(_('Rule Name'), Gtk.CellRendererText(), 
                                 text=0)
        self.rname.append_column(col)
        self.rname.set_model(self.store)

        prev = None
        last_top = None

        top_level = {}
        top_node = {}

        #
        # If editing a rule, get the name so that we can select it later
        #
        sel_node = None
        if self.active_rule is not None:
            self.sel_class = self.active_rule.__class__
        else:
            self.sel_class = None

        keys = sorted(the_map, key=lambda x: x.name, reverse=True)
        catlist = sorted(set(class_obj.category for class_obj in keys))

        for category in catlist:
            top_node[category] = self.store.insert_after(None, last_top)
            top_level[category] = []
            last_top = top_node[category]
            self.store.set(last_top, 0, category, 1, '')

        for class_obj in keys:
            category = class_obj.category
            top_level[category].append(class_obj.name)
            node = self.store.insert_after(top_node[category], prev)
            self.store.set(node, 0, class_obj.name, 1, class_obj)

            # if this is an edit rule, save the node
            if class_obj == self.sel_class:
                sel_node = (top_node[category], node)

        if sel_node:
            self.select_iter(sel_node)
            page = self.class2page[self.active_rule.__class__]
            self.notebook.set_current_page(page)
            self.display_values(self.active_rule.__class__)
            (class_obj, vallist, tlist, use_regex) = self.page[page]
            r = list(self.active_rule.values())
            for i in range(0, min(len(tlist), len(r))):
                tlist[i].set_text(r[i])
            if class_obj.allow_regex:
                use_regex.set_active(self.active_rule.use_regex)
            
        self.selection.connect('changed', self.on_node_selected)
        self.rname.connect('button-press-event', self._button_press)
        self.rname.connect('key-press-event', self._key_press)
        self.get_widget('rule_editor_ok').connect('clicked', self.rule_ok)
        self.get_widget('rule_editor_cancel').connect('clicked', self.close_window)
        self.get_widget('rule_editor_help').connect('clicked', self.on_help_clicked)

        self._set_size()
        self.show()

    def select_iter(self, data):
        """
        Workaround to get self.selection to move to iter row.
        self.selection.select_iter(iter) did not work, so we first
        select the top_node iter, expand it, and then select_iter.
        """
        top_node, iter = data
        self.selection.select_iter(top_node)
        self.expand_collapse()
        self.selection.select_iter(iter)

    def _button_press(self, obj, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS and event.button == 1:
            return self.expand_collapse()

    def _key_press(self, obj, event):
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            return self.expand_collapse()
        return False    
    
    def expand_collapse(self):
        """
        Expand or collapse the selected parent name node.
        Return True if change done, False otherwise
        """
        store, paths = self.selection.get_selected_rows()
        if paths and len(paths[0].get_indices()) == 1 :
            if self.rname.row_expanded(paths[0]):
                self.rname.collapse_row(paths[0])
            else:
                self.rname.expand_row(paths[0], 0)
            return True
        return False

    def on_help_clicked(self, obj):
        """
        Display the relevant portion of WearNow manual.
        """
        display_help()

    def close_window(self, obj):
        self.close()

    def on_node_selected(self, obj):
        """
        Update the informational display on the right hand side of the dialog 
        box with the description of the selected report.
        """

        store, node = self.selection.get_selected()
        if node:
            try:
                class_obj = store.get_value(node, 1)
                self.display_values(class_obj)
            except:
                self.valuebox.set_sensitive(0)
                self.rule_name.set_text(_('No rule selected'))
                self.get_widget('description').set_text('')

    def display_values(self, class_obj):
        page = self.class2page[class_obj]
        self.notebook.set_current_page(page)
        self.valuebox.set_sensitive(1)
        self.rule_name.set_text(class_obj.name)
        self.get_widget('description').set_text(class_obj.description)

    def rule_ok(self, obj):
        if self.rule_name.get_text() == _('No rule selected'):
            return

        try:
            page = self.notebook.get_current_page()
            (class_obj, vallist, tlist, use_regex) = self.page[page]
            value_list = [str(sclass.get_text()) for sclass in tlist]
            if class_obj.allow_regex:
                new_rule = class_obj(value_list, use_regex.get_active())
            else:
                new_rule = class_obj(value_list)

            self.update_rule(self.active_rule, new_rule)
            self.close()
        except KeyError:
            pass

#-------------------------------------------------------------------------
#
# EditFilter
#
#-------------------------------------------------------------------------
class EditFilter(ManagedWindow):
    
    def __init__(self, namespace, dbstate, uistate, track, gfilter,
                 filterdb, update=None, selection_callback=None):

        ManagedWindow.__init__(self, uistate, track, self)
        self.width_key = "interface.edit-filter-width"
        self.height_key = "interface.edit-filter-height"
        self.namespace = namespace
        self.update = update
        self.dbstate = dbstate
        self.db = dbstate.db
        self.filter = gfilter
        self.filterdb = filterdb
        self.selection_callback = selection_callback
        
        self.define_glade('define_filter', RULE_GLADE)
        
        self.set_window(
            self.get_widget('define_filter'),
            self.get_widget('definition_title'),
            _('Define filter'))
        
        self.rlist = ListModel(
            self.get_widget('rule_list'),
            [(_('Name'),-1,150),(_('Values'),-1,150)],
            self.select_row,
            self.on_edit_clicked)
                                         
        self.fname = self.get_widget('filter_name')
        self.logical = self.get_widget('rule_apply')
        self.logical_not = self.get_widget('logical_not')
        self.comment = self.get_widget('comment')
        self.ok_btn = self.get_widget('definition_ok')
        self.edit_btn = self.get_widget('definition_edit')
        self.del_btn = self.get_widget('definition_delete')
        self.add_btn = self.get_widget('definition_add')

        self.ok_btn.connect('clicked', self.on_ok_clicked)
        self.edit_btn.connect('clicked', self.on_edit_clicked)
        self.del_btn.connect('clicked', self.on_delete_clicked)
        self.add_btn.connect('clicked', self.on_add_clicked)
        
        self.get_widget('definition_help').connect('clicked',
                                        self.on_help_clicked)
        self.get_widget('definition_cancel').connect('clicked',
                                          self.close_window)
        self.fname.connect('changed', self.filter_name_changed)

        op = self.filter.get_logical_op()
        # WARNING: must be listed in this order:
        self.logical.set_active(["and", "or", "one", "sequence"].index(op))
        self.logical_not.set_active(self.filter.get_invert())
        if self.filter.get_name():
            self.fname.set_text(self.filter.get_name())
        self.comment.set_text(self.filter.get_comment())
        self.draw_rules()

        self._set_size()
        self.show()

    def on_help_clicked(self, obj):
        """Display the relevant portion of WearNow manual"""
        display_help(webpage=WIKI_HELP_PAGE)

    def close_window(self, obj):
        self.close()

    def filter_name_changed(self, obj):
        name = str(self.fname.get_text())
        # Make sure that the name is not empty
        # and not in the list of existing filters (excluding this one)
        names = [filt.get_name()
                 for filt in self.filterdb.get_filters(self.namespace)
                 if filt != self.filter]
        self.ok_btn.set_sensitive((len(name) != 0) and (name not in names))
    
    def select_row(self, obj):
        store, node = self.rlist.get_selected()
        if node:
            self.edit_btn.set_sensitive(True)
            self.del_btn.set_sensitive(True)
        else:
            self.edit_btn.set_sensitive(False)
            self.del_btn.set_sensitive(False)

    def draw_rules(self):
        self.rlist.clear()
        for r in self.filter.get_rules():
            self.rlist.add([r.name,r.display_values()],r)
            
    def on_ok_clicked(self, obj):
        n = str(self.fname.get_text()).strip()
        if n == '':
            return
        if n != self.filter.get_name():
            self.uistate.emit('filter-name-changed',
                        (self.namespace, str(self.filter.get_name()), n))
        self.filter.set_name(n)
        self.filter.set_comment(str(self.comment.get_text()).strip())
        for f in self.filterdb.get_filters(self.namespace)[:]:
            if n == f.get_name():
                self.filterdb.get_filters(self.namespace).remove(f)
                break
        val = self.logical.get_active()
        # WARNING: must be listed in this order:
        op = ('and' if val == 0 else 
              'or' if val == 1 else 
              'one' if val == 2 else 
              'sequence')
        self.logical.set_active(val)
        self.filter.set_logical_op(op)
        self.filter.set_invert(self.logical_not.get_active())
        self.filterdb.add(self.namespace,self.filter)
        if self.update:
            self.update()
        if self.selection_callback:
            self.selection_callback(self.filterdb, self.filter.get_name())
        self.close()
        
    def on_add_clicked(self, obj):
        try:
            EditRule(self.namespace, self.dbstate, self.uistate, self.track,
                     self.filterdb, None, _('Add Rule'), self.update_rule,
                     self.filter.get_name())
        except WindowActiveError:
            pass

    def on_edit_clicked(self, obj):
        store, node = self.rlist.get_selected()
        if node:
            d = self.rlist.get_object(node)

            try:
                EditRule(self.namespace, self.dbstate, self.uistate, self.track,
                         self.filterdb, d, _('Edit Rule'), self.update_rule,
                         self.filter.get_name())
            except WindowActiveError:
                pass

    def update_rule(self, old_rule, new_rule):
        if old_rule is not None:
            self.filter.delete_rule(old_rule)
        self.filter.add_rule(new_rule)
        self.draw_rules()

    def on_delete_clicked(self, obj):
        store, node = self.rlist.get_selected()
        if node:
            gfilter = self.rlist.get_object(node)
            self.filter.delete_rule(gfilter)
            self.draw_rules()
            
#-------------------------------------------------------------------------
#
# ShowResults
#
#-------------------------------------------------------------------------
class ShowResults(ManagedWindow):
    def __init__(self, db, uistate, track, handle_list, filtname, namespace):

        ManagedWindow.__init__(self, uistate, track, self)

        self.db = db
        self.filtname = filtname
        self.namespace = namespace
        self.define_glade('test', RULE_GLADE,)
        self.set_window(
            self.get_widget('test'),
            self.get_widget('test_title'),
            _('Filter Test'))

        render = Gtk.CellRendererText()
        
        tree = self.get_widget('list')
        model = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)
        tree.set_model(model)

        column_n = Gtk.TreeViewColumn(_('Name'), render, text=0)
        tree.append_column(column_n)

        column_n = Gtk.TreeViewColumn(_('ID'), render, text=1)
        tree.append_column(column_n)

        self.get_widget('test_close').connect('clicked', self.close)

        new_list = sorted(
                        (self.sort_val_from_handle(h) for h in handle_list),
                        key=lambda x: glocale.sort_key(x[0])
                        )

        for s_, handle in new_list:
            name, gid = self.get_name_id(handle)
            model.append(row=[name, gid])

        self.show()

    def get_name_id(self, handle):
        if self.namespace == 'Textile':
            textile = self.db.get_textile_from_handle(handle)
            name = textile.description
            gid = textile.get_wearnow_id()
        elif self.namespace == 'Ensemble':
            ensemble = self.db.get_ensemble_from_handle(handle)
            name = ensemble.name
            gid = ensemble.get_wearnow_id()
        elif self.namespace == 'Media':
            obj = self.db.get_object_from_handle(handle)
            name = obj.get_description()
            gid = obj.get_wearnow_id()
        elif self.namespace == 'Note':
            note = self.db.get_note_from_handle(handle)
            name = note.get().replace('\n', ' ')
            if len(name) > 80:
                name = name[:80]+"..."
            gid = note.get_wearnow_id()
        return (name, gid)
        
    def sort_val_from_handle(self, handle):
        if self.namespace == 'Textile':
            sortname = self.db.get_textile_from_handle(handle).name
        elif self.namespace == 'Ensemble':
            sortname = self.db.get_ensemble_from_handle(handle).name
        elif self.namespace == 'Media':
            sortname = self.db.get_object_from_handle(handle).get_description()
        elif self.namespace == 'Note':
            gid = self.db.get_note_from_handle(handle).get_wearnow_id()
            sortname = gid
        return (sortname, handle)

#-------------------------------------------------------------------------
#
# FilterEditor
#
#-------------------------------------------------------------------------
class FilterEditor(ManagedWindow):
    def __init__(self, namespace, filterdb, dbstate, uistate):

        ManagedWindow.__init__(self, uistate, [], FilterEditor)
        self.dbstate = dbstate
        self.db = dbstate.db
        self.filterdb = FilterList(filterdb)
        self.filterdb.load()
        self.width_key = "interface.filter-editor-width"
        self.height_key = "interface.filter-editor-height"
        self.namespace = namespace

        self.define_glade('filter_list', RULE_GLADE)
        self.filter_list = self.get_widget('filters')
        self.edit = self.get_widget('filter_list_edit')
        self.clone = self.get_widget('filter_list_clone')
        self.delete = self.get_widget('filter_list_delete')
        self.test = self.get_widget('filter_list_test')

        self.edit.set_sensitive(False)
        self.clone.set_sensitive(False)
        self.delete.set_sensitive(False)
        self.test.set_sensitive(False)

        self.set_window(self.get_widget('filter_list'),
                        self.get_widget('filter_list_title'),
                        _TITLES[self.namespace]) 

        self.edit.connect('clicked', self.edit_filter)
        self.clone.connect('clicked', self.clone_filter)
        self.test.connect('clicked', self.test_clicked)
        self.delete.connect('clicked', self.delete_filter)

        self.connect_button('filter_list_help', self.help_clicked)
        self.connect_button('filter_list_close', self.close)
        self.connect_button('filter_list_add', self.add_new_filter)
        
        self.uistate.connect('filter-name-changed', self.clean_after_rename)

        self.clist = ListModel(
                            self.filter_list,
                            [(_('Filter'), 0, 150), (_('Comment'), 1, 150)],
                            self.filter_select_row,
                            self.edit_filter)
        self.draw_filters()
        self._set_size()
        self.show()

    def build_menu_names(self, obj):
        return (_("Custom Filter Editor"), _("Custom Filter Editor"))
        
    def help_clicked(self, obj):
        """Display the relevant portion of WearNow manual"""
        display_help()

    def filter_select_row(self, obj):
        store, node = self.clist.get_selected()
        if node:
            self.edit.set_sensitive(True)
            self.clone.set_sensitive(True)
            self.delete.set_sensitive(True)
            self.test.set_sensitive(True)
        else:
            self.edit.set_sensitive(False)
            self.clone.set_sensitive(False)
            self.delete.set_sensitive(False)
            self.test.set_sensitive(False)
    
    def close(self, *obj):
        self.filterdb.save()
        reload_custom_filters()
        #reload_system_filters()
        self.uistate.emit('filters-changed', (self.namespace,))
        ManagedWindow.close(self, *obj)
        
    def draw_filters(self):
        self.clist.clear()
        for f in self.filterdb.get_filters(self.namespace):
            self.clist.add([f.get_name(), f.get_comment()], f)

    def add_new_filter(self, obj):
        the_filter = GenericFilterFactory(self.namespace)()
        EditFilter(self.namespace, self.dbstate, self.uistate, self.track,
                   the_filter, self.filterdb, self.draw_filters)

    def edit_filter(self, obj):
        store, node = self.clist.get_selected()
        if node:
            gfilter = self.clist.get_object(node)
            EditFilter(self.namespace, self.dbstate, self.uistate, self.track,
                       gfilter, self.filterdb, self.draw_filters)

    def clone_filter(self, obj):
        store, node = self.clist.get_selected()
        if node:
            old_filter = self.clist.get_object(node)
            the_filter = GenericFilterFactory(self.namespace)(old_filter)
            the_filter.set_name('')
            EditFilter(self.namespace, self.dbstate, self.uistate, self.track,
                       the_filter, self.filterdb, self.draw_filters)

    def test_clicked(self, obj):
        store, node = self.clist.get_selected()
        if node:
            filt = self.clist.get_object(node)
            handle_list = filt.apply(self.db, self.get_all_handles())
            ShowResults(self.db, self.uistate, self.track, handle_list,
                        filt.get_name(),self.namespace)

    def delete_filter(self, obj):
        store, node = self.clist.get_selected()
        if node:
            gfilter = self.clist.get_object(node)
            name = gfilter.get_name()
            if self.check_recursive_filters(self.namespace, name):
                QuestionDialog( _('Delete Filter?'),
                                _('This filter is currently being used '
                                  'as the base for other filters. Deleting'
                                  'this filter will result in removing all '
                                  'other filters that depend on it.'),
                                _('Delete Filter'),
                                self._do_delete_selected_filter,
                                self.window)
            else:
                self._do_delete_selected_filter()

    def _do_delete_selected_filter(self):
        store, node = self.clist.get_selected()
        if node:
            gfilter = self.clist.get_object(node)
            self._do_delete_filter(self.namespace, gfilter)
            self.draw_filters()

    def _do_delete_filter(self, space, gfilter):
        # Find everything we need to remove
        filter_set = set()
        self._find_dependent_filters(space, gfilter, filter_set)

        # Remove what we found
        filters = self.filterdb.get_filters(space)
        list(map(filters.remove, filter_set))

    def _find_dependent_filters(self, space, gfilter, filter_set):
        """
        This method recursively calls itself to find all filters that
        depend on the given filter, either directly through one of the rules,
        or through the chain of dependencies.

        The filter_set is amended with the found filters.
        """
        filters = self.filterdb.get_filters(space)        
        name = gfilter.get_name()
        for the_filter in filters:
            if the_filter.get_name() == name:
                continue
            for rule in the_filter.get_rules():
                values = list(rule.values())
                if issubclass(rule.__class__, MatchesFilterBase) \
                       and (name in values):
                    self._find_dependent_filters(space, the_filter, filter_set)
                    break
        # Add itself to the filter_set
        filter_set.add(gfilter)

    def get_all_handles(self):
        # Why use iter for some and get for others?
        if self.namespace == 'Textile':
            return self.db.iter_textile_handles()
        elif self.namespace == 'Ensemble':
            return self.db.iter_ensemble_handles()
        elif self.namespace == 'Media':
            return self.db.get_media_object_handles()
        elif self.namespace == 'Note':
            return self.db.get_note_handles()

    def clean_after_rename(self, space, old_name, new_name):
        if old_name == "":
            return

        if old_name == new_name:
            return

        for the_filter in self.filterdb.get_filters(space):
            for rule in the_filter.get_rules():
                values = list(rule.values())
                if issubclass(rule.__class__, MatchesFilterBase) \
                       and (old_name in values):
                    ind = values.index(old_name)
                    values[ind] = new_name

    def check_recursive_filters(self, space, name):
        for the_filter in self.filterdb.get_filters(space):
            for rule in the_filter.get_rules():
                values = list(rule.values())
                if issubclass(rule.__class__, MatchesFilterBase) \
                       and (name in values):
                    return True
        return False
