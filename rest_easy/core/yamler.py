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

import os, sys
major, minor = sys.version_info[0], sys.version_info[1]
if major == 2 and minor >= 7:
    from StringIO import StringIO
elif major == 3:
    from io import StringIO

import yaml
from copy import copy
import pprint


class Yamler(object):
    """
    Handles the loading of our yaml source files.

    We check for import statements at the head of the file, for example:

    'import stddef'

    Then we delete this line and insert the contents of stddef.yaml at the
    beginning of the parent file. If the imported file contains import
    statements itself, the process repeats until all imports have been
    handled. The final list of lines is turned into a StringIO object,
    parsed yaml.load, and returned.

    We do this so as to be able to, for example, separate common
    definitions into a single file for general use -- while a custom
    loader would allow us to import from multiple files, the anchor/alias
    feature will not work across files as each file is parsed separately.
    """
    def __init__(self, path):
        self.path = path
        self.imported = []

    def load(self, source_file, prevbuf=False):
        total = []
        lines = self.get_lines(source_file)
        _lines = copy(lines)
        imports = self.walk_imports(lines, total, _lines)
        docs = []
        if '---\n' in _lines:
            while '---\n' in _lines:
                i = _lines.index('---\n')
                docs.append(_lines[:i])
                _lines = _lines[i+1:]
            docs.append(_lines)
        else:
            docs.append(_lines)

        for num, doc in enumerate(docs):
            if imports:
                total.extend(imports + doc)
            else:
                total.extend(doc)
            if len(docs) > 1 and num < len(docs)-1:
                total.append('---\n')
              
        if prevbuf:
            return total
        else:
            total = StringIO(''.join(total))
            return yaml.load_all(total)

    def walk_imports(self, lines, total, _lines):
        imports = []
        for num, line in enumerate(lines):
            if line == '\n' or line.startswith('#'):
                continue
            tokens = line.split(' ')
            if tokens[0] != 'import':
                break
            else:
                _lines.remove(line)
                basename = tokens[1].rstrip('\n')
                if basename not in self.imported:
                    self.imported.append(basename)
                    import_file = self.path + '/' + basename + '.yaml'
                    i = self.load(import_file, True)
                    if i:
                        imports.extend([basename + ': \n'] + i)
        return imports

    def get_lines(self, source_file):
        with open(source_file, encoding='utf-8', mode='r') as yamlfile:
            lines = yamlfile.readlines()
            yamlfile.close()
        return lines

