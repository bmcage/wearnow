#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2010  Michiel D. Nauta
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
Provide merge capabilities for media objects.
"""

#-------------------------------------------------------------------------
#
# WearNow modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.sgettext
from wearnow.tex.const import URL_HOMEPAGE
from ..display import display_help
from ..managedwindow import ManagedWindow
from wearnow.tex.merge import MergeMediaQuery

#-------------------------------------------------------------------------
#
# WearNow constants
#
#-------------------------------------------------------------------------
WIKI_HELP_PAGE = '%s_-_Entering_and_Editing_Data:_Detailed_-_part_3' % \
        URL_HOMEPAGE
WIKI_HELP_SEC = _('manual|Merge_Media_Objects')
_GLADE_FILE = 'mergemedia.glade'

#-------------------------------------------------------------------------
#
# MergeMedia
#
#-------------------------------------------------------------------------
class MergeMedia(ManagedWindow):
    """
    Displays a dialog box that allows the media objects to be combined into one.
    """
    def __init__(self, dbstate, uistate, handle1, handle2):
        ManagedWindow.__init__(self, uistate, [], self.__class__)
        self.dbstate = dbstate
        database = dbstate.db
        self.mo1 = database.get_object_from_handle(handle1)
        self.mo2 = database.get_object_from_handle(handle2)

        self.define_glade('mergeobject', _GLADE_FILE)
        self.set_window(self._gladeobj.toplevel,
                        self.get_widget('object_title'),
                        _("Merge Media Objects"))

        # Detailed selection Widgets
        desc1 = self.mo1.get_description()
        desc2 = self.mo2.get_description()
        entry1 = self.get_widget("desc1")
        entry2 = self.get_widget("desc2")
        entry1.set_text(desc1)
        entry2.set_text(desc2)
        if entry1.get_text() == entry2.get_text():
            for widget_name in ('desc1', 'desc2', 'desc_btn1', 'desc_btn2'):
                self.get_widget(widget_name).set_sensitive(False)

        entry1 = self.get_widget("path1")
        entry2 = self.get_widget("path2")
        entry1.set_text(self.mo1.get_path())
        entry2.set_text(self.mo2.get_path())
        entry1.set_position(-1)
        entry2.set_position(-1)
        if entry1.get_text() == entry2.get_text():
            for widget_name in ('path1', 'path2', 'path_btn1', 'path_btn2'):
                self.get_widget(widget_name).set_sensitive(False)

        wearnow1 = self.mo1.get_wearnow_id()
        wearnow2 = self.mo2.get_wearnow_id()
        entry1 = self.get_widget("wearnow1")
        entry2 = self.get_widget("wearnow2")
        entry1.set_text(wearnow1)
        entry2.set_text(wearnow2)
        if entry1.get_text() == entry2.get_text():
            for widget_name in ('wearnow1', 'wearnow2', 'wearnow_btn1',
                    'wearnow_btn2'):
                self.get_widget(widget_name).set_sensitive(False)

        # Main window widgets that determine which handle survives
        rbutton1 = self.get_widget("handle_btn1")
        rbutton_label1 = self.get_widget("label_handle_btn1")
        rbutton_label2 = self.get_widget("label_handle_btn2")
        rbutton_label1.set_label("%s [%s]" % (desc1, wearnow1))
        rbutton_label2.set_label("%s [%s]" % (desc2, wearnow2))
        rbutton1.connect('toggled', self.on_handle1_toggled)

        self.connect_button('object_help', self.cb_help)
        self.connect_button('object_ok', self.cb_merge)
        self.connect_button('object_cancel', self.close)
        self.show()

    def on_handle1_toggled(self, obj):
        """ first chosen media object changes"""
        if obj.get_active():
            self.get_widget("path_btn1").set_active(True)
            self.get_widget("desc_btn1").set_active(True)
            self.get_widget("date_btn1").set_active(True)
            self.get_widget("wearnow_btn1").set_active(True)
        else:
            self.get_widget("path_btn2").set_active(True)
            self.get_widget("desc_btn2").set_active(True)
            self.get_widget("date_btn2").set_active(True)
            self.get_widget("wearnow_btn2").set_active(True)

    def cb_help(self, obj):
        """Display the relevant portion of the WearNow manual"""
        display_help(webpage = WIKI_HELP_PAGE, section = WIKI_HELP_SEC)

    def cb_merge(self, obj):
        """
        Perform the merge of the media objects when the merge button is clicked.
        """
        use_handle1 = self.get_widget("handle_btn1").get_active()
        if use_handle1:
            phoenix = self.mo1
            titanic = self.mo2
        else:
            phoenix = self.mo2
            titanic = self.mo1
            # Add second handle to history so that when merge is complete, 
            # phoenix is the selected row.
            self.uistate.set_active(phoenix.get_handle(), 'Media')

        if self.get_widget("path_btn1").get_active() ^ use_handle1:
            phoenix.set_path(titanic.get_path())
            phoenix.set_mime_type(titanic.get_mime_type())
        if self.get_widget("desc_btn1").get_active() ^ use_handle1:
            phoenix.set_description(titanic.get_description())
        if self.get_widget("wearnow_btn1").get_active() ^ use_handle1:
            phoenix.set_wearnow_id(titanic.get_wearnow_id())

        query = MergeMediaQuery(self.dbstate, phoenix, titanic)
        query.execute()
        self.close()
