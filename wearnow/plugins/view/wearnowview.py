# wearnow - a GTK+/GNOME based program
#
# Copyright (C) 2001-2007  Donald N. Allingham
# Copyright (C) 2009-2010  Gary Burton
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
WearNow Comfort View
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.sgettext
ngettext = glocale.translation.ngettext # else "nearby" comments are ignored

#-------------------------------------------------------------------------
#
# Set up logging
#
#-------------------------------------------------------------------------
import logging
_LOG = logging.getLogger("plugin.wearnowview")

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Pango

#-------------------------------------------------------------------------
#
# wearnow Modules
#
#-------------------------------------------------------------------------
from wearnow.tex.lib import (ChildRef, Ensemble, Textile, Attribute,
                             AttributeType, Url, UrlType, TextileType)
from wearnow.tex.lib.date import Today
from wearnow.tex.db.txn import DbTxn
from wearnow.gui.views.navigationview import NavigationView
from wearnow.gui.actiongroup import ActionGroup
from wearnow.gui.editors import EditTextile, EditEnsemble
from wearnow.gui.editors import FilterEditor
from wearnow.tex.utils.file import media_path_full
from wearnow.gui.utils import open_file_with_default_application
from wearnow.gui.thumbnails import get_thumbnail_image
from wearnow.gui.glade import Glade
from wearnow.tex.config import config
from wearnow.gui import widgets
from wearnow.gui.selectors import SelectorFactory
from wearnow.gui.editors.editensemble import EditEnsemble, ChildEmbedList
from wearnow.tex.errors import WindowActiveError
from wearnow.gui.views.bookmarks import EnsembleBookmarks
from wearnow.tex.const import CUSTOM_FILTERS
from wearnow.gui.ddtargets import DdTargets

_RETURN = Gdk.keyval_from_name("Return")
_KP_ENTER = Gdk.keyval_from_name("KP_Enter")
_SPACE = Gdk.keyval_from_name("space")
_LEFT_BUTTON = 1
_RIGHT_BUTTON = 3


SelectTextile = SelectorFactory('Textile')
SelectEnsemble = SelectorFactory('Ensemble')

Activity = {
    'Sleeping':40,
    'Reclining':45,
    'At rest,sitting':55,
    'At rest,standing':70,
    'Sedentary activity(office,dwelling,school,laboratory)':70,
    'Standing light activity(shopping,laboratory,light industry)':95,
    'Working with a handtool (light polishing)/ machine tool (light)':100,
    'Walking on level even path at 2km/h':110,
    'Standing, medium activity(shop assitant,domestic work,machine work)':115,
    'Walking on level even path at 3km/h or medium loading with machine tool':140,
    #'Working on a machine tool(medium loading)':140,
    'Working with a handtool (medium polishing)':160,
    'Walking on level even path at 4km/h':165,
    'Working on a machine tool(heavy)':210,
    'Carpentry work': 220,
    'Working with a handtool (heavy drilling)':230,
    'climbing ladder(11.2m/min)':290
}

