#
# WearNow - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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
Provide the different Attribute Types for WearNow.
"""

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
from ..const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext
#-------------------------------------------------------------------------
#
# WearNow modules
#
#-------------------------------------------------------------------------
from .grampstype import GrampsType

class AttributeType(GrampsType):

    UNKNOWN     = -1
    CUSTOM      = 0
    COLOR      = 1
    RFID_ID     = 2
    THERM_INS   = 3
    MOIST_VAP_RESIST = 4
    FABRIC_TYPE = 5
    STRUC_WEAVE = 6
    THICKNESS   = 7
    WEIGHT      = 8
    FIBER       = 9
    

    _CUSTOM = CUSTOM
    _DEFAULT = RFID_ID

    _DATAMAP = [
        (UNKNOWN     , _("Unknown"), "Unknown"),
        (CUSTOM      , _("Custom"), "Custom"),
        (COLOR       , _("Color"), "Color"),
        (RFID_ID     , _("RFID Key"), "RFID Key"),
        (THERM_INS   , _("Thermal insulation value"), "Thermal insulation value"),
        (MOIST_VAP_RESIST, _("Moisture Vapor resistance"), "Moisture Vapor resistance"),
        (FABRIC_TYPE , _("Fabric Type"), "Fabric Type"),
        (STRUC_WEAVE , _("Structure/Weave"), "Structure/Weave"),
        (THICKNESS   , _("Thickness"), "Thickness"),
        (WEIGHT      , _("Weight"), "Weight"),
        (FIBER       , _("Fiber"), "Fiber"),
        ]

    def __init__(self, value=None):
        GrampsType.__init__(self, value)

    def get_ignore_list(self, exception=None):
        """
        Return a list of the types to ignore and not include in default lists.
        
        Exception is a sublist of types that may not be ignored
        
        :param exception: list of integer values corresponding with types that
                          have to be excluded from the ignore list
        :type exception: list
        :returns: list of integers corresponding with the types to ignore when 
                  showing a list of different types
        :rtype: list
        
        """
        return []
