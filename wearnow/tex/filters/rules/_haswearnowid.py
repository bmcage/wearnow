#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2002-2006  Donald N. Allingham
# Copyright (C) 2010       Raphael Ackermann
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
class HasWearNowId(Rule):
    """Rule that checks for an object with a specific WEARNOW ID."""

    labels      = [ _('ID:') ]
    name        = 'Object with <Id>'
    description = "Matches objects with a specified WearNow ID"
    category    = _('General filters')

    def apply(self, db, obj):
        """
        apply the rule on the obj.
        return true if the rule passes, false otherwise.
        """
        return obj.wearnow_id == self.list[0]
