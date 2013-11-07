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

import sys
major, minor = sys.version_info[0], sys.version_info[1]
if major == 2 and minor >= 7:
    from urllib2 import urlopen
elif major == 3:
    from urllib.request import urlopen

import pprint
from copy import copy

from .parser import Parser
from .convert import Convert
import types


def GET(self, return_format='', inherit_from=None,
        pretty_print=False):
    query_string = self.get_query_string(reset=True)
    request = urlopen(query_string)
    results = request.read().decode('utf-8')
    results = self._convert_results_(results, self._output_format_,
                                     return_format, inherit_from)
    if pretty_print:
        pprint.pprint(results)

    return results

def POST(self):
    pass


class HTTPMethods(Parser, Convert):
    """Request methods for querying APIs."""
    def __init__(self, *args, **kwargs):
        Parser.__init__(self)
        for method in ('GET', 'POST'):
            if method in self._http_method_:
                setattr(self, method, types.MethodType(globals()[method], self))

    def get_query_string(self, reset=False):
        string = self._parse_(self._parent_._query_objects_, reset)
        submitted = self._find_in_requirements_()
        self._enforce_requirements_(submitted)
        self._clean_path_string_()
        qstring = self._baseurl_ + self._path_.format(string)
        if reset:
            self._parent_.reset_query()
        return qstring


class QueryTree(object):

    def _add_query_object_(self, parameter, child_kw, function, state, rset=None):
        if not rset:
            rset = []
        if parameter not in rset:
            rset.append(parameter)
        new_state = {parameter: self._get_state_(parameter, None)}
        for k,v in state.items():
            new_state[k] = v
        state = new_state
        if self._is_root_:
            rset.reverse()
            tree = self._query_objects_
            tree = self._make_tree_(rset, tree, state, parameter)
        else:
            self._parent_._add_query_object_(self._name_, child_kw,
                                             function, state, rset)
            return

    def _make_tree_(self, rset, tree, state, root):
        _rset = copy(rset)
        for num, item in enumerate(_rset):

            #ALREADY ENTRY
            if item == root or item in tree:
                rset.remove(item)
                if item in tree:
                    for f in state[item]['zfunctions']:
                        tree[item]['zfunctions'].append(f)

                elif item == root:
                    if 'zfunctions' in tree:
                        tree['zfunctions'].append(state[item])
                        if len(_rset) > 1:
                            for f in tree['zfunctions']:
                                if f['parameter'] == item:
                                    self._make_tree_(rset, f, state, _rset[num+1])
                                    return

                        self._make_tree_(rset, tree, state, item)
                        return
                    else:
                        tree[item] = state[item]

            #NEW ENTRY
            else:
                found = False
                for tree_f in tree[root]['zfunctions']:
                    if isinstance(tree_f, dict):
                        if tree_f['parameter'] == item:
                            if item in rset:
                                rset.remove(item)
                                found = True
                                for f in state[item]['zfunctions']:
                                    tree_f['zfunctions'].append(f)
                                break
                if not found:
                    self._make_tree_(rset, tree[root], state, item)
                    return
        return tree

