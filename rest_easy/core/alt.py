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

    def _get_query_components_(self, source, api, query):
        source_obj = self.get_wrappers(source)
        root_obj = source_obj._get_root_object_()
        api_obj = self._get_api_object_(source_obj, api)
        query_elements = Parser._parse_query_string_(query)
        return root_obj, api_obj, query_elements

    def get_query_string(self, source=None, api=None, query=None, reset=False):
        if not self._resource_method_:
            root_obj, api_obj, query_elements = \
              self._get_query_components_(source, api, query)
            self._submit_elements_(source, api, api_obj, query_elements)
            if not self._resource_method_:
                raise Exception('Insufficient arguments -- '+
                                'you must supply a Resource Method.')
        return self._resource_method_.get_query_string(reset=reset)

    def new_query(self, source, api, query):
        if self._resource_method_:
            self._resource_method_ = None
        root_obj, api_obj, query_elements = \
          self._get_query_components_(source, api, query)
        self._submit_elements_(source, api, root_obj, api_obj, query_elements)
        if not self._resource_method_:
            raise Exception('Insufficient arguments -- '+
                            'you must supply a Resource Method.')

    def _get_api_object_(self, source_object, api):
        try:
            api_obj = getattr(source_object, api)
        except:
            raise LookupError('Invalid API "' + str(api) + '"')
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
        except:
            raise LookupError('Could not find "' + str(keyword) + '"'+
                              ' in "'+ str(source)+ '" API "' +
                              str(api)+ '"')
        return param
