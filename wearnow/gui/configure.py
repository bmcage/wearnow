#
# WearNow - a GTK+ based Desktop App for wear comfort
#
# Copyright (C) 2015       Benny Malengier (UGent)
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2008       Raphael Ackermann
# Copyright (C) 2010       Benny Malengier
# Copyright (C) 2010       Nick Hall
# Copyright (C) 2012       Doug Blank <doug.blank@gmail.com>
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
# Standard python modules
#
#-------------------------------------------------------------------------
import collections

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from gi.repository import GObject
from gi.repository import Gdk
from gi.repository import Gtk

#-------------------------------------------------------------------------
#
# modules
#
#-------------------------------------------------------------------------
from wearnow.gen.config import config
from wearnow.gen.const import WEARNOW_LOCALE as glocale
from wearnow.gen.constfunc import conv_to_unicode
from .managedwindow import ManagedWindow
from .widgets import MarkupLabel, BasicLabel
from .dialog import ErrorDialog, QuestionDialog2, OkDialog
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# Constants 
#
#--------

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------

#-------------------------------------------------------------------------
#
# ConfigureDialog
#
#-------------------------------------------------------------------------

class ConfigureDialog(ManagedWindow):
    """
    Base class for configuration dialogs. They provide a Notebook, to which 
    pages are added with configuration options, and a Cancel and Save button.
    On save, a config file on which the dialog works, is saved to disk, and
    a callback called.
    """
    def __init__(self, uistate, dbstate, configure_page_funcs, configobj,
                 configmanager,
                 dialogtitle=_("Preferences"), on_close=None):
        """
        Set up a configuration dialog
        :param uistate: a DisplayState instance
        :param dbstate: a DbState instance
        :param configure_page_funcs: a list of function that return a tuple
            (str, Gtk.Widget). The string is used as label for the 
            configuration page, and the widget as the content of the 
            configuration page
        :param configobj: the unique object that is configured, it must be 
            identifiable (id(configobj)). If the configure dialog of the 
            configobj is already open, a WindowActiveError will be
            raised. Grab this exception in the calling method
        :param configmanager: a configmanager object. Several convenience
            methods are present in ConfigureDialog to set up widgets that 
            write changes directly via this configmanager.
        :param dialogtitle: the title of the configuration dialog
        :param on_close: callback that is called on close
        """
        self.dbstate = dbstate
        self.__config = configmanager
        ManagedWindow.__init__(self, uistate, [], configobj)
        self.set_window(
            Gtk.Dialog(dialogtitle, 
                       buttons=(_('_Close'), Gtk.ResponseType.CLOSE)),
                       None, dialogtitle, None)
        self.panel = Gtk.Notebook()
        self.panel.set_scrollable(True)
        self.window.vbox.pack_start(self.panel, True, True, 0)
        self.__on_close = on_close
        self.window.connect('response', self.done)
        
        self.__setup_pages(configure_page_funcs)
        
        self.show()
    
    def __setup_pages(self, configure_page_funcs):
        """
        This method builds the notebookpages in the panel
        """
        if isinstance(configure_page_funcs, collections.Callable):
            pages = configure_page_funcs()
        else:
            pages = configure_page_funcs
        for func in pages:
            labeltitle, widget = func(self)
            self.panel.append_page(widget, MarkupLabel(labeltitle))

    def done(self, obj, value):
        if self.__on_close:
            self.__on_close()
        self.close()

    def update_int_entry(self, obj, constant):
        """
        :param obj: an object with get_text method that should contain an
            integer
        :param constant: the config setting to which the integer value must be 
            saved
        """
        try:
            self.__config.set(constant, int(obj.get_text()))
        except:
            print("WARNING: ignoring invalid value for '%s'" % constant)

    def update_markup_entry(self, obj, constant):
        """
        :param obj: an object with get_text method 
        :param constant: the config setting to which the text value must be 
            saved
        """
        try:
            obj.get_text() % 'test_markup'
        except TypeError:
            print("WARNING: ignoring invalid value for '%s'" % constant)
            ErrorDialog(_("Invalid or incomplete format definition."), 
                        obj.get_text(), parent=self.window)
            obj.set_text('<b>%s</b>')
        except ValueError:
            print("WARNING: ignoring invalid value for '%s'" % constant)
            ErrorDialog(_("Invalid or incomplete format definition."),
                        obj.get_text(), parent=self.window)
            obj.set_text('<b>%s</b>')
        
        self.__config.set(constant, unicode(obj.get_text()))

    def update_entry(self, obj, constant):
        """
        :param obj: an object with get_text method 
        :param constant: the config setting to which the text value must be 
            saved
        """
        self.__config.set(constant, conv_to_unicode(obj.get_text()))

    def update_color(self, obj, constant, color_hex_label):
        rgba = obj.get_rgba()
        hexval = "#%02x%02x%02x" % (int(rgba.red * 255),
                                    int(rgba.green * 255),
                                    int(rgba.blue * 255))
        color_hex_label.set_text(hexval)
        self.__config.set(constant, hexval)

    def update_checkbox(self, obj, constant, config=None):
        if not config:
            config = self.__config
        config.set(constant, obj.get_active())

    def update_radiobox(self, obj, constant):
        self.__config.set(constant, obj.get_active())

    def update_combo(self, obj, constant):
        """
        :param obj: the ComboBox object
        :param constant: the config setting to which the value must be saved
        """
        self.__config.set(constant, obj.get_active())

    def update_slider(self, obj, constant):
        """
        :param obj: the HScale object
        :param constant: the config setting to which the value must be saved
        """
        self.__config.set(constant, int(obj.get_value()))

    def update_spinner(self, obj, constant):
        """
        :param obj: the SpinButton object
        :param constant: the config setting to which the value must be saved
        """
        self.__config.set(constant, int(obj.get_value()))

    def add_checkbox(self, grid, label, index, constant, start=1, stop=9,
                     config=None, extra_callback=None):
        if not config:
            config = self.__config
        checkbox = Gtk.CheckButton(label=label)
        checkbox.set_active(config.get(constant))
        checkbox.connect('toggled', self.update_checkbox, constant, config)
        if extra_callback:
            checkbox.connect('toggled', extra_callback)
        grid.attach(checkbox, start, index, stop - start, 1)
        return checkbox

    def add_radiobox(self, grid, label, index, constant, group, column,
                     config=None):
        if not config:
            config = self.__config
        radiobox = Gtk.RadioButton.new_with_mnemonic_from_widget(group, label)
        if config.get(constant) == True:
            radiobox.set_active(True)
        radiobox.connect('toggled', self.update_radiobox, constant)
        grid.attach(radiobox, column, index, 1, 1)
        return radiobox

    def add_text(self, grid, label, index, config=None, line_wrap=True):
        if not config:
            config = self.__config
        text = Gtk.Label()
        text.set_line_wrap(line_wrap)
        text.set_halign(Gtk.Align.START)
        text.set_text(label)
        grid.attach(text, 1, index, 8, 1)

    def add_path_box(self, grid, label, index, entry, path, callback_label, 
                     callback_sel, config=None):
        """ Add an entry to give in path and a select button to open a 
            dialog. 
            Changing entry calls callback_label
            Clicking open button call callback_sel
        """
        if not config:
            config = self.__config
        lwidget = BasicLabel("%s: " %label)
        hbox = Gtk.Box()
        if path:
            entry.set_text(path)
        entry.connect('changed', callback_label)
        btn = Gtk.Button()
        btn.connect('clicked', callback_sel)
        image = Gtk.Image()
        image.set_from_icon_name('document-open', Gtk.IconSize.BUTTON)
        image.show()
        btn.add(image)
        hbox.pack_start(entry, True, True, 0)
        hbox.pack_start(btn, False, False, 0)
        hbox.set_hexpand(True)
        grid.attach(lwidget, 1, index, 1, 1)
        grid.attach(hbox, 2, index, 1, 1)

    def add_entry(self, grid, label, index, constant, callback=None,
                  config=None, col_attach=0):
        if not config:
            config = self.__config
        if not callback:
            callback = self.update_entry
        if label:
            lwidget = BasicLabel("%s: " % label)
        entry = Gtk.Entry()
        entry.set_text(config.get(constant))
        entry.connect('changed', callback, constant)
        entry.set_hexpand(True)
        if label:
            grid.attach(lwidget, col_attach, index, 1, 1)
            grid.attach(entry, col_attach+1, index, 1, 1)
        else:
            grid.attach(entry, col_attach, index, 1, 1)
        return entry

    def add_pos_int_entry(self, grid, label, index, constant, callback=None,
                          config=None, col_attach=1, helptext=''):
        """ entry field for positive integers
        """
        if not config:
            config = self.__config
        lwidget = BasicLabel("%s: " % label)
        entry = Gtk.Entry()
        entry.set_text(str(config.get(constant)))
        entry.set_tooltip_markup(helptext)
        entry.set_hexpand(True)
        if callback:
            entry.connect('changed', callback, constant)
        grid.attach(lwidget, col_attach, index, 1, 1)
        grid.attach(entry, col_attach+1, index, 1, 1)

    def add_color(self, grid, label, index, constant, config=None, col=0):
        if not config:
            config = self.__config
        lwidget = BasicLabel("%s: " % label)
        hexval = config.get(constant)
        color = Gdk.color_parse(hexval)
        entry = Gtk.ColorButton(color=color)
        color_hex_label = BasicLabel(hexval)
        color_hex_label.set_hexpand(True)
        entry.connect('color-set', self.update_color, constant, color_hex_label)
        grid.attach(lwidget, col, index, 1, 1)
        grid.attach(entry, col+1, index, 1, 1)
        grid.attach(color_hex_label, col+2, index, 1, 1)
        return entry

    def add_combo(self, grid, label, index, constant, opts, callback=None,
                  config=None, valueactive=False, setactive=None):
        """
        A drop-down list allowing selection from a number of fixed options.
        :param opts: A list of options.  Each option is a tuple containing an
        integer code and a textual description.
        If valueactive = True, the constant stores the value, not the position
        in the list
        """
        if not config:
            config = self.__config
        if not callback:
            callback = self.update_combo
        lwidget = BasicLabel("%s: " % label)
        store = Gtk.ListStore(int, str)
        for item in opts:
            store.append(item)
        combo = Gtk.ComboBox(model=store)
        cell = Gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'text', 1)
        if valueactive:
            val = config.get(constant)
            pos = 0
            for nr, item in enumerate(opts):
                if item[-1] == val:
                    pos = nr
                    break
            combo.set_active(pos)
        else:
            if setactive is None:
                combo.set_active(config.get(constant))
            else:
                combo.set_active(setactive)
        combo.connect('changed', callback, constant)
        combo.set_hexpand(True)
        grid.attach(lwidget, 1, index, 1, 1)
        grid.attach(combo, 2, index, 1, 1)
        return combo

    def add_slider(self, grid, label, index, constant, range, callback=None,
                   config=None):
        """
        A slider allowing the selection of an integer within a specified range.
        :param range: A tuple containing the minimum and maximum allowed values.
        """
        if not config:
            config = self.__config
        if not callback:
            callback = self.update_slider
        lwidget = BasicLabel("%s: " % label)
        adj = Gtk.Adjustment(config.get(constant), range[0], range[1], 1, 0, 0)
        slider = Gtk.Scale(adjustment=adj)
        slider.set_digits(0)
        slider.set_value_pos(Gtk.PositionType.BOTTOM)
        slider.connect('value-changed', callback, constant)
        grid.attach(lwidget, 1, index, 1, 1)
        grid.attach(slider, 2, index, 1, 1)
        return slider

    def add_spinner(self, grid, label, index, constant, range, callback=None,
                   config=None):
        """
        A spinner allowing the selection of an integer within a specified range.
        :param range: A tuple containing the minimum and maximum allowed values.
        """
        if not config:
            config = self.__config
        if not callback:
            callback = self.update_spinner
        lwidget = BasicLabel("%s: " % label)
        adj = Gtk.Adjustment(config.get(constant), range[0], range[1], 1, 0, 0)
        spinner = Gtk.SpinButton(adjustment=adj, climb_rate=0.0, digits=0)
        spinner.connect('value-changed', callback, constant)
        spinner.set_hexpand(True)
        grid.attach(lwidget, 1, index, 1, 1)
        grid.attach(spinner, 2, index, 1, 1)
        return spinner

