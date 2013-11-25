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

import re
import pprint
from copy import copy, deepcopy
from collections import OrderedDict
import types

from .attributes import BaseAttributes, Aspects, Callable
from .query import HTTPMethods, QueryTree
from .requirements import Requirements


class Node(Callable, QueryTree):
    """ """
    _reserved_ = ('+this', '+mode', '+scope', '+prefix',
                  '+requirements', '+children', '+key',
                  '+expected_value', '+doc')

    def __init__(self, **kwargs):
        self._has_scope_ = None
        if 'is_root' in kwargs and kwargs['is_root']:
            self._is_root_ = True
            self._init_query_structs_()
        else:
            self._is_root_ = False

    def _init_query_structs_(self):
        self._current_tree_ = {}
        self._query_trees_ = {}#[{}]
        self._global_tree_ = {}
        self._query_requirements_ = {}#[Requirements()]
        self._submitted_ = {}#set()
        self._active_resource_methods_ = set()

    def _add_query_struct_entry_(self, r_method):
        if self._is_root_:
            if not r_method in self._current_tree_:
                self._current_tree_[r_method] = 0
                self._query_trees_[r_method] = [{}]
                self._query_requirements_[r_method] = [Requirements()]
                self._submitted_[r_method] = set()
        else:
            self._parent_._add_query_struct_entry_(r_method)

    def help(self, path=''):
        path = self._name_ + '->' + path
        self._parent_.help(path)

    def new_query(self, r_method=None):
        if self._is_root_:
            self._current_tree_[r_method] += 1
            self._query_trees_[r_method].append(deepcopy(self._global_tree_))
            self._query_requirements_[r_method].append(Requirements())
        else:
            if isinstance(self, ResourceMethod):
                r_method = self._name_
            self._parent_.new_query(r_method)

    def reset_query(self):
        if self._is_root_:
            self._current_tree_ = {}
            self._query_trees_ = {}
            self._query_requirements_ = {}
            #for item in self._submitted_:
            #    item._value_ = None
            self._submitted_ = {}
            self._active_resource_methods_ = set()
        else:
            self._parent_.reset_query()

    def _add_active_resource_method_(self, method=None):
        if self._is_root_:
            if method:
                self._active_resource_methods_.add(method)
                return method._name_
            else:
                return None
        else:
            if not method:
                if isinstance(self, ResourceMethod):
                    method = self
            return self._parent_._add_active_resource_method_(method)

    def _super_getattr_(self, keyword):
        if hasattr(self, keyword):
            return getattr(self, keyword)
        elif not hasattr(self._parent_, '_super_getattr_'):
            if hasattr(self._parent_, keyword):
                return getattr(self._parent_, keyword)
            else:
                raise AttributeError('No such attribute "'+keyword+'"')
        else:
            return self._parent_._super_getattr_(keyword)

    def _root_getattr_(self, keyword):
        if self._is_root_ and hasattr(self, keyword):
            return getattr(self, keyword)
        elif not hasattr(self._parent_, '_root_getattr_'):
            raise AttributeError('No such attribute "'+keyword+'"')
        else:
            return self._parent_._root_getattr_(keyword)

    def _raise_requirements_(self, requirements=None):
        if not requirements:
            requirements = []
        requirements.append(self._requirements_)
        if self._is_root_:
            return requirements
        else:
            return self._parent_._raise_requirements_(requirements)

    def _add_child_(self, keyword, data=None):
        if 'MK' in self._mode_.flags:
            if not hasattr(self, 'multikey'):
                self._create_multikey_function_()

        if '+this' in data:
            for attr in ( '+prefix', '+syntax', '+scope',
                          '+requirements', '+mode'):
                if attr in data and attr not in data['+this']:
                    data['+this'][attr] = data[attr]
            if '+syntax' not in data['+this'] and hasattr(self, '_syntax_'):
                data['+this']['+syntax'] = self._syntax_
            pattrs = Aspects(data['+this'])
            self._set_method_(keyword, None, pattrs)
            del data['+this']

        if '+key' not in data and '+expected_value' not in data:
            if not '+mode' in data:
                data['+mode'] = self._parse_mode_(None)
            if '+syntax' not in data and hasattr(self, '_syntax_'):
                data['+syntax'] = self._syntax_

            if '+http_method' in data:
                param = ResourceMethod(parent=self,
                                       name=keyword,
                                       data_dict=data)
            else:
                param = Property(parent=self,
                                 name=keyword,
                                 data_dict=data)
            if '+children' in data:
                for child_kw, child_data in data['+children'].items():
                    if child_kw in Node._reserved_:
                        continue
                    param._add_child_(child_kw, deepcopy(child_data))
                    if hasattr(self, keyword):
                        parent = getattr(self, keyword)
                        child = getattr(param, child_kw)
                        setattr(parent, child_kw, child)
                if not hasattr(self, keyword):
                    setattr(self, keyword, param)
            return

        if '+syntax' not in data and hasattr(self, '_syntax_'):
            data['+syntax'] = self._syntax_
        pattrs = Aspects(data)
        self._set_method_(keyword, None, pattrs)

    def _set_method_(self, parent_kw, child_kw, pattrs):
        """Set child function as attribute"""
        if not child_kw:
            child_kw = parent_kw
            method = self._get_method_(parent_kw, child_kw, pattrs)
            setattr(self, child_kw, method)
        else:
            if not hasattr(self, parent_kw):
                child_instance = self._get_instance_(parent_kw)
                setattr(self, parent_kw, child_instance)
            else:
                child_instance = getattr(self, parent_kw)
            method = self._get_method_(parent_kw, child_kw, pattrs)
            setattr(child_instance, child_kw, method)

    def _get_method_(self, parent_kw, child_kw, pattrs):
        """Create child function"""
        def function(*args):
            value = subproperty = None
            if len(args) == 1:
                value = args[0]
            elif len(args) == 2:
                subproperty, value = args

            if subproperty and hasattr( getattr(self, child_kw), subproperty ):
                child = getattr(self, child_kw)
                subp = getattr(child, subproperty)
                subp(value)
                return

            if (value is None and
                (( not isinstance(pattrs._expected_value_, tuple) and
                  pattrs._expected_value_ is not type(None)) or
                  ( isinstance(pattrs._expected_value_, tuple) and
                    type(None) not in pattrs._expected_value_))):
                return getattr(function, '_value_')
            else:
                value = self._validate_input_(child_kw, value, pattrs._expected_value_)

            """
            if hasattr(function, '_value_'):
                print ('try', value)
                if function._value_ is not None:
                    print ('setting', value)
                    f = self._get_method_(parent_kw, child_kw, pattrs)
                    f(value)
                    return
                    """
            setattr(function, '_value_', value)

            self._set_scope_()
            if parent_kw != 'multikey':
                state = self._get_state_(parent_kw, function)
                if self._is_root_:
                    make_global = True
                    r_method = None
                else:
                    make_global = False
                    r_method = self._add_active_resource_method_()
                    self._add_query_struct_entry_(r_method)
                self._add_to_query_tree_(r_method, parent_kw, child_kw,
                                         function, {parent_kw: state},
                                         None, make_global)

        function.__name__ = 'parameter.Property'
        function.__doc__ = pattrs.__doc__
        function._parent_ = self
        function._name_ = parent_kw
        function._prefix_ = pattrs._prefix_
        function._syntax_ = pattrs._syntax_
        function._scope_ = pattrs._scope_
        function._requirements_ = pattrs._requirements_
        function._mode_ = pattrs._mode_
        function._value_ = None
        function._key_ = pattrs._key_
        function._expected_value_ = pattrs._expected_value_
        setattr(function, 'help', types.MethodType(Node.help, function))

        return function

    def _validate_input_(self, keyword, value, expected_value):
        """Check input value against expected value"""
        if type(expected_value).__name__ == 'SRE_Pattern':
            if not expected_value.match( str(value) ):
                raise TypeError('"' + keyword + '" matches pattern "'
                                + expected_value.pattern + '", "'
                                + str(value) + '" given.' )
        elif isinstance(expected_value, dict):
            for k,v in expected_value.items():
                self._validate_input_(keyword, value, v)
                value = str(k) + str(value)
        elif isinstance(expected_value, tuple):
            exceptions = set()
            match = False
            for ev in expected_value:
                if match == True:
                    break
                if isinstance(ev, list):
                    if not isinstance(value, list):
                        exceptions.add( str(type(value)) )
                    else:
                        if not value:
                            exceptions.add( str(type(value)) )
                        for v in value:
                            if not isinstance(v, tuple(ev)):
                                exceptions.add( str(type(v)) )
                            else:
                                exceptions = []
                                match = True
                else:
                    if not isinstance(value, ev):
                        exceptions.add( str(type(value)) )
                    else:
                        exceptions = []
                        match = True
            if exceptions:
                raise TypeError('"' + keyword + '" expects ' +
                                '"' + str(expected_value) + '", ' +
                                ', '.join(exceptions) + ' given.' )
        else:
            if not isinstance(value, expected_value):
                raise TypeError('"' + keyword + '" expects ' +
                                '"' + str(expected_value) + '", '
                                + str(type(value)) + ' given.' )
        return value

    def _get_state_(self, keyword, function):
        subobj = getattr(self, keyword)
        state = {'parameter': keyword,
                 'zfunctions': []}
        params = ['scope',
                  'mode',
                  'prefix',
                  'syntax']
        for p in params:
            if hasattr(subobj, '_'+p+'_'):
                state[p] = getattr(subobj, '_'+p+'_')
        if hasattr(subobj, '_requirements_'):
            state['requirements'] = subobj._requirements_
        if function:
            if not isinstance(function, list):
                function = [function, ]
            for func in function:
                if isinstance(func, tuple):
                    f_copy = []
                    for f in func:
                        #f_copy.append(f)
                        f_copy.append(self._get_function_copy_(f))
                    f_copy = tuple(f_copy)
                else:
                    #f_copy = func
                    f_copy = self._get_function_copy_(func)
                state['zfunctions'].append(f_copy)
        return state

    def _get_function_copy_(self, func):
        f_copy = types.FunctionType(func.__code__,
                                    func.__globals__,
                                    name = func.__name__,
                                    argdefs = func.__defaults__,
                                    closure = func.__closure__)
        f_copy.__dict__.update(func.__dict__)
        return f_copy

    def _create_multikey_function_(self):
        def function(args):
            if not isinstance(args, list):
                raise TypeError('multikey expects list of tuples, '
                                + str( type(args) ) + ' given.')
            func_list = []
            state = {'multikey': {'zfunctions': []}}
            for item in args:
                if not isinstance(item, tuple):
                    raise TypeError('multikey expects list of tuples, list of '
                                    + str( type(item) ) + ' given.')
                key, value = item
                if hasattr(self, key):
                    f = getattr(self, key)
                    if hasattr(f, '_doc_'):
                        doc = f._doc_
                    else:
                        doc = None
                    f._syntax_ = self._syntax_
                    fdata = {'+doc': doc,
                             '+prefix': getattr(f, '_prefix_'),
                             '+syntax': getattr(f, '_syntax_'),
                             '+key': f._key_,
                             '+expected_value': f._expected_value_}
                    pattr = Aspects(fdata)
                    f = self._get_method_('multikey', key, pattr)
                    f(value)
                    func_list.append(f)
                else:
                    raise LookupError('no such attribute, "'+ key +'".')
            r_method = self._add_active_resource_method_()
            self._add_query_struct_entry_(r_method)
            self._add_to_query_tree_(r_method, 'multikey', 'multikey',
                                     function, {'multikey':
                                                self._get_state_('multikey',
                                                                 [tuple(func_list)])})
        function.__name__ = 'parameter.Property'
        function._parent_ = self
        function._name_ = 'multikey'
        function._prefix_ = self._prefix_
        function._syntax_ = self._syntax_
        function._scope_ = self._scope_
        function._requirements_ = self._requirements_
        function._mode_ = self._mode_
        setattr(self, 'multikey', function)

    def _set_scope_(self):
        if not hasattr(self, '_mode_'):
            return
        if 'S' in self._mode_.flags:
            self._parent_._assign_scope_(self._name_)
        elif isinstance(self._parent_, Node):
            self._parent_._set_scope_()

    def _assign_scope_(self, keyword):
        if not hasattr(self, keyword):
            return
        if self._has_scope_ is None:
            self._has_scope_ = keyword
        elif self._has_scope_ != keyword:
            raise ValueError('Scope is already set to "'+
                             self._scope_+'", given "'+keyword+'".')

    def _get_instance_(self, kw):
        _class = type(kw, (object,), {})
        return _class()


