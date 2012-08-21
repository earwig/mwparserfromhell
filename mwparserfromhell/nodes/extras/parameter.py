# -*- coding: utf-8  -*-
#
# Copyright (C) 2012 Ben Kurtovic <ben.kurtovic@verizon.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import unicode_literals

from ...string_mixin import StringMixIn
from ...utils import parse_anything
from ...compat import str, bytes

__all__ = ["Parameter"]

class Parameter(StringMixIn):
    def __init__(self, name, value, showkey=True):
        super(Parameter, self).__init__()
        self._name = name
        self._value = value
        self._showkey = showkey

    def __unicode__(self):
        if self.showkey:
            return str(self.name) + "=" + str(self.value)
        return str(self.value)

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    @property
    def showkey(self):
        return self._showkey

    @name.setter
    def name(self, newval):
        self._name = parse_anything(newval)

    @value.setter
    def value(self, newval):
        self._value = parse_anything(newval)

    @showkey.setter
    def showkey(self, newval):
        self._showkey = newval
