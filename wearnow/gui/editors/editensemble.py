#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2009       Gary Burton
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

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import pickle

#-------------------------------------------------------------------------
#
# enable logging for error handling
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".")

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext
from ..ddtargets import DdTargets
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import GObject
from gi.repository import GLib

#-------------------------------------------------------------------------
#
# wearnow modules
#
#-------------------------------------------------------------------------
from wearnow.tex.lib import ChildRef, Ensemble, NoteType, Textile
from wearnow.tex.db.txn import DbTxn
from wearnow.tex.errors import WindowActiveError
from ..glade import Glade

from .editprimary import EditPrimary
from .edittextile import EditTextile
from .displaytabs import (EmbeddedList, NoteTab, GalleryTab, 
                         ChildModel, TEXT_COL, MARKUP_COL, ICON_COL)
from ..widgets import (PrivacyButton, MonitoredEntry,
                         MonitoredTagList)
from wearnow.tex.plug import CATEGORY_QR_ENSEMBLE
from ..dialog import (ErrorDialog, WarningDialog, MessageHideDialog)
from ..selectors import SelectorFactory
from wearnow.tex.utils.id import create_id

SelectTextile = SelectorFactory('Textile')

_RETURN = Gdk.keyval_from_name("Return")
_KP_ENTER = Gdk.keyval_from_name("KP_Enter")
_LEFT_BUTTON = 1
_RIGHT_BUTTON = 3

class ChildEmbedList(EmbeddedList):
    """
    The child embed list is specific to the Edit Ensemble dialog, so it
    is contained here instead of in displaytabs.
    """

    _HANDLE_COL = 14
    _DND_TYPE = DdTargets.CHILDREF
    _DND_EXTRA = DdTargets.TEXTILE_LINK

    _MSG = {
        'add'   : _('Create a new garment and add to the ensemble'),
        'del'   : _('Remove the garment from the ensemble'),
        'edit'  : _('Edit the gar,emt reference'),
        'share' : _('Add an existing garment as a part of the ensemble'),
        'up'    : _('Move the garment up in the list'),
        'down'  : _('Move the garment down in the list'),
        }

    # (name, column in model, width, markup/text, font weight)
    _column_names = [
        (_('#'), 0, 25, TEXT_COL, -1, None),
        (_('ID'), 1, 60, TEXT_COL, -1, None),
        (_('Description'), 10, 250, TEXT_COL, -1, None),
        (_('Private'), 13,  30, ICON_COL, -1, 'wearnow-lock')
        ]
    
    def __init__(self, dbstate, uistate, track, ensemble):
        """
        Create the object, storing the passed ensemble value
        """
        self.ensemble = ensemble
        EmbeddedList.__init__(self, dbstate, uistate, track, _('_Garments'), 
                              ChildModel, share_button=True, move_buttons=True)

    def get_popup_menu_items(self):
        return [
            (False, _('Edit Garment'), 'gtk-edit',
                                            self.edit_child_button_clicked),
            (True, _('_Add'), 'list-add', self.add_button_clicked),
            (True, _('Add an existing Garment'), None, self.share_button_clicked),
            (False, _('Edit relationship'), 'gtk-edit',
                                            self.edit_button_clicked),
            (True, _('_Remove'), 'list-remove', self.del_button_clicked),
            ]

    def get_middle_click(self):
        return self.edit_child_button_clicked

    def get_icon_name(self):
        return 'wearnow-ensemble'

    def get_data(self):
        """
        Normally, get_data returns a list. However, we return ensemble
        object here instead.
        """
        return self.ensemble.get_child_ref_list()

    def column_order(self):
        return [(1, 0), (1, 1), (1, 2), (0, 3)]

    def add_button_clicked(self, obj=None):
        textile = Textile()

        EditTextile(self.dbstate, self.uistate, self.track, textile,
                   self.new_child_added)

    def handle_extra_type(self, objtype, obj):
        """
        Called when a textile is dropped onto the list.  objtype will be 
        'textile-link' and obj will contain a textile handle.
        """
        textile = self.dbstate.db.get_textile_from_handle(obj)
        self.new_child_added(textile)

    def new_child_added(self, textile):
        ref = ChildRef()
        ref.ref = textile.get_handle()
        self.ensemble.add_child_ref(ref)
        self.rebuild()
        GLib.idle_add(self.tree.scroll_to_cell,
                         len(self.ensemble.get_child_ref_list()) - 1)
