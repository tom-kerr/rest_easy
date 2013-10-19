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

from .IO import Input, Output
from .attributes import BaseAttributes, Aspects, Callable
from .query import HTTPMethods, QueryTree
from .requirements import Requirements


class Essential(object):
    """Initialize global requirement parameters"""
    def __init__(self, data, set_as_attr=False):
        self._essential_ = []
        self._essential_objects_ = {}
        if 'essential' in data:
            self._essential_ = [k for k in data['essential'].keys()]
        else:
            self._essential_ = []
        if set_as_attr:
            self._add_essential_(data)

    def _add_essential_(self, input_data):
        if 'essential' in input_data:
            for item, data in input_data['essential'].items():
                self._add_(item, None, data)
            del input_data['essential']


class Node(QueryTree):
    """ """
    _reserved_ = ('+this', '+mode', '+scope', '+prefix',
                  '+requirements', '+parameters', '+key',
                  '+expected_value', '+doc')

    def __init__(self):
        self._has_scope_ = None

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
            if not '+parameters' in data:
                Node._make_parameter_dict_entry_(data)
            if not '+mode' in data:
                data['+mode'] = self._parse_mode_(None)
            if '+syntax' not in data and hasattr(self, '_syntax_'):
                data['+syntax'] = self._syntax_

            if 'http_method' in data:
                param = Method(#api=self._api_,
                               parent=self,
                               method_name=parent_kw,
                               baseurl=self._baseurl_,
                               data=data)
            else:
                param = Property(#api=self._api_,
                                 parent=self,
                                 property_name=parent_kw,
                                 data=data)

            if '+parameters' in data:
                for keyword, pdata in data['+parameters'].items():
                    if keyword in Node._reserved_:
                        continue
                    param._add_property_(keyword, deepcopy(pdata))
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

    @staticmethod
    def _make_parameter_dict_entry_(data):
        """If not present, a 'parameter' entry is added to the data dict and all
        non-reserved (see Node._reserved_) items are moved there.
        """
        parameters = {}
        data['+parameters'] = {}
        for keyword, d in data.items():
            if keyword not in Node._reserved_:
                data['+parameters'] = parameters[keyword] = deepcopy(d)
        for keyword, pdata in parameters.items():
            del data[keyword]

    def _reset_query_data_(self):
        self._query_objects_ = {}
        self._essential_objects_ = {}

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
                ( not isinstance(pattrs._expected_value_, tuple) and
                  pattrs._expected_value_ is not type(None)) or
                  ( isinstance(pattrs._expected_value_, tuple) and
                    type(None) not in pattrs._expected_value_)):
                return getattr(function, '_value_')
            else:
                self._validate_input_(child_kw, value, pattrs._expected_value_)

            if hasattr(function, '_value_'):
                if function._value_ is not None:
                    f = self._get_method_(parameter, child_kw, pattrs)
                    f(value)
                    return
            setattr(function, '_value_', value)

            if pattrs._requirements_:
                self._determine_requirements_({'requirements':
                                               pattrs._requirements_})
            self._set_scope_()
            if parameter != 'multikey':
                state = self._get_state_(parameter, function)
                self._add_query_object_(parameter, child_kw,
                                        function, {parameter: state})

        function.__name__ = 'parameter.Property'
        function.__doc__ = pattrs.__doc__
        #function._api_ = self._api_
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
        return function

    def _validate_input_(self, child_kw, value, expected_value):
        """Check input value against expected value"""
        if type(expected_value).__name__ == 'SRE_Pattern':
            if not expected_value.match( str(value) ):
                raise TypeError('"' + child_kw + '" matches pattern "'
                                + expected_value.pattern + '", "'
                                + str(value) + '" given.' )
        else:
            if ( isinstance(expected_value, (list, tuple))
                 and isinstance(expected_value[0], list)):
                if not isinstance(value, list):
                    raise TypeError('"' + child_kw + '" expects list of "'
                                    + str(expected_value[0][0]) + '", "'
                                    + str(type(value).__name__) +  '" given.' )
                else:
                    for v in value:
                        if not isinstance(v, expected_value[0][0]):
                            raise TypeError('"' + child_kw + '" expects value of "'
                                            + str(expected_value[0][0]) + '", "'
                                            + str(type(v).__name__) + '" given.' )
            else:
                if not isinstance(value, expected_value):
                    raise TypeError('"' + child_kw + '" expects value of "'
                                    + str(expected_value) + '", "'
                                    + str(type(value).__name__) + '" given.' )

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
        if hasattr(self, '_requirements_'):
            state['requirements'] = self._requirements_
        if function:
            if not isinstance(function, list):
                function = [function, ]
            for f in function:
                state['zfunctions'].append(f)
        return state

    def _raise_essential_(self, essential=None):
        if not hasattr(self, '_essential_') and not essential:
            return
        elif not essential:
            essential = self._essential_
        if self._parent_ and hasattr(self, '_essential_'):
            self._parent_._raise_essential_(essential)
        else:
            for e in essential:
                if e not in self._essential_:
                    self._essential_.append(e)

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
        #function._api_ = self._api_
        function._parent_ = self
        function._name_ = 'multikey'
        function._prefix_ = self._prefix_
        function._syntax_ = self._syntax_
        function._scope_ = self._scope_
        function._requirements_ = self._requirements_
        function._mode_ = self._mode_
        setattr(self, 'multikey', function)

    def _determine_requirements_(self, data):
        if 'requirements' in data:
            if not hasattr(self, '_requirements_') or not self._requirements_:
                self._requirements_ = Requirements()
            self._requirements_.add_requirements(data['requirements'])

    def _set_scope_(self):
        if not hasattr(self, '_mode_'):
            return
        if 'S' in self._mode_.flags:
            self._parent_._assign_scope_(self._name_)
        elif self._parent_:
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


class Method(BaseAttributes, Aspects, Node,
             Essential, Callable, HTTPMethods):
    """Instantiate subobject(s), handle HTTP requests."""
    def __init__(self, **kwargs):
        #self._api_ = kwargs['api']
        self._parent_ = kwargs['parent']
        self._name_ = kwargs['method_name']
        self._baseurl_ = kwargs['baseurl']
        self._method_data_ = kwargs['data']
        self._essential_objects_ = {}
        BaseAttributes.__init__(self, ('path', 'http_method', 'output', ),
                                ('input', ), self._method_data_)
        Aspects.__init__(self, self._method_data_)
        Node.__init__(self)
        HTTPMethods.__init__(self)
        Essential.__init__(self, self._method_data_, True)
        self.new()

    def new(self):
        self._query_objects_ = {}
        self._optional_objects_ = {}
        self._configure_io_()

    def _configure_io_(self):
        self._input_ = Input(self._method_data_['input'])
        self._output_ = Output(self._method_data_['output'])
        for parameter, data in self._method_data_['input']['+parameters'].items():
            self._add_(parameter, None, data)


class Property(BaseAttributes, Aspects, Node, Callable):
    """ """
    def __init__(self, **kwargs):
        #self._api_ = kwargs['api']
        self._parent_ = kwargs['parent']
        self._name_ = kwargs['property_name']
        self._property_data_ = kwargs['data']
        BaseAttributes.__init__(self, ('+mode', ), None, self._property_data_)
        Aspects.__init__(self, self._property_data_)
        Node.__init__(self)
        self._determine_requirements_(self._property_data_)

    def _add_property_(self, keyword, data):
        self._add_(keyword, None, data)


