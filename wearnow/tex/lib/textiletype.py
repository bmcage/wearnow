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
Textile types.
"""

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from ..const import WEARNOW_LOCALE as glocale
_ = glocale.translation.sgettext

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from .grampstype import GrampsType

class TextileType(GrampsType):

    UNKNOWN    = -1
    CUSTOM     = 0
    TSHIRT_SHORTSLEEVE    = 1
    TSHIRT_LONGSLEEVE     = 2
    PULLOVER              = 3
    TROUSERS              = 4
    TROUSERS_SHORT        = 5
    DRESS                 = 6

    _CUSTOM = CUSTOM
    _DEFAULT = TROUSERS
    

    _DATAMAPREAL = [
        (UNKNOWN,     _("Unknown"),     "Unknown"),
        (CUSTOM,      _("Custom"),      "Custom"),
        (TSHIRT_SHORTSLEEVE,     _("T-Shirt - short sleeve"),     "T-Shirt - short sleeve"),
        (TSHIRT_LONGSLEEVE,   _("T-Shirt - long sleeve"),   "T-Shirt - long sleeve"),
        (PULLOVER,   _("Pullover"),   "Pullover"),
        (TROUSERS,   _("Trousers"),   "Trousers"),
        (TROUSERS_SHORT,   _("Trousers - short"),   "Trousers - short"),
        (DRESS,   _("Dress"),   "Dress"),
        ]
        
    _DATAMAPIGNORE = [
        ]
        
    _DATAMAP = _DATAMAPREAL + _DATAMAPIGNORE

    def __init__(self, value=None):
        GrampsType.__init__(self, value)
        
    def get_ignore_list(self, exception):
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
        ignlist = [x[0] for x in self._DATAMAPIGNORE]
        if exception:
            for type_ in exception:
                try: 
                    del ignlist[ignlist.index(type_)]
                except ValueError:
                    pass
        return ignlist
