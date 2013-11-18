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

from .help import Helper
from .yamler import Yamler
from .parameter import Source


class SourceBuilder(Helper):
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

    def get_wrappers(self, source):
        """Return API wrapper(s) for a given source."""
        source_data = self._get_source_(source)
        return SourceBuilder._parse_data_(self, source, source_data)

    @staticmethod
    def _parse_data_(parent_obj, source, source_data):
        """Create and return a Source instance."""
        new_source = Source(parent=parent_obj,
                            name=source,
                            data_dict=source_data)
        for kw, data in source_data['+children'].items():
            if '+http_method' in data:
                new_source._is_root_ = True
                new_source._init_query_structs_()
                new_source._add_child_(kw, data)
            else:
                new_source._add_api_(kw, data)
        return new_source
