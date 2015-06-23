# wearnow - a GTK+/GNOME based program
#
# Copyright (C) 2001-2006  Donald N. Allingham
# Copyright (C) 2010       Nick Hall
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
Ensemble View.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext
import logging
_LOG = logging.getLogger(".plugins.familyview")
#-------------------------------------------------------------------------
#
# GNOME/GTK+ modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk

#-------------------------------------------------------------------------
#
# wearnow modules
#
#-------------------------------------------------------------------------
from wearnow.tex.lib import Ensemble
from wearnow.gui.views.listview import ListView, TEXT, MARKUP, ICON
from wearnow.gui.views.treemodels import EnsembleModel
from wearnow.gui.views.bookmarks import EnsembleBookmarks
from wearnow.tex.errors import WindowActiveError
from wearnow.gui.dialog import ErrorDialog
from wearnow.gui.filters.sidebar import EnsembleSidebarFilter
from wearnow.tex.plug import CATEGORY_QR_ENSEMBLE
from wearnow.gui.ddtargets import DdTargets

#-------------------------------------------------------------------------
#
# EnsembleView
#
#-------------------------------------------------------------------------
class EnsembleView(ListView):
    """ EnsembleView class, derived from the ListView
    """
    # columns in the model used in view
    COL_ID = 0
    COL_PRIV = 1
    COL_TAGS = 2
    COL_CHAN = 3
    # column definitions
    COLUMNS = [
        (_('ID'), TEXT, None),
        (_('Private'), ICON, 'wearnow-lock'),
        (_('Tags'), TEXT, None),
        (_('Last Changed'), TEXT, None),
        ]
    #default setting with visible columns, order of the col, and their size
    CONFIGSETTINGS = (
        ('columns.visible', [COL_ID, COL_CHAN]),
        ('columns.rank', [COL_ID, COL_PRIV, COL_TAGS, COL_CHAN]),
        ('columns.size', [75, 40, 100, 100])
        )    

    ADD_MSG     = _("Add a new ensemble")
    EDIT_MSG    = _("Edit the selected ensemble")
    DEL_MSG     = _("Delete the selected ensemble")
    MERGE_MSG   = _("Merge the selected ensembles")
    FILTER_TYPE = "Ensemble"
    QR_CATEGORY = CATEGORY_QR_ENSEMBLE

    def __init__(self, pdata, dbstate, uistate, nav_group=0):

        signal_map = {
            'ensemble-add'     : self.row_add,
            'ensemble-update'  : self.row_update,
            'ensemble-delete'  : self.row_delete,
            'ensemble-rebuild' : self.object_build,
            }

        ListView.__init__(
            self, _('Ensembles'), pdata, dbstate, uistate,
            EnsembleModel,
            signal_map,
            EnsembleBookmarks, nav_group,
            multiple=True,
            filter_class=EnsembleSidebarFilter)

        self.func_list.update({
            '<PRIMARY>J' : self.jump,
            '<PRIMARY>BackSpace' : self.key_delete,
            })

        self.additional_uis.append(self.additional_ui())

    def navigation_type(self):
        return 'Ensemble'

    def get_stock(self):
        return 'wearnow-ensemble'

    def additional_ui(self):
        return '''<ui>
          <menubar name="MenuBar">
            <menu action="FileMenu">
              <placeholder name="LocalExport">
                <menuitem action="ExportTab"/>
              </placeholder>
            </menu>
            <menu action="GoMenu">
              <placeholder name="CommonGo">
                <menuitem action="Back"/>
                <menuitem action="Forward"/>
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
              <menuitem action="FilterEdit"/>
            </menu>
           <menu action="BookMenu">
              <placeholder name="AddEditBook">
                <menuitem action="AddBook"/>
                <menuitem action="EditBook"/>
              </placeholder>
           </menu>
          </menubar>
          <toolbar name="ToolBar">
            <placeholder name="CommonNavigation">
              <toolitem action="Back"/>  
              <toolitem action="Forward"/>  
            </placeholder>
            <placeholder name="CommonEdit">
              <toolitem action="Add"/>
              <toolitem action="Edit"/>
              <toolitem action="Remove"/>
              <toolitem action="Merge"/>
            </placeholder>
          </toolbar>
          <popup name="Popup">
            <menuitem action="Back"/>
            <menuitem action="Forward"/>
            <separator/>
            <menuitem action="Add"/>
            <menuitem action="Edit"/>
            <menuitem action="Remove"/>
            <menuitem action="Merge"/>
            <separator/>
            <menu name="QuickReport" action="QuickReport"/>
          </popup>
        </ui>'''

    def define_actions(self):
        """Add the Forward action group to handle the Forward button."""

        ListView.define_actions(self)

        self._add_action('FilterEdit', None, _('Ensemble Filter Editor'),
                        callback=self.filter_editor,)
                        
        self.all_action = Gtk.ActionGroup(name=self.title + "/EnsembleAll")
        self.all_action.add_actions([
                ('QuickReport', None, _("Quick View"), None, None, None),
                ])
        self._add_action_group(self.all_action)

    def add_bookmark(self, obj):
        mlist = self.selected_handles()
        if mlist:
            self.bookmarks.add(mlist[0])
        else:
            from wearnow.gui.dialog import WarningDialog
            WarningDialog(
                _("Could Not Set a Bookmark"), 
                _("A bookmark could not be set because "
                  "no one was selected."))
        
    def add(self, obj):
        from wearnow.gui.editors import EditEnsemble
        ensemble = Ensemble()
        try:
            EditEnsemble(self.dbstate, self.uistate, [], ensemble)
        except WindowActiveError:
            pass

    def remove(self, obj):
        """
        Method called when deleting a ensemble from a ensemble view.
        """
        from wearnow.gui.dialog import QuestionDialog, MultiSelectDialog
        from wearnow.tex.utils.string import data_recover_msg
        handles = self.selected_handles()
        if len(handles) == 1:
            ensemble = self.dbstate.db.get_ensemble_from_handle(handles[0])
            msg1 = self._message1_format(ensemble)
            msg2 = self._message2_format(ensemble)
            msg2 = "%s %s" % (msg2, data_recover_msg)
            QuestionDialog(msg1, 
                           msg2, 
                           _('_Delete Ensemble'), 
                           lambda: self.delete_ensemble_response(ensemble))
        else:
            MultiSelectDialog(self._message1_format,
                              self._message2_format, 
                              handles,
                              self.dbstate.db.get_ensemble_from_handle,
                              yes_func=self.delete_ensemble_response)

    def _message1_format(self, ensemble):
        """
        Header format for remove dialogs.
        """
        return _('Delete %s?') % (_('ensemble') + 
                                  (" [%s]" % ensemble.wearnow_id))

    def _message2_format(self, ensemble):
        """
        Detailed message format for the remove dialogs.
        """
        return _('Deleting item will remove it from the database.')

    def delete_ensemble_response(self, ensemble):
        """
        Deletes the ensemble from the database. Callback to remove
        dialogs.
        """
        pass
