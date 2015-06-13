#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2004-2007 Donald N. Allingham
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
Declare constants used by database modules
"""

#-------------------------------------------------------------------------
#
# constants
#
#-------------------------------------------------------------------------
__all__ = ( 'DBPAGE', 'DBMODE', 'DBCACHE', 'DBLOCKS', 'DBOBJECTS', 'DBUNDO',
            'DBEXT', 'DBMODE_R', 'DBMODE_W', 'DBUNDOFN', 'DBLOCKFN',
            'DBRECOVFN','BDBVERSFN', 'DBLOGNAME', 'SCHVERSFN',
            'DBBACKEND',
            'TEXTILE_KEY', 'ENSEMBLE_KEY', 'MEDIA_KEY', 'NOTE_KEY', 'TAG_KEY',
            'TXNADD', 'TXNUPD', 'TXNDEL',
            "CLASS_TO_KEY_MAP", "KEY_TO_CLASS_MAP", "KEY_TO_NAME_MAP"
        )

DBEXT     = ".db"           # File extension to be used for database files
DBUNDOFN  = "undo.db"       # File name of 'undo' database
DBLOCKFN  = "lock"          # File name of lock file
DBRECOVFN = "need_recover"  # File name of recovery file
BDBVERSFN = "dbversion.txt" # File name of DB version file
DBBACKEND = "database.txt"  # File name of Database backend file
SCHVERSFN = "schemaversion.txt"# File name of schema version file
DBLOGNAME = ".Db"           # Name of logger
DBMODE_R  = "r"             # Read-only access
DBMODE_W  = "w"             # Full Read/Write access
DBPAGE    = 16384           # Size of the pages used to hold items in the database
DBMODE    = 0o666            # Unix mode for database creation
DBCACHE   = 0x4000000       # Size of the shared memory buffer pool
DBLOCKS   = 100000          # Maximum number of locks supported
DBOBJECTS = 100000          # Maximum number of simultaneously locked objects
DBUNDO    = 1000            # Maximum size of undo buffer

TEXTILE_KEY     = 0
ENSEMBLE_KEY    = 1
MEDIA_KEY       = 2
NOTE_KEY        = 3
TAG_KEY         = 4

TXNADD, TXNUPD, TXNDEL = 0, 1, 2

CLASS_TO_KEY_MAP = {"Textile": TEXTILE_KEY, 
                    "Ensemble": ENSEMBLE_KEY, 
                    "MediaObject": MEDIA_KEY,
                    "Note" : NOTE_KEY,
                    "Tag": TAG_KEY}

KEY_TO_CLASS_MAP = {TEXTILE_KEY: "Textile",
                    ENSEMBLE_KEY: "Ensemble",
                    MEDIA_KEY: "MediaObject",
                    NOTE_KEY: "Note",
                    TAG_KEY: "Tag"}

KEY_TO_NAME_MAP = {TEXTILE_KEY: 'textile',
                   ENSEMBLE_KEY: 'ensemble',
                   MEDIA_KEY: 'media',
                   NOTE_KEY: 'note',
                   TAG_KEY: 'tag'}
