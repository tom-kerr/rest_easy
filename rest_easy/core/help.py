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
from colorama import init as colorama_init
from colorama import Fore, Back, Style
colorama_init()

from .parser import Parser
from .alt import AlternateInterface
from .parameter import API, ResourceMethod, Property


class Helper(object):

    fore = {'red': Fore.RED, 'black': Fore.BLACK,
            'green': Fore.GREEN, 'yellow': Fore.YELLOW,
            'blue': Fore.BLUE, 'white': Fore.WHITE,
            'cyan': Fore.CYAN, 'magenta': Fore.MAGENTA,
            'reset': Fore.RESET}

    back = {'red': Back.RED, 'black': Back.BLACK,
            'green': Back.GREEN, 'yellow': Back.YELLOW,
            'blue': Back.BLUE, 'white': Back.WHITE,
            'cyan': Back.CYAN, 'magenta': Back.MAGENTA,
            'reset': Back.RESET}

    style = {'dim': Style.DIM, 'normal': Style.NORMAL ,
             'bright': Style.BRIGHT, 'reset': Style.BRIGHT}

    def help(self, string=None):
        self._buffer_ = ''
        if string is None:
            self._print_sources_()
        else:
            source, api, detail = Parser._get_query_elements_(string)
            source_obj = self.get_wrappers(source)
            if not api:
                self._print_source_details_(source_obj)
            else:
                api_obj = getattr(source_obj, api)
                if not detail:
                    self._print_api_specs_(api_obj)
                else:
                    self._print_detail_(api_obj, detail)
        print (self._color_(self._buffer_, back='black'))

    def _print_sources_(self):
        self._buffer_ += self._color_('\nSource List\n', fore='red')
        for source in self.source_list:
            self._buffer_ += '\t' + self._color_(source, fore='green') + '\n'

    def _color_(self, string, **kwargs):
        colored_string = ''
        for atr in ('fore', 'back', 'style'):
            if atr in kwargs and kwargs[atr]:
                color = kwargs[atr]
                colored_string += getattr(self, atr)[color]
        colored_string += str(string)
        for atr in ('fore', 'back', 'style'):
            if atr in kwargs and kwargs[atr]:
                colored_string += getattr(self, atr)['reset']
        return colored_string

    def _print_source_details_(self, source):
        #if source.__doc__:
        #    self._buffer_ += '\n\t' + self._color_(source.__doc__, fore='yellow') + '\n'
        self._print_parameters_(source)

    def _print_api_specs_(self, api):
        #if api.__doc__:
        #    self._buffer_ += '\n\t' + self._color_(api.__doc__, fore='yellow') + '\n'
        self._print_parameters_(api)

    def _print_essential_(self, obj):
        if hasattr(obj, '_essential_'):
            if obj._essential_:
                self._buffer_ += ('    ' + self._color_('essential: ', fore='blue') +
                                  self._color_(obj._essential_, fore='white') + '\n')

    def _print_requirements_(self, obj):
        if hasattr(obj, '_requirements_'):
            requirements = obj._requirements_
            if requirements:
                self._buffer_ += '\n    ' + self._color_('requirements: \n', fore='blue')
                for k, v in requirements.required.items():
                    if v:
                        values = StringIO()
                        pprint.pprint(v, stream=values)
                        self._buffer_ += '\t' + self._color_(k, fore='cyan')
                        strings = values.getvalue().split('\n')
                        for s in strings:
                            self._buffer_ += self._color_('\n\t    ' + s,
                                                          fore='white')
                        self._buffer_ += '\n'

    def _print_parameters_(self, obj):
        apis = []
        methods = []
        properties = []
        obj_type = obj.__class__.__name__
        if obj_type == 'function':
            obj_type = 'Property'

        self._buffer_ += ('\n' + self._color_(obj_type, fore='red') +
                          self._color_(' "'+obj._name_+'"', fore='magenta') + '\n')
        if obj.__doc__:
            for s in obj.__doc__.split('\n'):
                self._buffer_ += '    ' + self._color_(s, fore='yellow') + '\n'

        #consolidate?
        if hasattr(obj, '_http_method_'):
            self._buffer_ += ('    ' + self._color_('http_method: ', fore='blue') +
                              self._color_(obj._http_method_, fore='cyan') + '\n')
        self._print_essential_(obj)
        self._print_requirements_(obj)
        if hasattr(obj, '__call__'):
           self._print_callable_(obj)

        for attrname in dir(obj):
            if not self._is_internal_(attrname):
                attr = getattr(obj, attrname)
                if isinstance(attr, ResourceMethod):
                    methods.append(attrname)
                elif isinstance(attr, Property) or attr.__class__.__name__ == 'function':
                    properties.append(attrname)
                elif isinstance(attr, API):
                    apis.append(attrname)

        self._buffer_ += '\n'

        if apis:
            self._buffer_ += self._color_('    apis:', fore='blue')
            for api in apis:
                self._buffer_ += '\n\t' + self._color_(api, fore='green')
            self._buffer_ += '\n'
        if methods:
            self._buffer_ += self._color_('    methods:', fore='blue')
            for method in methods:
                self._buffer_ += '\n\t' + self._color_(method, fore='green')
            self._buffer_ += '\n'
        if properties:
            self._buffer_ += self._color_('    properties:', fore='blue')
            for prop in properties:
                self._buffer_ += '\n\t' + self._color_(prop, fore='green')
            self._buffer_ += '\n'

    def _print_callable_(self, obj):
        if not obj._key_ and not obj._expected_value_:
            return
        self._buffer_ += (self._color_('    key: ', fore='blue') +
                          self._color_(obj._key_, fore='cyan'))
        if obj._expected_value_ and type(obj._expected_value_).__name__ == 'SRE_Pattern':
            self._buffer_ += ('\n    ' + self._color_('expected_value: ', fore='blue') +
                              self._color_(obj._expected_value_.pattern, fore='cyan'))
        else:
            self._buffer_ += ('\n    ' + self._color_('expected_value: ', fore='blue') +
                              self._color_(obj._expected_value_, fore='cyan'))
        self._buffer_ += '\n'

    def _print_detail_(self, api, detail):
        elements = Parser._parse_query_string_(detail, mode='lookup')
        self._find_detail_(api, [elements,])

    def _find_detail_(self, root, elements):
        for elem in elements:
            if isinstance(elem, str):
                attr = getattr(root, elem)
                self._print_parameters_(attr)

            elif isinstance(elem, dict):
                for k, v in elem.items():
                    if hasattr(root, k):
                        root = getattr(root, k)
                    if isinstance(v, dict):
                        self._find_detail_(root, [v,])
                        return
                    elif v and hasattr(root, v):
                        root = getattr(root, v)
                    self._print_parameters_(root)

    def _is_internal_(self, attr):
        if attr.startswith('_') and attr.endswith('_'):
            return True
        elif '__' in attr:
            return True
        else:
            return False
