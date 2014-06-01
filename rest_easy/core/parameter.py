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
import json
import pprint
from copy import copy, deepcopy
from collections import OrderedDict
import types

from .attributes import BaseAttributes, Aspects
from .query import HTTPMethods, QueryTree
from .requirements import Requirements
    

class AbstractNode(BaseAttributes, Aspects):
    """ Object-building behavior
    
        Creates internal state and handles the addition of child Nodes.
    """
    _attrs_ = ('parent', 'name', 'data_dict', )

    def __init__(self, **kwargs):
        self._init_internal_(**kwargs)
        if len(Node._func_list_) != 0:
            last_callable = Node._func_list_.pop()
            if last_callable:
                last_callable._parent_ = self
                Node._call_hash_[self] = last_callable
        self._is_root_ = False
        source_data = kwargs['data_dict']
        if '+children' in source_data:
            for kw, data in source_data['+children'].items():
                AbstractNode._set_attr_from_(source_data, data, ('+syntax', ))
                if '+http_method' in data:
                    self._is_root_ = True
                    self._init_query_structs_()
                    self._add_child_(kw, data)
                elif self._is_api_(data):
                    self._add_api_(kw, data, self)
                else:
                    self._add_child_(kw, data)

    def _init_internal_(self, **kwargs):
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
                
    def _add_api_(self, keyword, data_dict, obj=None):
        """Create and attach API objects"""
        dct = {'parent': self,
               'name': keyword,
               'data_dict': data_dict}
        new_api = CreateNode('API', (API, ), dct)
        new_api_instance = new_api(**dct)                
        if not obj:
            setattr(self, keyword, new_api_instance)
        else:
            setattr(obj, keyword, new_api_instance)

    def _set_attr_from_(source, dest, attrs):
        for attr in attrs:
            if attr in source and attr not in dest:
                dest[attr] = source[attr]
        
    def _make_this_(self, keyword, data):
        AbstractNode._set_attr_from_(data['+this'], data, ('+mode', '+syntax'))
        if '+syntax' not in data['+this'] and hasattr(self, '_syntax_'):
            data['+this']['+syntax'] = self._syntax_
        obj = self._get_new_node_(parent=self, name=keyword, data_dict=data)
        setattr(self, keyword, obj)
            
    def _get_new_node_(self, **kwargs):
        dct = kwargs
        if '+http_method' in dct['data_dict']:
            obj = CreateNode('ResourceMethod', (ResourceMethod, ), dct)
        else:
            obj = CreateNode('Property', (Property, ), dct)
        obj_instance = obj(**dct)
        return obj_instance

    def _add_child_(self, keyword, data=None):
        if 'MK' in self._mode_.flags:
            if not hasattr(self, 'multikey'):
                self._create_multikey_function_()
        if '+this' in data:
            self._make_this_(keyword, data)
            return
        obj = self._get_new_node_(parent=self, name=keyword, data_dict=data)
        setattr(self, keyword, obj)
        
    def _new_method_(keyword, data=None):
        pattrs = Aspects(data)
        return AbstractNode._get_method_(keyword, pattrs)

    def _get_method_(keyword, pattrs):
        def function(self, value):
            if hasattr(pattrs, '_default_value_'):
                kwargs = {'default_value': pattrs._default_value_}
            else:
                kwargs = {}
            value = self._validate_input_(keyword, value,
                                          pattrs._expected_value_,
                                          **kwargs)

            setattr(function, '_value_', value)

            self._set_scope_()
            if keyword != 'multikey':
                state = self._get_state_(keyword, function)
                if self._parent_._is_root_:
                    make_global = True
                    r_method = None
                else:
                    make_global = False
                    r_method = self._add_active_resource_method_()
                    self._add_query_struct_entry_(r_method)
                self._add_to_query_tree_(r_method, keyword, keyword,
                                         function, {keyword: state},
                                         None, make_global)

        function.__name__ = 'parameter.Property'
        function.__doc__ = pattrs.__doc__
        #function._parent_ = self
        function._name_ = keyword
        function._prefix_ = pattrs._prefix_
        function._syntax_ = pattrs._syntax_
        function._scope_ = pattrs._scope_
        function._requirements_ = pattrs._requirements_
        function._mode_ = pattrs._mode_
        function._value_ = None
        function._key_ = pattrs._key_
        try:
            function._default_value_ = pattrs._default_value_
        except:
            pass
        function._expected_value_ = pattrs._expected_value_
        setattr(function, 'help', types.MethodType(Node.help, function))
        return function

    def _get_instance_(kw):
        _class = type(kw, (object,), {})
        return _class()    
        
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
                    f = AbstractNode._get_method_('multikey', pattr)
                    f(self, value)
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


        
class CreateNode(type):
    """ Node Metaclass 
    
        rest_easy objects may refer to themselves by way of the '+this'
        field, and so at class creation we need to check for this reference
        and create a separate Node instance for it.
    """

    def __new__(cls, clsname, bases, dct):
        keyword = dct['name']
        data_dict = dct['data_dict']
        clsdct = {}
        if '+this' in data_dict:
            this = data_dict['+this']
            p_dct = {'name': keyword, 
                     'data_dict': this}
            kwargs = {'parent': cls,
                      'name': keyword,
                      'data_dict': this}
            prop = CreateNode('Property', (Property, ), p_dct)
            prop_instance = prop(**kwargs)
            Node._func_list_.append(prop_instance) 
            AbstractNode._set_attr_from_(this, data_dict, ('+mode', '+syntax'))                    
        elif Property in bases:
            func = AbstractNode._new_method_(keyword, data_dict)
            Node._func_list_.append(func)
        if '+http_method' in data_dict:
            if data_dict['+http_method'] == 'GET':
                clsdct['set_return_format'] = set_return_format
        return type.__new__(cls, clsname, bases, clsdct)
    


