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

class Parser(object):
    """ """

    @staticmethod
    def _get_query_elements_(string):
        source = api = detail = None
        elems = Parser._parse_query_string_(string, mode='lookup')[0]
        for k, v in elems.items():
            source = k
            if isinstance(v, dict):
                for i, j in v.items():
                    api = i
                    detail = j
                    break
            else:
                api = v
                detail = None
        return source, api, detail

    @staticmethod
    def _parse_query_string_(query, mode='query'):
        """For alternate interfaces"""
        if isinstance(query, dict):
            return query
        if isinstance(query, str):
            strings = re.split('(?<!\\\\):', query)
        new_elements = []
        for num, element in enumerate(strings):
            element = re.sub('\\\\:', ':', element)
            multi_e = Parser._try_multi_split_(element)
            if multi_e:
                 new_elements.append(multi_e)
            else:
                element = element.lstrip(' ').rstrip(' ').split('->')
                if mode == 'lookup':
                    if len(element)%2!=0:
                        element.append('')
                subelement = {}
                last = None
                for n, e in enumerate(element):
                    el = re.split('(?<!\\\\)\|', e)
                    if len(el) == 1:
                        el = el[0]
                    if len(element) == 2:
                        subelement[e] = element[n+1]
                        break
                    if last is None:
                        subelement[el] = {}
                        last = subelement[el]
                    else:
                        if n < len(element)-2:
                            last[el] = {}
                            last = last[el]
                        elif n == len(element)-2:
                            last[el] = None
                        else:
                            for k in last.keys():
                                last[k] = el
                new_elements.append(subelement)
        return new_elements

    @staticmethod
    def _try_multi_split_(element):
        """For alternate interfaces"""
        elements = re.split('(?<!\\\\)\|', element)
        if elements == [element,]:
            return False
        el = []
        for e in elements:
            items = e.lstrip(' ').rstrip(' ').split('->')
            el.append(items)
        for e in el:
            if len(e) == 1:
                return False
        e_dict = {}
        for elem in el:
            root = elem.pop(0)
            if root not in e_dict:
                e_dict[root] = {'multikey': []}
                #TODO: allow arbitrarily deep nesting of
                # multikey parameters
            k, v = elem
            e_dict[root]['multikey'].append( (k,v) )
        return e_dict

