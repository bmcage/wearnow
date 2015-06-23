#
# WearNow - a GTK+/GNOME based program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2008       Gary Burton
# Copyright (C) 2008       Robert Cheramy <robert@cheramy.net>
# Copyright (C) 2009       Douglas S. Blank
# Copyright (C) 2010       Jakim Friant
# Copyright (C) 2010-2011  Nick Hall
# Copyright (C) 2013  Benny Malengier
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
Contains the interface to allow a database to get written using
WearNow' XML file format.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import time
import shutil
import os
import codecs
from xml.sax.saxutils import escape

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".WriteXML")

#-------------------------------------------------------------------------
#
# WearNow modules
#
#-------------------------------------------------------------------------
from wearnow.tex.const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext
from wearnow.tex.const import URL_HOMEPAGE
from wearnow.tex.updatecallback import UpdateCallback
from wearnow.tex.db.exceptions import DbWriteFailure
from wearnow.version import VERSION
from wearnow.tex.constfunc import win, conv_to_unicode
from wearnow.gui.plug.export import WriterOptionBox
import wearnow.plugins.lib.libwearnowxml as libwearnowxml

#-------------------------------------------------------------------------
#
# Attempt to load the GZIP library. Some version of python do not seem
# to be compiled with this available.
#
#-------------------------------------------------------------------------
try:
    import gzip
    _gzip_ok = 1
except:
    _gzip_ok = 0

# table for skipping control chars from XML except 09, 0A, 0D
strip_dict = dict.fromkeys(list(range(9))+list(range(11,13))+list(range(14, 32)))

