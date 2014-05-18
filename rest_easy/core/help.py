#    Copyright (C) 2013 Tom Kerr
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import print_function

import os, sys
major, minor = sys.version_info[0], sys.version_info[1]
if major == 2 and minor >= 7:
    from StringIO import StringIO
elif major == 3:
    from io import StringIO

import pprint
from collections import OrderedDict

from .parser import Parser
from .alt import AlternateInterface
from .parameter import Source, API, ResourceMethod, Property


class FmtStr(object):
    indent = '    '
    reset = '\033[0m'
    bold = '\033[1m'
    italic = '\033[3m'
    under = '\033[4m'

    @staticmethod
    def header(string):
        return (FmtStr.bold + FmtStr.under +
                string + FmtStr.reset)
    
    @staticmethod
    def subheader(string):
        return (FmtStr.indent + FmtStr.bold + FmtStr.under +
                string + FmtStr.reset)

    @staticmethod
    def field(string, indent=0):
        s = ''
        for i in range(0, indent):
            s += FmtStr.indent
        return (s + FmtStr.italic +
                str(string) + FmtStr.reset)
        
        
class Helper(object):
    """ Prints object information.

        Examples:
    
            r = RestEasy()


            r.help() -> Prints the list of available Sources

            r.help('europeana') -> Prints information regarding europeana

            r.help('europeana->v2->Search->query') -> Prints information 
                                                      regarding a subobject

            dpla = r.get_wrappers('dpla')
            
            dpla.help()

            dpla('v2').searchIn.title.help()
        
    """

    def help(self, string=None):
        self._buffer_ = ''
        if string is None:
            self._get_sources_()
        else:
            source, api, detail = Parser._get_query_elements_(string)
            source_obj = self.get_wrappers(source)
            if not api:
                self._get_parameters_(source_obj)
            else:
                api_obj = getattr(source_obj, api)
                if not detail:
                    self._get_parameters_(api_obj)
                else:
                    self._get_detail_(api_obj, detail)
        print (self._buffer_)

    def _get_sources_(self):
        self._buffer_ += ('\n' + FmtStr.header('Source List') + '\n')
        for source in self.source_list:
            self._buffer_ += (FmtStr.field(source, 1) + '\n')

    def _get_essential_(self, obj):
        if hasattr(obj, '_essential_'):
            if obj._essential_:
                self._buffer_ += (FmtStr.subheader('essential:') +
                                  FmtStr.field(obj._essential_, 2) + '\n')

    def _get_requirements_(self, obj):
        if hasattr(obj, '_requirements_'):
            requirements = obj._requirements_
            if requirements:
                self._buffer_ += '\n' + FmtStr.subheader('requirements') + ': \n'
                for k, v in requirements.required.items():
                    if v:
                        values = StringIO()
                        pprint.pprint(v, stream=values)
                        self._buffer_ += FmtStr.field(k, 2)
                        strings = values.getvalue().split('\n')
                        for s in strings:
                            self._buffer_ += '\n' + FmtStr.field(s, 3)

    
    def _get_parameters_(self, obj):
        params = OrderedDict([('sources', []),
                              ('apis', []),
                              ('methods', []),
                              ('properties', [])])
        obj_type = obj.__class__.__name__
        if obj_type == 'function':
            obj_type = 'Property'

        self._buffer_ += ('\n' + FmtStr.header(obj_type) +
                          ' "'+obj._name_+'"' + '\n')
        if obj.__doc__:
            for s in obj.__doc__.split('\n'):
                self._buffer_ += '\n' + FmtStr.field(s, 1)

        if hasattr(obj, '_http_method_'):
            self._buffer_ += ('\n' + FmtStr.subheader('http_method') + ': ' +
                              FmtStr.field(obj._http_method_) + '\n')
        self._get_essential_(obj)
        self._get_requirements_(obj)
        if hasattr(obj, '__call__'):
           self._get_callable_(obj)

        for attrname in dir(obj):
            if not self._is_internal_(attrname):
                attr = getattr(obj, attrname)
                if isinstance(attr, Source):
                    params['sources'].append(attrname)
                elif isinstance(attr, API):
                    params['apis'].append(attrname)
                elif isinstance(attr, ResourceMethod):
                    params['methods'].append(attrname)
                elif isinstance(attr, Property) or \
                  attr.__class__.__name__ == 'function':
                    params['properties'].append(attrname)
        for param, fields in params.items():
            if fields:
                self._buffer_ += '\n' + FmtStr.subheader(param) + ':'
                for f in fields:
                    self._buffer_ += '\n' + FmtStr.field(f, 2)
                self._buffer_ += '\n'
                
    def _get_callable_(self, obj):
        if not obj._key_ and not obj._expected_value_:
            return
        self._buffer_ += ('\n' + FmtStr.subheader('key') + ': ' +
                          FmtStr.field(obj._key_))
        if obj._expected_value_ and \
          type(obj._expected_value_).__name__ == 'SRE_Pattern':
            ev = str(obj._expected_value_.pattern)
        else:
            ev = str(obj._expected_value_)
          
        self._buffer_ += ('\n' + FmtStr.subheader('expected_value') + ': '
                            + FmtStr.field(ev) + '\n')
      
    def _get_detail_(self, api, detail):
        elements = Parser._parse_query_string_(detail, mode='lookup')
        self._find_detail_(api, [elements,])

    def _find_detail_(self, root, elements):
        for elem in elements:
            if isinstance(elem, str):
                attr = getattr(root, elem)
                self._get_parameters_(attr)

            elif isinstance(elem, dict):
                for k, v in elem.items():
                    if hasattr(root, k):
                        root = getattr(root, k)
                    if isinstance(v, dict):
                        self._find_detail_(root, [v,])
                        return
                    elif v and hasattr(root, v):
                        root = getattr(root, v)
                    self._get_parameters_(root)

    def _is_internal_(self, attr):
        if attr.startswith('_') and attr.endswith('_'):
            return True
        elif '__' in attr:
            return True
        else:
            return False