class WearNowView(NavigationView):
    """
    View showing comfort data of an ensemble
    """
    def __init__(self, pdata, dbstate, uistate, nav_group=0):
        
        self.VAL2ACT = {}
        self.VALACTS = []
        for k,v in Activity.items():
            self.VAL2ACT[v] = k 
            self.VALACTS.append(v)
        self.VALACTS.sort()
        
        self.unsaved_ens = True
        self.ensemble = Ensemble()
        self.tag = None
        
        NavigationView.__init__(self, _('Ensemble'),
                                      pdata, dbstate, uistate, 
                                      EnsembleBookmarks,
                                      nav_group)        

        self.func_list.update({
            '<PRIMARY>J' : self.jump,
            })

        dbstate.connect('database-changed', self.change_db)
        self.redrawing = False

        self.child = None
        self.old_handle = None

        self.additional_uis.append(self.additional_ui())

    def _connect_db_signals(self):
        """
        implement from base class DbGUIElement
        Register the callbacks we need.
        """

        self.callman.add_db_signal('textile-update', self.textile_update)
        self.callman.add_db_signal('textile-rebuild', self.textile_rebuild)
        self.callman.add_db_signal('ensemble-update', self.ensemble_update)
        self.callman.add_db_signal('ensemble-delete', self.ensemble_delete)
        self.callman.add_db_signal('ensemble-rebuild', self.ensemble_rebuild)

        self.callman.add_db_signal('textile-delete', self.redraw)

    def navigation_type(self):
        return 'Ensemble'

    def can_configure(self):
        """
        See :class:`~gui.views.pageview.PageView 
        :return: bool
        """
        return True

    def goto_handle(self, handle):
        self.change_ensemble(handle)

    def build_tree(self):
        self.redraw()

    def ensemble_update(self, handle_list):
        if self.active:
            ensemble = self.get_active()
            if ensemble:
                while not self.change_ensemble(ensemble):
                    pass
            else:
                self.change_ensemble(None)
        else:
            self.dirty = True

    def ensemble_rebuild(self):
        """Large change to ensemble database"""
        if self.active:
            self.bookmarks.redraw()
            ensemble = self.get_active()
            if ensemble:
                while not self.change_ensemble(ensemble):
                    pass
            else:
                self.change_ensemble(None)
        else:
            self.dirty = True

    def ensemble_delete(self, handle_list):
        if self.active:
            ensemble = self.get_active()
            if ensemble:
                while not self.change_ensemble(ensemble):
                    pass
            else:
                self.change_ensemble(None)
        else:
            self.dirty = True
        
    def textile_update(self, handle_list):
        if self.active:
            ensemble = self.get_active()
            if ensemble:
                while not self.change_ensemble(ensemble):
                    pass
            else:
                self.change_ensemble(None)
        else:
            self.dirty = True

    def textile_add(self, handle_list):
        if self.active:
            ensemble = self.get_active()
            if ensemble:
                while not self.change_ensemble(ensemble):
                    pass
            else:
                self.change_ensemble(None)
        else:
            self.dirty = True

    def textile_delete(self, handle_list):
        if self.active:
            ensemble = self.get_active()
            if ensemble:
                while not self.change_ensemble(ensemble):
                    pass
            else:
                self.change_ensemble(None)
        else:
            self.dirty = True

    def textile_rebuild(self):
        if self.active:
            ensemble = self.get_active()
            if ensemble:
                while not self.change_ensemble(ensemble):
                    pass
            else:
                self.change_ensemble(None)
        else:
            self.dirty = True

    def change_page(self):
        NavigationView.change_page(self)
        self.uistate.clear_filter_results()
            
    def get_stock(self):
        """
        Return the name of the stock icon to use for the display.
        This assumes that this icon has already been registered with
        GNOME as a stock icon.
        """
        return 'wearnow-comfort'
    
    def get_viewtype_stock(self):
        """Type of view in category
        """
        return 'wearnow-wearnow'

    def build_widget(self):
        """
        Build the widget that contains the view, see 
        :class:`~gui.views.pageview.PageView 
        """
        self.glade = Glade('wearnow.glade')
        self.box = self.glade.get_child_object('box1')
        self.scroll = self.glade.get_child_object('scrolledwindow1')
        self.child_list = None
        self.scale_activity = self.glade.get_child_object('scale_activity')
        self.scale_RH = self.glade.get_child_object('scale_RH')
        self.scale_temp = self.glade.get_child_object('scale_temp')  
        self.act_box = self.glade.get_child_object('activitybtnbox')
        self.actlabel = self.glade.get_child_object('actlabel')
        self.btnselgar = self.glade.get_child_object('btnselgar')
        self.btncomfort = self.glade.get_child_object('btncomfort')
        self.entr_comfort = self.glade.get_child_object('entr_comfort')
        
        #remove box from current container so we can reuse it
        self.glade.get_child_object('windowwearnow').remove(self.box)
        
        self.btnselgar.connect('clicked', self.select_garment)
        self.btncomfort.connect('clicked', self.compute_comfort)
        #set up activity slider
        MIN_SLIDER_SIZE = 20
        self.scale_activity.set_range(40,350)
        self.scale_activity.set_slider_size_fixed(True) 
        self.scale_activity.set_min_slider_size(MIN_SLIDER_SIZE)
        self.scale_activity.set_value(55)
        self.actval_changed(self.scale_activity)
        #set up RH slider
        self.scale_RH.set_range(0,100)
        self.scale_RH.set_slider_size_fixed(True) 
        self.scale_RH.set_min_slider_size(MIN_SLIDER_SIZE)
        self.scale_RH.set_value(60)
        #set up temp slider
        self.scale_temp.set_range(-20,40)
        self.scale_temp.set_slider_size_fixed(True) 
        self.scale_temp.set_min_slider_size(MIN_SLIDER_SIZE)
        self.scale_temp.set_value(18)
              
        #set up activity responce
        self.scale_activity.connect('value-changed', self.actval_changed)
        
        
        return self.box

    def select_garment(self, obj):
        
        sel = SelectTextile(self.dbstate, self.uistate, self.track,
                           _("Select Garment"), skip=[])
        textile = sel.run()
        
        if textile:
            ref = ChildRef()
            ref.ref = textile.get_handle()
            self.ensemble.add_child_ref(ref)
            self.redraw()

    def actval_changed(self, actrange):
        val = self.scale_activity.get_value()
        prevv = self.VALACTS[0]
        for v in self.VALACTS[1:]:
            if v > val:
                break
            prevv = v
        self.actlabel.set_markup('<b>'+self.VAL2ACT[prevv]+'</b>')

    def additional_ui(self):
        """
        Specifies the UIManager XML code that defines the menus and buttons
        associated with the interface.
        """
        return '''<ui>
          <menubar name="MenuBar">
            <menu action="GoMenu">
              <placeholder name="CommonGo">
                <menuitem action="Back"/>
                <menuitem action="Forward"/>
                <separator/>
              </placeholder>
            </menu>
            <menu action="EditMenu">
              <menuitem action="Edit"/>
              <menuitem action="FilterEdit"/>
            </menu>
            <menu action="BookMenu">
              <placeholder name="AddEditBook">
                <menuitem action="AddBook"/>
                <menuitem action="EditBook"/>
              </placeholder>
            </menu>
            <menu action="ViewMenu">
            </menu>
          </menubar>
          <toolbar name="ToolBar">
            <placeholder name="CommonNavigation">
              <toolitem action="Back"/>  
              <toolitem action="Forward"/>  
            </placeholder>
            <placeholder name="CommonEdit">
              <toolitem action="Edit"/>
            </placeholder>
            <placeholder name = "Scan">
              <toolitem action="ScanStart"/>
              <toolitem action="ScanStop"/>
            </placeholder>
          </toolbar>
          <popup name="Popup">
            <menuitem action="Back"/>
            <menuitem action="Forward"/>
            <separator/>
          </popup>
        </ui>'''

    def define_actions(self):
        NavigationView.define_actions(self)

        self._add_action('FilterEdit',  None, _('Ensemble Filter Editor'), 
                        callback=self.filter_editor)

        self.scan_action_start = ActionGroup(name=self.title + "/TextileScanStart")
        self.scan_action_stop = ActionGroup(name=self.title + "/TextileScanStop")
        self.scan_action_start.add_actions(
            [
                ('ScanStart', 'wearnow-scanstart', _("_Start Scan"), None,
                _("Start up Scanner to find RFID tags") ,self.start_scan),
            ])
        self.scan_action_stop.add_actions(
            [
                ('ScanStop', 'wearnow-scanstop', _("_Stop Scan"), None,
                _("Stop Scanning for RFID tags") ,self.stop_scan),
            ])
        self.scan_action_stop.set_visible(False)

        self._add_action_group(self.scan_action_start)
        self._add_action_group(self.scan_action_stop)

    def enable_action_group(self, obj):
        """
        Turns on the visibility of the View's action group.
        """
        NavigationView.enable_action_group(self, obj)
        self.scan_action_start.set_visible(True)
        self.scan_action_stop.set_visible(False)
        
    def disable_action_group(self):
        """
        Turns off the visibility of the View's action group.
        """
        NavigationView.disable_action_group(self)
        self.scan_action_start.set_visible(False)
        self.stop_scan(None)
        self.scan_action_stop.set_visible(False)

    def filter_editor(self, obj):
        try:
            FilterEditor('Ensemble', CUSTOM_FILTERS, 
                         self.dbstate, self.uistate)
        except WindowActiveError:
            return

    def change_db(self, db):
        #reset the connects
        self._change_db(db)
        if self.active:
                self.bookmarks.redraw()
        self.redraw()

    def redraw(self, *obj):
        active_ensemble = self.get_active()
        if active_ensemble:
            self.change_ensemble(active_ensemble)
        else:
            self.change_ensemble(None)
        
    def change_ensemble(self, obj):
        if not self.unsaved_ens:
            self.change_active(obj)
        try:
            return self._change_ensemble(obj)
        except AttributeError as msg:
            import traceback
            exc = traceback.format_exc()
            _LOG.error(str(msg) +"\n" + exc)
            from wearnow.gui.dialog import RunDatabaseRepair
            RunDatabaseRepair(str(msg))
            self.redrawing = False
            return True

    def _change_ensemble(self, obj):
        self.old_handle = obj

        if self.redrawing:
            return False
        self.redrawing = True

        if obj:
            self.ensemble = self.dbstate.db.get_ensemble_from_handle(obj)
        else:
            # obj None, so unsaved ensemble.
            pass