def escxml(d):
    return escape(d,
                  {'"' : '&quot;',
                   '<' : '&lt;',
                   '>' : '&gt;',
                   }) if d else ""

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class WearNowXmlWriter(UpdateCallback):
    """
    Writes a database to the XML file.
    """

    def __init__(self, db, strip_photos=0, compress=1, version="unknown",
                 user=None):
        """
        Initialize, but does not write, an XML file.

        db - database to write
        strip_photos - remove paths off of media object paths
        >              0: do not touch the paths
        >              1: remove everything expect the filename (eg gpkg)
        >              2: remove leading slash (quick write)
        compress - attempt to compress the database
        """
        UpdateCallback.__init__(self, user.callback)
        self.user = user
        self.compress = compress
        if not _gzip_ok:
            self.compress = False
        self.db = db
        self.strip_photos = strip_photos
        self.version = version

        self.status = None

    def write(self, filename):
        """
        Write the database to the specified file.
        """
        if filename == '-':
            import sys
            g = sys.stdout
            self.compress = False
        else:
            base = os.path.dirname(filename)
            if os.path.isdir(base):
                if not os.access(base, os.W_OK) or not os.access(base, os.R_OK):
                    raise DbWriteFailure(
                            _('Failure writing %s') % filename,
                            _("The database cannot be saved because you do "
                            "not have permission to write to the directory. "
                            "Please make sure you have write access to the "
                                "directory and try again."))
                    return 0
            else:
                raise DbWriteFailure(_('No directory'),
                                     _('There is no directory %s.\n\n'
                                       'Please select another directory '
                                       'or create it.') % base )
                return 0

            if os.path.exists(filename):
                if not os.access(filename, os.W_OK):
                    raise DbWriteFailure(
                            _('Failure writing %s') % filename,
                            _("The database cannot be saved because you do "
                            "not have permission to write to the file. "
                            "Please make sure you have write access to the "
                            "file and try again."))
                    return 0

            self.fileroot = os.path.dirname(filename)
            try:
                if self.compress and _gzip_ok:
                    try:
                        g = gzip.open(filename,"wb")
                    except:
                        g = open(filename,"w")
                else:
                    g = open(filename,"w")
            except IOError as msg:
                LOG.warn(str(msg))
                raise DbWriteFailure(_('Failure writing %s') % filename,
                                        str(msg))
                return 0

        self.g = codecs.getwriter("utf8")(g)

        self.write_xml_data()
        if filename != '-':
            g.close()
        return 1

    def write_handle(self, handle):
        """
        Write the database to the specified file handle.
        """

        if self.compress and _gzip_ok:
            try:
                g = gzip.GzipFile(mode="wb", fileobj=handle)
            except:
                g = handle
        else:
            g = handle

        self.g = codecs.getwriter("utf8")(g)

        self.write_xml_data()
        g.close()
        return 1

    def write_xml_data(self):

        date = time.localtime(time.time())
        owner = self.db.get_owner()

        textile_len = self.db.get_number_of_textiles()
        ensemble_len = self.db.get_number_of_ensembles()
        obj_len = self.db.get_number_of_media_objects()
        note_len = self.db.get_number_of_notes()
        tag_len = self.db.get_number_of_tags()

        total_steps = (textile_len + ensemble_len + obj_len + note_len +
                       tag_len
                      )

        self.set_total(total_steps)

        self.g.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.g.write('<!DOCTYPE database '
                     'PUBLIC "-//WearNow//DTD WearNow XML %s//EN"\n'
                     '"%sxml/%s/wearnowxml.dtd">\n'
                     % (libwearnowxml.WEARNOW_XML_VERSION, URL_HOMEPAGE,
                        libwearnowxml.WEARNOW_XML_VERSION))
        self.g.write('<database xmlns="%sxml/%s/">\n'
                     % (URL_HOMEPAGE, libwearnowxml.WEARNOW_XML_VERSION))
        self.g.write("  <header>\n")
        self.g.write('    <created date="%04d-%02d-%02d\"' % date[:3])
        self.g.write(" version=\"" + self.version + "\"")
        self.g.write("/>\n")
        self.g.write("    <owner>\n")
        self.write_line("resname", owner.get_name(),3)
        self.write_line("resaddr", owner.get_address(),3)
        self.write_line("reslocality", owner.get_locality(),3)
        self.write_line("rescity", owner.get_city(),3)
        self.write_line("resstate", owner.get_state(),3)
        self.write_line("rescountry", owner.get_country(),3)
        self.write_line("respostal", owner.get_postal_code(),3)
        self.write_line("resphone", owner.get_phone(),3)
        self.write_line("resemail", owner.get_email(),3)
        self.g.write("    </owner>\n")
        self.write_metadata()
        self.g.write("  </header>\n")

        # Write table objects
        if tag_len > 0:
            self.g.write("  <tags>\n")
            for key in sorted(self.db.get_tag_handles()):
                tag = self.db.get_tag_from_handle(key)
                self.write_tag(tag, 2)
                self.update()
            self.g.write("  </tags>\n")

        if textile_len > 0:
            self.g.write("  <textiles")
            textile = self.db.get_default_textile()
            if textile:
                self.g.write(' home="_%s"' % textile.handle)
            self.g.write('>\n')

            for handle in sorted(self.db.get_textile_handles()):
                textile = self.db.get_textile_from_handle(handle)
                self.write_textile(textile, 2)
                self.update()
            self.g.write("  </textiles>\n")

        if ensemble_len > 0:
            self.g.write("  <ensembles>\n")
            for handle in sorted(self.db.iter_ensemble_handles()):
                ensemble = self.db.get_ensemble_from_handle(handle)
                self.write_ensemble(ensemble,2)
                self.update()
            self.g.write("  </ensembles>\n")

        if obj_len > 0:
            self.g.write("  <objects>\n")
            for handle in sorted(self.db.get_media_object_handles()):
                obj = self.db.get_object_from_handle(handle)
                self.write_object(obj,2)
                self.update()
            self.g.write("  </objects>\n")

        if note_len > 0:
            self.g.write("  <notes>\n")
            for key in sorted(self.db.get_note_handles()):
                note = self.db.get_note_from_handle(key)
                self.write_note(note, 2)
                self.update()
            self.g.write("  </notes>\n")

        # Data is written, now write bookmarks.
        self.write_bookmarks()

        self.g.write("</database>\n")

