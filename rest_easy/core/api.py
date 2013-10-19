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

from .attributes import BaseAttributes, Aspects, Callable
from .parameter import Node, Method, Essential


class API(BaseAttributes, Aspects,
          Node, Callable, Essential):
    """Collections of Methods."""
    def __init__(self, name, baseurl, api_data):
        self._api_ = None
        self._parent_ = None
        self._name_ = name
        self._baseurl_ = baseurl
        self._query_objects_ = {}
        BaseAttributes.__init__(self, data=api_data)
        Aspects.__init__(self, data=api_data)
        Essential.__init__(self, api_data, True)

    def _add_method_(self, pname, pdata):
        new_method = Method(api=self,
                            parent=self,
                            method_name=pname,
                            baseurl=self._baseurl_,
                            data=pdata)
        setattr(self, pname, new_method)

