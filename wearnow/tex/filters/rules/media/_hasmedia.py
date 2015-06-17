#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
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
# Standard Python modules
#
#-------------------------------------------------------------------------
from ....const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from .. import Rule

#-------------------------------------------------------------------------
#
# HasMedia
#
#-------------------------------------------------------------------------
class HasMedia(Rule):
    """Rule that checks for a media with a particular value"""


    labels      = [ _('Title:'), 
                    _('Type:'), 
                    _('Path:'),
                    ]
    name        = _('Media objects matching parameters')
    description = _("Matches media objects with particular parameters")
    category    = _('General filters')
    allow_regex = True

    def prepare(self,db):
        pass

    def apply(self,db, obj):
        if not self.match_substring(0, obj.get_description()):
            return False

        if not self.match_substring(1, obj.get_mime_type()):
            return False

        if not self.match_substring(2, obj.get_path()):
            return False

        return True