#        self.status.end()
#        self.status = None

    def write_metadata(self):
        """ Method to write out metadata of the database
        """
        mediapath= self.db.get_mediapath()
        if mediapath is not None:
            self.write_line("mediapath", mediapath, 2)

    def write_bookmarks(self):
        bm_textile_len = len(self.db.bookmarks.get())
        bm_ensemble_len = len(self.db.ensemble_bookmarks.get())
        bm_obj_len = len(self.db.media_bookmarks.get())
        bm_note_len = len(self.db.note_bookmarks.get())

        bm_len = (bm_textile_len + bm_ensemble_len + bm_obj_len + bm_note_len
                  )

        if bm_len > 0:
            self.g.write("  <bookmarks>\n")

            for handle in self.db.get_bookmarks().get():
                self.g.write('    <bookmark target="textile" hlink="_%s"/>\n'
                             % handle )
            for handle in self.db.get_ensemble_bookmarks().get():
                self.g.write('    <bookmark target="ensemble" hlink="_%s"/>\n'
                             % handle )
            for handle in self.db.get_media_bookmarks().get():
                self.g.write('    <bookmark target="media" hlink="_%s"/>\n'
                             % handle )
            for handle in self.db.get_repo_bookmarks().get():
                self.g.write('    <bookmark target="repository" hlink="_%s"/>\n'
                             % handle )
            for handle in self.db.get_note_bookmarks().get():
                self.g.write('    <bookmark target="note" hlink="_%s"/>\n'
                             % handle )

            self.g.write("  </bookmarks>\n")

    def write_tag(self, tag, index=2):
        """
        Write a tag definition.
        """
        if not tag:
            return

        self.write_table_tag('tag', tag, index, close=False)
        self.g.write(' name="%s"' % escxml(tag.get_name()))
        self.g.write(' color="%s"' % tag.get_color())
        self.g.write(' priority="%d"' % tag.get_priority())
        self.g.write('/>\n')

    def fix(self,line):
        try:
            l = str(line)
        except:
            l = conv_to_unicode(str(line), errors='replace')
        l = l.strip().translate(strip_dict)
        return escxml(l)

    def write_note_list(self, note_list,indent=0):
        for handle in note_list:
            self.write_ref("noteref", handle,indent)

    def write_note(self, note, index=2):
        if not note:
            return

        self.write_primary_tag('note', note, index, close=False)

        ntype = escxml(note.get_type().xml_str())
        format = note.get_format()
        text = note.get_styledtext()
        styles = text.get_tags()
        text = str(text)

        self.g.write(' type="%s"' % ntype)
        if format != note.FLOWED:
            self.g.write(' format="%d"' % format)
        self.g.write('>\n')

        self.write_text('text', text, index + 1)

        if styles:
            self.write_styles(styles, index + 1)

        for tag_handle in note.get_tag_list():
            self.write_ref("tagref", tag_handle, index+1)

        self.g.write('  ' * index + '</note>\n')

    def write_styles(self, styles, index=3):
        for style in styles:
            name = style.name.xml_str()
            value = style.value

            self.g.write('  ' * index + '<style name="%s"' % name)
            if value:
                self.g.write(' value="%s"' % escxml(str(value)))
            self.g.write('>\n')

            for (start, end) in style.ranges:
                self.g.write(('  ' * (index + 1)) +
                             '<range start="%d" end="%d"/>\n' % (start, end))

            self.g.write('  ' * index + '</style>\n')

    def write_text(self, val, text, indent=0):
        if not text:
            return

        if indent:
            self.g.write('  ' * indent)

        self.g.write('<%s>' % val)
        self.g.write(self.fix(text.rstrip()))
        self.g.write("</%s>\n" % val)

    def write_textile(self,textile,index=1):
        sp = "  "*index
        self.write_primary_tag("textile",textile,index,close=False)
        desc = textile.get_description()
        if desc:
            self.g.write(' description="%s"' % self.fix(desc))
        else:
            self.g.write(' description=""')

        ttype = escxml(textile.get_type().xml_str())
        self.g.write(' type="%s"' % ttype)
        self.g.write('>\n')

        self.write_media_list(textile.get_media_list(),index+1)

        self.write_attribute_list(textile.get_attribute_list())
        self.write_url_list(textile.get_url_list(),index+1)

        self.write_note_list(textile.get_note_list(),index+1)

        for tag_handle in textile.get_tag_list():
            self.write_ref("tagref", tag_handle, index+1)

        self.g.write("%s</textile>\n" % sp)

    def write_ensemble(self,ensemble,index=1):
        sp = "  "*index
        self.write_ensemble_handle(ensemble,index)

        self.write_media_list(ensemble.get_media_list(),index+1)

        for child_ref in ensemble.get_child_ref_list():
            self.dump_child_ref(child_ref,index+1)

        self.write_note_list(ensemble.get_note_list(),index+1)

        for tag_handle in ensemble.get_tag_list():
            self.write_ref("tagref", tag_handle, index+1)

        self.g.write("%s</ensemble>\n" % sp)

    def dump_child_ref(self,childref,index=1):
        if not childref or not childref.ref:
            return
        sp = "  "*index
        
