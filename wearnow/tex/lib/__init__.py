#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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

"""The core library of WearNow objects
"""

# Secondary objects
from .secondaryobj import SecondaryObject

# Primary objects
from .primaryobj import PrimaryObject
# Table objects
from .tag import Tag

# These are actually metadata
from .researcher import Researcher

# Type classes
from .grampstype import GrampsType
from .styledtexttagtype import StyledTextTagType

# Text
from .styledtexttag import StyledTextTag
from .styledtext import StyledText

#objects
from .attribute import Attribute
from .attrtype import AttributeType
from .childref import ChildRef
from .ensemble import Ensemble
from .mediaobj import MediaObject
from .mediaref import MediaRef
from .note import Note
from .notetype import NoteType
from .textile import Textile
from .researcher import Researcher
from .url import Url
