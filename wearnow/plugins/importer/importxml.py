#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 200?-2013  Benny Malengier
# Copyright (C) 2009       Douglas S. Blank
# Copyright (C) 2010-2011  Nick Hall
# Copyright (C) 2011       Michiel D. Nauta
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

#-------------------------------------------------------------------------
#
# Standard Python Modules
#
#-------------------------------------------------------------------------
import os
import sys
import time
from xml.parsers.expat import ExpatError, ParserCreate
from xml.sax.saxutils import escape
from wearnow.tex.const import URL_HOMEPAGE
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext
import re
import logging
import collections
LOG = logging.getLogger(".ImportXML")

#-------------------------------------------------------------------------
#
# WearNow Modules
#
#-------------------------------------------------------------------------
from wearnow.tex.mime import get_type
from wearnow.tex.lib import (Attribute, AttributeType, ChildRef, Ensemble,
                            MediaObject, MediaRef, Note, NoteType, Textile,
                            Researcher, StyledText,
                            StyledTextTag, StyledTextTagType, Tag, Url)
from wearnow.tex.db.txn import DbTxn
#from wearnow.tex.db.write import CLASS_TO_KEY_MAP
from wearnow.tex.errors import WearNowImportError
from wearnow.tex.utils.id import create_id
from wearnow.tex.utils.unknown import make_unknown, create_explanation_note
from wearnow.tex.utils.file import create_checksum
from wearnow.tex.db.dbconst import (TEXTILE_KEY, ENSEMBLE_KEY, MEDIA_KEY,
                                    NOTE_KEY, TAG_KEY, CLASS_TO_KEY_MAP)
from wearnow.tex.updatecallback import UpdateCallback
from wearnow.version import VERSION
from wearnow.tex.config import config
#import wearnow.plugins.lib.libwearnowxml
from wearnow.plugins.lib import libwearnowxml
from wearnow.tex.plug.utils import version_str_to_tup

#-------------------------------------------------------------------------
#
# Try to detect the presence of gzip
#
#-------------------------------------------------------------------------
try:
    import gzip
    GZIP_OK = True
except:
    GZIP_OK = False

TEXTILE_RE = re.compile(r"\s*\<textile\s(.*)$")

HANDLE = 0
INSTANTIATED = 1

#-------------------------------------------------------------------------
#
# Importing data into the currently open database. 
# Must takes care of renaming media files according to their new IDs.
#
#-------------------------------------------------------------------------
def importData(database, filename, user):
    filename = os.path.normpath(filename)
    basefile = os.path.dirname(filename)
    database.smap = {}
    database.pmap = {}
    database.fmap = {}
    line_cnt = 0
    textile_cnt = 0
    
    database.prepare_import()
    with ImportOpenFileContextManager(filename, user) as xml_file:
        if xml_file is None:
            return
    
        if filename == '-':
            change = time.time()
        else:
            change = os.path.getmtime(filename)
        if database.get_feature("skip-import-additions"): # don't add source or tags
            parser = WearNowParser(database, user, change, None)
        else:
            parser = WearNowParser(database, user, change,
                                  (config.get('preferences.tag-on-import-format') if 
                                   config.get('preferences.tag-on-import') else None))

        if filename != '-':
            linecounter = LineParser(filename)
            line_cnt = linecounter.get_count()
            textile_cnt = linecounter.get_textile_count()
    
        read_only = database.readonly
        database.readonly = False
        
        try:
            info = parser.parse(xml_file, line_cnt, textile_cnt)
        except WearNowImportError as err: # version error
            user.notify_error(*err.messages())
            return
        except IOError as msg:
            user.notify_error(_("Error reading %s") % filename, str(msg))
            import traceback
            traceback.print_exc()
            return
        except ExpatError as msg:
            user.notify_error(_("Error reading %s") % filename, 
                        str(msg) + "\n" +
                        _("The file is probably either corrupt or not a "
                          "valid WearNow database."))
            return

    database.commit_import()
    database.readonly = read_only
    return info

##  TODO - WITH MEDIA PATH, IS THIS STILL NEEDED? 
##         BETTER LEAVE ALL RELATIVE TO NEW RELATIVE PATH
##   save_path is in .wearnow/dbbase, no good place !
##    # copy all local images into <database>.images directory
##    db_dir = os.path.abspath(os.path.dirname(database.get_save_path()))
##    db_base = os.path.basename(database.get_save_path())
##    img_dir = os.path.join(db_dir, db_base)
##    first = not os.path.exists(img_dir)
##    
##    for m_id in database.get_media_object_handles():
##        mobject = database.get_object_from_handle(m_id)
##        oldfile = mobject.get_path()
##        if oldfile and not os.path.isabs(oldfile):
##            if first:
##                os.mkdir(img_dir)
##                first = 0
##            newfile = os.path.join(img_dir, oldfile)
##
##            try:
##                oldfilename = os.path.join(basefile, oldfile)
##                shutil.copyfile(oldfilename, newfile)
##                try:
##                    shutil.copystat(oldfilename, newfile)
##                except:
##                    pass
##                mobject.set_path(newfile)
##                database.commit_media_object(mobject, None, change)
##            except (IOError, OSError), msg:
##                ErrorDialog(_('Could not copy file'), str(msg))

#-------------------------------------------------------------------------
#
# Remove extraneous spaces
#
#-------------------------------------------------------------------------

def rs(text):
    return ' '.join(text.split())