#        priv_text = conf_priv(childref)

        self.write_ref('childref',childref.ref,index,close=True)
#                       extra_text=priv_text)

    def write_ref(self,tagname, handle,index=1,close=True,extra_text=''):
        if handle:
            if close:
                close_tag = "/"
            else:
                close_tag = ""
            sp = "  "*index
            self.g.write('%s<%s hlink="_%s"%s%s>\n'
                         % (sp,tagname, handle,extra_text,close_tag))

    def write_primary_tag(self, tagname, obj, index=1, close=True):
        """
        Write the tag attributes common to all primary objects.
        """
        if not obj:
            return
        priv_text = conf_priv(obj)
        id_text = ' id="%s"' % escxml(obj.wearnow_id)

        self.write_table_tag(tagname, obj, index, False)
        self.g.write(id_text + priv_text)
        if close:
            self.g.write('>\n')

    def write_table_tag(self, tagname, obj, index=1, close=True):
        """
        Write the tag attributes common to all table objects.
        """
        if not obj:
            return
        sp = "  " * index
        try:
            change_text = ' change="%d"' %  obj.get_change_time()
        except:
            change_text = ' change="%d"' %  0

        handle_text = ' handle="_%s"' % obj.get_handle()

        obj_text = '%s<%s' % (sp, tagname)
        self.g.write(obj_text + handle_text + change_text)
        if close:
            self.g.write('>\n')

    def write_ensemble_handle(self,ensemble,index=1):
        sp = "  "*index
        self.write_primary_tag('ensemble',ensemble,index)

    def write_line(self,tagname,value,indent=1):
        if value:
            self.g.write('%s<%s>%s</%s>\n' %
                         ('  '*indent,tagname,self.fix(value),tagname))

    def write_line_nofix(self,tagname,value,indent=1):
        """Writes a line, but does not escape characters.
            Use this instead of write_line if the value is already fixed,
            this avoids &amp; becoming &amp;amp;
        """
        if value:
            self.g.write('%s<%s>%s</%s>\n' %
                         ('  '*indent, tagname, value, tagname))

    def write_line_always(self,tagname,value,indent=1):
        """Writes a line, always, even with a zero value."""
        self.g.write('%s<%s>%s</%s>\n' %
                     ('  '*indent,tagname,self.fix(value),tagname))

    def write_force_line(self,label,value,indent=1):
        if value is not None:
            self.g.write('%s<%s>%s</%s>\n' % ('  '*indent,label,self.fix(value),label))

    def append_value(self, orig,val):
        if orig:
            return "%s, %s" % (orig,val)
        else:
            return val

    def write_attribute_list(self, list, indent=3):
        sp = '  ' * indent
        for attr in list:
            self.g.write('%s<attribute%s type="%s" value="%s"' %
                         (sp,conf_priv(attr),escxml(attr.get_type().xml_str()),
                         self.fix(attr.get_value()))
                         )
            nlist = attr.get_note_list()
            if (len(nlist)) == 0:
                self.g.write('/>\n')
            else:
                self.g.write('>\n')
                self.write_note_list(attr.get_note_list(),indent+1)
                self.g.write('%s</attribute>\n' % sp)

    def write_media_list(self,list,indent=3):
        sp = '  '*indent
        for photo in list:
            mobj_id = photo.get_reference_handle()
            self.g.write('%s<objref hlink="%s"' % (sp,"_"+mobj_id))
            if photo.get_privacy():
                self.g.write(' priv="1"')
            rect = photo.get_rectangle()
            if rect is not None :
                corner1_x = rect[0]
                corner1_y = rect[1]
                corner2_x = rect[2]
                corner2_y = rect[3]
                if corner1_x is None : corner1_x = 0
                if corner1_y is None : corner1_y = 0
                if corner2_x is None : corner2_x = 100
                if corner2_y is None : corner2_y = 100
                #don't output not set rectangle
                if (corner1_x == corner1_y == corner2_x == corner2_y == 0 or
                   corner1_x == corner1_y == 0 and
                   corner2_x == corner2_y == 100):
                    rect = None
            if (rect is None):
                self.g.write("/>\n")
            else:
                self.g.write(">\n")
                if rect is not None :
                    self.g.write(' %s<region corner1_x="%d" corner1_y="%d" '
                                 'corner2_x="%d" corner2_y="%d"/>\n' % (
                                    sp,
                                    corner1_x,
                                    corner1_y,
                                    corner2_x,
                                    corner2_y
                                    )
                                )
                self.g.write('%s</objref>\n' % sp)

    def write_url_list(self, list, index=1):
        sp = "  "*index
        for url in list:
            url_type = url.get_type().xml_str()
            if url_type:
                type_text = ' type="%s"' % escxml(url_type)
            else:
                type_text = ''
            priv_text = conf_priv(url)
            if url.get_description() != "":
                desc_text = ' description="%s"' % self.fix(
                    url.get_description())
            else:
                desc_text = ''
            path_text = '  href="%s"' % self.fix(url.get_path())
            self.g.write('%s<url%s%s%s%s/>\n' % (
                            sp,
                            priv_text,
                            path_text,
                            type_text,
                            desc_text
                            )
                        )

    def write_object(self, obj, index=1):
        self.write_primary_tag("object", obj, index)
        handle = obj.get_wearnow_id()
        mime_type = obj.get_mime_type()
        path = obj.get_path()
        desc = obj.get_description()
        if desc:
            desc_text = ' description="%s"' % self.fix(desc)
        else:
            desc_text = ''
        checksum = obj.get_checksum()
        if checksum:
            checksum_text = ' checksum="%s"' % checksum
        else:
            checksum_text = ''
        if self.strip_photos == 1:
            path = os.path.basename(path)
        elif self.strip_photos == 2 and (len(path)>0 and os.path.isabs(path)):
            drive, path = os.path.splitdrive(path)
            path = path[1:]
        if win():
            # Always export path with \ replaced with /. Otherwise import
            # from Windows to Linux of gpkg's path to images does not work.
            path = path.replace('\\','/')
        self.g.write('%s<file src="%s" mime="%s"%s%s/>\n'
                     % ("  "*(index+1), self.fix(path), self.fix(mime_type),
                        checksum_text, desc_text))

        for tag_handle in obj.get_tag_list():
            self.write_ref("tagref", tag_handle, index+1)

        self.g.write("%s</object>\n" % ("  "*index))

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def sortById(first,second):
    fid = first.get_wearnow_id()
    sid = second.get_wearnow_id()

    if fid < sid:
        return -1
    else:
        return fid != sid

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def conf_priv(obj):
    if obj.get_privacy() != 0:
        return ' priv="%d"' % obj.get_privacy()
    else:
        return ''

