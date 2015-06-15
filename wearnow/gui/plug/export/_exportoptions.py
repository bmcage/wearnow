#
# wearnow - a GTK+/GNOME based program
#
# Copyright (C) 2007-2008 Donald N. Allingham
# Copyright (C) 2008      Gary Burton 
# Copyright (C) 2008      Robert Cheramy <robert@cheramy.net>
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

"""Provide the common export options for Exporters."""

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------

#-------------------------------------------------------------------------
#
# wearnow modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext
ngettext = glocale.translation.ngettext # else "nearby" comments are ignored
from wearnow.tex.config import config
from wearnow.tex.filters import GenericFilter, rules
from ...utils import ProgressMeter
from wearnow.tex.proxy import (PrivateProxyDb, 
                              #FilterProxyDb, 
                              #ReferencedBySelectionProxyDb
                               )
        
class Progress(object):
    """
    Mirrros the same interface that the ExportAssistant uses in the
    selection, but this is for the preview selection.
    """
    def __init__(self, uistate):
        from gi.repository import Gtk
        self.pm = ProgressMeter(_("Selecting Preview Data"), _('Selecting...'),
                                parent=uistate.window)
        self.progress_cnt = 0
        self.title = _("Selecting...")
        while Gtk.events_pending():
            Gtk.main_iteration()

    def reset(self, title):
        from gi.repository import Gtk
        self.pm.set_header(title)
        self.title = title
        while Gtk.events_pending():
            Gtk.main_iteration()

    def set_total(self, count):
        from gi.repository import Gtk
        self.pm.set_pass(self.title, total=count+1)
        while Gtk.events_pending():
            Gtk.main_iteration()

    def update(self, count):
        from gi.repository import Gtk
        self.pm.step()
        while Gtk.events_pending():
            Gtk.main_iteration()

    def close(self):
        self.pm.step()
        self.pm.close()