def fix_spaces(text_list):
    return '\n'.join(map(rs, text_list))

#-------------------------------------------------------------------------
#
# 
#
#-------------------------------------------------------------------------

class ImportInfo(object):
    """
    Class object that can hold information about the import
    """
    keyorder = [TEXTILE_KEY, ENSEMBLE_KEY, MEDIA_KEY, NOTE_KEY, TAG_KEY]
    key2data = {
            TEXTILE_KEY : 0,
            ENSEMBLE_KEY : 1,
            MEDIA_KEY: 2, 
            NOTE_KEY: 3,
            TAG_KEY: 4,
            }
    
    def __init__(self):
        """
        Init of the import class.
        
        This creates the datastructures to hold info
        """
        self.data_mergecandidate = [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}]
        self.data_newobject = [0] * 10
        self.data_unknownobject = [0] * 10
        self.data_ensembles = ''
        self.expl_note = ''
        self.data_relpath = False
        
    def add(self, category, key, obj, sec_obj=None):
        """
        Add info of a certain category. Key is one of the predefined keys,
        while obj is an object of which information will be extracted
        """
        if category == 'merge-candidate':
            self.data_mergecandidate[self.key2data[key]][obj.handle] = \
                    self._extract_mergeinfo(key, obj, sec_obj)
        elif category == 'new-object':
            self.data_newobject[self.key2data[key]] += 1
        elif category == 'unknown-object':
            self.data_unknownobject[self.key2data[key]] += 1
        elif category == 'relative-path':
            self.data_relpath = True

    def _extract_mergeinfo(self, key, obj, sec_obj):
        """
        Extract info from obj about 'merge-candidate', Key is one of the 
        predefined keys.
        """
        if key == TEXTILE_KEY:
            return _("  %(id)s - with id %(id2)s\n") % {
                        'id': obj.wearnow_id, 
                        'id2': sec_obj.wearnow_id
                        }
        elif key == ENSEMBLE_KEY :
            return _("  Ensemble %(id)s with %(id2)s\n") % {
                        'id': obj.wearnow_id, 'id2': sec_obj.wearnow_id}
        elif key == MEDIA_KEY:
            return _("  Media Object %(id)s with %(id2)s\n") % {
                        'id': obj.wearnow_id, 'id2': sec_obj.wearnow_id}
        elif key == NOTE_KEY:
            return _("  Note %(id)s with %(id2)s\n") % {
                        'id': obj.wearnow_id, 'id2': sec_obj.wearnow_id}
        elif key == TAG_KEY:
            pass # Tags can't be merged

    def info_text(self):
        """
        Construct an info message from the data in the class.
        """
        key2string = {
            TEXTILE_KEY     : _('  Textiles: %d\n'),
            ENSEMBLE_KEY    : _('  Ensembles: %d\n'),
            MEDIA_KEY       : _('  Media Objects: %d\n'),
            NOTE_KEY        : _('  Notes: %d\n'),
            TAG_KEY         : _('  Tags: %d\n'),
            }
        txt = _("Number of new objects imported:\n")
        for key in self.keyorder:
            if any(self.data_unknownobject):
                strng = key2string[key][0:-1] + ' (%d)\n'
                txt += strng % (self.data_newobject[self.key2data[key]],
                                self.data_unknownobject[self.key2data[key]])
            else:
                txt += key2string[key] % self.data_newobject[self.key2data[key]]
        if any(self.data_unknownobject):
            txt += _("\n The imported file was not self-contained.\n"
                     "To correct for that, %(new)d objects were created and\n"
                     "their typifying attribute was set to 'Unknown'.\n"
                     "The breakdown per category is depicted by the\n"
                     "number in parentheses. Where possible these\n"
                     "'Unkown' objects are referenced by note %(unknown)s.\n"
                     ) % {'new': sum(self.data_unknownobject), 'unknown': self.expl_note}
        if self.data_relpath:
            txt += _("\nMedia objects with relative paths have been\n"
                     "imported. These paths are considered relative to\n"
                     "the media directory you can set in the preferences,\n"
                     "or, if not set, relative to the user's directory.\n"
                    )
        merge = False
        for key in self.keyorder:
            if self.data_mergecandidate[self.key2data[key]]:
                merge = True
                break
        if merge:
            txt += _("\n\nObjects that are candidates to be merged:\n")
            for key in self.keyorder:
                datakey = self.key2data[key]
                for handle in list(self.data_mergecandidate[datakey].keys()):
                    txt += self.data_mergecandidate[datakey][handle]
        
        if self.data_ensembles:
            txt += "\n\n"
            txt += self.data_ensembles
        
        return txt

class LineParser(object):
    def __init__(self, filename):

        self.count = 0
        self.textile_count = 0

        if GZIP_OK:
            use_gzip = 1
            try:
                f = gzip.open(filename, "r")
                f.read(1)
                f.close()
            except IOError as msg:
                use_gzip = 0
            except ValueError as msg:
                use_gzip = 1
        else:
            use_gzip = 0

        try:
            if use_gzip:
                import io
                # Bug 6255. TextIOWrapper is required for python3 to
                #           present file contents as text, otherwise they
                #           are read as binary. However due to a missing
                #           method (read1) in early python3 versions this
                #           try block will fail.
                #           WearNow will still import XML files using python
                #           versions < 3.3.0 but the file progress meter
                #           will not work properly, going immediately to
                #           100%.
                #           It should work correctly from version 3.3.
                ofile = io.TextIOWrapper(gzip.open(filename, "rb"))
            else:
                ofile = open(filename, "r")

            for line in ofile:
                self.count += 1
                if TEXTILE_RE.match(line):
                    self.textile_count += 1
        except:
            self.count = 0
            self.textile_count = 0
        finally:
            # Ensure the file handle is always closed
            ofile.close()

    def get_count(self):
        return self.count

    def get_textile_count(self):
        return self.textile_count

