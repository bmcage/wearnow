#
# wearnow - a GTK+/GNOME based program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2009-2011  Gary Burton
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
EditTextile Dialog. Provide the interface to allow the wearnow program
to edit information about a particular Textile.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.sgettext
import pickle

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk
from gi.repository import Gdk

#-------------------------------------------------------------------------
#
# wearnow modules
#
#-------------------------------------------------------------------------
from wearnow.tex.utils.file import media_path_full
from ..thumbnails import get_thumbnail_image
from ..utils import is_right_click, open_file_with_default_application
from wearnow.tex.lib import NoteType, Textile
from wearnow.tex.db.txn import DbTxn
from .. import widgets
from wearnow.tex.errors import WindowActiveError
from ..glade import Glade
from ..ddtargets import DdTargets
from ..widgets.menuitem import add_menuitem

from .editprimary import EditPrimary
from ..dialog import ErrorDialog, ICON

from .displaytabs import (AttrEmbedList, NoteTab, GalleryTab,
                          WebEmbedList,TextileBackRefList)
from wearnow.tex.plug import CATEGORY_QR_TEXTILE
from wearnow.tex.const import URL_HOMEPAGE
from wearnow.tex.utils.id import create_id

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------

WIKI_HELP_PAGE = _('%s_-_Entering_and_editing_data:_detailed_-_part_1') % URL_HOMEPAGE