#-------------------------------------------------------------------------
#
# WearnowPreferences
#
#-------------------------------------------------------------------------
class WearNowPreferences(ConfigureDialog):

    def __init__(self, uistate, dbstate):
        page_funcs = (
            self.add_behavior_panel,
            self.add_famtree_panel,
            self.add_formats_panel,
            self.add_places_panel,
            self.add_text_panel,
            self.add_prefix_panel,
            self.add_date_panel,
            self.add_researcher_panel,
            self.add_advanced_panel,
            self.add_color_panel
            )
        ConfigureDialog.__init__(self, uistate, dbstate, page_funcs, 
                                 WearNowPreferences, config,
                                 on_close=update_constants)

    def add_researcher_panel(self, configdialog):
        grid = Gtk.Grid()
        grid.set_border_width(12)
        grid.set_column_spacing(6)
        grid.set_row_spacing(6)
        self.add_text(grid, _('Enter your information so people can contact you when you'
                        ' distribute your Family Tree'), 0, line_wrap=False)
        self.add_entry(grid, _('Name'), 1, 'researcher.researcher-name')
        self.add_entry(grid, _('Address'), 2, 'researcher.researcher-addr')
        self.add_entry(grid, _('Locality'), 3, 'researcher.researcher-locality')
        self.add_entry(grid, _('City'), 4, 'researcher.researcher-city')
        self.add_entry(grid, _('State/County'), 5, 'researcher.researcher-state')
        self.add_entry(grid, _('Country'), 6, 'researcher.researcher-country')
        self.add_entry(grid, _('ZIP/Postal Code'), 7, 'researcher.researcher-postal')
        self.add_entry(grid, _('Phone'), 8, 'researcher.researcher-phone')
        self.add_entry(grid, _('Email'), 9, 'researcher.researcher-email')
        return _('Researcher'), grid

        
    def add_behavior_panel(self, configdialog):
        grid = Gtk.Grid()
        grid.set_border_width(12)
        grid.set_column_spacing(6)
        grid.set_row_spacing(6)

        current_line = 0
        
        current_line += 1
        self.add_checkbox(grid, 
                _('Remember last view displayed'), 
                current_line, 'preferences.use-last-view')

        current_line += 1
        # Check for updates:
        obox = Gtk.ComboBoxText()
        formats = [_("Never"), 
                   _("Once a month"), 
                   _("Once a week"), 
                   _("Once a day"), 
                   _("Always"), ]
        list(map(obox.append_text, formats))
        active = config.get('behavior.check-for-updates')
        obox.set_active(active)
        obox.connect('changed', self.check_for_updates_changed)
        lwidget = BasicLabel("%s: " % _('Check for updates'))
        grid.attach(lwidget, 1, current_line, 1, 1)
        grid.attach(obox, 2, current_line, 1, 1)

        current_line += 1
        button = Gtk.Button(label=_("Check now"))
        button.connect("clicked", self.check_for_updates)
        grid.attach(button, 3, current_line, 1, 1)

        return _('General'), grid

    def check_for_updates(self, button):
        OkDialog(_("Checking Addons Failed"),
                 _("This functionality has not been implemented yet."
                   "Please try again later."),
                 self.window)

    def build_menu_names(self, obj):
        return (_('Preferences'), _('Preferences'))
