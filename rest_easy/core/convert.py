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

from dicttoxml import dicttoxml
import xmltodict
from lxml import etree


class Convert(object):
    """ Handles the conversion of JSON or XML to another format.
        
        The options for conversion are 'json', 'xml', or 'obj', where 'obj' is a
        DynamicAccessor (see convert.DynamicAccessor)
    """
    def _convert_results_(self, results, output_format, 
                          return_format=None, lazy=False, deferred=False):
        if output_format == 'application/json':
            if not return_format:
                results = json.loads(results, encoding='utf-8')
            elif return_format.lower() == 'xml':
                results = dicttoxml(json.loads(results, encoding='utf-8'))
            elif return_format.lower() == 'obj':
                jsonresults = json.loads(results, encoding='utf-8')
                results = DynamicAccessor(jsonresults, lazy, deferred)
        elif output_format == 'text/xml':
            if not return_format:
                return results
            if return_format.lower() == 'json':
                results = json.loads(json.dumps(xmltodict.parse(results)),
                                     encoding='utf-8')
            elif return_format.lower() == 'obj':
                jsonresults = json.loads(json.dumps(xmltodict.parse(results)),
                                         encoding='utf-8')
                results = DynamicAccessor(jsonresults, lazy, deferred)
        elif output_format == 'javascript':
            if not return_format:
                return results
            if return_format.lower() in ('json', 'xml', 'obj'):
                print ('Cannot Convert \'JavaScript\' response to \'' +
                       return_format.lower() +'\'...returning \'JavaScript\'')
        return results


