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

import pprint
import os
import glob
import re
from copy import deepcopy

from .yamler import Yamler
from .attributes import BaseAttributes, Aspects, Callable
from .api import API
from .parameter import Node, Method, Essential


class Source(BaseAttributes, Aspects,
             Callable, Node, Essential):
    """Root object of a wrapper."""
    def __init__(self, source_data):
        self._parent_ = None
        self._query_objects_ = {}
        BaseAttributes.__init__(self, ('baseurl', ), ('+parameters', ), source_data)
        Aspects.__init__(self, source_data)
        Essential.__init__(self, source_data, True)

    def _add_api_(self, name, api_data, obj=None):
        """Create API object(s) and set as attributes"""
        new_api = API(name, self._baseurl_, api_data)
        for parameter, data in api_data.items():
            if 'http_method' in data:
                new_api._add_method_(parameter, data)
            else:
                self._add_api_(parameter, data, new_api)
        if not obj:
            setattr(self, name, new_api)
        else:
            setattr(obj, name, new_api)


class SourceBuilder(Source):
    """Fetch source files and create Source objects"""
    def __init__(self):
        self.sources = {}
        self._find_sources_()

    def _find_sources_(self):
        """Find all source yaml files"""
        self.sourcefile_list = glob.glob(self.source_dir + '/*.yaml')
        self.source_list = []
        for sourcefile in self.sourcefile_list:
            sf = os.path.basename(sourcefile).split('.yaml')[0]
            if not sf.endswith('.def') and sf not in ('stddef', 'stdregex'):
                self.source_list.append(sf)

    def _get_source_(self, source):
        """Return Source data, either from file or if previously imported, from dict"""
        if source in self.sources:
            return deepcopy(self.sources[source])
        elif source is not None and source not in self.sources:
            return self._import_source_(source)
        else:
            raise Exception('Invalid source \'' + str(source) + '\'')

    def _import_source_(self, namespace):
        """Retrieve and return source data from file(s)"""
        yamler = Yamler(self.source_dir)
        for source_file in self.sourcefile_list:
            match = re.match('^(?i)'+namespace+'.yaml$',
                             os.path.basename(source_file))
            if match:
                y = yamler.load(source_file)
                self.sources[namespace] = y
                return deepcopy(y)
        raise Exception('Invalid Source.')

    def getSourceAPIs(self, source):
        """Return API wrapper(s) for a given source."""
        source_data = self._get_source_(source)
        return SourceBuilder._parse_data_(source, source_data)

    @staticmethod
    def _parse_data_(source, source_data):
        """Create and return a Source instance."""
        new_source = Source(source_data)
        new_source._name_ = source
        for api, data in source_data['+parameters'].items():
            if 'http_method' in data:
                method = api
                param = Method(parent=new_source,
                               method_name=method,
                               baseurl=new_source._baseurl_,
                               data=data)
                setattr(new_source, method, param)
            else:
                new_source._add_api_(api, data)
        return new_source