class EditTextile(EditPrimary):
    """
    The EditTextile dialog is derived from the EditPrimary class.

    It allows for the editing of the primary object type of Textile.

    """

    QR_CATEGORY = CATEGORY_QR_TEXTILE

    def __init__(self, dbstate, uistate, track, textile, callback=None):
        """
        Create an EditTextile window.

        Associate a textile with the window.

        """
        EditPrimary.__init__(self, dbstate, uistate, track, textile,
                             dbstate.db.get_textile_from_handle,
                             dbstate.db.get_textile_from_wearnow_id, callback)

    def empty_object(self):
        """
        Return an empty Textile object for comparison for changes.

        This is used by the base class (EditPrimary).

        """
        textile = Textile()
        return textile

    def get_menu_title(self):
        if self.obj and self.obj.get_handle():
            name = self.obj.description
            title = _('Garment: %(name)s') % {'name': name}
        else:
            name = self.obj.description
            if name:
                title = _('New Garment: %(name)s')  % {'name': name}
            else:
                title = _('New Garment')
        return title

    def get_preview_name(self):
        prevname = self.obj.description
        return prevname

    def _local_init(self):
        """
        Performs basic initialization, including setting up widgets and the
        glade interface.

        Local initialization function.
        This is called by the base class of EditPrimary, and overridden here.

        """
        self.width_key = 'interface.textile-width'
        self.height_key = 'interface.textile-height'

        self.added = self.obj.handle is None
        if self.added:
            self.obj.handle = create_id()

        self.top = Glade()

        self.set_window(self.top.toplevel, None,
                        self.get_menu_title())

        self.obj_photo = self.top.get_object("personPix")
        self.frame_photo = self.top.get_object("frame5")
        self.eventbox = self.top.get_object("eventbox1")

        self.set_contexteventbox(self.top.get_object("eventboxtop"))

    def _post_init(self):
        """
        Handle any initialization that needs to be done after the interface is
        brought up.

        Post initalization function.
        This is called by _EditPrimary's init routine, and overridden in the
        derived class (this class).

        """
        self.load_textile_image()
        self.description.grab_focus()

    def _connect_signals(self):
        """
        Connect any signals that need to be connected.
        Called by the init routine of the base class (_EditPrimary).
        """
        self.define_cancel_button(self.top.get_object("button15"))
        self.define_ok_button(self.top.get_object("ok"), self.save)
        self.define_help_button(self.top.get_object("button134"),
                WIKI_HELP_PAGE,
                _('manpage section id|Editing_information_about_people'))

        self.eventbox.connect('button-press-event',
                                self._image_button_press)
        # allow to initiate a drag-and-drop with this textile if it has a handle
        #if self.obj.get_handle():
        tglist = Gtk.TargetList.new([])
        tglist.add(DdTargets.TEXTILE_LINK.atom_drag_type,
                   DdTargets.TEXTILE_LINK.target_flags,
                   DdTargets.TEXTILE_LINK.app_id)
        self.contexteventbox.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,
                                   [],
                                   Gdk.DragAction.COPY)
        self.contexteventbox.drag_source_set_target_list(tglist)
        self.contexteventbox.drag_source_set_icon_name('wearnow-textile')
        self.contexteventbox.connect('drag_data_get', self._top_drag_data_get)

    def _connect_db_signals(self):
        """
        Connect any signals that need to be connected.
        Called by the init routine of the base class (_EditPrimary).
        """
        self._add_db_signal('textile-rebuild', self._do_close)
        self._add_db_signal('textile-delete', self.check_for_close)
        self._add_db_signal('ensemble-rebuild', self.ensemble_change)
        self._add_db_signal('ensemble-delete', self.ensemble_change)
        self._add_db_signal('ensemble-update', self.ensemble_change)
        self._add_db_signal('ensemble-add', self.ensemble_change)

    def ensemble_change(self, handle_list=[]):
        """
        Callback for ensemble change signals.

        This should rebuild the
           backreferences to ensemble in textile

        """
        #As this would be an extensive check, we choose the easy path and
        #   rebuild ensemble backreferences on all ensemble changes
        self._update_ensembles()

    def _update_ensembles(self):
        phandle = self.obj.get_handle()
        if phandle:
            #new textile has no handle yet and cannot be in a ensemble.
            textile = self.dbstate.db.get_textile_from_handle(phandle)
            #do nothing a the moment.
            #TODO: check if rebuild is needed to update back references ...

    def _setup_fields(self):
        """
        Connect the wearnowWidget objects to field in the interface.

        This allows the widgets to keep the data in the attached Textile object
        up to date at all times, eliminating a lot of need in 'save' routine.

        """

        self.private = widgets.PrivacyButton(
            self.top.get_object('private'),
            self.obj,
            self.db.readonly)

        self.ntype_field = widgets.MonitoredDataType(
            self.top.get_object("ntype"),
            self.obj.set_type,
            self.obj.get_type,
            self.db.readonly,
            self.db.get_textile_types())

        #part of Given Name section
        self.description = widgets.MonitoredEntry(
            self.top.get_object("description"),
            self.obj.set_description,
            self.obj.get_description,
            self.db.readonly)

        #other fields

        self.tags = widgets.MonitoredTagList(
            self.top.get_object("tag_label"),
            self.top.get_object("tag_button"),
            self.obj.set_tag_list,
            self.obj.get_tag_list,
            self.db,
            self.uistate, self.track,
            self.db.readonly)

        self.gid = widgets.MonitoredEntry(
            self.top.get_object("gid"),
            self.obj.set_wearnow_id,
            self.obj.get_wearnow_id,
            self.db.readonly)

        #make sure title updates automatically
        for obj in [self.top.get_object("description"),
                    ]:
            obj.connect('changed', self._changed_name)

    def _create_tabbed_pages(self):
        """
        Create the notebook tabs and insert them into the main window.
        """
        notebook = Gtk.Notebook()
        notebook.set_scrollable(True)

        self.attr_list = AttrEmbedList(self.dbstate,
                                       self.uistate,
                                       self.track,
                                       self.obj.get_attribute_list())
        self._add_tab(notebook, self.attr_list)
        self.track_ref_for_deletion("attr_list")

        self.note_tab = NoteTab(self.dbstate,
                                self.uistate,
                                self.track,
                                self.obj.get_note_list(),
                                self.get_menu_title(),
                                notetype=NoteType.TEXTILE)
        self._add_tab(notebook, self.note_tab)
        self.track_ref_for_deletion("note_tab")

        self.gallery_tab = GalleryTab(self.dbstate,
                                      self.uistate,
                                      self.track,
                                      self.obj.get_media_list(),
                                      self.load_textile_image)
        self._add_tab(notebook, self.gallery_tab)
        self.track_ref_for_deletion("gallery_tab")

        self.web_list = WebEmbedList(self.dbstate,
                                     self.uistate,
                                     self.track,
                                     self.obj.get_url_list())
        self._add_tab(notebook, self.web_list)
        self.track_ref_for_deletion("web_list")

        self.backref_tab = TextileBackRefList(self.dbstate,
                                             self.uistate,
                                             self.track,
                              self.db.find_backlink_handles(self.obj.handle))
        self._add_tab(notebook, self.backref_tab)
        self.track_ref_for_deletion("backref_tab")

        self._setup_notebook_tabs(notebook)
        notebook.show_all()
        self.top.get_object('vbox').pack_start(notebook, True, True, 0)

    def _changed_name(self, *obj):
        """
        callback to changes typed by user to the textile name.
        Update the window title, and default name in name tab
        """
        self.update_title(self.get_menu_title())

    def build_menu_names(self, textile):
        """
        Provide the information needed by the base class to define the
        window management menu entries.
        """
        return (_('Edit Garment'), self.get_menu_title())

    def _image_button_press(self, obj, event):
        """
        Button press event that is caught when a button has been pressed while
        on the image on the main form.

        This does not apply to the images in galleries, just the image on the
        main form.

        """
        if event.type == Gdk.EventType._2BUTTON_PRESS and event.button == 1:

            from .editmediaref import EditMediaRef
            media_list = self.obj.get_media_list()
            if media_list:
                media_ref = media_list[0]
                object_handle = media_ref.get_reference_handle()
                media_obj = self.db.get_object_from_handle(object_handle)

                try:
                    EditMediaRef(self.dbstate, self.uistate, self.track,
                                 media_obj, media_ref, self.load_photo)
                except WindowActiveError:
                    pass

        elif is_right_click(event):
            media_list = self.obj.get_media_list()
            if media_list:
                photo = media_list[0]
                self._show_popup(photo, event)
        #do not propagate further:
        return True

    def _show_popup(self, photo, event):
        """
        Look for right-clicks on a picture and create a popup menu of the
        available actions.
        """
        self.imgmenu = Gtk.Menu()
        menu = self.imgmenu
        menu.set_title(_("Media Object"))
        obj = self.db.get_object_from_handle(photo.get_reference_handle())
        if obj:
            add_menuitem(menu, _("View"), photo,
                                   self._popup_view_photo)
        add_menuitem(menu, _("Edit Object Properties"), photo,
                               self._popup_change_description)
        menu.popup(None, None, None, None, event.button, event.time)

    def _popup_view_photo(self, obj):
        """
        Open this picture in the default picture viewer.
        """
        media_list = self.obj.get_media_list()
        if media_list:
            photo = media_list[0]
            object_handle = photo.get_reference_handle()
            ref_obj = self.db.get_object_from_handle(object_handle)
            photo_path = media_path_full(self.db, ref_obj.get_path())
            open_file_with_default_application(photo_path)

    def _popup_change_description(self, obj):
        """
        Bring up the EditMediaRef dialog for the image on the main form.
        """
        media_list = self.obj.get_media_list()
        if media_list:
            from .editmediaref import EditMediaRef
            media_ref = media_list[0]
            object_handle = media_ref.get_reference_handle()
            media_obj = self.db.get_object_from_handle(object_handle)
            EditMediaRef(self.dbstate, self.uistate, self.track,
                         media_obj, media_ref, self.load_photo)

    def _top_contextmenu(self):
        """
        Override from base class, the menuitems and actiongroups for the top
        of context menu.
        """
        self.all_action    = Gtk.ActionGroup(name="/TextileAll")
        self.home_action   = Gtk.ActionGroup(name="/TextileHome")
        self.track_ref_for_deletion("all_action")
        self.track_ref_for_deletion("home_action")

        self.all_action.add_actions([
                ('ActiveTextile', None, _("Make Active Garment"),
                    None, None, self._make_active),
                ])
        self.home_action.add_actions([
                ('HomeTextile', 'go-home', _("Make Home Garment"),
                    None, None, self._make_home_textile),
                ])

        self.all_action.set_visible(True)
        self.home_action.set_visible(True)

        ui_top_cm = '''
            <menuitem action="ActiveTextile"/>
            <menuitem action="HomeTextile"/>'''

        return ui_top_cm, [self.all_action, self.home_action]

    def _top_drag_data_get(self, widget, context, sel_data, info, time):
        if info == DdTargets.TEXTILE_LINK.app_id:
            data = (DdTargets.TEXTILE_LINK.drag_type, id(self), self.obj.get_handle(), 0)
            sel_data.set(DdTargets.TEXTILE_LINK.atom_drag_type, 8, pickle.dumps(data))

    def _post_build_popup_ui(self):
        """
        Override base class, make inactive home action if not needed.
        """
        if (self.dbstate.db.get_default_textile() and
                self.obj.get_handle() ==
                    self.dbstate.db.get_default_textile().get_handle()):
            self.home_action.set_sensitive(False)
        else:
            self.home_action.set_sensitive(True)

    def _make_active(self, obj):
        self.uistate.set_active(self.obj.get_handle(), 'Textile')

    def _make_home_textile(self, obj):
        handle = self.obj.get_handle()
        if handle:
            self.dbstate.db.set_default_textile_handle(handle)

    def save(self, *obj):
        """
        Save the data.
        """
        self.ok_button.set_sensitive(False)
        if self.object_is_empty():
            ErrorDialog(_("Cannot save garment"),
                        _("No data exists for this garment. Please "
                          "enter data or cancel the edit."))
            self.ok_button.set_sensitive(True)
            return

        # fix id problems
        (uses_dupe_id, id) = self._uses_duplicate_id()
        if uses_dupe_id:
            prim_object = self.get_from_wearnow_id(id)
            name = prim_object.description
            msg1 = _("Cannot save garment. ID already exists.")
            msg2 = _("You have attempted to use the existing wearnow ID with "
                     "value %(id)s. This value is already used by '"
                     "%(prim_object)s'. Please enter a different ID or leave "
                     "blank to get the next available ID value.") % {
                         'id' : id, 'prim_object' : name }
            ErrorDialog(msg1, msg2)
            self.ok_button.set_sensitive(True)
            return

        with DbTxn('', self.db) as trans:
            if not self.obj.get_handle():
                self.db.add_textile(self.obj, trans)
                msg = _("Add Garment (%s)") % \
                        self.obj.description
            else:
                if not self.obj.get_wearnow_id():
                    self.obj.set_wearnow_id(self.db.find_next_textile_wearnow_id())
                self.db.commit_textile(self.obj, trans)
                msg = _("Edit Garment (%s)") % \
                        self.obj.description
            trans.set_description(msg)

        self.close()
        if self.callback:
            self.callback(self.obj)
        self.callback = None

    def load_textile_image(self):
        """
        Load the primary image into the main form if it exists.

        Used as callback on Gallery Tab too.

        """
        media_list = self.obj.get_media_list()
        if media_list:
            ref = media_list[0]
            handle = ref.get_reference_handle()
            obj = self.dbstate.db.get_object_from_handle(handle)
            if obj is None :
                #notify user of error
                from ..dialog import RunDatabaseRepair
                RunDatabaseRepair(
                            _('Non existing media found in the Gallery'))
            else :
                self.load_photo(ref, obj)
        else:
            self.obj_photo.hide()
            self.frame_photo.hide()

    def load_photo(self, ref, obj):
        """
        Load the textile's main photo using the Thumbnailer.
        """
        pixbuf = get_thumbnail_image(
                        media_path_full(self.dbstate.db,
                                              obj.get_path()),
                        obj.get_mime_type(),
                        ref.get_rectangle())

        self.obj_photo.set_from_pixbuf(pixbuf)
        self.obj_photo.show()
        self.frame_photo.show_all()

    def _cleanup_on_exit(self):
        """Unset all things that can block garbage collection.
        Finalize rest
        """
        EditPrimary._cleanup_on_exit(self)
        #config.save()
