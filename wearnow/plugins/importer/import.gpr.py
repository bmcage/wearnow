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

MODULE_VERSION="1.0" 

#------------------------------------------------------------------------
#
# WEARNOW package (portable XML)
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'im_gpkg'
plg.name  = _('WearNow package (portable XML)')
plg.description =  _('Import data from a WearNow package (an archived XML '
                     'Collection together with the media object files.)')
plg.version = '0.0'
plg.wearnow_target_version = MODULE_VERSION
plg.status = STABLE
plg.fname = 'importwpkg.py'
plg.ptype = IMPORT
plg.import_function = 'impData'
plg.extension = "wpkg"

#------------------------------------------------------------------------
#
# WEARNOW XML database
#
#------------------------------------------------------------------------

plg = newplugin()
plg.id    = 'im_gramps'
plg.name  = _('WearNow XML Collection')
plg.description =  _('The WearNow XML format is a text '
                     'version of a Collection. It is '
                     'read-write compatible with the '
                     'present WearNow database format.')
plg.version = '0.0'
plg.wearnow_target_version = MODULE_VERSION
plg.status = STABLE
plg.fname = 'importxml.py'
plg.ptype = IMPORT
plg.import_function = 'importData'
plg.extension = "wnow"
