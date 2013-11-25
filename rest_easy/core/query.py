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
import pprint
from copy import copy, deepcopy
from time import sleep
from multiprocessing import Process, Queue
import socket
import ssl

from .parser import Parser
from .convert import Convert
import types


class TemplateGET(object):
    def __init__(self, parent):
        self.parent = parent
        self.q = Queue()
        self.threads = {}
        self.proc_count = 0
        self.finished = 0

    def proc_spawn_loop(self):
        pass

    def collect_results(self):
        pass

    def __call__(self, return_format='', inherit_from=None,
                 pretty_print=False, reset=True,
                 pid=None, queue=None, timeout=30):
        self.return_format = return_format
        self.inherit_from =  inherit_from
        self.pretty_print = pretty_print
        self.reset = reset
        self.timeout = timeout
        self.proc_spawn_loop()
        results =  self.collect_results(timeout)
        if queue:
            queue.put((pid, results))
        else:
            return results


class GET_QueryTrees(TemplateGET):
    """Creates a thread for each branch of a query tree."""
    def proc_spawn_loop(self):
        qtrees = self.parent._root_getattr_('_query_trees_')[self.parent._name_]
        self.proc_count = len(qtrees)
        for num, tree in enumerate(qtrees):
            host, protocol, port, path = self.parent._get_query_components_(tree)
            self.threads[num] = Process(target=connect, name=num,
                                        args=(num, host, protocol, port, path,
                                              self.q, self.timeout))
            self.threads[num].start()

    def collect_results(self, timeout):
        results = [None] * self.proc_count
        slept = 0
        while self.finished < self.proc_count:
            if slept > timeout:
                break
            try:
                item = self.q.get_nowait()
            except:
                sleep(1)
                slept += 1
                continue
            else:
                num, response = item
                self.finished += 1
                del self.threads[num]
            response = response.decode('utf-8')
            if not response:
                message = ''
            else:
                header, message = response.split('\r\n\r\n', 1)
                status = header.split('\r\n', 1)[0]
                if not 'OK' in status:
                    message = Exception(status)
                else:
                    message = self.parent._convert_results_(message, \
                                        self.parent._output_format_,
                                        self.return_format, self.inherit_from)
                results[num] = message
        if self.pretty_print:
            pprint.pprint(message)
        if self.reset:
            self.parent.reset_query()
        return results


class GET_ResourceMethods(TemplateGET):
    """Creates a thread for each ResourceMethod, which in turn will spawn a
    thread for each branch of its query tree."""
    def proc_spawn_loop(self):
        for src_name, source  in self.parent.source_objects.items():
            self.threads[src_name] = {}
            root = source._get_root_object_()
            active_methods = root._active_resource_methods_
            self.proc_count += len(active_methods)
            for method in active_methods:
                m_name = method._name_
                self.threads[src_name][m_name] = \
                  Process(target=method.GET, name=m_name,
                          args=(self.return_format, self.inherit_from,
                                self.pretty_print, self.reset, (src_name, m_name), self.q))
                self.threads[src_name][m_name].start()

    def collect_results(self, timeout):
        results = {}
        slept = 0
        while self.finished < self.proc_count:
            if slept > timeout:
                break
            try:
                item = self.q.get_nowait()
            except:
                sleep(1)
                slept += 1
                continue
            else:
                pid, responses = item
                src_name, m_name = pid
                self.finished += 1
                if not src_name in results:
                    results[src_name] = {}
                results[src_name][m_name] = responses
        return results



def connect(conn_id, host, protocol, port, path, queue, timeout=10):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if protocol == 'https':
        sock = ssl.wrap_socket(sock)
    sock.connect((host, port))
    msg = bytes("GET {0} HTTP/1.0\r\nHost: {1}\r\n\r\n".\
            format(path, host), 'ascii')
    sock.sendall(msg)
    response = b''
    slept = 0
    while True:
        if slept > timeout:
            response = None
            break
        data = sock.recv(1024)
        if data:
            response += data
        elif not data and not response and slept <= timeout:
            slept += 1
            sleep(1)
        else:
            break
    sock.close()
    queue.put((conn_id, response))