class DynamicAccessor(object):
    """ An object that dynamically builds convenience functions for JSON input.

        To begin, simply pass json to the constructor:
           da = DynamicAccessor(myjson)

        The object returned will have a variety of methods for accessing your 
        data and of the following flavors:

        getField -> where 'field' is the key of an item one layer into a 
                    structure to be returned*, such as: 
                    
                         {'field': {'deeper_field': value}}
                    

        getFieldBySubField -> where 'field' is the key of a list of dicts which
                              can be retrieved based on the value of a 'SubField',
                              for example:

                                  {'items': [ {'id': 1, 'title': ...,
                                              {'id': 2, 'title': ...,
                                            ]}
                              
                              we can retieve an item by id (getItemsById), or by
                              title (getItemsByTitle), or any other subfield. 
                              All items that match the input for that subfield 
                              will be returned*.


        aggrField -> where 'field' is a subfield that occurs more than once among
                     a list of dicts, and 'aggr' stands for aggregate. 
                     Considering the previous structure, a method called 'aggrId'
                     would return* a list of the values of every 'id' field.
 
        
      * If the field being returned contains another nested structure, another 
        DynamicAccessor will be generated and returned for further access, 
        otherwise, the value of that field or a list of values will be returned.
        
        One can defer the construction of nested DynamicAccessors by passing
        lazy=True to the parent's contructor, and even defer the parent's 
        construction by passing it deferred=True. Construction of these objects 
        will take place when one tries to access them.

    """

    def __init__(self, response, lazy=False, deferred=False):
        self._lazy_ = lazy
        self._deferred_ = deferred
        self._data_ = response
        if not deferred:
            self._build_accessors_()
        else:
            self._built_ = False            

    def __getattribute__(self, name):
        if object.__getattribute__(self, '_deferred_') and \
                not object.__getattribute__(self, '_built_'):
            object.__getattribute__(self, '_build_accessors_')()
        return object.__getattribute__(self, name)        

    def _build_accessors_(self):
        self._built_ = True
        _data = self._data_
        if isinstance(self._data_, list):
            parent = False
        elif isinstance(self._data_, dict):
            parent = True

        if not isinstance(self._data_, list):
            hasgetby=False
            _data = [_data, ]
        elif isinstance(self._data_, list) and len(self._data_)==1:
            hasgetby=False
        else:
            hasgetby=True
            self._add_getby_func_('', _data)

        for d in _data:
            if isinstance(d, dict):
                for item in d.items():
                    attr, data = item
                    if not hasgetby and isinstance(data, list):
                        if len(data) == 1 and isinstance(data[0], dict):
                            if len(data[0].keys()) > 1:
                                self._add_getby_func_(attr, data)
                        elif len(data) > 1:
                            nondicts = [i for i in data if not isinstance(i, dict)]
                            if not nondicts:
                                self._add_getby_func_(attr, data)
                    self._add_get_func_(attr, data, parent)
            else:
                raise NotImplementedError()

    def _add_get_func_(self, attr, data, parent):
        def function(raw=False):
            fdata = function._data_
            if raw:
                return fdata
            return self._get_formatted_data_(fdata)
        attr = self._format_attr_name_(attr)
        plural_attr = self._make_plural_(attr)
        if hasattr(self, 'get'+attr) or hasattr(self, 'aggr'+plural_attr):
            self._append_get_func_(attr, data)
        else:
            if parent:
                self._add_child_get_func_(data)
            function._data_ = data
            if isinstance(self._data_, list):
                setattr(self, 'aggr'+plural_attr, function)
            else:
                setattr(self, 'get'+attr, function)

    def _get_formatted_data_(self, data):
        if isinstance(data, list):
            return self._format_list_(data)
        elif isinstance(data, dict):
            return self._format_dict_(data)
        else:
            return data

    def _format_list_(self, lst):
        l = []
        if not self._is_flat_(lst):
            for item in lst:
                if self._lazy_:
                    deferred = True
                else:
                    deferred = False
                l.append(DynamicAccessor(item, lazy=self._lazy_, 
                                         deferred=deferred))
        else:
            for item in lst:
                if isinstance(item, dict):
                    l.append(self._format_dict_(item))
                else:
                    l.append(item)
        return l

    def _format_dict_(self, dct):
        if len(dct.keys()) == 1:
            for v in dct.values():
                return v
        else:
            if self._lazy_:
                deferred = True
            else:
                deferred = False
            return DynamicAccessor(dct, lazy=self._lazy_, 
                                   deferred=deferred)

    def _add_child_get_func_(self, data):
        if isinstance(data, list):
            for i in data:
                if isinstance(i, dict):
                    for a,d in i.items():
                        self._add_get_func_(a,d, parent=False)
        elif isinstance(data, dict):
            for a,d in data.items():
                self._add_get_func_(a,d, parent=False)

    def _append_get_func_(self, attr, data):
        try:
            instance = getattr(self, 'get'+attr)
            nattr = attr
        except AttributeError:
            nattr = self._make_plural_(attr)
            instance = getattr(self, 'aggr'+nattr)
        if not isinstance(instance._data_, list):
            instance._data_ = [instance._data_, ]
        if isinstance(data, list) and len (data) == 1:
            data = data[0]
        if not isinstance(data, dict):
            instance._data_.append(data)
        else:
            newdata = {}
            for k,v in data.items():
                for item in instance._data_:
                    if not item:
                        continue
                    if k not in item:
                        if not k in newdata:
                            newdata[k] = [v,]
                        else:
                            newdata[k].append(v)
                    elif k in item:
                        if not k in newdata:
                            newdata[k] = []
                        if not isinstance(item[k], list):
                            item[k] = [item[k], ]
                        for i in item[k]:
                            newdata[k].append(i)
                        if isinstance(v, list) and len(v) == 1:
                            newdata[k].append(v[0])
                        else:
                            newdata[k].append(v)
            if newdata:
                instance._data_ = newdata

        if hasattr(self, 'get'+attr):
            newinstance = deepcopy(instance)
            delattr(self, 'get'+attr)
            plural_attr = self._make_plural_(attr)
            setattr(self, 'aggr'+plural_attr, newinstance)

    def _add_getby_func_(self, attr, data):
        for item in data:
            for chattr, chdata in item.items():
                function = self._get_match_func_(chattr, data)
                parent = self._format_attr_name_(attr)
                child = self._format_attr_name_(chattr)
                setattr(self, 'get'+parent+'By'+child, deepcopy(function))

    def _get_match_func_(self, attr, data):
        def function(value, raw=False):
            matches = []
            for item in data:
                if attr not in item:
                    continue
                if isinstance(item[attr], (str, int, float, bool)):
                    if self._match_str_(item[attr], value):
                        matches.append(item)
                elif isinstance(item[attr], list):
                    if self._match_list_(item[attr], value):
                        matches.append(item)
                    else:
                        for i in item[attr]:
                            if isinstance(i, dict):
                                if self._match_dict_(i, value):
                                    matches.append(item)
                elif isinstance(item[attr], dict):
                    if self._match_dict_(item[attr], value):
                        matches.append(item)
            if raw:
                return matches
            else:
                if self._lazy_:
                    deferred = True
                else:
                    deferred = False
                return DynamicAccessor(matches, lazy=self._lazy_, 
                                       deferred=deferred)
        return function

    def _match_str_(self, string, value):
        if string == value:
            return True
        else:
            return False

    def _match_list_(self, lst, value):
        if value in lst:
            return True
        else:
            return False

    def _match_dict_(self, dct, value):
        if isinstance(value, dict):
            for k,v in value.items():
                if k in dct:
                    if v == dct[k] or \
                      isinstance(dct[k], list) and v in dct[k]:
                        return True
        else:
            if len(dct.keys()) != 1:
                raise LookupError('Too many fields; cannot disambiguate.')
            for v in dct.values():
                if value == v or \
                  isinstance(v, list) and value in v:
                    return True
        return False

    def _format_attr_name_(self, attr):
        for num, i in enumerate(attr):
            if re.match('[a-zA-Z]', i):
                attr = attr[:num] + attr[num].upper() + attr[num+1:]
                break
        seg = attr.split('_')
        if len(seg) > 1:
            attr = ''
            for s in seg:
                if s == '':
                    attr += '_'
                else:
                    attr += s[0].upper() + s[1:]
        attr = attr.replace('@', 'Arobase')
        attr = attr.replace('#', 'Hash')
        return attr

    def _make_plural_(self, attr):
        if not attr.endswith('s'):
            if attr.endswith('y') and \
              attr[-2] not in ('a','e','i','o','u'):
                attr = attr[:-1] + 'ies'
            else:
                attr += 's'
        elif attr.endswith('ss'):
            attr += 'es'
        return attr

    def _is_flat_(self, data):
        if isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    if not self._is_flat_(item):
                        return False
            return True
        elif isinstance(data, dict):
            for k,v in data.items():
                if isinstance(v, (dict, list)):
                    return False
        return True
