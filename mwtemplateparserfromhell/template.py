# -*- coding: utf-8  -*-
#
# Copyright (C) 2012 by Ben Kurtovic <ben.kurtovic@verizon.net>
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

from collections import OrderedDict

__all__ = ["Template"]

class Template(object):
    def __init__(self, name, params=None):
        self._name = name
        self._params = OrderedDict()
        if params:
            for param in params:
                self._params[param.name] = param

    def __repr__(self):
        paramlist = []
        for name, param in self._params.iteritems():
            paramlist.append('"{0}": "{1}"'.format(name, str(param)))
        params = "{" + ", ".join(paramlist) + "}"
        return "Template(name={0}, params={1})".format(self.name, params)

    def __eq__(self, other):
        if isinstance(other, Template):
            return self.name == other.name and self._params == other._params
        return False

    def __ne__(self, other):
        if isinstance(other, Template):
            return self.name != other.name or self._params != other._params
        return True

    @property
    def name(self):
        return self._name

    @property
    def params(self):
        return self._params.values()

    def get(self, name):
        try:
            return self._params[name]
        except KeyError:  # Try lookup by order in param list
            return self._params.values()[name]
