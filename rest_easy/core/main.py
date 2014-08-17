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

import os

from .source import SourceBuilder
from .alt import AlternateInterface
from .query import AsyncMultiResourceMethod

class RestEasy(SourceBuilder, AlternateInterface):

    def __init__(self):
        self.source_dir = os.path.abspath(os.path.dirname(__file__))+'/sources'
        self._name_ = 'RestEasy'
        super(RestEasy, self).__init__()
        for http_method in ('GET', 'POST', 'PUT'):
            setattr(self, http_method, AsyncMultiResourceMethod(self, http_method))
