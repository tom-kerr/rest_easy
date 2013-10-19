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

class Requirements(object):

    def __init__(self):
        self.required = {'mandatory': [],
                         'all_or_none': [],
                         'at_least_one': [],
                         'either_or': [],
                         'mutually_exclusive': []}

    def add_requirements(self, requirements):
        if isinstance(requirements, Requirements):
            requirements = [i for i in requirements.required.values()]
        if requirements:
            for k, v in self.required.items():
                if k in requirements and requirements[k]:
                    v.append( set([i for i in requirements[k] if i not in v]) )


class EnforceRequirements(object):

    def __init__(self, parameter, requirements, submitted):
        self._parameter_ = parameter
        self._requirements_ = requirements.required
        self._submitted_ = submitted

    def __call__(self):
        if self._requirements_:
            self._check_requirements_()

    def _check_requirements_(self):
        self._check_mandatory_()
        self._check_all_or_none_()
        self._check_at_least_one_()
        self._check_either_or_()
        self._check_mutually_exclusive_()

    def _check_mandatory_(self):
        for num, req_set in enumerate(self._requirements_['mandatory']):
            if req_set.intersection(self._submitted_.required['mandatory'][num]):
                missing = list(self._submitted_.required['mandatory'][num])
                raise Exception(self._parameter_ + ' -- missing "mandatory" fields ' +
                                str(missing))

    def _check_all_or_none_(self):
        for num, req_set in enumerate(self._requirements_['all_or_none']):
            diff = req_set.difference(self._submitted_.required['all_or_none'][num])
            if diff and len(diff) != len(req_set):
                missing = list(self._submitted_.required['all_or_none'][num])
                raise Exception(self._parameter_ + ' -- missing "all_or_none" fields ' +
                                str(missing))

    def _check_at_least_one_(self):
        for num, req_set in enumerate(self._requirements_['at_least_one']):
            diff = req_set.difference(self._submitted_.required['at_least_one'][num])
            if len(diff) < 1:
                missing = list(self._submitted_.required['at_least_one'][num])
                raise Exception(self._parameter_ + ' -- missing "at_least_one" fields ' +
                                str(missing))

    def _check_either_or_(self):
        for num, req_set in enumerate(self._requirements_['either_or']):
            diff = req_set.difference(self._submitted_.required['either_or'][num])
            if len(self._submitted_.required['either_or'][num]) != len(req_set)-1:
                raise Exception(self._parameter_ + ' -- invalid number of "either_or" fields given: ' +
                                str( list(diff)) + ' of ' + str( list(req_set) ) )

    def _check_mutually_exclusive_(self):
        for num, req_set in enumerate(self._requirements_['mutually_exclusive']):
            diff = req_set.difference(self._submitted_.required['mutually_exclusive'][num])
            if (len(self._submitted_.required['mutually_exclusive'][num])
                not in ( len(req_set)-1, len(req_set) )):
                raise Exception(self._parameter_ +
                                ' -- invalid number of "mutually_exclusive" fields given: ' +
                                str( list(diff)) + ' of ' + str( list(req_set) ) )
