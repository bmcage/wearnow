#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2009 Benny Malengier
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

MODULE_VERSION="0.0" 

#------------------------------------------------------------------------
#
# GRAMPS package (portable XML)
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'ex_gpkg'
plg.name  = _('WearNow XML Package (collection and media)')
plg.name_accell  = _('WearNow XML _Package (collection and media)')
plg.description =  _('WearNow package is an archived XML collection together '
                 'with the media object files.')
plg.version = '0.0'
plg.wearnow_target_version = MODULE_VERSION
plg.status = STABLE
plg.fname = 'exportpkg.py'
plg.ptype = EXPORT
plg.export_function = 'writeData'
plg.export_options = 'WriterOptionBox'
plg.export_options_title = _('WearNow package export options')
plg.extension = "gpkg"

#------------------------------------------------------------------------
#
# GRAMPS XML database
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'ex_gramps'
plg.name  = _('WearNow XML (collection)')
plg.name_accell  = _('_WearNow _XML (collection)')
plg.description =  _('WearNow XML export is a complete archived XML backup of a' 
                 ' WearNow collection without the media object files.'
                 ' Suitable for backup purposes.')
plg.version = '0.0'
plg.wearnow_target_version = MODULE_VERSION
plg.status = STABLE
plg.fname = 'exportxml.py'
plg.ptype = EXPORT
plg.export_function = 'export_data'
plg.export_options = 'WriterOptionBox'
plg.export_options_title = _('WearNow XML export options')
plg.extension = "gramps"