class Parameter(BaseAttributes, Aspects):
    """ """
    _attrs_ = ('parent', 'name', 'data_dict', )

    def __init__(self, **kwargs):
        for attr in self._attrs_:
            if attr in kwargs:
                setattr(self, '_'+attr+'_', kwargs[attr])
            else:
                setattr(self, '_'+attr+'_', None)
        for kw in ('_attr_add_', '_attr_check_'):
            if not hasattr(self, kw):
                setattr(self, kw, None)
        BaseAttributes.__init__(self, self._attr_add_,
                                self._attr_check_, self._data_dict_)
        Aspects.__init__(self, self._data_dict_)


class Source(Parameter, Node):
    """Root object of a wrapper."""
    _attr_add_ = ('+hostname', '+protocol', '+port')
    _attr_check_ = ('+children', )

    def __init__(self, **kwargs):
        Parameter.__init__(self, **kwargs)
        Node.__init__(self, **kwargs)

    def _add_api_(self, keyword, data_dict, obj=None):
        """Create and attach API objects"""
        new_api = API(parent=self,
                      name=keyword,
                      data_dict=data_dict)
        for kw, data in data_dict['+children'].items():
            if '+http_method' in data:
                new_api._is_root_ = True
                new_api._init_query_structs_()
                new_api._add_child_(kw, data)
            elif self._is_api_(data):
                self._add_api_(kw, data, new_api)
            else:
                new_api._add_child_(kw, data)
        if not obj:
            setattr(self, keyword, new_api)
        else:
            setattr(obj, keyword, new_api)

    def _is_api_(self, data):
        if not '+children' in data:
            return False
        for item in data['+children']:
            if '+http_method' in data:
                return False
        return True

    def _get_root_object_(self, obj=None):
        if not obj:
            obj = self
        if obj._is_root_:
            return obj
        else:
            for attr in dir(obj):
                if attr == '_parent_':
                    continue
                attr_obj = getattr(obj, attr)
                if isinstance(attr_obj, (Source, API, ResourceMethod)):
                    if  attr_obj._is_root_:
                        return attr_obj
                    else:
                        return self._get_root_object_(attr_obj)

                    
class API(Parameter, Node):
    """Collections of ResourceMethods."""
    def __init__(self, **kwargs):
        Parameter.__init__(self, **kwargs)
        Node.__init__(self, **kwargs)


class ResourceMethod(Parameter, Node, HTTPMethods):
    """Instantiate subobject(s), handle HTTP requests."""
    _attr_add_ = ('+path', '+http_method', '+output_format', '+input_format', )

    def __init__(self, **kwargs):
        Parameter.__init__(self, **kwargs)
        Node.__init__(self, **kwargs)
        HTTPMethods.__init__(self, **kwargs)


class Property(Parameter, Node):
    """ """
    _attr_add_ = ('+mode', )

    def __init__(self, **kwargs):
        Parameter.__init__(self, **kwargs)
        Node.__init__(self, **kwargs)
