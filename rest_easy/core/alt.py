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
    from urllib2 import quote, urlopen
    from StringIO import StringIO
elif major == 3:
    from urllib.parse import quote
    from urllib.request import urlopen
    from io import StringIO

import glob
import json
import re
import copy
import pprint
from collections import OrderedDict

from dicttoxml import dicttoxml
import xmltodict
from lxml import etree
import yaml

from .parser import Parser

class AlternateInterface(object):
    """Interface for querying with strings/dicts.

    Example:

       RestEasy.new_query('dpla', 'v2', 'apikey->xxxx:Items->searchIn->title->Dead Souls')

    or,

       RestEasy.new_query('dpla', 'v2', {'apiKey': 'xxxx',
                                          'Items': {'searchIn':
                                                    {'title': 'Dead Souls'}}})
    then,

       results = RestEasy.GET()
    """
    _resource_method_ = None

    def _get_query_components_(self, query):
        query_elements = []
        queries = (Parser._parse_query_string_(query))
        if not isinstance(queries, list):
            queries = [queries,]
        source_obj = api_object = None
        elem = queries
        for q in queries:
            for k, v in q.items():
                try:
                    source_obj = self.get_wrappers(k)
                except: 
                    pass
                else:
                    elem = v
                    break
            else:
                elem = v
            root_obj = source_obj._get_root_object_()
            for k, v in q.items():
                try:
                    api_obj = self._get_api_object_(source_obj, k)
                except:
                    api_obj = source_obj
                else:
                    elem = v
                    break
            else:
                elem = v
            query_elements.append(Parser._parse_query_string_(elem))
        return source_obj._name_, api_obj._name_, \
            root_obj, api_obj, query_elements

    def get_url(self, query, reset=False):
        if not self._resource_method_:
            source, api, root_obj, api_obj, query_elements = \
              self._get_query_components_(query)
            self._submit_elements_(source, api, root_obj, api_obj, query_elements)
            if not self._resource_method_:
                raise Exception('Insufficient arguments -- '+
                                'you must supply a Resource Method.')        
        url = self._resource_method_.get_url(reset=reset)
        self._resource_method_ = None
        return url

    def new_query(self, query):
        if self._resource_method_:
            self._resource_method_ = None
        source, api, root_obj, api_obj, query_elements = \
          self._get_query_components_(query)
        self._submit_elements_(source, api, root_obj, api_obj, query_elements)
        if not self._resource_method_:
            raise Exception('Insufficient arguments -- '+
                            'you must supply a Resource Method.')

    def _get_api_object_(self, source_object, api):
        try:
            api_obj = getattr(source_object, api)
        except AttributeError:
            raise AttributeError('Invalid API "' + str(api) + '"')
        return api_obj

    def _assign_resource_method_(self, root_obj, method_obj):
        if self._resource_method_ is None:
            self._resource_method_ = method_obj
            if self._resource_method_ in root_obj._active_resource_methods_:
                self._resource_method_.new_query()
        else:
            if self._resource_method_ != method_obj:
                raise Exception('Invalid query -- conflicting Resource Methods '+
                                '"'+self._resource_method_._name_+'" and '+
                                '"'+method_obj._name_+'"')

    def _submit_elements_(self, source, api, root_obj, api_obj, query_elements):
        if not isinstance(query_elements, list):
            query_elements = [query_elements, ]
        for element in query_elements:
            if isinstance(element, dict):
                for k, v in element.items():
                    param = self._get_parameter_(source, api, api_obj, k)
                    for flags in param._mode_.flags:
                        if 'M' in flags:
                            lt = []
                            for a, b in v.items():
                                for i in b:
                                    lt.append((a, i)) 
                            param.multikey(lt)
                            return
                    if hasattr(param, '_http_method_'):
                        self._assign_resource_method_(root_obj, getattr(api_obj, k) )
                    if isinstance(v, dict):
                        self._submit_elements_(source, api, root_obj, param, v)
                    else:
                        if hasattr(param, '__call__'):
                            if not v:
                                v = None
                            param(v)

    def _get_parameter_(self, source, api, api_obj, keyword):
        try:
            param = getattr(api_obj, keyword)
        except AttributeError:
            raise AttributeError('Could not find "' + str(keyword) + '"'+
                                 ' in "'+ str(source)+ '" API "' +
                                 str(api)+ '"')
        return param