#            self.ensemble = Ensemble()
        if not self.ensemble:
            self.redrawing = False
            return
        
        if self.child_list:
            #update the existing
            self.child_list.rebuild()
        else:
            self.child_list = ChildEmbedList(self.dbstate,
                                             self.uistate,
                                             [],
                                             self.ensemble)
            self.scroll.add(self.child_list)

        self.redrawing = False
        return True

    def view_photo(self, photo):
        """
        Open this picture in the default picture viewer.
        """
        photo_path = media_path_full(self.dbstate.db, photo.get_path())
        open_file_with_default_application(photo_path)

    def _button_press(self, obj, event, handle):
        if button_activated(event, _LEFT_BUTTON):
            self.change_active(handle)
        elif button_activated(event, _RIGHT_BUTTON):
            self.myMenu = Gtk.Menu()
            self.myMenu.append(self.build_menu_item(handle))
            self.myMenu.popup(None, None, None, None, event.button, event.time)

    def build_menu_item(self, handle):
        person = self.dbstate.db.get_person_from_handle(handle)
        name = name_displayer.display(person)

        item = Gtk.ImageMenuItem(None)
        image = Gtk.Image.new_from_icon_name('gtk-edit', Gtk.IconSize.MENU)
        image.show()
        label = Gtk.Label(label=_("Edit %s") % name)
        label.show()
        label.set_halign(Gtk.Align.START)

        item.set_image(image)
        item.add(label)

        item.connect('activate', self.edit_menu, handle)
        item.show()
        return item

    def edit_menu(self, obj, handle):
        person = self.dbstate.db.get_person_from_handle(handle)
        try:
            EditPerson(self.dbstate, self.uistate, [], person)
        except WindowActiveError:
            pass

    def edit_button_press(self, obj, event, handle):
        if button_activated(event, _LEFT_BUTTON):
            self.edit_ensemble(obj, handle)
        
    def edit_textile(self, obj, handle):
        textile = self.dbstate.db.textile(handle)
        try:
            EditTextile(self.dbstate, self.uistate, [], textile)
        except WindowActiveError:
            pass

    def edit_active(self, obj):
        phandle = self.get_active()
        self.edit_ensemble(obj, phandle)

    def config_panel(self, configdialog):
        """
        Function that builds the widget in the configuration dialog
        """
        grid = Gtk.Grid()
        grid.set_border_width(12)
        grid.set_column_spacing(6)
        grid.set_row_spacing(6)

