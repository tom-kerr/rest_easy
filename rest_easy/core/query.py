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
import sys
import pprint
from copy import copy, deepcopy
from time import sleep
from multiprocessing import Process, Queue
from queue import Empty
import socket
import ssl
import types

from .composer import Composer
from .convert import Convert


class RESTfulAsyncTemplate(object):
    def __init__(self, parent, http_method):
        self.parent = parent
        self.http_method = http_method
        self.queue = Queue()
        self.threads = {}
        self.proc_count = 0
        self.finished = 0

    def __call__(self, header_dict=None, return_format=None, lazy=False, 
                 deferred=False, pretty_print=False, 
                 reset=True, pid=None, queue=None, 
                 timeout=15):
        self.custom_headers = header_dict
        if hasattr(self.parent, '_return_format_'):
            self.return_format = self.parent._return_format_
        else:
            self.return_format = return_format
        self.lazy = lazy
        self.deferred = deferred
        self.pretty_print = pretty_print
        self.reset = reset
        self.timeout = timeout
        self.build_requests()
        self.proc_spawn_loop()
        results = self.collect_results(lazy, deferred)
        self.proc_count = 0
        self.finished = 0
        if queue:
            queue.put((pid, results))
        else:
            return results

    def build_requests(self):
        pass
        
    def proc_spawn_loop(self):
        pass

    def collect_results(self):
        pass


class AsyncSingleResourceMethod(RESTfulAsyncTemplate):
    """Creates a thread for each query tree."""

    def build_requests(self):
        self.requests = []
        qtrees = self.parent._root_getattr_('_query_trees_')[self.parent._name_]
        self.proc_count = len(qtrees)
        for tree in qtrees:
            host, protocol, port, header_fields, path, body = \
              self.parent._get_query_components_(tree)
            http_request = HTTPRequest(self.http_method, host,
                                       protocol, port, path, body)
            if self.custom_headers:
                header_fields.update(self.custom_headers)
            http_request.add_header_fields(header_fields)
            http_request.compose_request()
            self.requests.append(http_request)
     
    def proc_spawn_loop(self):
        for num, request in enumerate(self.requests):
            sock = RESTSocket(request, self.parent._output_format_,
                              num, self.queue)
            self.threads[num] = Process(target=sock, name=num)
            self.threads[num].start()

    def collect_results(self, lazy=False, deferred=False):
        results = [None] * self.proc_count
        slept = 0
        while self.finished < self.proc_count:
            if slept > self.timeout:
                break
            try:
                item = self.queue.get_nowait()
            except Empty:
                sleep(1)
                slept += 1
                continue
            else:
                num, response = item
                self.finished += 1
                message, mime = response
                if message and not isinstance(message, 
                                              (Exception, BaseException)):
                    message = self.parent._convert_results_(message, mime,
                                                            self.return_format, 
                                                            lazy, deferred)
                results[num] = message                

        if self.pretty_print:
            pprint.pprint(message)
        if self.reset:
            self.parent.reset_query()
        self.threads = {}
        return results


class AsyncMultiResourceMethod(RESTfulAsyncTemplate):
    """Creates a thread for each ResourceMethod, which in turn will spawn a
    thread for each of its query trees."""
    def proc_spawn_loop(self):
        for src_name, source  in self.parent.source_objects.items():
            self.threads[src_name] = {}
            root = source._get_root_object_()
            active_methods = root._active_resource_methods_
            self.proc_count += len(active_methods)
            for method in active_methods:
                m_name = method._name_
                try:
                    
                    target = getattr(method, self.http_method)
                except Exception:
                    continue
                
                self.threads[src_name][m_name] = \
                  Process(target=target, name=m_name,
                          args=(self.custom_headers, self.return_format,
                                self.lazy, self.deferred, self.pretty_print,
                                self.reset, (src_name, m_name), self.queue))
                self.threads[src_name][m_name].start()
            if not self.threads[src_name]:
                del self.threads[src_name]

    def collect_results(self, *args, **kwargs):
        results = {}
        slept = 0
        while self.finished < self.proc_count:
            if slept > self.timeout or len(self.threads) == 0:
                break
            try:
                item = self.queue.get_nowait()
            except Empty:
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
        self.threads = {}
        return results


class Redirect(Exception):
    pass


class HTTPRequest(object):
    methods = ('GET', 'POST', 'PUT')
    
    def __init__(self, method, host, protocol, port, path, body):
        if method not in self.methods:
            raise LookupError("No such HTTP request method '" + str(method) + "'.")
        self.message = '{method} {path} {version}\r\n{fields}\r\n\r\n'
        self.host = host
        self.protocol = protocol
        self.port = port
        self.request = {'method': method,
                        'path': path}        
        if method == 'GET':
            self.request['version'] = 'HTTP/1.0'
        else:
            self.request['version'] = 'HTTP/1.1'
        self.header = {'Host': host}
        self.body = b'\n\r'.join(body)
        if method in ('POST'):
            self.header['Content-Type'] = 'application/x-www-form-urlencoded'
                    
    def add_header_fields(self, header_dict):
        for field, value in header_dict.items():
            if isinstance(value, list):
                for val in value:
                    if isinstance(val, dict):
                        num = len(val.keys())
                        n = 1
                        for k, v in val.items():
                            if num > 1:
                                ns = '%02d' % n
                            else:
                                ns = ''
                            f = field + ns + '-' + k
                            self.header[f] = v
                            n += 1
                    else:
                        self.header[field] = val
            elif isinstance(value, (str, int)):
                self.header[field] = str(value)
            else:
                raise ValueError('Bad header value.')

    def compose_request(self):
        missing = [f for f,v in self.header.items() if v is None]
        missing.extend( [f for f,v in self.request.items() if v is None] )
        if missing:
            raise ValueError('Missing essential header fields:' + str(missing))
        fields = '\r\n'.join([k+':'+str(v) for k,v in self.header.items()])
        if not self.body:
            self.body = ''
        self.message = bytes(self.message.format(method=self.request['method'],
                                                 path=self.request['path'],
                                                 version=self.request['version'],
                                                 fields=fields), 'ascii')
        if not isinstance(self.body, bytes):
            self.body = bytes(self.body, 'ascii')
        self.message = self.message + self.body
        