#        self.call_edit_childref(ref)

    def child_ref_edited(self, textile):
        self.rebuild()

    def share_button_clicked(self, obj=None):
        # it only makes sense to skip those who are already in the ensemble
        skip_list = []
        skip_list.extend(x.ref for x in self.ensemble.get_child_ref_list())

        sel = SelectTextile(self.dbstate, self.uistate, self.track,
                           _("Select Garment"), skip=skip_list)
        textile = sel.run()
        
        if textile:
            ref = ChildRef()
            ref.ref = textile.get_handle()
            self.ensemble.add_child_ref(ref)
            self.rebuild()
            GLib.idle_add(self.tree.scroll_to_cell,
                             len(self.ensemble.get_child_ref_list()) - 1)
            self.call_edit_childref(ref)

    def run(self, skip):
        skip_list = [_f for _f in skip if _f]
        SelectTextile(self.dbstate, self.uistate, self.track,
                     _("Select Garment"), skip=skip_list)

    def del_button_clicked(self, obj=None):
        ref = self.get_selected()
        if ref:
            self.ensemble.remove_child_ref(ref)
            self.rebuild()

    def edit_button_clicked(self, obj=None):
        ref = self.get_selected()
        if ref:
            self.call_edit_childref(ref)

    def call_edit_childref(self, ref):
        t = self.dbstate.db.get_textile_from_handle(ref.ref)
        try:
            EditTextile(self.dbstate, self.uistate, self.track,
                         t, self.child_ref_edited)
        except WindowActiveError:
            pass

    def edit_child_button_clicked(self, obj=None):
        ref = self.get_selected()
        if ref:
            t = self.dbstate.db.get_textile_from_handle(ref.ref)
            try:
                EditTextile(self.dbstate, self.uistate, self.track,
                       t, self.child_ref_edited)
            except WindowActiveError:
                pass