#        from wearnow.tex.db.txn import DbTxn
#        # set the busy cursor, so the user knows that we are working
#        self.uistate.set_busy_cursor(True)
#        # create the transaction
#        with DbTxn('', self.dbstate.db) as trans:
#            wearnow_id = ensemble.wearnow_id
#            trans.set_description(_("Ensemble [%s]") % wearnow_id)
#        self.uistate.set_busy_cursor(False)
    
    def edit(self, obj):
        from wearnow.gui.editors import EditEnsemble
        for handle in self.selected_handles():
            ensemble = self.dbstate.db.get_ensemble_from_handle(handle)
            try:
                EditEnsemble(self.dbstate, self.uistate, [], ensemble)
            except WindowActiveError:
                pass
                
    def merge(self, obj):
        """
        Merge the selected Ensembles.
        """
        mlist = self.selected_handles()

        if len(mlist) != 2:
            msg = _("Cannot merge ensembles.")
            msg2 = _("Exactly two ensembles must be selected to perform a merge."
                     " A second ensemble can be selected by holding down the "
                     "control key while clicking on the desired ensemble.")
            ErrorDialog(msg, msg2)
        else:
            from wearnow.gui.merge import MergeEnsemble
            MergeEnsemble(self.dbstate, self.uistate, mlist[0], mlist[1])
            
    def drag_info(self):
        """
        Indicate that the drag type is a ENSEMBLE_LINK
        """
        return DdTargets.ENSEMBLE_LINK

    def tag_updated(self, handle_list):
        """
        Update tagged rows when a tag color changes.
        """
        all_links = set([])
        for tag_handle in handle_list:
            links = set([link[1] for link in
                         self.dbstate.db.find_backlink_handles(tag_handle,
                                                    include_classes='Ensemble')])
            all_links = all_links.union(links)
        self.row_update(list(all_links))

    def add_tag(self, transaction, ensemble_handle, tag_handle):
        """
        Add the given tag to the given ensemble.
        """
        ensemble = self.dbstate.db.get_ensemble_from_handle(ensemble_handle)
        ensemble.add_tag(tag_handle)
        self.dbstate.db.commit_ensemble(ensemble, transaction)

    def get_default_gramplets(self):
        """
        Define the default gramplets for the sidebar and bottombar.
        """
        return (("Ensemble Filter",),
                ("Ensemble Gallery",
                 "Ensemble Garments",
                 "Ensemble Backlinks"))
