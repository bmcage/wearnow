# WearNow - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2008       Gary Burton
# Copyright (C) 2009-2010  Nick Hall
# Copyright (C) 2010       Benny Malengier
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
Provide the base for a list textile view.
"""

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk
import os, sys
#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
_LOG = logging.getLogger(".gui.textileview")

#-------------------------------------------------------------------------
#
# wearnow modules
#
#-------------------------------------------------------------------------
from wearnow.tex.lib import Textile
from wearnow.tex.db.txn import DbTxn
from wearnow.gui.views.listview import ListView, TEXT, MARKUP, ICON
from wearnow.gui.actiongroup import ActionGroup
from wearnow.tex.utils.string import data_recover_msg
from wearnow.gui.dialog import ErrorDialog, MultiSelectDialog, QuestionDialog
from wearnow.tex.errors import WindowActiveError
from wearnow.gui.views.bookmarks import TextileBookmarks
from wearnow.tex.config import config
from wearnow.tex.utils.board import get_the_board
from wearnow.gui.ddtargets import DdTargets
from wearnow.gui.filters.sidebar import TextileSidebarFilter
from wearnow.tex.plug import CATEGORY_QR_TEXTILE

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.sgettext

#-------------------------------------------------------------------------
#
# TextileView
#
#-------------------------------------------------------------------------
class BaseTextileView(ListView):
    """
    Base view for TextileView listviews ListView, a treeview
    """
    COL_DESCR = 0
    COL_ID    = 1
    COL_PRIV  = 2
    COL_TAGS  = 3
    COL_CHAN  = 4
    # column definitions
    COLUMNS = [
        (_('Description'), TEXT, None),
        (_('ID'), TEXT, None),
        (_('Private'), ICON, 'wearnow-lock'),
        (_('Tags'), TEXT, None),
        (_('Last Changed'), TEXT, None),
        ]
    # default setting with visible columns, order of the col, and their size
    CONFIGSETTINGS = (
        ('columns.visible', [COL_DESCR, COL_ID]),
        ('columns.rank', [COL_DESCR, COL_ID, COL_PRIV,
                           COL_TAGS, COL_CHAN]),
        ('columns.size', [275, 75, 30, 100, 100])
        )  
    ADD_MSG     = _("Add a new textile")
    EDIT_MSG    = _("Edit the selected textile")
    DEL_MSG     = _("Remove the selected textile")
    MERGE_MSG   = _("Merge the selected textiles")
    FILTER_TYPE = "Textile"
    QR_CATEGORY = CATEGORY_QR_TEXTILE 

    def __init__(self, pdata, dbstate, uistate, title, model, nav_group=0):
        """
        Create the Textile View
        """
        signal_map = {
            'textile-add'     : self.row_add,
            'textile-update'  : self.row_update,
            'textile-delete'  : self.row_delete,
            'textile-rebuild' : self.object_build,
            'no-database': self.no_database,
            }
 
        ListView.__init__(
            self, title, pdata, dbstate, uistate,
            model, signal_map,
            TextileBookmarks, nav_group,
            multiple=True,
            filter_class=TextileSidebarFilter)
            
        self.func_list.update({
            '<PRIMARY>J' : self.jump,
            '<PRIMARY>BackSpace' : self.key_delete,
            })

        self.additional_uis.append(self.additional_ui())

    def navigation_type(self):
        """
        Return the navigation type of the view.
        """
        return 'Textile'

    def drag_info(self):
        """
        Specify the drag type for a single selection
        """
        return DdTargets.TEXTILE_LINK
        
    def exact_search(self):
        """
        Returns a tuple indicating columns requiring an exact search
        'female' contains the string 'male' so we need an exact search
        """
        return ()

    def get_stock(self):
        """
        Use the wearnowtextile stock icon
        """
        return 'wearnow-textile'

    def additional_ui(self):
        """
        Defines the UI string for UIManager
        """
        return '''<ui>
          <menubar name="MenuBar">
            <menu action="FileMenu">
              <placeholder name="LocalExport">
                <menuitem action="ExportTab"/>
              </placeholder>
            </menu>
            <menu action="BookMenu">
              <placeholder name="AddEditBook">
                <menuitem action="AddBook"/>
                <menuitem action="EditBook"/>
              </placeholder>
            </menu>
            <menu action="GoMenu">
              <placeholder name="CommonGo">
                <menuitem action="Back"/>
                <menuitem action="Forward"/>
                <separator/>
                <menuitem action="HomeTextile"/>
                <separator/>
              </placeholder>
            </menu>
            <menu action="EditMenu">
              <placeholder name="CommonEdit">
                <menuitem action="Add"/>
                <menuitem action="Edit"/>
                <menuitem action="Remove"/>
                <menuitem action="Merge"/>
              </placeholder>
              <menuitem action="SetActive"/>
              <menuitem action="FilterEdit"/>
            </menu>
          </menubar>
          <toolbar name="ToolBar">
            <placeholder name="CommonNavigation">
              <toolitem action="Back"/>
              <toolitem action="Forward"/>  
              <toolitem action="HomeTextile"/>
            </placeholder>
            <placeholder name="CommonEdit">
              <toolitem action="Add"/>
              <toolitem action="Edit"/>
              <toolitem action="Remove"/>
              <toolitem action="Merge"/>
            </placeholder>
            <placeholder name = "Scan">
              <toolitem action="ScanStart"/>
              <toolitem action="ScanStop"/>
            </placeholder>
          </toolbar>
          <popup name="Popup">
            <menuitem action="Back"/>
            <menuitem action="Forward"/>
            <menuitem action="HomeTextile"/>
            <separator/>
            <menuitem action="Add"/>
            <menuitem action="Edit"/>
            <menuitem action="Remove"/>
            <menuitem action="Merge"/>
            <separator/>
            <menu name="QuickReport" action="QuickReport"/>
            <menu name="WebConnect" action="WebConnect"/>
          </popup>
        </ui>'''

    def get_handle_from_wearnow_id(self, gid):
        """
        Return the handle of the textile having the given WearNow ID. 
        """
        obj = self.dbstate.db.get_textile_from_wearnow_id(gid)
        if obj:
            return obj.get_handle()
        else:
            return None

    def add(self, obj):
        """
        Add a new textile to the database.
        """
        textile = Textile()
        from wearnow.gui.editors import EditTextile
        try:
            EditTextile(self.dbstate, self.uistate, [], textile)
        except WindowActiveError:
            pass
 
    def edit(self, obj):
        """
        Edit an existing textile in the database.
        """
        from wearnow.gui.editors import EditTextile
        for handle in self.selected_handles():
            textile = self.dbstate.db.get_textile_from_handle(handle)
            try:
                EditTextile(self.dbstate, self.uistate, [], textile)
            except WindowActiveError:
                pass

    def remove(self, obj):
        """
        Remove a textile from the database.
        """
        handles = self.selected_handles()
        if len(handles) == 1:
            textile = self._lookup_textile(handles[0])
            msg1 = self._message1_format(textile)
            msg2 = self._message2_format(textile)
            msg2 = "%s %s" % (msg2, data_recover_msg)
            # This gets textile to delete deom self.active_textile:
            QuestionDialog(msg1, 
                           msg2, 
                           _('_Delete Textile'), 
                           self.delete_textile_response)
        else:
            # Ask to delete; option to cancel, delete rest
            # This gets textile to delete from parameter
            MultiSelectDialog(self._message1_format,
                              self._message2_format, 
                              handles,
                              self._lookup_textile,
                              yes_func=self.delete_textile_response) # Yes

    def _message1_format(self, textile):
        return _('Delete %s?') % (textile.description + 
                                  (" [%s]" % textile.wearnow_id))

    def _message2_format(self, textile):
        return _('Deleting the textile will remove the textile '
                 'from the database.')

    def _lookup_textile(self, handle):
        """
        Get the next textile from handle.
        """
        textile = self.dbstate.db.get_textile_from_handle(handle)
        self.active_textile = textile
        return textile

    def delete_textile_response(self, textile=None):
        """
        Deletes the textile from the database.
        """
        # set the busy cursor, so the user knows that we are working
        self.uistate.set_busy_cursor(True)

        # create the transaction
        with DbTxn('', self.dbstate.db) as trans:
        
            # create name to save
            textile = self.active_textile
            active_name = _("Delete Textile (%s)") % textile.description

            # delete the textile from the database
            # Above will emit textile-delete, which removes the textile via 
            # callback to the model, so row delete is signaled
            self.dbstate.db.delete_textile_from_database(textile, trans)
            trans.set_description(active_name)

        self.uistate.set_busy_cursor(False)

    def define_actions(self):
        """
        Required define_actions function for PageView. Builds the action
        group information required. We extend beyond the normal here, 
        since we want to have more than one action group for the TextileView.
        Most PageViews really won't care about this.

        Special action groups for Forward and Back are created to allow the
        handling of navigation buttons. Forward and Back allow the user to
        advance or retreat throughout the history, and we want to have these
        be able to toggle these when you are at the end of the history or
        at the beginning of the history.
        """

        ListView.define_actions(self)

        self.all_action = ActionGroup(name=self.title + "/TextileAll")
        self.edit_action = ActionGroup(name=self.title + "/TextileEdit")
        self.scan_action_start = ActionGroup(name=self.title + "/TextileScanStart")
        self.scan_action_stop = ActionGroup(name=self.title + "/TextileScanStop")

        self.all_action.add_actions([
                ('FilterEdit', None, _('Textile Filter Editor'), None, None,
                self.filter_editor),
                ('Edit', 'gtk-edit', _("action|_Edit..."),
                "<PRIMARY>Return", self.EDIT_MSG, self.edit), 
                ('QuickReport', None, _("Quick View"), None, None, None), 
                ('WebConnect', None, _("Web Connection"), None, None, None), 
                ])


        self.edit_action.add_actions(
            [
                ('Add', 'list-add', _("_Add..."), "<PRIMARY>Insert",
                 self.ADD_MSG, self.add),
                ('Remove', 'list-remove', _("_Remove"), "<PRIMARY>Delete",
                 self.DEL_MSG, self.remove),
                ('Merge', 'wearnow-merge', _('_Merge...'), None,
                 self.MERGE_MSG, self.merge),
                ('ExportTab', None, _('Export View...'), None, None,
                 self.export),
                ])

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
        self._add_action_group(self.edit_action)
        self._add_action_group(self.all_action)
        self._add_action_group(self.scan_action_start)
        self._add_action_group(self.scan_action_stop)

    def enable_action_group(self, obj):
        """
        Turns on the visibility of the View's action group.
        """
        ListView.enable_action_group(self, obj)
        self.all_action.set_visible(True)
        self.edit_action.set_visible(True)
        self.edit_action.set_sensitive(not self.dbstate.db.readonly)
        self.scan_action_start.set_visible(True)
        self.scan_action_stop.set_visible(False)
        
    def disable_action_group(self):
        """
        Turns off the visibility of the View's action group.
        """
        ListView.disable_action_group(self)

        self.all_action.set_visible(False)
        self.edit_action.set_visible(False)
        self.scan_action_start.set_visible(False)
        self.stop_scan(None)
        self.scan_action_stop.set_visible(False)

    def merge(self, obj):
        """
        Merge the selected people.
        """
        mlist = self.selected_handles()

        if len(mlist) != 2:
            ErrorDialog(
        _("Cannot merge people"), 
        _("Exactly two people must be selected to perform a merge. "
          "A second textile can be selected by holding down the "
          "control key while clicking on the desired textile."))
        else:
            from wearnow.gui.merge import MergeTextile
            MergeTextile(self.dbstate, self.uistate, mlist[0], mlist[1])

    def tag_updated(self, handle_list):
        """
        Update tagged rows when a tag color changes.
        """
        all_links = set([])
        for tag_handle in handle_list:
            links = set([link[1] for link in
                         self.dbstate.db.find_backlink_handles(tag_handle,
                                                    include_classes='Textile')])
            all_links = all_links.union(links)
        self.row_update(list(all_links))

    def add_tag(self, transaction, textile_handle, tag_handle):
        """
        Add the given tag to the given textile.
        """
        textile = self.dbstate.db.get_textile_from_handle(textile_handle)
        textile.add_tag(tag_handle)
        self.dbstate.db.commit_textile(textile, transaction)

    def start_scan(self, obj):
        print ("starting scan")
        import serial
        base_dir = config.get('board.basedir')
        try:
            port = get_the_board(base_dir   =base_dir,
                                 identifier =config.get('board.port-id'))
        except:
            import traceback
            _LOG.warn("Error obtaining board")
            print (port)
            traceback.print_exc()
        self.arduino = serial.Serial(base_dir + os.sep + port, 9600,
                                     timeout=5, writeTimeout=0)
        if sys.platform == 'linux':
            # noinspection PyUnresolvedReferences
            self.arduino.nonblocking()
        import time
        time.sleep(5)
        read = []
        start = False
        while 1:
            input_string = self.arduino.readline()
            input_string = input_string.decode('utf-8')
            input_string = input_string.strip('\r\n')
            print ('read', input_string, type(input_string))
            if input_string.strip() == "Scan a NFC tag":
                print ("START ON TRUE")
                start = True
            if start:
                read.append( input_string)
                print ('test', read)
                if read[-1] == 'End Tag':
                    break
#        self.uistate.viewmanager.do_connect_board()
#        
#        #scan a tag if a board was found and initialized
#        board = self.uistate.viewmanager.board
#        if board:
#            self.scan_action_start.set_visible(False)
#            self.scan_action_stop.set_visible(True)
#            board.ndef_request_read_tag()
#            #at the moment this will block the app.
#            import time
#            time.sleep(10)
#            board.get_ndef_read_tag(timeout=20)
#            
#            #AGAIN
#            print ('doing it again')
#            board.ndef_request_read_tag()
#            board.get_ndef_read_tag(timeout=20)
        
    def stop_scan(self, obj):
        print ("stop scanning")
        self.uistate.viewmanager.do_reset_board()
        self.scan_action_start.set_visible(True)
        self.scan_action_stop.set_visible(False)

    def get_default_gramplets(self):
        """
        Define the default gramplets for the sidebar and bottombar.
        """
        return (("Textile Filter",),
                ("Textile Details",
                 "Textile Gallery",
                 "Textile Events",
                 "Textile Notes",
                 "Textile Attributes",
                 "Textile Backlinks"))