class HTTPMethods(Convert):
    """Request methods for querying APIs."""
    def __init__(self, *args, **kwargs):
        for method in ('GET', 'POST'):
            if method in self._http_method_:
                setattr(self, 'GET', GET_QueryTrees(self))

    def _get_query_components_(self, tree):
        parser = Parser(self)
        string = parser._parse_(tree)
        host = self._super_getattr_('_hostname_')
        protocol = self._super_getattr_('_protocol_')
        port = self._super_getattr_('_port_')
        path = self._path_.format(string)
        return (host, protocol, port, path)

    def get_query_string(self, treenum=None, reset=False):
        if not treenum:
            treenum = self._root_getattr_('_current_tree_')[self._name_]
        qtrees = self._root_getattr_('_query_trees_')
        tree = qtrees[self._name_][treenum]
        #pprint.pprint(qtrees)
        host, protocol, port, path = self._get_query_components_(tree)
        qstring = host + ':' + str(port) + path
        if reset:
            self.reset_query()
        return qstring


class QueryTree(object):

    def _add_to_query_tree_(self, r_method, parent_kw, child_kw,
                            function, state, rset=None,
                            make_global=False):
        if not rset:
            rset = []
        if parent_kw not in rset:
            rset.append(parent_kw)
        new_state = {parent_kw: self._get_state_(parent_kw, None)}
        for k,v in state.items():
            new_state[k] = v
        state = new_state
        if self._is_root_:
            rset.reverse()
            if make_global:
                for active_method in self._active_resource_methods_:
                    method = active_method._name_
                    ctree = self._current_tree_[method]
                    tree = self._query_trees_[method][ctree]
                    tree = self._create_entry_(copy(rset), tree,
                                               state, parent_kw)
                gtree = self._global_tree_
                gtree = self._create_entry_(copy(rset), gtree,
                                            state, parent_kw)
            else:
                ctree = self._current_tree_[r_method]
                tree = self._query_trees_[r_method]
                self._create_entry_(copy(rset), tree[ctree],
                                           state, parent_kw)
                if self._global_tree_:
                    for k, v in self._global_tree_.items():
                        for t in tree:
                            if k not in t:
                                t[k] = v

        else:
            self._parent_._add_to_query_tree_(r_method, self._name_, child_kw,
                                              function, state, rset)
            return

    #holy shit, refactor this unintelligible nonsense.
    def _create_entry_(self, rset, tree, state, root):
        _rset = copy(rset)
        for num, item in enumerate(_rset):
            if item == root or item in tree:
                rset.remove(item)
                if item in tree:
                    replaced = False
                    for f in state[item]['zfunctions']:
                        for n, _f in enumerate(tree[item]['zfunctions']):
                            if (_f._name_ == f._name_ and
                                _f._parent_ == f._parent_):
                                tree[item]['zfunctions'][n] = f
                                replaced = True
                        if not replaced:
                            tree[item]['zfunctions'].append(f)

                elif item == root:
                    if 'zfunctions' in tree:
                        tree['zfunctions'].append(state[item])
                        if len(_rset) > 1:
                            for f in tree['zfunctions']:
                                if f['parameter'] == item:
                                    self._create_entry_(rset, f, state, _rset[num+1])
                                    return

                        self._create_entry_(rset, tree, state, item)
                        return
                    else:
                        tree[item] = state[item]

            else:
                found = False
                for tree_f in tree[root]['zfunctions']:
                    if isinstance(tree_f, dict):
                        if tree_f['parameter'] == item:
                            if item in rset:
                                rset.remove(item)
                                found = True
                                if state[item]['zfunctions']:
                                    replaced = False
                                    for f in state[item]['zfunctions']:
                                        for n, _f in enumerate(tree_f['zfunctions']):
                                            if (_f._name_ == f._name_ and
                                                _f._parent_ == f._parent_):
                                                tree_f['zfunctions'][n] = f
                                                replaced = True
                                        if not replaced:
                                            tree_f['zfunctions'].append(f)
                                else:
                                    self._create_entry_(rset, {item: tree_f}, state, item)
                                break
                if not found and rset:
                    self._create_entry_(rset, tree[root], state, item)
                    return
        return tree

