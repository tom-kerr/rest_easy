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

class AlternateInterface(Parser):
    """Interface for querying with strings/dicts.

    Example:

       RestEasy.GET('dpla', 'v2', 'apikey->xxxx:Items->searchIn->title->Dead Souls')

    or,

       RestEasy.GET('dpla', 'v2', {'apiKey': 'xxxx',
                                   'Items': {'searchIn':
                                             {'title': 'Dead Souls'}}})
    """
    def GET(self, source, api, query,
            return_format='', inherit_from=None, pretty_print=False):
        self._method_ = None
        source_apis = self.get_wrappers(source)
        query_elements = self._parse_query_string_(query)
        api_object = self._get_api_object_(source_apis, api)
        self._submit_elements_(source, api, api_object, query_elements)
        if not self._method_:
            raise Exception('Insufficient arguments -- you must supply a Method.')
        return self._method_.GET(return_format, inherit_from, pretty_print)

    def get_query_string(self, source, api, input_strings, reset=False):
        self._method_ = None
        source_apis = self.get_wrappers(source)
        query_elements = self._parse_query_string_(input_strings)
        api_object = self._get_api_object_(source_apis, api)
        self._submit_elements_(source, api, api_object, query_elements)
        if not self._method_:
            raise Exception('Insufficient arguments -- you must supply a Method.')
        return self._method_.get_query_string(reset)

    def _get_api_object_(self, source_object, api):
        try:
            api_object = getattr(source_object, api)
        except:
            raise LookupError('Invalid API "' + str(api) + '"')
        return api_object

    def _assign_method_(self, method_obj):
        if self._method_ is None:
            self._method_ = method_obj
        else:
            if self._method_ != method_obj:
                raise Exception('Invalid query -- conflicting Methods '+
                                '"'+self._method_+'" and "'+method_obj+'"')

    def _submit_elements_(self, source, api, api_object, query_elements):
        if not isinstance(query_elements, list):
            query_elements = [query_elements, ]
        for element in query_elements:
            if isinstance(element, dict):
                for k, v in element.items():
                    param = self._get_parameter_(source, api, api_object, k)
                    if hasattr(param, '_http_method_'):
                        self._assign_method_( getattr(api_object, k) )
                    if isinstance(v, dict):
                        self._submit_elements_(source, api, param, v)
                    else:
                        if hasattr(param, '__call__'):
                            if not v:
                                v = None
                            param(v)

    def _get_parameter_(self, source, api, api_object, keyword):
        try:
            param = getattr(api_object, keyword)
        except:
            raise LookupError('Could not find "' + str(keyword) + '"'+
                              ' in "'+ str(source)+ '" API "' +
                              str(api)+ '"')
        return param
