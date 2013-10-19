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

from dicttoxml import dicttoxml
import xmltodict
from lxml import etree


class Convert(object):

    def _convert_results_(self, results, output_format,
                          return_format, inherit_from):
        if output_format == 'json':
            if return_format.lower() == 'xml':
                results = dicttoxml(json.loads(results))
            elif return_format.lower() == 'object':
                results = self._json_to_object_(json.loads(results),
                                               'QueryObject',
                                               inherit_from)
            else:
                results = json.loads(results)
        elif output_format == 'xml':
            if return_format.lower() == 'json':
                results = json.loads(json.dumps(xmltodict.parse(results)))
            elif return_format.lower() == 'object':
                jsonresults = json.loads(json.dumps(xmltodict.parse(results)))
                results = self._json_to_object_(jsonresults,
                                               'QueryObject',
                                               inherit_from)
        elif output_format == 'javascript':
            if return_format.lower() in ('json', 'xml', 'object'):
                print ('Cannot Convert \'JavaScript\' response to \'' +
                       return_format.lower() +'\'...returning \'JavaScript\'')
            pass
        return results

    def _json_to_object_(self, json, classname, inherit_from=None):
        cls = 'QueryObjectSubElement'
        if isinstance(json, list):
            object_list = []
            for item in json:
                object_list.append(self._json_to_object_(item, classname))
            return object_list
        elif isinstance(json, dict):
            object_dict = {}
            for key, value in json.items():
                key = self._make_valid_python_variable_name_(key)
                if isinstance(value, list):
                    object_list = []
                    for item in value:
                        object_list.append(self._json_to_object_(item, cls))
                    object_dict[key] = object_list
                elif isinstance(value, dict):
                    object_dict[key] = self._json_to_object_(value, cls)
                else:
                    object_dict[key] = value
            if isinstance(inherit_from, tuple):
                inherits = inherit_from
            else:
                inherits = ()
            return type(classname, inherits, object_dict)
        else:
            return json

    def _make_valid_python_variable_name_(self, string):
        return re.sub('[^a-zA-Z0-9_]', '__', string)
