#
# WEARNOW - a GTK+/GNOME based genealogy program
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
import re
from ...const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# WEARNOW modules
#
#-------------------------------------------------------------------------
from . import Rule

#-------------------------------------------------------------------------
#
# HasIdOf
#
#-------------------------------------------------------------------------
class RegExpIdBase(Rule):
    """
    Objects with a WEARNOW ID that contains a substring or matches a 
    regular expression.
    """

    labels      = [ _('Text:') ]
    name        = 'Objects with <Id>'
    description = "Matches objects whose WEARNOW ID contains a substring " \
                   "or matches a regular expression"
    category    = _('General filters')
    allow_regex = True

    def apply(self, db, obj):
        return self.match_substring(0, obj.wearnow_id)
