#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2002-2006  Donald N. Allingham
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
Package providing filter rules for WEARNOW.

The following filters are provided in gen.filters.rules.

"""

# Need to expose this to be available for filter plugins:
# the plugins should say: from .. import Rule
from ._rule import Rule

from ._everything import Everything
from ._haswearnowid import HasWearNowId
from ._isprivate import IsPrivate
from ._matchesfilterbase import MatchesFilterBase
from ._regexpidbase import RegExpIdBase