class RESTSocket(object):
    
    def __init__(self, http_request, accepted_formats,
                 pid=None, queue=None, timeout=5):
        self.http_request = http_request
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        if http_request.protocol == 'https':
            self.sock = ssl.wrap_socket(self.sock)
        self.accepted_formats = accepted_formats
        self.pid = pid
        self.queue = queue
        self.timeout = timeout

    def __call__(self):
        self.connect()
        self.send()
        response = self.recv()
        if self.queue:
            self.queue.put((self.pid, response))
        else:
            return response

    def connect(self):
        self.sock.connect((self.http_request.host,
                           self.http_request.port))

    def recv(self):
        response = b''
        while True:
            try:
                data = self.sock.recv(1024)
            except socket.timeout:
                break
            if data:
                response += data
            if not data and not response:
                sleep(1)
            elif not data and response:
                break
        self.sock.close()
        return self.handle_response(response)

    def send(self):
        self.sock.sendall(self.http_request.message)
    
    def handle_response(self, response):
        response = response.decode('utf-8')
        if not response:
            message = ''
            mime = None
        else:
            message = None
            while not message:
                try:
                    header, message = response.split('\r\n\r\n', 1)
                    mime = self.parse_header(header)            
                except (ValueError, IOError) as e:
                    return e, None
                except Redirect as e:
                    match = re.search('Location:.+', str(e))
                    if match:
                        location = match.group(0).split(' ')[1]
                        location = location.split('://')[1]
                        host, path = location.split('/')[0], \
                            '/'+'/'.join(location.split('/')[1:])
                        self.http_request.host = host
                        self.http_request.path = path
                        self.http_request.compose_request()
                        newsock = RESTSocket(self.http_request, self.accepted_formats,
                                             self.pid, self.queue, self.timeout)
                        newsock.connect()
                        newsock.send()
                        message, mime = newsock.recv()
                        newsock.sock.close()
        return message, mime

    def parse_header(self, header):
        mime = re.search('Content-Type:.+', header)
        if not mime:
            raise ValueError('Header missing Content-Type')
        else:
            mime = mime.group(0).split(':')[1]
            mime = mime.split(';')[0].lstrip(' ').rstrip(' ').rstrip('\r')
            if mime not in self.accepted_formats:
                raise ValueError('Server response is of unexpected Content-Type.\n'+
                                 'expecting: '+str(self.accepted_formats)+
                                 '\ngot: '+str(mime))            
            status = header.split('\r\n', 1)[0].split(' ')
            proto, code, msg = status[0], status[1], ' '.join(status[2:])
            if code.startswith('3'):
                raise Redirect(header)
            if code.startswith('4') or code.startswith('5'):
                raise IOError(' '.join((proto, code, msg)))
        return mime


class HTTPMethods(Convert):
    """Request methods for querying APIs."""
    def __init__(self, *args, **kwargs):
        for http_method in ('GET', 'POST', 'PUT'):
            if http_method in self._http_method_:
                setattr(self, http_method,
                        AsyncSingleResourceMethod(self, http_method))
    
    def _get_query_components_(self, tree):
        composer = Composer(self)        
        host = self._super_getattr_('_hostname_')
        protocol = self._super_getattr_('_protocol_')
        port = self._super_getattr_('_port_')
        header, path, body = composer.compose(tree)
        return (host, protocol, port, header, path, body)

    def get_url(self, treenum=None, reset=False):
        if not treenum:
            treenum = self._root_getattr_('_current_tree_')[self._name_]
        qtrees = self._root_getattr_('_query_trees_')
        tree = qtrees[self._name_][treenum]
        #pprint.pprint(qtrees)
        host, protocol, port, header, path, body = \
          self._get_query_components_(tree)
        url = host + ':' + str(port) + path
        if reset:
            self.reset_query()
        return url

    def get_request_strings(self, treenum=None,reset=False):
        if not treenum:
            treenum = self._root_getattr_('_current_tree_')[self._name_]
        qtrees = self._root_getattr_('_query_trees_')
        tree = qtrees[self._name_][treenum]
        host, protocol, port, header, path, body = \
          self._get_query_components_(tree)
        if reset:
            self.reset_query()
        return '\nHost: ' + str(host) + \
            '\nProtocol: ' + str(protocol) + \
            '\nPort: ' + str(port) + \
            '\nHeader: ' + str(header) + \
            '\nPath: ' + str(path) + \
            '\nBody: ' + str(body) + '\n'
        
            


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
                                              function, state, rset, make_global)
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
                            if isinstance(_f, dict):
                                if _f['parameter'] == f._name_:
                                    tree[item]['zfunctions'][n] = state[item]
                                    replaced = True
                            else:
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

