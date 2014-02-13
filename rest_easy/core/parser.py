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

from .requirements import Requirements, EnforceRequirements


class Parser(EnforceRequirements):
    """Turns a QueryTree into a URL"""
    def __init__(self, obj):
        self.parent = obj
        self.p_name = obj._name_
        self.path = self.parent._path_        
        self._init_format_tokens_()

    def _parse_(self, tree):
        self._requirements_ = Requirements()
        for r in self.parent._raise_requirements_():
            if r and r.required:
                self._requirements_.add_requirements(r)
        self._submitted_ = self.parent._root_getattr_('_submitted_')[self.p_name]
        if self.parent._input_format_ == 'key_value':
            strings = self._parse_key_value_(tree)
            path = self._format_with_path_(strings)
        elif self.parent._input_format_ == 'json':
            path = str(json.dumps(self._parse_json_(tree))).replace(' ', '')
        self._enforce_requirements_()        
        return path

    @staticmethod
    def _get_query_elements_(string):
        source = api = detail = None
        elems = Parser._parse_query_string_(string, mode='lookup')[0]
        for k, v in elems.items():
            source = k
            if isinstance(v, dict):
                for i, j in v.items():
                    api = i
                    detail = j
                    break
            else:
                api = v
                detail = None
        return source, api, detail

    def _init_format_tokens_(self):
        formatter = string.Formatter()
        tokensgen = formatter.parse(self.parent._path_)
        self._tokens_ = []
        for tokens in tokensgen:
            if tokens[1] != '0':
                if not re.search('[a-zA-Z0-9]$', tokens[1]):
                    token = tokens[1][:-1]
                    chain = tokens[1][-1]
                    self.path = self.path.replace('{'+tokens[1]+'}', 
                                                  '{'+token+'}')
                else:
                    token = tokens[1]
                    chain = None
                token_tuple = (token, chain)
                self._tokens_.append(token_tuple)

    def _get_clean_path_string_(self):
        path = self.path
        if self._tokens_:
            for token_tuple in self._tokens_:
                token, chain = token_tuple
                if token and token != '0':
                    path = path.replace('{'+token+'}', '')
        return path

    def _format_with_path_(self, strings_dict):        
        path = self._get_clean_path_string_()
        for k,v in strings_dict.items():
            strings_dict[k] = ''.join(v)
        main = strings_dict['0']
        del strings_dict['0']
        if strings_dict:
            path = path.format(main, **strings_dict)
        else:
            path = path.format(main)    
        while not re.search('[a-zA-Z0-9]$', path):
            path = path[:-1]
        return path

    def _parse_json_(self, tree, has_scope=False, has_prefix=False):
        json = {}
        for k, item in tree.items():
            requirements = self._retrieve_requirements_(item)
            self._requirements_.add_requirements(requirements)
            scope = self._format_scope_(item)
            if scope:
                if isinstance(scope, dict):
                    for k,v in scope.items():
                        json[k] = v
                        has_scope = True
                else:
                    json[scope] = {}
                    has_scope = json[scope]

            prefix = self._get_parameter_prefix_(item)
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
                    for k,v in self._parse_json_({func['parameter']: func},
                                                 has_scope, has_prefix).items():
                        json[k] = v
                elif isinstance(func, tuple) or hasattr(func, '__call__'):
                    j = self._parse_func_(num, fcount, func, item['syntax'],
                                          item['mode'], has_scope, has_prefix)
                    if not isinstance(has_prefix, dict):
                        for k,v in j.items():
                            json[k] = v
                else:
                    raise Exception('Invalid item found in ' +
                                    str(k) + '\'s zfunction list')
        return json

    def _parse_key_value_(self, tree, has_scope=False, has_prefix=False):
        strings = {'0': []}
        for k, item in tree.items():
            if type(item).__name__ == 'function':
                #might be able to remove this, and this the parent reference
                item = self.parent._get_state_(k, item)
            item_string = ''
            requirements = self._retrieve_requirements_(item)
            self._requirements_.add_requirements(requirements)
            scope = self._format_scope_(item)
            if scope:
                item_string += scope
                has_scope = True
            parent_prefix = self._get_parameter_prefix_(item)
            if parent_prefix:
                item_string += parent_prefix
                has_prefix = True
            for num, func in enumerate(item['zfunctions']):
                fcount = len(item['zfunctions'])
                if isinstance(func, dict):
                    for t, v in self._parse_key_value_({func['parameter']: func},
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

                    func_prefix = self._get_func_prefix_(f)
                    if func_prefix and func_prefix != parent_prefix:
                        item_string += func_prefix
                        has_prefix = True

                    syntax = f._syntax_

                    item_string += self._parse_func_(num, fcount, func, syntax,
                                                     item['mode'], has_scope,
                                                     has_prefix)
                else:
                    raise Exception('Invalid item found in ' + str(k) +
                                    '\'s zfunction list')
            rm_token = None
            if item_string:
                for tnum, token_tuple in enumerate(self._tokens_):
                    token, chain = token_tuple
                    if k == token:
                        if chain:
                            item_string += chain
                        if k not in strings:
                            strings[k] = [item_string, ]
                        else:
                            strings[k].append(item_string)
                        rm_token = tnum
                        break
                if not rm_token and k not in strings:
                    strings['0'].append(item_string)
                if rm_token is not None:
                    del self._tokens_[rm_token]
        return strings

    def _parse_func_(self, num, fcount, func, syntax, mode,
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
                self._submitted_.add(f)
                if self.parent._input_format_ == 'key_value':
                    string += self._parse_func_(n, len(func), f, syntax, mode,
                                               has_scope, has_prefix)
                elif self.parent._input_format_ == 'json':
                    for k,v in self._parse_func_(n, len(func), f, syntax, mode,
                                                has_scope, has_prefix).items():
                        json[k] = str(v)
        else:
            self._submitted_.add(func)
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

    def _retrieve_requirements_(self, item):
        if 'requirements' in item and item['requirements']:
            return item['requirements']
        else:
            return Requirements()

    def _get_parameter_prefix_(self, parameter):
        prefix = None
        if 'prefix' in parameter and parameter['prefix']:
            prefix = parameter['prefix']
            if self.parent._input_format_ == 'key_value':
                syntax = parameter['syntax']
                prefix = self._format_prefix_(prefix, syntax)
        return prefix

    def _get_func_prefix_(self, func):
        prefix = None
        if func._prefix_:
            prefix = func._prefix_
            if self.parent._input_format_ == 'key_value':
                syntax = func._syntax_
                prefix = self._format_prefix_(prefix, syntax)
        return prefix

    def _format_prefix_(self, prefix, syntax):
        if isinstance(prefix, dict):
            p = ''
            for k,v in prefix.items():
                p += '{}{}{}{}'.format(k, syntax['+bind'],
                                       v, syntax['+chain'])
            prefix = p
        elif isinstance(prefix, str):
            prefix = '{}{}'.format(prefix, syntax['+bind'])
        return prefix

    def _format_scope_(self, item):
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

    def _enforce_requirements_(self):
        submitted = self._find_in_requirements_()
        e = EnforceRequirements(self._requirements_, submitted)
        e()

    def _find_in_requirements_(self):
        submitted = deepcopy(self._requirements_)
        for k,v in submitted.required.items():
            for rset in v:
                for item in self._submitted_:
                    if item._name_ in rset:
                        rset.remove(item._name_)
        return submitted

    @staticmethod
    def _parse_query_string_(query, mode='query'):
        """For alternate interfaces"""
        if isinstance(query, dict):
            return query
        if isinstance(query, str):
            strings = re.split('(?<!\\\\):', query)
        new_elements = []
        for num, element in enumerate(strings):
            element = re.sub('\\\\:', ':', element)
            multi_e = Parser._try_multi_split_(element)
            if multi_e:
                 new_elements.append(multi_e)
            else:
                element = element.lstrip(' ').rstrip(' ').split('->')
                if mode == 'lookup':
                    if len(element)%2!=0:
                        element.append('')
                subelement = {}
                last = None
                for n, e in enumerate(element):
                    el = re.split('(?<!\\\\)\|', e)
                    if len(el) == 1:
                        el = el[0]
                    if len(element) == 2:
                        subelement[e] = element[n+1]
                        break
                    if last is None:
                        subelement[el] = {}
                        last = subelement[el]
                    else:
                        if n < len(element)-2:
                            last[el] = {}
                            last = last[el]
                        elif n == len(element)-2:
                            last[el] = None
                        else:
                            for k in last.keys():
                                last[k] = el
                new_elements.append(subelement)
        return new_elements

    @staticmethod
    def _try_multi_split_(element):
        """For alternate interfaces"""
        elements = re.split('(?<!\\\\)\|', element)
        if elements == [element,]:
            return False
        el = []
        for e in elements:
            items = e.lstrip(' ').rstrip(' ').split('->')
            el.append(items)
        for e in el:
            if len(e) == 1:
                return False
        e_dict = {}
        for elem in el:
            root = elem.pop(0)
            if root not in e_dict:
                e_dict[root] = {'multikey': []}
                #TODO: allow arbitrarily deep nesting of
                # multikey parameters
            k, v = elem
            e_dict[root]['multikey'].append( (k,v) )
        return e_dict