#-------------------------------------------------------------------------
#
# ImportOpenFileContextManager
#
#-------------------------------------------------------------------------
class ImportOpenFileContextManager:
    """
    Context manager to open a file or stdin for reading.
    """
    def __init__(self, filename, user):
        self.filename = filename
        self.filehandle = None
        self.user = user

    def __enter__(self):
        if self.filename == '-':
            self.filehandle = sys.stdin
        else:
            self.filehandle = self.open_file(self.filename)
        return self.filehandle

    def __exit__(self, exc_type, exc_value, traceback):
        if self.filename != '-':
            if self.filehandle:
                self.filehandle.close()
        return False

    def open_file(self, filename):
        """ 
        Open the xml file.
        Return a valid file handle if the file opened sucessfully.
        Return None if the file was not able to be opened.
        """
        if GZIP_OK:
            use_gzip = True
            try:
                ofile = gzip.open(filename, "r")
                ofile.read(1)
                ofile.close()
            except IOError as msg:
                use_gzip = False
            except ValueError as msg:
                use_gzip = True
        else:
            use_gzip = False

        try:
            if use_gzip:
                xml_file = gzip.open(filename, "rb")
            else:
                xml_file = open(filename, "rb")
        except IOError as msg:
            self.user.notify_error(_("%s could not be opened") % filename, str(msg))
            xml_file = None
        except:
            self.user.notify_error(_("%s could not be opened") % filename)
            xml_file = None
            
        return xml_file

