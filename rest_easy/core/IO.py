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
from .attributes import BaseAttributes

class Input(BaseAttributes):

    def __init__(self, input_data):
        super(Input, self).__init__(('format', ),
                                    ('+parameters', ),
                                    input_data)

class Output(BaseAttributes):

    def __init__(self, output_data):
        super(Output, self).__init__(('format', ),
                                     (),
                                     output_data)

        
