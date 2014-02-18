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

from .requirements import Requirements

class BaseAttributes(object):
    """ Verify the existence of and/or add attributes from
        source/api/method/property data.
    """
    def __init__(self, attr_add=None, attr_check=None, data=None):
        if attr_add:
            self.__add_attributes(attr_add, data)
        if attr_check:
            self.__check_attributes(attr_check, data)

    def __add_attributes(self, attributes, data):
        for attr in attributes:
            if attr not in data:
                raise LookupError('Failed to find required attribute "'+attr+
                                  '" for object ' + self._name_)
            else:
                setattr(self, '_'+attr.lstrip('+')+'_', data[attr])

    def __check_attributes(self, attributes, data):
        for attr in attributes:
            if attr not in data:
                raise LookupError('Failed to find required attribute "'+attr+
                                  '" for object ' + self._name_)


class Aspects(object):
    """Retrieve and set internal parameters of source/api/method/property."""
    def __init__(self, data=None):
        if data is not None:
            self.__doc__ = self._get_doc_string_(data)
            self._prefix_ = self._get_prefix_(data)
            self._syntax_ = self._get_syntax_(data)
            self._scope_ = self._get_scope_(data)
            self._requirements_ = self._get_requirements_(data)
            self._mode_ = self._parse_mode_(data)
            self._key_ = self._get_key_(data)
            self._expected_value_ = self._get_expected_value_(data)

    def _get_doc_string_(self, data):
        if '+doc' in data:
            return data['+doc']
        else:
            return None

    def _get_prefix_(self, data):
        if '+prefix' in data:
            return data['+prefix']
        else:
            return None

    def _get_syntax_(self, data):
        syntax = {}
        if '+syntax' in data:
            syntax = data['+syntax']
        return self._set_default_syntax_(syntax)

    def _set_default_syntax_(self, syntax):
        if '+bind' not in syntax:
            syntax['+bind'] = '='
        if '+chain' not in syntax:
            syntax['+chain'] = '&'
        return syntax

    def _get_scope_(self, data):
        if '+scope' in data:
            return data['+scope']
        else:
            return None

    def _get_key_(self, data):
        if '+key' in data:
            return data['+key']
        else:
            return None

    def _get_expected_value_(self, data):
        if '+expected_value' in data:
            return self._parse_type_(data['+expected_value'])
        else:
            return None

    def _parse_type_(self, data_type):
        if isinstance(data_type, list):
            return self._get_type_tuple_(data_type)
        elif isinstance(data_type, dict):
            d = {}
            for k,v in data_type.items():
                d[k] = self._parse_type_(v)
            return d
        else:
            _type = self._check_type_(data_type)
            if _type is not False:
                return _type
            else:
                return re.compile(data_type)

    def _get_type_tuple_(self, data_type):
        typelist = []
        for dt in data_type:
            _type = self._check_type_(dt)
            if _type is list:
                typelist.append( list(self._get_type_tuple_(dt)) )
            elif _type is not False:
                typelist.append(_type)
            else:
                typelist.append(re.compile(dt))
        return tuple(typelist)

    def _check_type_(self, data_type):
        for dtype in ( int, bool, str, float ):
            if dtype.__name__ == data_type:
                 return dtype
        for dtype in ( list,  ):
            if isinstance(data_type, dtype):
                return dtype
        if data_type is None:
            return type(None)
        return False

    def _get_requirements_(self, data):
        if '+requirements' in data:
            requirements = Requirements()
            requirements.add_requirements(data['+requirements'])
            return requirements
        else:
            return None

    def _parse_mode_(self, data):
        if data is None:
            return 'K+V'
        elif '+mode' in data:
            mode_string = data['+mode']
        else:
            data['+mode'] = mode_string = 'K+V'
        mode_flags = mode_string.split('+')
        return type('mode', (), {'string': mode_string,
                                 'flags': mode_flags})()
