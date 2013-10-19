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
import pprint
import string
from copy import copy, deepcopy
from collections import OrderedDict

from .requirements import Requirements, EnforceRequirements

class Parser(EnforceRequirements):
    """Turns a QueryTree into a URL"""
    def __init__(self):
        self._init_format_tokens_()

    def _parse_(self, tree):
        if self._input_._format_ == 'key_value':
            return str(self._parse_key_value_(tree))[:-1]
        elif self._input_._format_ == 'json':
            return str(self._parse_json_(tree)).replace("'", '"').replace(' ', '')

    def _get_query_elements_(self, string):
        source = api = detail = None
        elems = self._parse_query_string_(string, mode='lookup')[0]
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
        tokensgen = formatter.parse(self._path_)
        self._format_tokens_ = []
        for tokens in tokensgen:
            for t in tokens:
                self._format_tokens_.append(t)

    def _parse_json_(self, tree, has_scope=False, has_prefix=False):
        json = {}
        for k, item in tree.items():
            requirements = self._get_requirements_(item)
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
                if requirements:
                    requirements = self._find_in_requirements_(func, requirements)
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
            if requirements:
                self._enforce_requirements_(k, requirements)
        return json

    def _parse_key_value_(self, tree, has_scope=False, has_prefix=False):
        string = ''
        for k, item in tree.items():
            if type(item).__name__ == 'function':
                item = self._get_state_(k, item)
            item_string = ''
            requirements = self._get_requirements_(item)
            self.submitted = deepcopy(requirements)
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
                    item_string += self._parse_key_value_({func['parameter']: func},
                                                          has_scope, has_prefix)
                elif isinstance(func, tuple) or hasattr(func, '__call__'):
                    if requirements:
                        self._find_in_requirements_(func)

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
                                                     item['mode'], has_scope, has_prefix)
                else:
                    raise Exception('Invalid item found in ' + str(k) + '\'s zfunction list')
            if k in self._format_tokens_:
                self._path_ = self._path_.replace('{'+k+'}', item_string)
            else:
                string += item_string
            if requirements:
                self._enforce_requirements_(k, requirements)
        return string

    def _parse_func_(self, num, fcount, func, syntax, mode,
                    has_scope=False, has_prefix=False):
        if self._input_._format_ == 'key_value':
            string = ''
            bind = syntax['bind']
            chain = syntax['chain']
            if has_scope or has_prefix or 'MV' in mode.flags or 'MK' in mode.flags:
                if 'args' in syntax:
                    if syntax['args'] is None:
                        bind = ''
                    else:
                        bind = syntax['args']
                if 'multi' in syntax:
                    if isinstance(func, tuple):
                        chain = syntax['multi']
                        #syntax = {'bind': bind, 'chain': chain}
                    elif num != fcount-1:
                        chain = syntax['multi']
        elif self._input_._format_ == 'json':
            if isinstance(has_scope, dict):
                json = has_scope
            elif isinstance(has_prefix, dict):
                json = has_prefix
            else:
                json = {}

        if isinstance(func, tuple):
            for n, f in enumerate(func):
                if self._input_._format_ == 'key_value':
                    string += self._parse_func_(n, len(func), f, syntax, mode,
                                               has_scope, has_prefix)
                elif self._input_._format_ == 'json':
                    for k,v in self._parse_func_(n, len(func), f, syntax, mode,
                                                has_scope, has_prefix).items():
                        json[k] = v
        else:
            if func._value_:
                if self._input_._format_ == 'key_value':
                    if 'K' not in mode.flags and 'MK' not in mode.flags:
                        if 'MV' in mode.flags and chain == syntax['multi']:
                            string += '{}{}'.format(quote( str(func._value_) ), chain)
                        else:
                            string += '{}'.format(quote( str(func._value_)) )
                    else:
                        string += '{}{}{}{}'.format(func._key_, bind,
                                                    quote( str(func._value_)), chain)

                elif self._input_._format_ == 'json':
                    json[func._key_] = quote( str(func._value_))
            elif not func._value_ and not has_scope:
                if self._input_._format_ == 'key_value':
                    string += '{}{}'.format(func._key_, chain)
                elif self._input_._format_ == 'json':
                    pass
        if self._input_._format_ == 'key_value':
            return string
        elif self._input_._format_ == 'json':
            return json

    def _get_requirements_(self, item):
        if 'requirements' in item:
            return item['requirements']
        else:
            None

    def _get_parameter_prefix_(self, parameter):
        prefix = None
        if 'prefix' in parameter and parameter['prefix']:
            prefix = parameter['prefix']
            if self._input_._format_ == 'key_value':
                syntax = parameter['syntax']
                prefix = self._format_prefix_(prefix, syntax)
        return prefix

    def _get_func_prefix_(self, func):
        prefix = None
        if func._prefix_:
            prefix = func._prefix_
            if self._input_._format_ == 'key_value':
                syntax = func._syntax_
                prefix = self._format_prefix_(prefix, syntax)
        return prefix

    def _format_prefix_(self, prefix, syntax):
        if isinstance(prefix, dict):
            p = ''
            for k,v in prefix.items():
                p += '{}{}{}{}'.format(k, syntax['bind'],
                                       v, syntax['chain'])
            prefix = p
        elif isinstance(prefix, str):
            prefix = '{}{}'.format(prefix, syntax['bind'])
        return prefix

    def _format_scope_(self, item):
        scope = None
        if 'scope' in item and item['scope']:
            scope = item['scope']
            if self._input_._format_ == 'key_value':
                syntax = item['syntax']
                if isinstance(scope, dict):
                    s = ''
                    for k,v in scope.items():
                        s += '{}{}{}{}'.format(k, syntax['bind'],
                                               v, syntax['chain'])
                    scope = s
        return scope

    def _check_essential_(self, essential, submitted):
        if essential:
            if isinstance(submitted, dict):
                for item, data in submitted.items():
                    if item in essential:
                        essential.remove(item)
                        self._parent_._query_objects_[item] = data
                    if data and 'zfunctions' in data:
                        try:
                            self._check_essential_(essential, data['zfunctions'])
                        except:
                            pass
            elif isinstance(submitted, list):
                for item in submitted:
                    if item.__class__ == 'function' or hasattr(item, '__call__'):
                        name = item._name_
                    else:
                        name = item['parameter']
                        if 'zfunctions' in item:
                            try:
                                self._check_essential_(essential, item['zfunctions'])
                            except:
                                pass
                    if name in essential:
                        essential.remove(name)

                        self._parent_._query_objects_[name] = item

            if essential:
                raise Exception('Missing essential ' + str(essential))

    def _enforce_requirements_(self, parameter, required):
        e = EnforceRequirements(parameter, required, self.submitted)
        e()


    def _find_in_requirements_(self, func):
        name = func.__name__.split('.')[-1]
        for k, v in self.submitted.required.items():
            for lst in v:
                if name in lst:
                    lst.remove(name)

    def _parse_query_string_(self, query, mode='query'):
        """For alternate interfaces"""
        if isinstance(query, dict):
            return query
        if isinstance(query, str):
            strings = re.split('(?<!\\\\):', query)
        new_elements = []
        for num, element in enumerate(strings):
            element = re.sub('\\\\:', ':', element)
            multi_e = self._try_multi_split_(element)
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

    def _try_multi_split_(self, element):
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



