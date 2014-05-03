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
    from urllib2 import quote
elif major == 3:
    from urllib.parse import quote

import re
import json
import pprint
import string
from copy import copy, deepcopy
from collections import OrderedDict

from .requirements import Requirements


class Composer(object):
    """Turns a QueryTree into a URL"""
    def __init__(self, obj):
        self.parent = obj
        self.init_path(self.parent._path_)

    def init_path(self, path):
        formatter = string.Formatter()
        tokensgen = formatter.parse(path)
        self.tokens = []
        for tokens in tokensgen:
            prefix = suffix = None
            tok = _tok = tokens[1]
            if not re.search('^[a-zA-Z0-9]', tok):
                prefix = tok[0]
                tok = tok[1:]
            if not re.search('[a-zA-Z0-9]$', tok):
                suffix = tok[-1]
                tok = tok[:-1]                    
            token = tok
            path = path.replace('{'+_tok+'}', 
                                '{'+token+'}')
            token_tuple = (prefix, token, suffix)
            self.tokens.append(token_tuple)
        self.path = path

    def get_clean_path_string(self):
        """we remove any tokens from the path that are left over after
        traversing the query tree, meaning they were not involved in this 
        particular query
        """
        path = self.path
        if self.tokens:
            for token_tuple in self.tokens:
                token = token_tuple[1]
                if token and token != '0':
                    path = path.replace('{'+token+'}', '')
        return path

    def get_formatted_path(self, strings_dict):        
        path = self.get_clean_path_string()
        for k,v in strings_dict.items():
            strings_dict[k] = ''.join(v)
        main = strings_dict['0']
        del strings_dict['0']
        if strings_dict:
            path = path.format(main, **strings_dict)
        else:
            path = path.format(main)    
        while not re.search('[a-zA-Z0-9}]$', path):
            path = path[:-1]
        return path

    def compose(self, tree):
        self.requirements = Requirements()
        for r in self.parent._raise_requirements_():
            if r and r.required:
                self.requirements.add_requirements(r)
        self.submitted = \
            self.parent._root_getattr_('_submitted_')[self.parent._name_]
        if self.parent._input_format_ == 'key_value':
            strings = self.parse_key_value(tree)
            path = self.get_formatted_path(strings)
        elif self.parent._input_format_ == 'json':
            json_string = str(json.dumps(self.parse_json(tree))).replace(' ', '')
            path = self.get_formatted_path({'0': json_string})
        self.enforce_requirements()        
        return path

    def retrieve_requirements(self, item):
        if 'requirements' in item and item['requirements']:
            return item['requirements']
        else:
            return Requirements()

    def enforce_requirements(self):
        submitted = self.find_in_requirements()
        self.requirements.enforce_requirements(submitted.required)

    def find_in_requirements(self):
        submitted = deepcopy(self.requirements)
        for k,v in submitted.required.items():
            for rset in v:
                for item in self.submitted:
                    if item._name_ in rset:
                        rset.remove(item._name_)
        return submitted

    def parse_json(self, tree, has_scope=False, has_prefix=False):
        json = {}
        for k, item in tree.items():

            requirements = self.retrieve_requirements(item)
            self.requirements.add_requirements(requirements)

            scope = self.get_scope_string(item)
            if scope:
                if isinstance(scope, dict):
                    for k,v in scope.items():
                        json[k] = v
                        has_scope = True
                else:
                    json[scope] = {}
                    has_scope = json[scope]

            prefix = self.get_prefix_string(item)
            if prefix:
                if isinstance(prefix, dict):
                    for k,v in prefix.items():
                        json[k] = v
                        has_prefix = True
                else:
                    json[prefix] = {}
                    has_prefix = json[prefix]

            for num, func in enumerate(item['zfunctions']):
                fcount = len(item['zfunctions'])
                if isinstance(func, dict):
                    for k,v in self.parse_json({func['parameter']: func},
                                               has_scope, has_prefix).items():
                        json[k] = v
                elif isinstance(func, tuple) or hasattr(func, '__call__'):
                    j = self.parse_func(num, fcount, func, item['syntax'],
                                        item['mode'], has_scope, has_prefix)
                    if not isinstance(has_prefix, dict):
                        for k,v in j.items():
                            json[k] = v
                else:
                    raise Exception('Invalid item found in ' +
                                    str(k) + '\'s zfunction list')
        return json

    def parse_key_value(self, tree, has_scope=False, has_prefix=False):
        strings = {'0': []}
        for k, item in tree.items():

            item_string = ''
            requirements = self.retrieve_requirements(item)
            self.requirements.add_requirements(requirements)

            scope = self.get_scope_string(item)
            if scope:
                item_string += scope
                has_scope = True

            parent_prefix = self.get_prefix_string(item)
            if parent_prefix:
                item_string += parent_prefix
                has_prefix = True

            for num, func in enumerate(item['zfunctions']):
                fcount = len(item['zfunctions'])
                if isinstance(func, dict):
                    for t, v in self.parse_key_value({func['parameter']: func},
                                                     has_scope, has_prefix).items():
                        if t != '0':
                            if t not in strings:
                                strings[t] = v
                            else:
                                strings[t].extend(v)
                        else:
                            item_string += ''.join(v)
                elif isinstance(func, tuple) or hasattr(func, '__call__'):
                    #hack
                    if isinstance(func, tuple):
                        f = func[0]
                    else:
                        f = func
                    
                    func_prefix = self.get_prefix_string(f)
                    if func_prefix and func_prefix != parent_prefix:
                        item_string += func_prefix
                        has_prefix = True

                    syntax = f._syntax_

                    item_string += self.parse_func(num, fcount, func, syntax,
                                                   item['mode'], has_scope,
                                                   has_prefix)
                    
                else:
                    raise Exception('Invalid item found in ' + str(k) +
                                    '\'s zfunction list')
            rm_token = None
            if item_string:
                for tnum, token_tuple in enumerate(self.tokens):
                    prefix, token, suffix = token_tuple
                    if k == token:
                        if prefix:
                            item_string = prefix + item_string
                        if suffix:
                            item_string += suffix
                        if k not in strings:
                            strings[k] = [item_string, ]
                        else:
                            strings[k].append(item_string)
                        rm_token = tnum
                        break
                if not rm_token and k not in strings:
                    strings['0'].append(item_string)
                if rm_token is not None:
                    del self.tokens[rm_token]
        return strings

    def parse_func(self, num, fcount, func, syntax, mode,
                   has_scope=False, has_prefix=False):
        if self.parent._input_format_ == 'key_value':
            string = ''
            bind = syntax['+bind']
            chain = syntax['+chain']
            if has_scope or has_prefix or 'MV' in mode.flags or 'MK' in mode.flags:
                if '+args' in syntax:
                    if syntax['+args'] is None:
                        bind = ''
                    else:
                        bind = syntax['+args']
                if '+multi' in syntax:
                    if isinstance(func, tuple):
                        chain = syntax['+multi']
                        #syntax = {'+bind': bind, '+chain': chain}
                    elif num != fcount-1:
                        chain = syntax['+multi']

        elif self.parent._input_format_ == 'json':
            if isinstance(has_scope, dict):
                json = has_scope
            elif isinstance(has_prefix, dict):
                json = has_prefix
            else:
                json = {}

        if isinstance(func, tuple):
            for n, f in enumerate(func):
                self.submitted.add(f)
                if self.parent._input_format_ == 'key_value':
                    string += self.parse_func(n, len(func), f, syntax, mode,
                                              has_scope, has_prefix)
                elif self.parent._input_format_ == 'json':
                    for k,v in self.parse_func(n, len(func), f, syntax, mode,
                                               has_scope, has_prefix).items():
                        json[k] = str(v)
        else:
            self.submitted.add(func)
            if func._value_:
                if self.parent._input_format_ == 'key_value':
                    if 'K' not in mode.flags and 'MK' not in mode.flags:
                        if 'MV' in mode.flags and chain == syntax['+multi']:
                            string += '{}{}'.format(quote( str(func._value_) ), chain)
                        else:
                            string += '{}'.format(quote( str(func._value_)) )
                    else:
                        string += '{}{}{}{}'.format(func._key_, bind,
                                                    quote( str(func._value_)), chain)
                elif self.parent._input_format_ == 'json':
                    if func._value_ in ( True, False, None):
                        json[func._key_] = func._value_
                    else:
                        json[func._key_] = str(func._value_)

            elif not func._value_ and not has_scope:
                if self.parent._input_format_ == 'key_value':
                    string += '{}{}'.format(func._key_, chain)
                elif self.parent._input_format_ == 'json':
                    json[func._key_] = func._value_

        if self.parent._input_format_ == 'key_value':
            return string
        elif self.parent._input_format_ == 'json':
            return json

    def get_prefix_string(self, item):
        prefix = None
        if isinstance(item, dict):
            if 'prefix' in item and item['prefix']:
                prefix = item['prefix']
            if self.parent._input_format_ == 'key_value':
                syntax = item['syntax']
        elif hasattr(item, '_prefix_'):
            prefix = item._prefix_
            if self.parent._input_format_ == 'key_value':
                syntax = item._syntax_
        if prefix and self.parent._input_format_ == 'key_value':
            prefix = self.format_prefix(prefix, syntax)
        return prefix

    def format_prefix(self, prefix, syntax):
        if isinstance(prefix, dict):
            p = ''
            for k,v in prefix.items():
                p += '{}{}{}{}'.format(k, syntax['+bind'],
                                       v, syntax['+chain'])
            prefix = p
        elif isinstance(prefix, str):
            prefix = '{}{}'.format(prefix, syntax['+bind'])
        return prefix

    def get_scope_string(self, item):
        scope = None
        if 'scope' in item and item['scope']:
            scope = item['scope']
            if self.parent._input_format_ == 'key_value':
                syntax = item['syntax']
                if isinstance(scope, dict):
                    s = ''
                    for k,v in scope.items():
                        s += '{}{}{}{}'.format(k, syntax['+bind'],
                                               v, syntax['+chain'])
                    scope = s
        return scope




