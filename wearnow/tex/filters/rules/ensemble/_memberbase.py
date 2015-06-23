#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
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
Set of wrappers for Ensemble filter rules based on personal rules.

Any rule that matches Ensemble based on personal rule applied
to father, mother, or any child, just needs to do two things:
> Set the class attribute 'base_class' to the personal rule
> Set apply method to be an appropriate wrapper below
Example:
in the class body, outside any method:
>    base_class = SearchName
>    apply = child_base
"""

def child_base(self,db,ensemble):
    for child_ref in ensemble.get_child_ref_list():
        child = db.get_textile_from_handle(child_ref.ref)
        if self.base_class.apply(self,db,child):
            return True
    return False
