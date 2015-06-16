# encoding:utf-8
#
# WearNow - a GTK+/GNOME based  program
#
# Copyright (C) 2009 Benny Malengier
# Copyright (C) 2009 Douglas S. Blank
# Copyright (C) 2009 Nick Hall
# Copyright (C) 2011 Tim G L Lyons
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
# default views of WearNow
#
#------------------------------------------------------------------------

register(VIEW, 
id    = 'ensembleview',
name  = _("Ensembles"),
description =  _("The view showing all ensembles"),
version = '0.0',
wearnow_target_version = MODULE_VERSION,
status = STABLE,
fname = 'ensembleview.py',
authors = ["UGent Dep. Textiles"],
authors_email = ["http://www.ugent.be/ea/textiles/"],
category = ("Ensembles", _("Ensembles")),
viewclass = 'EnsembleView',
order = START,
  )

register(VIEW, 
id    = 'mediaview',
name  = _("Media"),
description =  _("The view showing all the media objects"),
version = '0.0',
wearnow_target_version = MODULE_VERSION,
status = STABLE,
fname = 'mediaview.py',
authors = ["UGent Dep. Textiles"],
authors_email = ["http://www.ugent.be/ea/textiles/"],
category = ("Media", _("Media")),
viewclass = 'MediaView',
order = START,
  )

register(VIEW, 
id    = 'noteview',
name  = _("Notes"),
description =  _("The view showing all the notes"),
version = '0.0',
wearnow_target_version = MODULE_VERSION,
status = STABLE,
fname = 'noteview.py',
authors = ["UGent Dep. Textiles"],
authors_email = ["http://www.ugent.be/ea/textiles/"],
category = ("Notes", _("Notes")),
viewclass = 'NoteView',
order = START,
  )

register(VIEW, 
id    = 'textilelistview',
name  = _("Garments"),
description =  _("The view showing all garments in your Collection"
                 " in a flat list"),
version = '0.0',
wearnow_target_version = MODULE_VERSION,
status = STABLE,
fname = 'personlistview.py',
authors = ["UGent Dep. Textiles"],
authors_email = ["http://www.ugent.be/ea/textiles/"],
category = ("Garments", _("Garments")),
viewclass = 'TextileListView',
order = START,
stock_icon = 'wearnow-tree-list',
  )
