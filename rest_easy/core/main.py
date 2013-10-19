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
from .parser import Parser
from .help import Helper
from .alt import AlternateInterface

class RestEasy(SourceBuilder, AlternateInterface, Parser, Helper):

    def __init__(self):
        self.source_dir = os.path.abspath(os.path.dirname(__file__))+'/sources'
        super(RestEasy, self).__init__()