#-------------------------------------------------------------------------
#
# export_data
#
#-------------------------------------------------------------------------
def export_data(database, filename, user, option_box=None):
    """
    Call the XML writer with the syntax expected by the export plugin.
    """
    if os.path.isfile(filename):
        try:
            shutil.copyfile(filename, filename + ".bak")
            shutil.copystat(filename, filename + ".bak")
        except:
            pass

    compress = _gzip_ok == 1

    if option_box:
        option_box.parse_options()
        database = option_box.get_filtered_database(database)

    g = XmlWriter(database, user, 0, compress)
    return g.write(filename)

#-------------------------------------------------------------------------
#
# XmlWriter
#
#-------------------------------------------------------------------------
class XmlWriter(WearNowXmlWriter):
    """
    Writes a database to the XML file.
    """

    def __init__(self, dbase, user, strip_photos, compress=1):
        WearNowXmlWriter.__init__(
            self, dbase, strip_photos, compress, VERSION, user)
        self.user = user

    def write(self, filename):
        """
        Write the database to the specified file.
        """
        ret = 0 #False
        try:
            ret = WearNowXmlWriter.write(self, filename)
        except DbWriteFailure as msg:
            (m1, m2) = msg.messages()
            self.user.notify_error("%s\n%s" % (m1, m2))
        return ret
