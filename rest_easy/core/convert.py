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

    def _convert_results_(self, results, output_format, return_format):
        if output_format == 'json':
            if return_format.lower() == 'xml':
                results = dicttoxml(json.loads(results))
            elif return_format.lower() == 'obj':
                results = DynamicAccessor(json.loads(results))
            else:
                results = json.loads(results)
        elif output_format == 'xml':
            if return_format.lower() == 'json':
                results = json.loads(json.dumps(xmltodict.parse(results)))
            elif return_format.lower() == 'obj':
                jsonresults = json.loads(json.dumps(xmltodict.parse(results)))
                results = DynamicAccessor(jsonresults)
        elif output_format == 'javascript':
            if return_format.lower() in ('json', 'xml', 'obj'):
                print ('Cannot Convert \'JavaScript\' response to \'' +
                       return_format.lower() +'\'...returning \'JavaScript\'')
            pass
        return results


class DynamicAccessor(object):

    def __init__(self, response):
        self._data_ = response
        self._build_accessors_()

    def _build_accessors_(self):
        if not isinstance(self._data_, list):
            parent = False
            hasgetby=False
            self._data_ = [self._data_, ]
        elif isinstance(self._data_, list) and len(self._data_)==1:
            parent=False
            hasgetby=False
        else:
            parent=True
            hasgetby=True
            self._add_getby_func_('', self._data_)

        for d in self._data_:
            if isinstance(d, dict):
                for item in d.items():
                    attr, data = item
                    if not hasgetby and isinstance(data, list) and \
                      data and isinstance(data[0], dict):
                        self._add_getby_func_(attr, data)
                        self._add_get_func_(attr, data, parent)
                    else:
                        self._add_get_func_(attr, data, parent)
            else:
                raise NotImplementedError()

    def _add_get_func_(self, attr, data, parent=True):
        def function(raw=False):
            fdata = function._data_
            if raw:
                return fdata
            return self._get_formatted_data_(fdata)
        attr = self._format_attr_name_(attr)
        plural_attr = self._make_plural_(attr)
        if hasattr(self, 'get'+attr) or hasattr(self, 'get'+plural_attr):
            self._append_get_func_(attr, data)
        else:
            if parent:
                self._add_child_get_func_(data)
            function._data_ = data
            setattr(self, 'get'+attr, function)

    def _get_formatted_data_(self, data):
        if isinstance(data, list) and not self._is_flat_(data):
            l = []
            for item in data:
                l.append(DynamicAccessor(item))
            return l
        elif isinstance(data, dict) and not self._is_flat_(data):
            if len(data.keys()) == 1:
                for v in data.values():
                    return v
            else:
                return DynamicAccessor(data)
        else:
            return data

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
        except:
            nattr = self._make_plural_(attr)
            instance = getattr(self, 'get'+nattr)
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
            setattr(self, 'get'+plural_attr, newinstance)

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
            #if not raw:
            #matches = [self._get_formatted_data_(item) for item in matches]
            if raw:
                return matches
            return DynamicAccessor(matches)
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