#-------------------------------------------------------------------------
#
# WearNow database parsing class.  Derived from SAX XML parser
#
#-------------------------------------------------------------------------
class WearNowParser(UpdateCallback):

    def __init__(self, database, user, change, default_tag_format=None):
        UpdateCallback.__init__(self, user.callback)
        self.user = user
        self.__wearnow_version = 'unknown'
        self.__xml_version = (0, 0, 1)
        self.stext_list = []
        self.scomments_list = []
        self.note_list = []
        self.tlist = []
        self.conf = 2
        self.gid2id = {}
        self.gid2fid = {}
        self.gid2pid = {}
        self.gid2oid = {}
        self.gid2nid = {}
        self.change = change
        self.info = ImportInfo()
        self.all_abs = True
        self.db = database
        # Data with handles already present in the db will overwrite existing
        # data, so all imported data gets a new handle. This behavior is not
        # needed and even unwanted if data is imported in an empty collection
        # because NarWeb urls are based on handles. Also for debugging purposes
        # it can be advantageous to preserve the orginal handle.
        self.replace_import_handle = (self.db.get_number_of_textiles() > 0 and
                                      not LOG.isEnabledFor(logging.DEBUG))
        
        # Similarly, if the data is imported into an empty collection, we also
        # import the owner; if the tree was not empty, the existing
        # owner is retained
        self.import_owner = self.db.is_empty()
        self.ord = None
        self.objref = None
        self.object = None
        self.in_note = 0
        self.in_stext = 0
        self.in_scomments = 0
        self.note = None
        self.note_text = None
        self.note_tags = []
        self.photo = None
        self.textile = None
        self.ensemble = None
        self.attribute = None
        
        self.resname = ""
        self.resaddr = "" 
        self.reslocality = ""
        self.rescity = ""
        self.resstate = ""
        self.rescon = "" 
        self.respos = ""
        self.resphone = ""
        self.resemail = ""

        self.mediapath = ""

        self.pmap = {}
        self.fmap = {}
        self.lmap = {}
        self.media_file_map = {}

        self.childref = None
        self.home = None
        self.owner = Researcher()
        self.func_list = [None]*50
        self.func_index = 0
        self.func = None
        self.idswap = {}
        self.fidswap = {}
        self.pidswap = {}
        self.oidswap = {}
        self.nidswap = {}
        self.import_handles = {}

        if default_tag_format:
            name = time.strftime(default_tag_format)
            tag = self.db.get_tag_from_name(name)
            if tag:
                self.default_tag = tag
            else:
                self.default_tag = Tag()
                self.default_tag.set_name(name)
        else:
            self.default_tag = None

        self.func_map = {
            "childlist": (None, None),  
            "attribute": (self.start_attribute, self.stop_attribute), 
            "attr_type": (None, self.stop_attr_type), 
            "attr_value": (None, self.stop_attr_value),
            "bookmark": (self.start_bmark, None), 
            "bookmarks": (None, None), 
            "childref": (self.start_childref, self.stop_childref), 
            "created": (self.start_created, None), 
            "database": (self.start_database, self.stop_database), 
            "ensembles": (None, self.stop_ensembles), 
            "ensemble": (self.start_ensemble, self.stop_ensemble), 
            "header": (None, self.stop_header), 
            "mediapath": (None, self.stop_mediapath),
            "note": (self.start_note, self.stop_note), 
            "noteref": (self.start_noteref, None), 
            "textiles": (self.start_textiles, self.stop_textiles), 
            "textile": (self.start_textile, self.stop_textile), 
            "objref": (self.start_objref, self.stop_objref), 
            "object": (self.start_object, self.stop_object), 
            "file": (self.start_file, None), 
            "owner": (None, self.stop_research), 
            "resname": (None, self.stop_resname), 
            "resaddr": (None, self.stop_resaddr), 
            "reslocality": (None, self.stop_reslocality), 
            "rescity": (None, self.stop_rescity), 
            "resstate": (None, self.stop_resstate), 
            "rescountry": (None, self.stop_rescountry), 
            "respostal": (None, self.stop_respostal), 
            "resphone": (None, self.stop_resphone), 
            "resemail": (None, self.stop_resemail), 
            "style": (self.start_style, None),
            "tag": (self.start_tag, self.stop_tag),
            "tagref": (self.start_tagref, None),
            "tags": (None, None),
            "text": (None, self.stop_text),
            "url": (self.start_url, None), 
        }
        self.wearnowuri = re.compile(r"^wearnow://(?P<object_class>[A-Z][a-z]+)/"
            "handle/(?P<handle>\w+)$")

    def inaugurate(self, handle, target, prim_obj):
        """
        Assign a handle (identity) to a primary object (and create it if it
        doesn't exist yet) and add it to the database.

        This method can be called with an object instance or with a
        class object. Be aware that in the first case the side effect of this
        function is to fill the object instance with the data read from the db.
        In the second case, an empty object with the correct handle will be
        created.

        :param handle: The handle of the primary object, typically as read
                       directly from the XML attributes.
        :type handle: str
        :param target: Indicates the primary object type this handle relates to.
        :type target: str, identical to target attr of bookmarks.
        :param prim_obj: template of the primary object that is to be created.
        :type prim_obj: Either an empty instance of a primary object or the
                         class object of a primary object.
        :returns: The handle of the primary object.
        :rtype: str
        """
        handle = str(handle.replace('_', ''))
        orig_handle = handle
        if (orig_handle in self.import_handles and
                target in self.import_handles[orig_handle]):
            handle = self.import_handles[handle][target][HANDLE]
            if not isinstance(prim_obj, collections.Callable): 
                # This method is called by a start_<primary_object> method.
                get_raw_obj_data = {"textile": self.db.get_raw_textile_data,
                                    "ensemble": self.db.get_raw_ensemble_data,
                                    "media": self.db.get_raw_object_data,
                                    "note": self.db.get_raw_note_data,
                                    "tag": self.db.get_raw_tag_data}[target]
                raw = get_raw_obj_data(handle)
                prim_obj.unserialize(raw)
                self.import_handles[orig_handle][target][INSTANTIATED] = True
            return handle
        elif handle in self.import_handles:
            LOG.warn("The file you import contains duplicate handles "
                    "which is illegal and being fixed now.")
            handle = create_id()
            while handle in self.import_handles:
                handle = create_id()
            self.import_handles[orig_handle][target] = [handle, False]
        else:
            orig_handle = handle
            if self.replace_import_handle:
                handle = create_id()
                while handle in self.import_handles:
                    handle = create_id()
            else:
                has_handle_func = {"textile": self.db.has_textile_handle,
                                   "ensemble": self.db.has_ensemble_handle,
                                   "media": self.db.has_object_handle,
                                   "note": self.db.has_note_handle,
                                   "tag": self.db.has_tag_handle}[target]
                while has_handle_func(handle):
                    handle = create_id()
            self.import_handles[orig_handle] = {target: [handle, False]}
        if isinstance(prim_obj, collections.Callable): # method is called by a reference
            prim_obj = prim_obj()
        else:
            self.import_handles[orig_handle][target][INSTANTIATED] = True
        prim_obj.set_handle(handle)
        if target == "tag":
            self.db.add_tag(prim_obj, self.trans)
        else:
            add_func = {"textile": self.db.add_textile,
                        "ensemble": self.db.add_ensemble,
                        "media": self.db.add_object,
                        "note": self.db.add_note}[target]
            add_func(prim_obj, self.trans, set_gid=False)
        return handle

    def legalize_id(self, id_, key, wearnow_ids, id2user_format,
                    find_next_wearnow_id):
        """
        Given an import id, adjust it so that it fits with the existing data.
        
        :param id_: The id as it is in the Xml import file, might be None.
        :type id_: str
        :param key: Indicates kind of primary object this id is for.
        :type key: int
        :param wearnow_ids: Dictionary with id's that have already been imported.
        :type import_ids: dict
        :param id2user_format: Function to convert a raw id into the format as
                               specified in the prefixes.
        :type id2user_format: func
        :param find_next_wearnow_id: function to get the next available id.
        :type find_next_wearnow_id: func
        :returns: The id.
        :rtype: str
        """
        wearnow_id = id2user_format(id_)
        if wearnow_id is None or not wearnow_ids.get(id_):
            if wearnow_id is None or self.db.has_wearnow_id(key, wearnow_id):
                wearnow_ids[id_] = find_next_wearnow_id()
            else:
                wearnow_ids[id_] = wearnow_id
        return wearnow_ids[id_]

    def parse(self, ifile, linecount=0, textilecount=0):
        """
        Parse the xml file
        :param ifile: must be a file handle that is already open, with position
                      at the start of the file
        """
        if textilecount < 1000:
            no_magic = True
        else:
            no_magic = False
        with DbTxn(_("WearNow XML import"), self.db, batch=True,
                   no_magic=no_magic) as self.trans:
            self.set_total(linecount)

            self.db.disable_signals()

            if self.default_tag and self.default_tag.handle is None:
                self.db.add_tag(self.default_tag, self.trans)

            self.p = ParserCreate()
            self.p.StartElementHandler = self.startElement
            self.p.EndElementHandler = self.endElement
            self.p.CharacterDataHandler = self.characters
            self.p.ParseFile(ifile)

            # If the database was originally empty we update the owner from
            # the XML (or initialised to no owner)
            if self.import_owner:
                self.db.set_owner(self.owner)
            if self.home is not None:
                textile = self.db.get_textile_from_handle(self.home)
                self.db.set_default_textile_handle(textile.handle)
    
            #set media path, this should really do some parsing to convert eg
            # windows path to unix ?
            if self.mediapath:
                oldpath = self.db.get_mediapath()
                if not oldpath:
                    self.db.set_mediapath(self.mediapath)
                elif not oldpath == self.mediapath:
                    self.user.notify_error(_("Could not change media path"), 
                        _("The opened file has media path %s, which conflicts with"
                          " the media path of the Collection you import into. "
                          "The original media path has been retained. Copy the "
                          "files to a correct directory or change the media "
                          "path in the Preferences."
                         ) % self.mediapath )
    
            self.fix_not_instantiated()
            for key in list(self.func_map.keys()):
                del self.func_map[key]
            del self.func_map
            del self.func_list
            del self.p
            del self.update
        self.db.enable_signals()
        self.db.request_rebuild()
        return self.info

    def start_database(self, attrs):
        """
        Get the xml version of the file.
        """
        if 'xmlns' in attrs:
            xmlns = attrs.get('xmlns').split('/')
            try:
                self.__xml_version = version_str_to_tup(xmlns[4], 3)
            except:
                #leave version at 1.0.0 although it could be 0.0.0 ??
                pass
        else:
            #1.0 or before xml, no dtd schema yet on 
            # http://www.wearnow-project.org/xml/
            self.__xml_version = (0, 0, 0)

    def start_created(self, attrs):
        """
        Get the WearNow version that produced the file.
        """
        if 'version' in attrs:
            self.__wearnow_version = attrs.get('version')

    def stop_header(self, *dummy):
        """
        Check the version of WearNow and XML.
        """
        xmlversion_str = '.'.join(str(i) for i in self.__xml_version)
        if self.__wearnow_version == 'unknown':
            msg = _("The .wearnow file you are importing does not contain information about "
                    "the version of WearNow with, which it was produced.\n\n"
                    "The file will not be imported.")
            raise WearNowImportError(_('Import file misses WearNow version'), msg)
        if self.__xml_version > libwearnowxml.WEARNOW_XML_VERSION_TUPLE:
            msg = _("The .wnow file you are importing was made by "
                    "version %(newer)s of "
                    "WearNow, while you are running an older version %(older)s. "
                    "The file will not be imported. Please upgrade to the "
                    "latest version of WearNow and try again." ) % {
                    'newer' : self.__wearnow_version, 'older' : VERSION }
            raise WearNowImportError('', msg)
        if self.__xml_version < (0, 0, 0):
            msg = _("The .wnow file you are importing was made by version "
                    "%(oldwearnow)s of WearNow, while you are running a more "
                    "recent version %(newwearnow)s.\n\n"
                    "The file will not be imported. Please use an older version"
                    " of WearNow that supports version %(xmlversion)s of the "
                    "xml.\nSee\n  %(wearnow_wiki_xml_url)s\n for more info."
                    ) % {'oldwearnow': self.__wearnow_version, 
                        'newwearnow': VERSION,
                        'xmlversion': xmlversion_str,
                        'wearnow_wiki_xml_url': URL_HOMEPAGE ,
                        }
            raise WearNowImportError(_('The file will not be imported'), msg)
        elif self.__xml_version < (0, 0, 0):
            msg = _("The .wnow file you are importing was made by version "
                    "%(oldwearnow)s of WearNow, while you are running a much "
                    "more recent version %(newwearnow)s.\n\n"
                    "Ensure after import everything is imported correctly. In "
                    "the event of problems, please submit a bug and use an "
                    "older version of WearNow in the meantime to import this "
                    "file, which is version %(xmlversion)s of the xml.\nSee\n  "
                    "%(wearnow_wiki_xml_url)s\nfor more info."
                    ) % {'oldwearnow': self.__wearnow_version, 
                        'newwearnow': VERSION,
                        'xmlversion': xmlversion_str,
                        'wearnow_wiki_xml_url': URL_HOMEPAGE ,
                        }
            self.user.warn(_('Old xml file'), msg)

    def start_attribute(self, attrs):
        self.attribute = Attribute()
        self.attribute.private = bool(attrs.get("priv"))
        self.attribute.type = AttributeType()
        if 'type' in attrs:
            self.attribute.type.set_from_xml_str(attrs["type"])
        self.attribute.value = attrs.get("value", '')
        if self.textile:
            self.textile.add_attribute(self.attribute)

    def start_bmark(self, attrs):
        """
        Add a bookmark to db.
        """
        target = attrs.get('target')
        if not target:
            # Old XML. Can be either handle or id reference
            # and this is guaranteed to be a textile bookmark
            if 'hlink' in attrs:
                handle = self.inaugurate(attrs['hlink'], "textile",
                                         Textile)
            else:
                handle = self.inaugurate_id(attrs.get('ref'), TEXTILE_KEY,
                                            Textile)
            self.db.bookmarks.append(handle)
            return

        # This is new XML, so we are guaranteed to have a handle ref
        handle = attrs['hlink'].replace('_', '')
        handle = self.import_handles[handle][target][HANDLE]
        # Bookmarks are at end, so all handle must exist before we do bookmrks
        if target == 'textile':
            if (self.db.get_textile_from_handle(handle) is not None
                    and handle not in self.db.bookmarks.get() ):
                self.db.bookmarks.append(handle)
        elif target == 'ensemble':
            if (self.db.get_ensemble_from_handle(handle) is not None
                    and handle not in self.db.ensemble_bookmarks.get() ):
                self.db.ensemble_bookmarks.append(handle)
        elif target == 'media':
            if (self.db.get_object_from_handle(handle) is not None
                    and handle not in self.db.media_bookmarks.get() ):
                self.db.media_bookmarks.append(handle)
        elif target == 'note':
            if (self.db.get_note_from_handle(handle) is not None
                    and handle not in self.db.note_bookmarks.get() ):
                self.db.note_bookmarks.append(handle)
        
    def start_textile(self, attrs):
        """
        Add a textile to db if it doesn't exist yet and assign
        id, privacy and changetime.
        """
        self.update(self.p.CurrentLineNumber)
        self.textile = Textile()
        
        orig_handle = attrs['handle'].replace('_', '')
        is_merge_candidate = (self.replace_import_handle and
                              self.db.has_textile_handle(orig_handle))
        self.inaugurate(orig_handle, "textile", self.textile)
        wearnow_id = self.legalize_id(attrs.get('id'), TEXTILE_KEY,
                                    self.idswap, self.db.id2user_format,
                                    self.db.find_next_textile_wearnow_id)
        self.textile.set_wearnow_id(wearnow_id)
        if is_merge_candidate:
            orig_textile = self.db.get_textile_from_handle(orig_handle)
            self.info.add('merge-candidate', TEXTILE_KEY, orig_textile,
                          self.textile)
        self.textile.private = bool(attrs.get("priv"))
        self.textile.change = int(attrs.get('change', self.change))
        self.info.add('new-object', TEXTILE_KEY, self.textile)
        
        if self.default_tag: 
            self.textile.add_tag(self.default_tag.handle)
        return self.textile

    def start_textiles(self, attrs):
        """
        Store the home textile of the database.
        """
        if 'home' in attrs:
            handle = self.inaugurate(attrs['home'], "textile", Textile)
            self.home = handle

    def start_childref(self, attrs):
        """
        Add a child reference to the ensemble currently processed.

        """
        self.childref = ChildRef()
        handle = self.inaugurate(attrs['hlink'], "textile", Textile)
        self.childref.ref = handle
        self.childref.private = bool(attrs.get('priv'))

        self.ensemble.add_child_ref(self.childref)

    def start_url(self, attrs):
        if "href" not in attrs:
            return
        url = Url()
        url.path = attrs["href"]
        url.set_description(attrs.get("description", ''))
        url.private = bool(attrs.get('priv'))
        url.type.set_from_xml_str(attrs.get('type', ''))
        if self.textile:
            self.textile.add_url(url)

    def start_file(self, attrs):
        self.object.mime = attrs['mime']
        if 'description' in attrs:
            self.object.desc = attrs['description']
        else:
            self.object.desc = ""
        #keep value of path, no longer make absolute paths on import
        src = attrs["src"]
        if src:
            self.object.path = src
            if self.all_abs and not os.path.isabs(src):
                self.all_abs = False
                self.info.add('relative-path', None, None)
        if 'checksum' in attrs:
            self.object.checksum = attrs['checksum']
        else:
            if os.path.isabs(src):
                full_path = src
            else:
                full_path = os.path.join(self.mediapath, src)
            self.object.checksum = create_checksum(full_path)

    def start_ensemble(self, attrs):
        """
        Add a ensemble object to db if it doesn't exist yet and assign
        id, privacy and changetime.
        """
        self.update(self.p.CurrentLineNumber)
        self.ensemble = Ensemble()
        
        orig_handle = attrs['handle'].replace('_', '')
        is_merge_candidate = (self.replace_import_handle and
                              self.db.has_ensemble_handle(orig_handle))
        self.inaugurate(orig_handle, "ensemble", self.ensemble)
        wearnow_id = self.legalize_id(attrs.get('id'), ENSEMBLE_KEY,
                                    self.fidswap, self.db.fid2user_format,
                                    self.db.find_next_ensemble_wearnow_id)
        self.ensemble.set_wearnow_id(wearnow_id)
        
        if is_merge_candidate:
            orig_ensemble = self.db.get_ensemble_from_handle(orig_handle)
            self.info.add('merge-candidate', ENSEMBLE_KEY, orig_ensemble,
                          self.ensemble)
        self.ensemble.private = bool(attrs.get("priv"))
        self.ensemble.change = int(attrs.get('change', self.change))
        self.info.add('new-object', ENSEMBLE_KEY, self.ensemble)
        if self.default_tag: 
            self.ensemble.add_tag(self.default_tag.handle)
        return self.ensemble

    def start_style(self, attrs):
        """
        Styled text tag in notes (v1.4.0 onwards).
        """
        tagtype = StyledTextTagType()
        tagtype.set_from_xml_str(attrs['name'].lower())
        try:
            val = attrs['value']
            match = self.wearnowuri.match(val)
            if match:
                target = {"Textile":"textile", "Ensemble":"ensemble",
                          "Media":"media",
                          "Note":"note"}[str(match.group('object_class'))]
                if match.group('handle') in self.import_handles:
                    if target in self.import_handles[match.group('handle')]:
                        val = "wearnow://%s/handle/%s" % (
                                match.group('object_class'),
                                self.import_handles[match.group('handle')]
                                                   [target][HANDLE])
            tagvalue = StyledTextTagType.STYLE_TYPE[int(tagtype)](val)
        except KeyError:
            tagvalue = None
        except ValueError:
            return
        
        self.note_tags.append(StyledTextTag(tagtype, tagvalue))

    def start_tag(self, attrs):
        """
        Tag definition.
        """
        if self.note is not None:
            # Styled text tag in notes (prior to v1.4.0)
            self.start_style(attrs)
            return

        # Tag defintion
        self.tag = Tag()
        self.inaugurate(attrs['handle'], "tag", self.tag)
        self.tag.change = int(attrs.get('change', self.change))
        self.info.add('new-object', TAG_KEY, self.tag)
        self.tag.set_name(attrs.get('name', _('Unknown when imported')))
        self.tag.set_color(attrs.get('color', '#000000000000'))
        self.tag.set_priority(int(attrs.get('priority', 0)))
        return self.tag

    def stop_tag(self, *tag):
        if self.note is not None:
            # Styled text tag in notes (prior to v1.4.0)
            return
        self.db.commit_tag(self.tag, self.trans, self.tag.get_change_time())
        self.tag = None

    def start_tagref(self, attrs):
        """
        Tag reference in a primary object.
        """
        handle = self.inaugurate(attrs['hlink'], "tag", Tag)

        if self.textile:
            self.textile.add_tag(handle)

        if self.ensemble:
            self.ensemble.add_tag(handle)

        if self.object:
            self.object.add_tag(handle)

        if self.note:
            self.note.add_tag(handle)

    def start_range(self, attrs):
        self.note_tags[-1].ranges.append((int(attrs['start']),
                                          int(attrs['end'])))
        
    def start_note(self, attrs):
        """
        Add a note to db if it doesn't exist yet and assign
        id, privacy, changetime, format and type.
        """
        self.in_note = 0
        
        # This is new note, with ID and handle already existing
        self.update(self.p.CurrentLineNumber)
        self.note = Note()
        
        orig_handle = attrs['handle'].replace('_', '')
        is_merge_candidate = (self.replace_import_handle and
                              self.db.has_note_handle(orig_handle))
        self.inaugurate(orig_handle, "note", self.note)
        wearnow_id = self.legalize_id(attrs.get('id'), NOTE_KEY,
                                  self.nidswap, self.db.nid2user_format,
                                  self.db.find_next_note_wearnow_id)
        self.note.set_wearnow_id(wearnow_id)
        if is_merge_candidate: 
            orig_note = self.db.get_note_from_handle(orig_handle)
            self.info.add('merge-candicate', NOTE_KEY, orig_note,
                              self.note)
                              
        self.note.private = bool(attrs.get("priv"))
        self.note.change = int(attrs.get('change', self.change))
        self.info.add('new-object', NOTE_KEY, self.note)
        self.note.format = int(attrs.get('format', Note.FLOWED))
        self.note.type.set_from_xml_str(attrs.get('type',
                                                  NoteType.UNKNOWN))
        
        self.note_text = None
        self.note_tags = []
            
        if self.default_tag: 
            self.note.add_tag(self.default_tag.handle)
        return self.note

    def start_noteref(self, attrs):
        """
        Add a note reference to the object currently processed.
        """
        if 'hlink' in attrs:
            handle = self.inaugurate(attrs['hlink'], "note", Note)
        else:
            raise WearNowImportError(_("The WearNow Xml you are trying to "
                "import is malformed."), _("Any note reference must have a "
                "'hlink' attribute."))

        # The order in this long if-then statement should reflect the
        # DTD: most deeply nested elements come first.
        if self.attribute:
            self.attribute.add_note(handle)
        elif self.textile:
            self.textile.add_note(handle)

    def start_objref(self, attrs):
        """
        Add a media object reference to the object currently processed.
        """
        self.objref = MediaRef()
        handle = self.inaugurate(attrs['hlink'], "media",
                                 MediaObject)
        self.objref.ref = handle
        self.objref.private = bool(attrs.get('priv'))
        if self.ensemble:
            self.ensemble.add_media_reference(self.objref)
        elif self.textile:
            self.textile.add_media_reference(self.objref)

    def start_region(self, attrs):
        rect = (int(attrs.get('corner1_x')),
                int(attrs.get('corner1_y')),
                int(attrs.get('corner2_x')),
                int(attrs.get('corner2_y')) )
        self.objref.set_rectangle(rect)

    def start_object(self, attrs):
        """
        Add a media object to db if it doesn't exist yet and assign
        id, privacy and changetime.
        """
        self.object = MediaObject()
        orig_handle = attrs['handle'].replace('_', '')
        is_merge_candidate = (self.replace_import_handle and
                              self.db.has_object_handle(orig_handle))
        self.inaugurate(orig_handle, "media", self.object)
        wearnow_id = self.legalize_id(attrs.get('id'), MEDIA_KEY,
                                     self.oidswap, self.db.oid2user_format,
                                     self.db.find_next_object_wearnow_id)
        self.object.set_wearnow_id(wearnow_id)
        if is_merge_candidate:
            orig_object = self.db.get_object_from_handle(orig_handle)
            self.info.add('merge-candidate', MEDIA_KEY, orig_object,
                          self.object)
        self.object.private = bool(attrs.get("priv"))
        self.object.change = int(attrs.get('change', self.change))
        self.info.add('new-object', MEDIA_KEY, self.object)

        if self.default_tag: 
            self.object.add_tag(self.default_tag.handle)
        return self.object

    def stop_textiles(self, *tag):
        pass

    def stop_database(self, *tag):
        self.update(self.p.CurrentLineNumber)

    def stop_object(self, *tag):
        self.db.commit_media_object(self.object, self.trans, 
                                    self.object.get_change_time())
        self.object = None

    def stop_objref(self, *tag):
        self.objref = None

    def stop_attribute(self, *tag):
        self.attribute = None

    def stop_attr_type(self, tag):
        self.attribute.set_type(tag)

    def stop_attr_value(self, tag):
        self.attribute.set_value(tag)

    def stop_ensemble(self, *tag):
        self.db.commit_ensemble(self.ensemble, self.trans,
                              self.ensemble.get_change_time())
        self.ensemble = None

    def stop_childref(self, tag):
        self.childref = None
        
    def stop_ensembles(self, *tag):
        self.ensemble = None

    def stop_textile(self, *tag):
        self.db.commit_textile(self.textile, self.trans,
                              self.textile.get_change_time())
        self.textile = None

    def stop_text(self, tag):
        self.note_text = tag
        
    def stop_note(self, tag):
        self.in_note = 0
        if self.note_text is not None:
            text = self.note_text
        else:
            text = tag
            
        self.note.set_styledtext(StyledText(text, self.note_tags))

        # The order in this long if-then statement should reflect the
        # DTD: most deeply nested elements come first.
        if self.attribute:
            self.attribute.add_note(self.note.handle)
        elif self.textile:
            self.textile.add_note(self.note.handle)

        self.db.commit_note(self.note, self.trans, self.note.get_change_time())
        self.note = None

    def stop_note_asothers(self, *tag):
        self.db.commit_note(self.note, self.trans, self.note.get_change_time())
        self.note = None

    def stop_research(self, tag):
        self.owner.set_name(self.resname)
        self.owner.set_address(self.resaddr)
        self.owner.set_locality(self.reslocality)
        self.owner.set_city(self.rescity)
        self.owner.set_state(self.resstate)
        self.owner.set_country(self.rescon)
        self.owner.set_postal_code(self.respos)
        self.owner.set_phone(self.resphone)
        self.owner.set_email(self.resemail)

    def stop_resname(self, tag):
        self.resname = tag

    def stop_resaddr(self, tag):
        self.resaddr = tag

    def stop_reslocality(self, tag):
        self.reslocality = tag

    def stop_rescity(self, tag):
        self.rescity = tag

    def stop_resstate(self, tag):
        self.resstate = tag

    def stop_rescountry(self, tag):
        self.rescon = tag

    def stop_respostal(self, tag):
        self.respos = tag

    def stop_resphone(self, tag):
        self.resphone = tag

    def stop_resemail(self, tag):
        self.resemail = tag

    def stop_mediapath(self, tag):
        self.mediapath = tag

    def startElement(self, tag, attrs):
        self.func_list[self.func_index] = (self.func, self.tlist)
        self.func_index += 1
        self.tlist = []

        try:
            f, self.func = self.func_map[tag]
            if f:
                f(attrs)
        except KeyError:
            self.func_map[tag] = (None, None)
            self.func = None

    def endElement(self, tag):
        if self.func:
            self.func(''.join(self.tlist))
        self.func_index -= 1    
        self.func, self.tlist = self.func_list[self.func_index]
        
    def characters(self, data):
        if self.func:
            self.tlist.append(data)

    def fix_not_instantiated(self):
        uninstantiated = []
        for orig_handle in self.import_handles.keys():
            tglist = [target for target in self.import_handles[orig_handle].keys() if
                    not self.import_handles[orig_handle][target][INSTANTIATED]]
            for target in tglist:
                uninstantiated += [(orig_handle, target)]
        if uninstantiated:
            expl_note = create_explanation_note(self.db)
            self.db.commit_note(expl_note, self.trans, time.time())
            self.info.expl_note = expl_note.get_wearnow_id()
            for orig_handle, target in uninstantiated:
                class_arg = {'handle': orig_handle, 'id': None, 'priv': False}
                if target == 'ensemble':
                    objs = make_unknown(class_arg, expl_note.handle,
                            self.func_map[target][0], self.func_map[target][1],
                            self.trans, db=self.db)
                elif target == 'note':
                    objs = make_unknown(class_arg, expl_note.handle,
                            self.func_map[target][0], self.stop_note_asothers,
                            self.trans)
                else:
                    if target == 'media':
                        target = 'object'
                    objs = make_unknown(class_arg, expl_note.handle,
                            self.func_map[target][0], self.func_map[target][1],
                            self.trans)
                for obj in objs:
                    key = CLASS_TO_KEY_MAP[obj.__class__.__name__]
                    self.info.add('unknown-object', key, obj)

def append_value(orig, val):
    if orig:
        return "%s, %s" % (orig, val)
    else:
        return val
