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
import mimetypes

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
            strings_dict[k] = ''
            for s in v:
                strings_dict[k] += s
        main = strings_dict['0']
        del strings_dict['0']
        if strings_dict:
            path = path.format(main, **strings_dict)
        else:
            path = path.format(main)
        if re.search('[a-zA-Z0-9}]', path):
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
            header_dict, query_dict, body_list, strings = self.compose_key_value(tree)
            for s in strings:
                query_dict['0'].append(s)
            path = self.get_formatted_path(query_dict)
        elif self.parent._input_format_ == 'json':
            header_dict, query_dict, body_list = self.compose_json(tree)
            json_string = str(json.dumps(query_dict)).replace(' ', '')
            path = self.get_formatted_path({'0': json_string})
        self.enforce_requirements()
        return header_dict, path, body_list

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

    def compose_json(self, tree, header_dict=None, json=None,
                     body_list=None, fcount=None, depth=-1):
        if header_dict is None:
            header_dict = {}
        if json is None:
            json = {}
        if body_list is None:
            body_list = []
        for key, item in tree.items():
            requirements = self.retrieve_requirements(item)
            self.requirements.add_requirements(requirements)

            scope = self.get_scope_string(item)
            if scope:
                if isinstance(scope, dict):
                    for k,v in scope.items():
                        json[k] = v
                else:
                    json[scope] = {}

            prefix = self.get_prefix_string(item)
            if prefix:
                if isinstance(prefix, dict):
                    for k,v in prefix.items():
                        json[k] = v
                else:
                    json[prefix] = {}
                    
            if depth == -1:
                fcount = self.get_function_count(item['zfunctions'])
                
            for num, func in enumerate(item['zfunctions']):
                fcount = len(item['zfunctions'])
                if isinstance(func, dict):
                    depth += 1
                    h,j,b = self.compose_json({func['parameter']: func},
                                                    header_dict, None, body_list,
                                                    fcount, depth)
                    if prefix and not isinstance(prefix, dict):
                        for k,v in j.items():
                            json[prefix][k] = v
                    elif scope and not isinstance(scope, dict):
                        for k,v in j.items():
                            json[scope][k] = v
                    else:
                        for k,v in j.items():
                            json[k] = v
                    depth -= 1
                elif isinstance(func, tuple) or hasattr(func, '__call__'):
                    if item['mode'].string == 'header':
                        self.add_header_string(func, header_dict)
                    elif 'body' in item['mode'].flags:
                        self.add_body_string(func, body_list, header_dict)
                    else:
                        j = self.compose_func(fcount, func)
                        for k,v in j.items():
                            json[k] = v
                else:
                    raise Exception('Invalid item found in ' +
                                    str(k) + '\'s zfunction list')
        return header_dict, json, body_list

    def get_function_count(self, functions, fcount=None, depth=0):
        if fcount is None:
            fcount = {}
        for num, f in enumerate(functions):
            if hasattr(f, '__call__'):
                obj = f
                while True:
                    if hasattr(obj, '_parent_'):
                        if obj._parent_._name_ in fcount:
                            fcount[obj._parent_._name_]['num'] += 1
                            fcount[obj._parent_._name_]['funcs'].append(obj)
                        else:
                            fcount[obj._parent_._name_] = {}
                            fcount[obj._parent_._name_]['num'] = 1
                            fcount[obj._parent_._name_]['funcs'] = [obj,]
                            fcount[obj._parent_._name_]['depth'] = depth
                        obj = obj._parent_
                        depth -= 1
                    else:
                        break                    
            if isinstance(f, dict):
                depth += 1
                self.get_function_count(f['zfunctions'], fcount, depth)
                depth -= 1                        
        return fcount

    def compose_key_value(self, tree, header_dict=None, 
                          query_dict=None, body_list=None, 
                          strings=None, fcounts=None, depth=-1):
        strings = []
        if header_dict is None:
            header_dict = {}
        if query_dict is None:
            query_dict = {'0': []}
        if body_list is None:
            body_list = []
            
        for k, item in tree.items():
            item_string = ''
            requirements = self.retrieve_requirements(item)
            self.requirements.add_requirements(requirements)
  
            scope = self.get_scope_string(item)
            prefix = self.get_prefix_string(item)
            if scope: 
                item_string += scope
            if prefix:
                item_string += prefix
  
            if item_string:
                if not self.add_item_string(k, item_string, query_dict):
                    strings.append(item_string)

            if depth == -1:
                fcounts = self.get_function_count(item['zfunctions'])                
                
            for func in item['zfunctions']:
                if isinstance(func, dict):
                                            
                    depth += 1                    
                    h,q,b, strs, = self.compose_key_value({func['parameter']: func},
                                                     header_dict, query_dict, body_list, 
                                                     strings, fcounts, depth)
                    depth -= 1                                              
                    for n, s in enumerate(strs):
                        strings.append(s)
                    item_string = ''
                                                    
                elif isinstance(func, tuple) or hasattr(func, '__call__'):                    
                    
                    #hack
                    if isinstance(func, tuple):
                        f = func[0]
                        fcount = len(func)
                    else:
                        f = func
                        main_node = f._get_main_node_()
                        if main_node._name_ in fcounts:
                            fcount = fcounts[main_node._name_]['num']
                        else:
                            #hack
                            fcount = 1

                    syntax = f._syntax_
                    if item['mode'].string == 'header':
                        self.add_header_string(func, header_dict)
                    elif 'body' in item['mode'].flags:
                        self.add_body_string(func, body_list, header_dict)
                    else:
                        item_string += self.compose_func(fcount, func)
                        try:
                            fcounts[main_node._name_]['num'] -= 1
                        except:
                            pass
                else:
                    raise Exception('Invalid item found in ' + str(k) +
                                    '\'s zfunction list')
                if item_string:
                    if not self.add_item_string(f._name_, item_string, query_dict):
                        strings.append(item_string)
        return header_dict, query_dict, body_list, strings

    def compose_func(self, fcount, func):
        pmode = self.get_parent_mode_list(func)
        syntax = self.get_parent_syntax_list(func)
        if self.parent._input_format_ == 'key_value':
            string = ''
            mode = pmode[0]            
            bind = syntax['+bind']
            chain = syntax['+chain']
            if self.apply_multi(mode, pmode):
                if '+args' in syntax:
                    if syntax['+args'] is None:
                        bind = ''
                    else:
                        bind = syntax['+args']
                if '+multi' in syntax:
                    if isinstance(func, tuple) or fcount-1 > 0:
                        chain = syntax['+multi']
                    else:
                        chain = syntax['+chain']
            else:
                if '+args' in syntax:
                    if syntax['+args'] is None:
                        bind = ''
                    else:
                        bind = syntax['+args']
                
        elif self.parent._input_format_ == 'json':
            json = {}

        if isinstance(func, tuple):
            for n, f in enumerate(func):
                self.submitted.add(f)
                if self.parent._input_format_ == 'key_value':
                    string += self.compose_func(len(func), f)
                elif self.parent._input_format_ == 'json':
                    for k,v in self.compose_func(len(func), f).items():
                        json[k] = str(v)
        else:
            self.submitted.add(func)
            if func._value_:
                if self.parent._input_format_ == 'key_value':
                    
                    if self.parent._http_method_ == 'GET':
                        value = quote(str(func._value_))
                    else:
                        value = str(func._value_)
                    
                    if 'K' not in mode.flags and 'MK' not in mode.flags:
                        if 'MV' in mode.flags and chain == syntax['+multi']:
                            string += '{}{}'.format(value, chain)
                        else:
                            string += '{}'.format(value)
                    else:
                        string += '{}{}{}{}'.format(func._key_, bind,
                                                    value, chain)
                elif self.parent._input_format_ == 'json':
                    if func._value_ in ( True, False, None):
                        json[func._key_] = func._value_
                    else:
                        json[func._key_] = str(func._value_)

            elif not func._value_ :
                if self.parent._input_format_ == 'key_value':
                    string += '{}{}'.format(func._key_, chain)
                elif self.parent._input_format_ == 'json':
                    json[func._key_] = func._value_
        
        if self.parent._input_format_ == 'key_value':
            return string
        elif self.parent._input_format_ == 'json':
            return json
                
    def add_body_string(self, func, body_list, header_dict):
        if 'file' in func._mode_.flags:
            filename = func._value_
            if os.path.exists(filename):
                value = open(filename, 'rb').read()
                self.path = self.path + '/' + filename.split('/')[-1]
                header_dict['Content-Type'] = mimetypes.guess_type(filename)[0]
            else:
                raise OSError("No such file '"+filename+"'")
        else:
            value = func._key_ + ': ' + func._value_
            header_dict['Content-Type'] = 'text/plain'
        body_list.append(value)
        header_dict['Content-Length'] = sum([len(i) for i in body_list])
           
    def add_header_string(self, func, header_dict):
        key = func._key_
        value = func._value_
        if key not in header_dict:
            header_dict[key] = [value, ]
        else:
            header_dict[key].append(value)
    
    def add_item_string(self, key, item_string, query_dict):
        rm_token = None
        for tnum, token_tuple in enumerate(self.tokens):
            prefix, token, suffix = token_tuple
            if key == token:
                if prefix is not None:
                    item_string = prefix + item_string
                if suffix is not None:
                    item_string += suffix
                if key not in query_dict:
                    query_dict[key] = [item_string, ]
                else:
                    query_dict[key].append(item_string)
                rm_token = tnum
                break
        if rm_token is not None:
            del self.tokens[rm_token]
            return True
        else:
            return False
        
    def get_parent_mode_list(self, func, modes=None):
        if hasattr(func, '__iter__'):
            func = func[0]
        if not modes:
            modes = [func._mode_]
        if func._parent_._is_root_:
            modes.append(func._parent_._mode_)
            return modes
        else:
            modes.append(func._parent_._mode_)
            return self.get_parent_mode_list(func._parent_, modes)
    
    def get_parent_syntax_list(self, func, syntax=None):
        if hasattr(func, '__iter__'):
            func = func[0]
        if not syntax:
            syntax = func._syntax_
        if hasattr(func, '__iter__'):
            func = func[0]
        syntax = self.inherit_parent_syntax(syntax, func._parent_._syntax_)
        if func._parent_._is_root_:
            return syntax
        else:
            return self.get_parent_syntax_list(func._parent_, syntax)

    def inherit_parent_syntax(self, syntax, parent_syntax):
        for c in ('+bind', '+chain', '+multi', '+args'):
            if c not in syntax and c in parent_syntax:
                syntax[c] = parent_syntax[c]
            elif c in syntax and c in parent_syntax:
                if c == '+chain' and parent_syntax[c] != '&':
                    syntax[c] = parent_syntax[c]
                elif c == '+bind' and parent_syntax[c] != '=':
                    syntax[c] = parent_syntax[c]
                elif c in ('+multi', '+args'):
                    syntax[c] = parent_syntax[c]
        return syntax

    def apply_multi(self, mode, pmode):
        if 'V' == mode.string:
            return False
        else:
            for f in ('MV', 'MK'):
                if f in mode.flags:
                    return True
            for mode in pmode:
                for f in ('MV', 'MK'):
                    if f in mode.flags:
                        return True
        return False

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