#-------------------------------------------------------------------------
#
# WriterOptionBox
#
#-------------------------------------------------------------------------
class WriterOptionBox(object):
    """
    Create a VBox with the option widgets and define methods to retrieve
    the options.
     
    """
    def __init__(self, textile, dbstate, uistate):
        self.textile = textile
        self.dbstate = dbstate
        self.uistate = uistate
        self.preview_dbase = None
        self.preview_button = None
        self.preview_proxy_button = {}
        self.proxy_options_showing = False
        self.proxy_dbase = {}
        self.private = 0
        self.restrict_num = 0
        self.reference_num = 0
        self.cfilter = None
        self.nfilter = None
        self.private_check = None
        self.filter_obj = None
        self.filter_note = None
        self.reference_filter = None
        self.initialized_show_options = False
        self.set_config(config)
        # The following are special properties. Create them to force the
        # export wizard to not ask for a file, and to override the 
        # confirmation message:
        #self.no_fileselect = True
        #self.confirm_text = "You made it, kid!"

    def set_config(self, config):
        """
        Set the config used for these proxies. Allows WriterOptionBox
        to be used by reports, etc. The default is to use wearnow's
        system config.
        """
        self.config = config

    def mark_dirty(self, widget=None):
        self.preview_dbase = None
        if self.preview_button:
            self.preview_button.set_sensitive(1)
        for proxy_name in self.preview_proxy_button:
            if proxy_name != "unfiltered":
                self.preview_proxy_button[proxy_name].set_sensitive(0)
        self.parse_options()

    def get_option_box(self):
        """Build up a Gtk.Box that contains the standard options."""
        from gi.repository import Gtk
        from gi.repository import Pango
        widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        full_database_row = Gtk.Box()
        label = Gtk.Label(label=_("Unfiltered Collection:"))
        full_database_row.pack_start(label, True, True, 0)
        textiles_count = len(self.dbstate.db.get_textile_handles())
        # translators: leave all/any {...} untranslated
        button = Gtk.Button(ngettext("{number_of} Textile",
                                     "{number_of} Textiles", textiles_count
                                    ).format(number_of=textiles_count) )
        button.set_tooltip_text(_("Click to see preview of unfiltered data"))
        button.set_size_request(107, -1)
        button.connect("clicked", self.show_preview_data)
        button.proxy_name = "unfiltered"
        self.preview_proxy_button["unfiltered"] = button
        self.spacer = Gtk.Box()
        full_database_row.pack_end(self.spacer, False, True, 0)
        full_database_row.pack_end(button, False, True, 0)

        widget.pack_start(full_database_row, False, True, 0)
        
        self.private_check = Gtk.CheckButton.new_with_mnemonic(
            _('_Do not include records marked private'))
        self.private_check.connect("clicked", self.mark_dirty)
        self.private_check.set_active(self.get_proxy_value("privacy"))

        self.proxy_widget = {}
        self.vbox_n = []
        self.up_n = []
        self.down_n = []
        row = 0
        for proxy_name in self.get_proxy_names():
            frame = self.build_frame(proxy_name, row)
            widget.pack_start(frame, False, True, 0)
            row += 1

        hbox = Gtk.Box()
        self.advanced_button = Gtk.Button(label=_("Change order"))
        self.advanced_button.set_size_request(150, -1)
        self.proxy_options_showing = False
        self.advanced_button.connect("clicked", self.show_options)
        hbox.pack_end(self.advanced_button, False, True, 0)
        self.preview_button = Gtk.Button(label=_("Calculate Previews"))
        self.preview_button.connect("clicked", self.preview)
        hbox.pack_end(self.preview_button, False, True, 0)
        widget.pack_start(hbox, False, True, 0)

        cell = Gtk.CellRendererText()
        cell.set_property('ellipsize', Pango.EllipsizeMode.END)
        self.filter_obj.pack_start(cell, True)
        self.filter_obj.add_attribute(cell, 'text', 0)
        self.filter_obj.set_model(self.build_model("textile"))
        self.filter_obj.set_active(self.get_proxy_value("textile"))

        cell = Gtk.CellRendererText()
        cell.set_property('ellipsize', Pango.EllipsizeMode.END)
        self.reference_filter.pack_start(cell, True)
        self.reference_filter.add_attribute(cell, 'text', 0)
        self.reference_filter.set_model(self.build_model("reference"))
        self.reference_filter.set_active(self.get_proxy_value("reference"))

        notes_cell = Gtk.CellRendererText()
        notes_cell.set_property('ellipsize', Pango.EllipsizeMode.END)
        self.filter_note.pack_start(notes_cell, True)
        self.filter_note.add_attribute(notes_cell, 'text', 0)
        self.filter_note.set_model(self.build_model("note"))
        self.filter_note.set_active(self.get_proxy_value("note"))

        self.filter_note.connect("changed", self.mark_dirty)
        self.filter_obj.connect("changed", self.mark_dirty)
        self.reference_filter.connect("changed", self.mark_dirty)
        return widget

    def show_preview_data(self, widget):
        from wearnow.tex.dbstate import DbState
        from ..quick import run_quick_report_by_name
        if widget.proxy_name == "unfiltered":
            dbstate = self.dbstate
        else:
            dbstate = DbState()
            dbstate.db = self.proxy_dbase[widget.proxy_name]
            dbstate.open = True
        run_quick_report_by_name(dbstate,
                                 self.uistate, 
                                 'filterbyname', 
                                 'all')

    def preview(self, widget):
        """
        Calculate previews to see the selected data.
        """
        self.parse_options()
        pm = Progress(self.uistate)
        self.preview_dbase = self.get_filtered_database(self.dbstate.db, pm, preview=True)
        pm.close()
        self.preview_button.set_sensitive(0)

    def build_frame(self, proxy_name, row):
        """
        Build a frame for a proxy option. proxy_name is a string.
        """
        # Make a box and put the option in it:
        from gi.repository import Gtk
        from ...widgets import SimpleButton
        # translators: leave all/any {...} untranslated
        button = Gtk.Button(ngettext("{number_of} Textile",
                                     "{number_of} Textiles", 0
                                    ).format(number_of=0) )
        button.set_size_request(107, -1)
        button.connect("clicked", self.show_preview_data)
        button.proxy_name = proxy_name
        if proxy_name == "textile":
            # Frame Textile:
            self.filter_obj = Gtk.ComboBox()
            label = Gtk.Label(label=_('_Textile Filter') + ": ")
            label.set_halign(Gtk.Align.START)
            label.set_size_request(150, -1)
            label.set_use_underline(True)
            label.set_mnemonic_widget(self.filter_obj)
            box = Gtk.Box()
            box.pack_start(label, False, True, 0)
            box.pack_start(self.filter_obj, True, True, 0)
            box.pack_start(
                SimpleButton('gtk-edit',
                   lambda obj: self.edit_filter('Textile', self.filter_obj)),
                False, True, 0)
            button.set_tooltip_text(_("Click to see preview after textile filter"))
        elif proxy_name == "note":
            # Frame Note:
            # Objects for choosing a Note filter:
            self.filter_note = Gtk.ComboBox()
            label_note = Gtk.Label(label=_('_Note Filter') + ": ")
            label_note.set_halign(Gtk.Align.START)
            label_note.set_size_request(150, -1)
            label_note.set_use_underline(True)
            label_note.set_mnemonic_widget(self.filter_note)
            box = Gtk.Box()
            box.pack_start(label_note, False, True, 0)
            box.pack_start(self.filter_note, True, True, 0)
            box.pack_start(
                SimpleButton('gtk-edit',
                   lambda obj: self.edit_filter('Note', self.filter_note)),
                False, True, 0)
            button.set_tooltip_text(_("Click to see preview after note filter"))
        elif proxy_name == "privacy":
            # Frame 3:
            label = Gtk.Label(label=_("Privacy Filter") + ":")
            label.set_halign(Gtk.Align.START)
            label.set_size_request(150, -1)
            box = Gtk.Box()
            box.pack_start(label, False, True, 0)
            box.add(self.private_check)
            button.set_tooltip_text(_("Click to see preview after privacy filter"))
        elif proxy_name == "reference":
            # Frame 5:
            self.reference_filter = Gtk.ComboBox()
            label = Gtk.Label(label=_('Reference Filter') + ": ")
            label.set_halign(Gtk.Align.START)
            label.set_size_request(150, -1)
            box = Gtk.Box()
            box.pack_start(label, False, True, 0)
            box.pack_start(self.reference_filter, True, True, 0)
            button.set_tooltip_text(_("Click to see preview after reference filter"))
        else:
            raise AttributeError("Unknown proxy '%s'" % proxy_name)

        frame = Gtk.Frame()
        hbox = Gtk.Box()
        frame.add(hbox)
        vbox = Gtk.Box()
        self.vbox_n.append(vbox)
        up = Gtk.Button()
        up.connect("clicked", self.swap)
        if row == 0:
            up.set_sensitive(0) # can't go up
        image = Gtk.Image()
        image.set_from_icon_name('go-up', Gtk.IconSize.MENU)
        up.set_image(image)
        up.row = row - 1
        self.up_n.append(up)
        down = Gtk.Button()
        down.connect("clicked", self.swap)
        image = Gtk.Image()
        image.set_from_icon_name('go-down', Gtk.IconSize.MENU)
        down.set_image(image)
        down.row = row
        if row == 4:
            down.set_sensitive(0) # can't go down
        self.down_n.append(down)
        self.preview_proxy_button[proxy_name] = button
        self.preview_proxy_button[proxy_name].set_sensitive(0)
        box.pack_end(button, False, True, 0)
        hbox.pack_start(box, True, True, 0)
        hbox.pack_end(vbox, False, True, 0)
        self.proxy_widget[proxy_name] = box
        return frame

    def show_options(self, widget=None):
        """
        Show or hide the option arrows. Needs to add them if first
        time due to the fact that wearnow tends to use show_all rather
        than show.
        """
        from gi.repository import Gtk
        if self.proxy_options_showing:
            self.advanced_button.set_label(_("Change order"))
            self.spacer_up.hide()
            self.spacer_down.hide()
            for n in range(5):
                self.up_n[n].hide()
                self.down_n[n].hide()
        else:
            self.advanced_button.set_label(_("Hide order"))
            if not self.initialized_show_options:
                self.initialized_show_options = True
                # This is necessary because someone used show_all up top
                # Now, we can't add something that we want hidden
                for n in range(5):
                    self.vbox_n[n].pack_start(self.up_n[n], True, True, 0)
                    self.vbox_n[n].pack_end(self.down_n[n], False, True, 0)
                # some spacer buttons:
                up = Gtk.Button()
                up.set_sensitive(0) 
                image = Gtk.Image()
                image.set_from_icon_name('go-up', Gtk.IconSize.MENU)
                up.set_image(image)
                self.spacer.pack_start(up, False, True, 0)
                down = Gtk.Button()
                down.set_sensitive(0) 
                image = Gtk.Image()
                image.set_from_icon_name('go-down', Gtk.IconSize.MENU)
                down.set_image(image)
                self.spacer.pack_end(down, False, True, 0)
                self.spacer_up = up
                self.spacer_down = down
            self.spacer_up.show()
            self.spacer_down.show()
            for n in range(5):
                self.up_n[n].show()
                self.down_n[n].show()
            
        self.proxy_options_showing = not self.proxy_options_showing

    def swap(self, widget):
        """
        Swap the order of two proxies. 
        """
        row1 = widget.row
        row2 = widget.row + 1
        proxy1 = self.config.get('export.proxy-order')[row1][0]
        proxy2 = self.config.get('export.proxy-order')[row2][0]
        widget1 = self.proxy_widget[proxy1]
        widget2 = self.proxy_widget[proxy2]
        parent1 = widget1.get_parent()
        parent2 = widget2.get_parent()
        widget1.reparent(parent2)
        widget2.reparent(parent1)
        self.swap_proxy_order(row1, row2)
        self.mark_dirty(widget)

    def __define_textile_filters(self):
        """Add textile filters if the active textile is defined."""

        wearnow_id = self.textile.get_wearnow_id()

        return []

    def get_proxy_value(self, proxy_name):
        return [value for (name, value) in 
                self.config.get('export.proxy-order') if name == proxy_name][0]

    def set_proxy_value(self, proxy_name, proxy_value):
        [name_value for name_value in 
         self.config.get('export.proxy-order') if name_value[0] == proxy_name][0][1] = int(proxy_value)

    def get_proxy_names(self):
        return [name for (name, value) in self.config.get('export.proxy-order')]

    def swap_proxy_order(self, row1, row2):
        po = self.config.get('export.proxy-order')
        po[row1], po[row2] = po[row2], po[row1]

    def parse_options(self):
        """
        Extract the common values from the GTK widgets. 
        
        After this function is called, the following variables are defined:

           private  = privacy requested
           cfitler  = return the GenericFilter selected
           nfilter  = return the NoteFilter selected
           reference = restrict referenced/orphaned records

        """
        if self.private_check:
            self.private = self.private_check.get_active()
            self.set_proxy_value("privacy", self.private)

        if self.filter_obj:
            model = self.filter_obj.get_model()
            node = self.filter_obj.get_active_iter()
            if node:
                self.cfilter = model[node][1]
            self.set_proxy_value("textile", self.filter_obj.get_active())
        
        if self.filter_note:
            model = self.filter_note.get_model()
            node = self.filter_note.get_active_iter()
            if node:
                self.nfilter = model[node][1]
            self.set_proxy_value("note", self.filter_note.get_active())

        if self.reference_filter:
            model = self.reference_filter.get_model()
            node = self.reference_filter.get_active_iter()
            if node:
                self.reference_num = model[node][1]
            self.set_proxy_value("reference", self.reference_filter.get_active())

    def get_filtered_database(self, dbase, progress=None, preview=False):
        """
        dbase - the database
        progress - instance that has:
           .reset() method
           .set_total() method
           .update() method
           .progress_cnt integer representing N of total done
        """
        # Increment the progress count for each filter type chosen
        if self.private and progress:
            progress.progress_cnt += 1

        if self.restrict_num > 0 and progress:
            progress.progress_cnt += 1

        if (self.cfilter != None and (not self.cfilter.is_empty())) and progress:
            progress.progress_cnt += 1

        if (self.nfilter != None and (not self.nfilter.is_empty())) and progress:
            progress.progress_cnt += 1

        if self.reference_num > 0 and progress:
            progress.progress_cnt += 1

        if progress:
            progress.set_total(progress.progress_cnt)
            progress.progress_cnt = 0

        if self.preview_dbase:
            if progress:
                progress.progress_cnt += 5
            return self.preview_dbase

        self.proxy_dbase.clear()
        for proxy_name in self.get_proxy_names():
            dbase = self.apply_proxy(proxy_name, dbase, progress)
            if preview:
                self.proxy_dbase[proxy_name] = dbase
                self.preview_proxy_button[proxy_name].set_sensitive(1)
                textiles_count = len(dbase.get_textile_handles())
                self.preview_proxy_button[proxy_name].set_label(
                    # translators: leave all/any {...} untranslated
                    ngettext("{number_of} Textile",
                             "{number_of} Textiles", textiles_count
                            ).format(number_of=textiles_count) )
        return dbase

    def apply_proxy(self, proxy_name, dbase, progress=None):
        """
        Apply the named proxy to the dbase, and return.
        proxy_name is one of 
           ["textile", "note", "privacy", "reference"]
        """
        # If the private flag is set, apply the PrivateProxyDb
        if proxy_name == "privacy":
            if self.private:
                if progress:
                    progress.reset(_("Filtering private data"))
                    progress.progress_cnt += 1
                    progress.update(progress.progress_cnt)
                dbase = PrivateProxyDb(dbase)

        # If the filter returned by cfilter is not empty, apply the 
        # FilterProxyDb (Textile Filter)
        elif proxy_name == "textile":
            if self.cfilter != None and not self.cfilter.is_empty():
                if progress:
                    progress.reset(_("Applying selected textile filter"))
                    progress.progress_cnt += 1
                    progress.update(progress.progress_cnt)
                dbase = FilterProxyDb(
                    dbase, self.cfilter)

        # Apply the Note Filter
        elif proxy_name == "note":
            if self.nfilter != None and not self.nfilter.is_empty():
                if progress:
                    progress.reset(_("Applying selected note filter"))
                    progress.progress_cnt += 1
                    progress.update(progress.progress_cnt)
                dbase = FilterProxyDb(
                    dbase, note_filter=self.nfilter)

        # Apply the ReferencedBySelection
        elif proxy_name == "reference":
            if progress:
                progress.reset(_("Filtering referenced records"))
                progress.progress_cnt += 1
                progress.update(progress.progress_cnt)
            if self.reference_num == 0:
                pass
            elif self.reference_num == 1:
                dbase = ReferencedBySelectionProxyDb(dbase,
                                                     all_textiles=True)
        else:
            raise AttributeError("no such proxy '%s'" % proxy_name)

        return dbase

    def edit_filter(self, namespace, filter_obj):
        """
        Callback which invokes the EditFilter dialog. Will create new
        filter if called if none is selected.
        """
        from ...editors import EditFilter
        from wearnow.tex.filters import FilterList, GenericFilterFactory
        from wearnow.tex.const import CUSTOM_FILTERS
        the_filter = None
        filterdb = FilterList(CUSTOM_FILTERS)
        filterdb.load()
        if filter_obj.get_active() != 0:
            model = filter_obj.get_model()
            node = filter_obj.get_active_iter()
            if node:
                sel_filter = model.get_value(node, 1)
                # the_filter needs to be a particular object for editor
                for filt in filterdb.get_filters(namespace):
                    if filt.get_name() == sel_filter.get_name():
                        the_filter = filt
        else:
            the_filter = GenericFilterFactory(namespace)()
        if the_filter:
            EditFilter(namespace, self.dbstate, self.uistate, [],
                       the_filter, filterdb,
                       lambda : self.edit_filter_save(filterdb, namespace))
        else: # can't edit this filter
            from ...dialog import ErrorDialog
            ErrorDialog(_("Cannot edit a system filter"), 
                        _("Please select a different filter to edit"))

    def edit_filter_save(self, filterdb, namespace):
        """
        If a filter changed, save them all. Reloads, and also calls callback.
        """
        from wearnow.tex.filters import CustomFilters
        from wearnow.tex.filters import reload_custom_filters
        filterdb.save()
        reload_custom_filters()
        if namespace == "Textile":
            model = self.build_model("textile")
            widget = self.filter_obj
        elif namespace == "Note":
            model = self.build_model("note")
            widget = self.filter_note
        widget.set_model(model)
        widget.set_active(0)

    def build_model(self, namespace):
        """
        Build a model for the combo box selector.
        """
        from gi.repository import Gtk
        from gi.repository import GObject
        from wearnow.tex.filters import CustomFilters
        if namespace == "textile":
            # Populate the Textile Filter
            entire_db = GenericFilter()
            entire_db.set_name(_("Include all selected textiles"))
            the_filters = [entire_db]

            if self.textile:
                the_filters += self.__define_textile_filters()

            the_filters.extend(CustomFilters.get_filters('Textile'))

            model = Gtk.ListStore(GObject.TYPE_STRING, object)
            for item in the_filters:
                model.append(row=[item.get_name(), item])
        elif namespace == "note":
            # Populate the Notes Filter
            entire_db = GenericFilter()
            entire_db.set_name(_("Include all selected notes"))
            notes_filters = [entire_db]
            notes_filters.extend(CustomFilters.get_filters('Note'))
            model = Gtk.ListStore(GObject.TYPE_STRING, object)
            for item in notes_filters:
                model.append(row=[item.get_name(), item])

        elif namespace == "reference":
            model = Gtk.ListStore(GObject.TYPE_STRING, int)
            row = 0
            for item in [
                _('Include all selected records'),
                _('Do not include records not linked to a selected textile'),]:
                model.append(row=[item, row])
                row += 1

        return model
