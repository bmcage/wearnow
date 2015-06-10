#! /usr/bin/env python3
#
# WearNow - a GTK+ based Desktop App for wear comfort
#
# Copyright (C) 2015       Benny Malengier (UGent)
# Copyright (C) 2015       Mahmood Ahmed   (UGent)
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#

"""
This is a stub to start WearNow. It is provided for the sole reason of being
able to run from the source directory without setting PYTHONPATH
"""

import os
os.environ['WEARNOW_RESOURCES'] = os.path.dirname(os.path.abspath(__file__))
import wearnow.wearnowapp as app
app.main()
