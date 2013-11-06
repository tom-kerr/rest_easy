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


class Node(BaseAttributes, Aspects, Callable, QueryTree):
    """ """
    _reserved_ = ('+this', '+mode', '+scope', '+prefix',
                  '+requirements', '+children', '+key',
                  '+expected_value', '+doc')

    def __init__(self, attr_add=None, attr_check=None, data=None, is_root=False):
        BaseAttributes.__init__(self, attr_add, attr_check, data)
        Aspects.__init__(self, data)
        self._has_scope_ = None
        self._is_root_ = is_root

    def help(self, path=''):
        path = self._name_ + '->' + path
        self._parent_.help(path)

    def reset_query(self):
        if self._is_root_:
            self._query_objects_ = {}
        else:
            self._parent_.reset_query()

    def _add_(self, parent_kw, child_kw=None, data=None):
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
            self._set_method_(parent_kw, None, pattrs)
            del data['+this']

        if '+key' not in data and '+expected_value' not in data:
            if not '+mode' in data:
                data['+mode'] = self._parse_mode_(None)
            if '+syntax' not in data and hasattr(self, '_syntax_'):
                data['+syntax'] = self._syntax_

            if '+http_method' in data:
                param = Method(parent=self,
                               method_name=parent_kw,
                               baseurl=self._baseurl_,
                               data=data)
            else:
                param = Property(parent=self,
                                 property_name=parent_kw,
                                 data=data)
            if '+children' in data:
                for keyword, pdata in data['+children'].items():
                    if keyword in Node._reserved_:
                        continue
                    param._add_(keyword, None, deepcopy(pdata))
                    if hasattr(self, parent_kw):
                        parent = getattr(self, parent_kw)
                        new_property = getattr(param, keyword)
                        setattr(parent, keyword, new_property)
                if not hasattr(self, parent_kw):
                    setattr(self, parent_kw, param)
            return

        if '+syntax' not in data and hasattr(self, '_syntax_'):
            data['+syntax'] = self._syntax_
        pattrs = Aspects(data)
        self._set_method_(parent_kw, child_kw, pattrs)
        
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

    def _get_method_(self, parameter, child_kw, pattrs):
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

            if hasattr(function, '_value_'):
                if function._value_ is not None:
                    f = self._get_method_(parameter, child_kw, pattrs)
                    f(value)
                    return
            setattr(function, '_value_', value)

            self._set_scope_()
            if parameter != 'multikey':
                state = self._get_state_(parameter, function)
                self._add_query_object_(parameter, child_kw,
                                        function, {parameter: state})

        function.__name__ = 'parameter.Property'
        function.__doc__ = pattrs.__doc__
        function._parent_ = self
        function._name_ = parameter
        function._prefix_ = pattrs._prefix_
        function._syntax_ = pattrs._syntax_
        function._scope_ = pattrs._scope_
        function._requirements_ = pattrs._requirements_
        function._mode_ = pattrs._mode_
        function._value_ = None
        function._key_ = pattrs._key_
        function._expected_value_ = pattrs._expected_value_
        setattr(function, 'help', types.MethodType(self.help, self._name_))
        return function

    def _validate_input_(self, child_kw, value, expected_value):
        """Check input value against expected value"""
        if type(expected_value).__name__ == 'SRE_Pattern':
            if not expected_value.match( str(value) ):
                raise TypeError('"' + child_kw + '" matches pattern "'
                                + expected_value.pattern + '", "'
                                + str(value) + '" given.' )
        elif isinstance(expected_value, dict):
            for k,v in expected_value.items():
                self._validate_input_(child_kw, value, v)
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
                raise TypeError('"' + child_kw + '" expects ' +
                                '"' + str(expected_value) + '", ' +
                                ', '.join(exceptions) + ' given.' )
        else:
            if not isinstance(value, expected_value):
                raise TypeError('"' + child_kw + '" expects ' +
                                '"' + str(expected_value) + '", '
                                + str(type(value)) + ' given.' )
        return value

    def _get_state_(self, parameter, function):
        subobj = getattr(self, parameter)
        state = {'parameter': parameter,
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
            for f in function:
                state['zfunctions'].append(f)
        return state

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

            self._add_query_object_('multikey', 'multikey',
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

    def _assign_scope_(self, parameter):
        if not hasattr(self, parameter):
            return
        if self._has_scope_ is None:
            self._has_scope_ = parameter
        elif self._has_scope_ != parameter:
            raise ValueError('Scope is already set to "'+
                             self._scope_+'", given "'+parameter+'".')

    def _get_instance_(self, kw):
        _class = type(kw, (object,), {})
        return _class()


class Source(Node):
    """Root object of a wrapper."""
    def __init__(self, parent, source_data):
        self._parent_ = parent
        self._query_objects_ = {}
        Node.__init__(self, ('+baseurl', ), ('+children', ), source_data)

    def _add_api_(self, name, api_data, obj=None):
        """Create API object(s) and set as attributes"""
        new_api = API(self, name, self._baseurl_, api_data)
        for parameter, data in api_data['+children'].items():
            if self._is_api_(data):
                self._add_api_(parameter, data, new_api)
            else:
                new_api._add_(parameter, None, data)
        if not obj:
            setattr(self, name, new_api)
        else:
            setattr(obj, name, new_api)

    def _is_api_(self, data):
        if not '+children' in data:
            return False
        for item in data['+children']:
            if '+http_method' in data:
                return False
        return True


class API(Node):
    """Collections of Methods."""
    def __init__(self, parent, name, baseurl, api_data, is_root=True):
        self._parent_ = parent
        self._name_ = name
        self._baseurl_ = baseurl
        self._query_objects_ = {}
        Node.__init__(self, None, None, api_data, is_root)


class Method(Node, HTTPMethods):
    """Instantiate subobject(s), handle HTTP requests."""
    def __init__(self, parent, method_name, baseurl, data, is_root=False):
        self._parent_ = parent
        self._name_ = method_name
        self._baseurl_ = baseurl
        self._method_data_ = data
        Node.__init__(self, ('+path', '+http_method', '+output_format', '+input_format'),
                      None, self._method_data_, is_root)
        HTTPMethods.__init__(self)


class Property(Node):
    """ """
    def __init__(self, parent, property_name, data, is_root=False):
        self._parent_ = parent
        self._name_ = property_name
        self._property_data_ = data
        Node.__init__(self, ('+mode', ), None, self._property_data_, is_root)


