#
# Gramps - a GTK+/GNOME based genealogy program
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
Note types.
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

class NoteType(GrampsType):

    UNKNOWN    = -1
    CUSTOM     = 0
    GENERAL    = 1
    #per object with notes a Type to distinguish the notes
    TEXTILE    = 10
    ENSEMBLE   = 11
    ATTRIBUTE  = 12
    # indicate a note is html code
    HTML_CODE  = 20

    _CUSTOM = CUSTOM
    _DEFAULT = GENERAL
    

    _DATAMAPREAL = [
        (UNKNOWN,     _("Unknown"),     "Unknown"),
        (CUSTOM,      _("Custom"),      "Custom"),
        (GENERAL,     _("General"),     "General"),
        (HTML_CODE,   _("Html code"),   "Html code"),
        ]
        
    _DATAMAPIGNORE = [
        (TEXTILE,     _("Garment"),     "Garment"),
        (ENSEMBLE,    _("Ensemble"),    "Ensemble"),
        (ATTRIBUTE,  _("Attribute Note"),   "Attribute Note"),
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
