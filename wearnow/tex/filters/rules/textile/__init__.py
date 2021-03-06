#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2002-2007  Donald N. Allingham
# Copyright (C) 2007-2008   Brian G. Matherly
# Copyright (C) 2011       Tim G L Lyons
# Copyright (C) 2011       Doug Blank <doug.blank@gmail.com>
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
Package providing filter rules for WearNow
"""

from ._everyone import Everyone
from ._matchesfilter import MatchesFilter
from ._textilesprivate import TextilesPrivate
from ._hasnoteregexp import HasNoteRegexp
from ._hastag import HasTag
from ._regexpidof import RegExpIdOf
from ._regexpname import RegExpName
#-------------------------------------------------------------------------
#
# This is used by Custom Filter Editor tool
#
#-------------------------------------------------------------------------
editor_rule_list = [
    Everyone,
    MatchesFilter,
    TextilesPrivate,
    HasNoteRegexp,
    HasTag,
    RegExpIdOf,
    RegExpName,
]

