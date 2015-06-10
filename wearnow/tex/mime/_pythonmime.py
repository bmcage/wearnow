#
# WearNow - a GTK+ based Desktop App for wear comfort
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2015       Benny Malengier (UGent)
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
# gen/mime/_pythonmime.py

import mimetypes
from ..const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext

_type_map = {
    'application/x-wearnow' : 'WearNow App Data',
    'image/jpeg' : 'JPEG image',
    'application/pdf' : 'PDF document',
}

mimetypes.add_type('application/x-wearnow','.wnow')
mimetypes.add_type('text/x-comma-separated-values', '.csv')

def get_description(mime_type):
    """Return the description of the specified mime type"""
    return _type_map.get(mime_type,_("unknown"))

def get_type(filename):
    """Return the mime type of the specified file"""
    value = mimetypes.guess_type(filename)
    if value and value[0]:
        return value[0]
    else:
        return _('unknown')
    
def mime_type_is_defined(mime_type):
    """
    Return True if a description for a mime type exists.
    """
    return mime_type in _type_map