#        configdialog.add_checkbox(grid, 
#                _('Use shading'), 
#                0, 'preferences.relation-shade')
#        configdialog.add_checkbox(grid, 
#                _('Display edit buttons'), 
#                1, 'preferences.releditbtn')
#        checkbox = Gtk.CheckButton(label=_('View links as website links'))
#        theme = self._config.get('preferences.relation-display-theme')
#        checkbox.set_active(theme == 'WEBPAGE')
#        checkbox.connect('toggled', self._config_update_theme)
#        grid.attach(checkbox, 1, 2, 8, 1)

        return _('Layout'), grid

    def _get_configure_page_funcs(self):
        """
        Return a list of functions that create gtk elements to use in the 
        notebook pages of the Configure dialog
        
        :return: list of functions
        """
        return [self.config_panel]

    def start_scan(self, obj):
        print ("starting scan")
        self.uistate.viewmanager.do_connect_board()
        
        #scan a tag if a board was found and initialized
        board = self.uistate.viewmanager.board
        if board:
            self.scan_action_start.set_visible(False)
            self.scan_action_stop.set_visible(True)
            GLib.timeout_add(1000, self.test_for_tag, self.uistate.viewmanager)

    def stop_scan(self, obj):
        print ("stop scanning")
        self.uistate.viewmanager.do_reset_board()
        self.tag = None
        self.scan_action_start.set_visible(True)
        self.scan_action_stop.set_visible(False)

    def test_for_tag(self, vm):
        board = self.uistate.viewmanager.board
        if board:            
            tag = self.uistate.viewmanager.obtain_last_read_tag()
            if tag:
                GLib.idle_add(self.react_to_new_tag, tag)
            return True
        else:
            #stop the thread
            return False

    def react_to_new_tag(self, tag):
        #print ("Found a new tag", tag)
        tagdict = {}
        stringvalues = ['Type', 'ID', 'URL', 'C']
        floatvalues = ['Id', 'Vres', 'Th', 'W']
        for messvalue in tag:
            # a message contains optionally valuelist;;valuelist;;valuelist
            if messvalue.startswith('NFC Tag ID:'):
                tagdict['TAGID'] = messvalue.split(':')[-1].strip()
            for value in messvalue.split(';;'):
                #print ('processing value', value)
                vdata = value.split(';')
                if len(vdata) < 2:
                    #no data that interests us
                    continue
                if vdata[0] in stringvalues:
                    tagdict[vdata[0]] = vdata[1].strip()
                elif vdata[0] in floatvalues:
                    tagdict[vdata[0]] = float(vdata[1].strip())
        
        textile = Textile()
        textile.wearnow_id = tagdict.get('ID', None)
        tagkey2attrkey = {
            'TAGID'     : AttributeType.RFID_ID,
            'Id'        : AttributeType.THERM_INS ,
            'Vres'      : AttributeType.MOIST_VAP_RESIST,
            'C'         : AttributeType.COLOR,
            'W'         : AttributeType.WEIGHT,
            'Th'        : AttributeType.THICKNESS,
        }
        for key in tagkey2attrkey.keys():
            if key in tagdict:
                attr = Attribute()
                attr.set_type(tagkey2attrkey[key])
                attr.value = str(tagdict[key])
                textile.add_attribute(attr)
                #print ('added attr', attr)
        if 'Type' in tagdict:
            ttype = TextileType()
            ttype.set_from_xml_str(tagdict['Type'])
            textile.set_type(ttype)
        if 'URL' in tagdict:
            url = Url()
            path = tagdict['URL']
            if not (path.startswith('http://') or path.startswith('https://')):
                path = 'http://' + path
            url.set_path(path)
            url.set_type(UrlType.WEB_HOME)
            textile.add_url(url)
            #print ('added url', url)
        if self.tag and self.tag.get_wearnow_id() == textile.get_wearnow_id():
            #same tag as before read. We do not process it again!
            return False
        else:
            self.tag = textile
            self.local_tag_react(textile)
        return False
    
    def local_tag_react(self, textile):
        textiledb = self.dbstate.db.get_textile_from_wearnow_id(textile.get_wearnow_id())
        if textiledb:
            #existing garment, add it to the list
            ref = ChildRef()
            ref.ref = textiledb.get_handle()
            self.ensemble.add_child_ref(ref)
            self.redraw()
        else:
            #new garment, show editor first
            from wearnow.gui.editors import EditTextile
            try:
                EditTextile(self.dbstate, self.uistate, [], textile, 
                            callback=self.textile_new_added)
            except WindowActiveError:
                pass

    def textile_new_added(self, textile):
        """ a textile was added, we add to ensemble
        """
        ref = ChildRef()
        ref.ref = textile.get_handle()
        self.ensemble.add_child_ref(ref)
        self.redraw()

    def compute_comfort(self, obj):
        from wearnow.tex.logic.pmv import calc_comfort
        garments = []
        for ref in self.ensemble.get_child_ref_list(): 
            garments.append(self.dbstate.db.get_textile_from_handle(ref.ref))
        ins = []
        vapres = []
        ttype = []
        for garm in garments:
            ins.append(None)
            vapres.append(None)
            ttype.append(garm.get_type())
            for attr in garm.get_attribute_list():
                if attr.get_type() == AttributeType.THERM_INS:
                    ins[-1] = float(attr.get_value())
                if attr.get_type() == AttributeType.MOIST_VAP_RESIST:
                    vapres[-1] = float(attr.get_value())
                
                    
        appdata = {
            'climate': {
                'ta' : self.scale_temp.get_value(),
                'RH' : self.scale_RH.get_value(),
                },
            'activity' : self.scale_activity.get_value(),
            'ensemble' : {
                'insulation': ins,
                'vapresist' : vapres,
                'garmtype'  : ttype,
                }
        }
        print ('appdata', appdata)
    
        comf = calc_comfort(appdata)
        self.entr_comfort.set_text(str(comf))

def button_activated(event, mouse_button):
    if (event.type == Gdk.EventType.BUTTON_PRESS and
        event.button == mouse_button) or \
       (event.type == Gdk.EventType.KEY_PRESS and
        event.keyval in (_RETURN, _KP_ENTER, _SPACE)):
        return True
    else:
        return False