#-------------------------------------------------------------------------
#
# EditEnsemble
#
#-------------------------------------------------------------------------
class EditEnsemble(EditPrimary):

    QR_CATEGORY = CATEGORY_QR_ENSEMBLE
    
    def __init__(self, dbstate, uistate, track, ensemble, callback=None):
        
        EditPrimary.__init__(self, dbstate, uistate, track,
                             ensemble, dbstate.db.get_ensemble_from_handle,
                             dbstate.db.get_ensemble_from_wearnow_id,
                             callback)

    def _cleanup_on_exit(self):
        """Unset all things that can block garbage collection.
        Finalize rest
        """
        #FIXME, we rebind show_all below, this prevents garbage collection of
        #  the dialog, fix the rebind
        self.window.show_all = None
        EditPrimary._cleanup_on_exit(self)

    def empty_object(self):
        return Ensemble()

    def _local_init(self):
        self.build_interface()
        
        self.added = self.obj.handle is None
        if self.added:
            self.obj.handle = create_id()
            
    
    def _connect_db_signals(self):
        """
        implement from base class DbGUIElement
        Register the callbacks we need.
        Note:
            * we do not connect to person-delete, as a delete of a person in
                the ensemble outside of this editor will cause a ensemble-update
                signal of this ensemble
        """
        self.callman.register_handles({'ensemble': [self.obj.get_handle()]})
        self.callman.register_callbacks(
           {'ensemble-update': self.check_for_ensemble_change,
            'ensemble-delete': self.check_for_close,
            'ensemble-rebuild': self._do_close,
            'textile-rebuild': self._do_close,
           })
        self.callman.connect_all(keys=['ensemble', 'textile'])

    def check_for_ensemble_change(self, handles):
        """
        Callback for ensemble-update signal
        1. This method checks to see if the ensemble shown has been changed. This 
            is possible eg in the relationship view. If the ensemble was changed, 
            the view is refreshed and a warning dialog shown to indicate all 
            changes have been lost.
            If a source/note/event is deleted, this method is called too. This
            is unfortunate as the displaytabs can track themself a delete and
            correct the view for this. Therefore, these tabs are not rebuild.
            Conclusion: this method updates so that remove/change of parent or
            remove/change of children in relationship view reloads the ensemble
            from db.
        2. Changes in other Ensembles are of no consequence to the ensemble shown
        """ 
        if self.obj.get_handle() in handles:
            #rebuild data
            ## Todo: Gallery and note tab are not rebuild ??
            objreal = self.dbstate.db.get_ensemble_from_handle(
                                                        self.obj.get_handle())
            #update selection of data that we obtain from database change:
            maindatachanged = (self.obj.wearnow_id != objreal.wearnow_id or
                self.obj.private != objreal.private or
                self.obj.get_tag_list() != objreal.get_tag_list() or
                self.obj.child_ref_list != objreal.child_ref_list)
            if maindatachanged:
                self.obj.wearnow_id = objreal.wearnow_id
                self.obj.private = objreal.private
                self.obj.set_tag_list(objreal.get_tag_list())
                self.obj.child_ref_list = objreal.child_ref_list
                self.reload_textiles()

            # No matter why the ensemble changed (eg delete of a source), we notify
            # the user
            WarningDialog(
            _("Ensemble has changed"),
            _("The %(object)s you are editing has changed outside this editor." 
              " This can be due to a change in one of the main views, for "
              "example a source used here is deleted in the source view.\n"
              "To make sure the information shown is still correct, the "
              "data shown has been updated. Some edits you have made may have"
              " been lost.") % {'object': _('ensemble')}, parent=self.window)

    def reload_textiles(self):
        self.child_tab.rebuild()

    def get_menu_title(self):
        if self.obj and self.obj.get_handle():
            dialog_title = self.obj.get_wearnow_id() or "New Ensemble"
            dialog_title = _("Ensemble") + ': ' + dialog_title
        else:
            dialog_title = _("New Ensemble")
        return dialog_title

    def build_menu_names(self, ensemble):
        return (_('Edit Ensemble'), self.get_menu_title())

    def build_interface(self):
        self.width_key = 'interface.ensemble-width'
        self.height_key = 'interface.ensemble-height'
        
        self.top = Glade()
        self.set_window(self.top.toplevel, None, self.get_menu_title())

        # HACK: how to prevent hidden items from showing
        #       when you use show_all?
        # Consider using show() rather than show_all()?
        # FIXME: remove if we can use show()
        self.window.show_all = self.window.show

        #allow for a context menu
        self.set_contexteventbox(self.top.get_object("eventboxtop"))
        #allow for drag of the ensemble object from eventboxtop
        self.contexteventbox.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, 
                                   [], Gdk.DragAction.COPY)
        tglist = Gtk.TargetList.new([])
        tglist.add(DdTargets.ENSEMBLE_LINK.atom_drag_type,
                   DdTargets.ENSEMBLE_LINK.target_flags,
                   DdTargets.ENSEMBLE_LINK.app_id)
        self.contexteventbox.drag_source_set_target_list(tglist)
        self.contexteventbox.drag_source_set_icon_name('wearnow-ensemble')
        self.contexteventbox.connect('drag_data_get', self.on_drag_data_get_ensemble)

    def on_drag_data_get_ensemble(self,widget, context, sel_data, info, time):
        if info == DdTargets.ENSEMBLE_LINK.app_id:
            data = (DdTargets.ENSEMBLE_LINK.drag_type, id(self), self.obj.get_handle(), 0)
            sel_data.set(DdTargets.ENSEMBLE_LINK.atom_drag_type, 8, pickle.dumps(data))

    def _connect_signals(self):
        self.define_ok_button(self.top.get_object('ok'), self.save)
        self.define_cancel_button(self.top.get_object('cancel'))
        self.define_help_button(self.top.get_object('button119'))

    def _can_be_replaced(self):
        pass

    def _setup_fields(self):
        
        self.private = PrivacyButton(
            self.top.get_object('private'),
            self.obj,
            self.db.readonly)

        self.gid = MonitoredEntry(
            self.top.get_object('gid'),
            self.obj.set_wearnow_id,
            self.obj.get_wearnow_id,
            self.db.readonly)
        
        self.tags = MonitoredTagList(
            self.top.get_object("tag_label"), 
            self.top.get_object("tag_button"), 
            self.obj.set_tag_list, 
            self.obj.get_tag_list,
            self.db,
            self.uistate, self.track,
            self.db.readonly)

    def _create_tabbed_pages(self):

        notebook = Gtk.Notebook()

        self.child_list = ChildEmbedList(self.dbstate,
                                         self.uistate,
                                         self.track,
                                         self.obj)
        self.child_tab = self._add_tab(notebook, self.child_list)
        self.track_ref_for_deletion("child_list")
        self.track_ref_for_deletion("child_tab")

        self.note_tab = NoteTab(self.dbstate,
                                self.uistate,
                                self.track,
                                self.obj.get_note_list(),
                                self.get_menu_title(),
                                notetype=NoteType.ENSEMBLE)
        self._add_tab(notebook, self.note_tab)
        self.track_ref_for_deletion("note_tab")
            
        self.gallery_tab = GalleryTab(self.dbstate,
                                      self.uistate,
                                      self.track,
                                      self.obj.get_media_list())
        self._add_tab(notebook, self.gallery_tab)
        self.track_ref_for_deletion("gallery_tab")

        self._setup_notebook_tabs( notebook)
        notebook.show_all()

        self.hidden = (notebook, self.top.get_object('info'))
        self.top.get_object('vbox').pack_start(notebook, True, True, 0)

    def edit_textile(self, obj, event, handle):
        if button_activated(event, _LEFT_BUTTON):
            try:
                textile = self.db.get_textile_from_handle(handle)
                EditTextile(self.dbstate, self.uistate,
                           self.track, textile)
            except WindowActiveError:
                pass

    def object_is_empty(self):
        return (
                len(self.obj.get_child_ref_list()) == 0
               )
            
    def save(self, *obj):
        ## FIXME: how to catch a specific error?
        #try:
        self.__do_save()
        #except bsddb_db.DBRunRecoveryError as msg:
        #    RunDatabaseRepair(msg[1])

    def __do_save(self):
        self.ok_button.set_sensitive(False)

        if not self.added:
            original = self.db.get_ensemble_from_handle(self.obj.handle)
        else:
            original = None

        # do some basic checks

        child_list = [ ref.ref for ref in self.obj.get_child_ref_list() ]

        if not original and self.object_is_empty():
            ErrorDialog(
                _("Cannot save ensemble"),
                _("No data exists for this ensemble. "
                  "Please enter data or cancel the edit."))
            self.ok_button.set_sensitive(True)
            return
        
        (uses_dupe_id, id) = self._uses_duplicate_id()
        if uses_dupe_id:
            msg1 = _("Cannot save ensemble. ID already exists.")
            msg2 = _("You have attempted to use the existing WearNow ID with "
                         "value %(id)s. This value is already used. Please "
                         "enter a different ID or leave "
                         "blank to get the next available ID value.") % {
                         'id' : id}
            ErrorDialog(msg1, msg2)
            self.ok_button.set_sensitive(True)
            return

        # We disconnect the callbacks to all signals we connected earlier.
        # This prevents the signals originating in any of the following
        # commits from being caught by us again.
        self._cleanup_callbacks()
            
        if not original and not self.object_is_empty():
            with DbTxn(_("Add Ensemble"), self.db) as trans:
