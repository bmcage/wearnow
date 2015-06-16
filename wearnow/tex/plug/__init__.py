#
# Gramps - a GTK+/GNOME based  program
#
# Copyright (C) 2008  Brian G. Matherly
# Copyright (C) 2010  Jakim Friant
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

"""
The "plug" package for handling plugins in Gramps.
"""

from ._plugin import Plugin
from ._pluginreg import (PluginData, PluginRegister, REPORT, TOOL,
            CATEGORY_TEXT, CATEGORY_DRAW, CATEGORY_CODE, 
            CATEGORY_WEB, CATEGORY_BOOK, CATEGORY_GRAPHVIZ,
            TOOL_DEBUG, TOOL_ANAL, TOOL_DBPROC, TOOL_DBFIX, TOOL_REVCTL,
            TOOL_UTILS,
            CATEGORY_QR_MISC, CATEGORY_QR_TEXTILE, CATEGORY_QR_ENSEMBLE,
            CATEGORY_QR_NOTE, CATEGORY_QR_MEDIA,
            START, END, make_environment,
            )
from ._import import ImportPlugin
from ._export import ExportPlugin
from ._docgenplugin import DocGenPlugin
from ._manager import BasePluginManager
from .utils import *
from ._options import (Options, OptionListCollection, OptionList,
                      OptionHandler, MenuOptions)

__all__ = [ "docbackend", "docgen", "menu", Plugin, PluginData,
            PluginRegister, BasePluginManager, 
            ImportPlugin, ExportPlugin, DocGenPlugin,
            REPORT, TOOL, CATEGORY_TEXT, CATEGORY_DRAW, CATEGORY_CODE, 
            CATEGORY_WEB, CATEGORY_BOOK, CATEGORY_GRAPHVIZ,
            TOOL_DEBUG, TOOL_ANAL, TOOL_DBPROC, TOOL_DBFIX, TOOL_REVCTL,
            TOOL_UTILS,
            START, END, make_environment]