class Node(QueryTree):
    """An object in wrapper tree
    """
    _reserved_ = ('+this', '+mode', '+scope', '+prefix',
                  '+requirements', '+children', '+key',
                  '+default_value', '+expected_value', '+doc')
    _func_list_ = []
    _call_hash_ = {}

    def __init__(self, **kwargs):
        self._has_scope_ = None
        if self._is_root_:
            self._init_query_structs_()

    def __call__(self, k=None, v=None):
        if k and not v or not k and not v:
            if isinstance(k, str) and hasattr(self, k):
                return getattr(self, k)
            else:
                if self not in Node._call_hash_:
                    raise LookupError(self._name_ + 
                                      ' -- no such item in Node._call_hash_ ...' +
                                      ' object not callable')
                instance_callable = Node._call_hash_[self]
                if isinstance(instance_callable, Node):
                    instance_callable(k)
                else:
                    instance_callable(self, k)
        elif k and v:
            attr = getattr(self, k)
            attr(v)
        else:
            raise Exception('Too many arguments.')


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

    def _get_state_(self, keyword, function):        
        if hasattr(self, keyword):
            subobj = getattr(self, keyword)
        else:
            subobj = self
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
                             str(self._scope_)+'", given "'+keyword+'".')

    def _is_api_(self, data):
        if self.__class__.__name__ == 'RestEasy':
            return False
        elif isinstance(self, (Source, API)):
            if not '+children' in data:
                return False
            child_has_children = False
            for kw, item in data['+children'].items():
                if '+http_method' in item:
                    return True
                if '+children' in item:
                    child_has_children = True
            if child_has_children:
                return True
            else:
                return False
        elif isinstance(self, (ResourceMethod, Property)):
            return False
        else:
            return False



class Source(AbstractNode, Node):
    """Root object of a wrapper.
    """
    _attr_add_ = ('+hostname', '+protocol', '+port')
    _attr_check_ = ('+children', )

    def __init__(self, **kwargs):
        AbstractNode.__init__(self, **kwargs)
        Node.__init__(self, **kwargs)

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

                    
class API(AbstractNode, Node):
    """Collections of ResourceMethods.
    """
    def __init__(self, **kwargs):
        AbstractNode.__init__(self, **kwargs)
        Node.__init__(self, **kwargs)


class ResourceMethod(AbstractNode, Node, HTTPMethods):
    """Exposes a REST method (GET, POST, etc) and relevant child properties. 
    """
    _attr_add_ = ('+path', '+http_method', '+input_format', )
    _attr_check_ = ('+output_format',)

    def __init__(self, **kwargs):
        AbstractNode.__init__(self, **kwargs)
        Node.__init__(self, **kwargs)
        HTTPMethods.__init__(self, **kwargs)
        
#this method is attached to GET ResourceMethods
def set_return_format(self, fmt):
    self._return_format_ = fmt


class Property(AbstractNode, Node):
    """A field, where user query values are accepted/verified.
    """
    _attr_add_ = ('+mode', )

    def __init__(self, **kwargs):
        AbstractNode.__init__(self, **kwargs)
        Node.__init__(self, **kwargs)

    def _validate_input_(self, keyword, value, expected_value, **kwargs):
        """Check input value against expected value and set default value
        if necessary.
        """
        if type(expected_value).__name__ == 'SRE_Pattern':
            if not expected_value.match( str(value) ):
                raise TypeError('"' + keyword + '" matches pattern "'
                                + expected_value.pattern + '", "'
                                + str(value) + '" given.' )
        elif isinstance(expected_value, dict):
            if expected_value:
                for k,v in expected_value.items():
                    self._validate_input_(keyword, value, v, **kwargs)
                    value = str(k) + str(value)
            else:
                if isinstance(value, dict):
                    value = json.dumps(value)
                else:
                    raise TypeError('"' + keyword + '" expects "'
                                    + str(expected_value) + '", "'
                                    + str(type(value)) + '" given.' )
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
                if value is None and 'default_value' in kwargs:
                    value = kwargs['default_value']
        else:
            if not isinstance(value, expected_value):
                raise TypeError('"' + keyword + '" expects ' +
                                '"' + str(expected_value) + '", '
                                + str(type(value)) + ' given.' )
            elif value is None and 'default_value' in kwargs:
                    value = kwargs['default_value']
        return value