#
#                # for each child, add the ensemble handle to the child
#                for ref in self.obj.get_child_ref_list():
#                    child = self.db.get_person_from_handle(ref.ref)
#                    # fix - relationships need to be extracted from the list
#                    child.add_parent_ensemble_handle(self.obj.handle)
#                    self.db.commit_person(child, trans)

                self.db.add_ensemble(self.obj, trans)
        elif original.serialize() != self.obj.serialize():

            with DbTxn(_("Edit Ensemble"), self.db) as trans:
#
#                orig_set = set(original.get_child_ref_list())
#                new_set = set(self.obj.get_child_ref_list())

#                # remove the ensemble from children which have been removed
#                for ref in orig_set.difference(new_set):
#                    person = self.db.get_person_from_handle(ref.ref)
#                    person.remove_parent_ensemble_handle(self.obj.handle)
#                    self.db.commit_person(person, trans)
            
#                # add the ensemble to children which have been added
#                for ref in new_set.difference(orig_set):
#                    person = self.db.get_person_from_handle(ref.ref)
#                    person.add_parent_ensemble_handle(self.obj.handle)
#                    self.db.commit_person(person, trans)

                if not self.object_is_empty():
                    if not self.obj.get_wearnow_id():
                        self.obj.set_wearnow_id(
                                         self.db.find_next_ensemble_wearnow_id())
                    self.db.commit_ensemble(self.obj, trans)

        self._do_close()
        if self.callback:
            self.callback(self.obj)
        self.callback = None

def button_activated(event, mouse_button):
    if (event.type == Gdk.EventType.BUTTON_PRESS and
        event.button == mouse_button) or \
       (event.type == Gdk.EventType.KEY_PRESS and
        event.keyval in (_RETURN, _KP_ENTER)):
        return True
    else:
        return False
