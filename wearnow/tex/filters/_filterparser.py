#
# WearNow - a GTK+/GNOME based genealogy program
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

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
from xml.sax import handler
from ..const import WEARNOW_LOCALE as glocale
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from ._genericfilter import GenericFilterFactory
from . import rules

#-------------------------------------------------------------------------
#
# FilterParser
#
#-------------------------------------------------------------------------
class FilterParser(handler.ContentHandler):
    """Parses the XML file and builds the list of filters"""
    
    def __init__(self, gfilter_list):
        handler.ContentHandler.__init__(self)
        self.gfilter_list = gfilter_list
        self.f = None
        self.r = None
        self.a = []
        self.cname = None
        self.namespace = 'Textile'
        self.use_regex = False
        
    def setDocumentLocator(self, locator):
        self.locator = locator

    def startElement(self, tag, attrs):
        if tag == "object":
            if 'type' in attrs:
                self.namespace = attrs['type']
            else:
                self.namespace = "generic"
        elif tag == "filter":
            self.f = GenericFilterFactory(self.namespace)()
            self.f.set_name(attrs['name'])
            if 'function' in attrs:
                try:
                    if int(attrs['function']):
                        op = 'or'
                    else:
                        op = 'and'
                except ValueError:
                    op = attrs['function']
                self.f.set_logical_op(op)
            if 'invert' in attrs:
                self.f.set_invert(attrs['invert'])
            if 'comment' in attrs:
                self.f.set_comment(attrs['comment'])
            self.gfilter_list.add(self.namespace, self.f)
        elif tag == "rule":
            if 'use_regex' in attrs:
                self.use_regex = attrs['use_regex'] == 'True'
            else:
                self.use_regex = False
            save_name = attrs['class']
            if save_name in old_names_2_class:
                self.r = old_names_2_class[save_name]
            else:
                try:
                    # First try to use fully qualified name
                    exec('self.r = %s' % save_name)
                except (ImportError, NameError, AttributeError ):
                    # Now try to use name from rules.namespace
                    mc_match = save_name.split('.')
                    last_name = mc_match[-1]
                    try:
                        exec('self.r = rules.%s.%s' % (
                            self.namespace.lower(), last_name))
                    except (ImportError, NameError, AttributeError ):
                        print("ERROR: Filter rule '%s' in "\
                              "filter '%s' not found!"\
                                  % (save_name, self.f.get_name()))
                        self.r = None
                        return
            self.a = []
        elif tag == "arg":
            self.a.append(attrs['value'])

    def endElement(self, tag):
        if tag == "rule" and self.r is not None:
            if len(self.r.labels) != len(self.a):
                self.__upgrade()
            if len(self.r.labels) < len(self.a):
                print(_("WARNING: Too many arguments in filter '%s'!\n"\
                        "Trying to load with subset of arguments.")  %\
                        self.f.get_name())
                nargs = len(self.r.labels)
                rule = self.r(self.a[0:nargs], self.use_regex)
                self.f.add_rule(rule)
            else:
                if len(self.r.labels) > len(self.a):
                    print(_("WARNING: Too few arguments in filter '%s'!\n" \
                            "         Trying to load anyway in the hope this "\
                            "will be upgraded.") %\
                            self.f.get_name())
                try:
                    rule = self.r(self.a, self.use_regex)
                except AssertionError as msg:
                    print(msg)
                    print(_("ERROR: filter %s could not be correctly loaded. "
                            "Edit the filter!") % self.f.get_name())
                    return
                
                self.f.add_rule(rule)
            
    def characters(self, data):
        pass

    def __upgrade(self):
        """
        Upgrade argument lists to latest version.
        eg if self.r == rules.IsPrivate and len(self.a) == ?? :
           change self.a to correct length
        """

#-------------------------------------------------------------------------
#
# Name to class mappings
#
#-------------------------------------------------------------------------
# This dict is mapping from old names to new names, so that the existing
# custom_filters.xml will continue working
old_names_2_class = {
    
}
