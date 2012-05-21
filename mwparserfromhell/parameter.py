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

from mwparserfromhell.template import Template

__all__ = ["Parameter"]

class Parameter(object):
    def __init__(self, name, value, templates=None):
        self._name = name
        self._value = value
        if templates:
            self._templates = templates
        else:
            self._templates = []

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return self.value

    def __lt__(self, other):
        if isinstance(other, Parameter):
            return self.value < other.value
        return self.value < other

    def __le__(self, other):
        if isinstance(other, Parameter):
            return self.value <= other.value
        return self.value <= other

    def __eq__(self, other):
        if isinstance(other, Parameter):
            return (self.name == other.name and self.value == other.value and
                    self.templates == other.templates)
        return self.value == other

    def __ne__(self, other):
        if isinstance(other, Parameter):
            return (self.name != other.name or self.value != other.value or
                    self.templates != other.templates)
        return self.value != other

    def __gt__(self, other):
        if isinstance(other, Parameter):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other):
        if isinstance(other, Parameter):
            return self.value >= other.value
        return self.value >= other

    def __nonzero__(self):
        return bool(self.value)

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        for char in self.value:
            yield char

    def __getitem__(self, key):
        return self.value[key]

    def __contains__(self, item):
        return item in self.value or item in self.templates

    def __add__(self, other):
        if isinstance(other, Parameter):
            return Parameter(self.name, self.value + other.value,
                             self.templates + other.templates)
        if isinstance(other, Template):
            return Parameter(self.name, self.value + other.render(),
                             self.templates + [other])
        return self.value + other

    def __radd__(self, other):
        if isinstance(other, Template):
            return Template(other.name, other.params + [self])
        return other + self.value

    def __iadd__(self, other):
        if isinstance(other, Parameter):
            self.value += other.value
            self.templates += other.templates
        elif isinstance(other, Template):
            self.value += other.render()
            self.templates.append(other)
        else:
            self.value += other
        return self

    def __mul__(self, other):
        return Parameter(self.name, self.value * other, self.templates * other)

    def __rmul__(self, other):
        return Parameter(self.name, other * self.value, other * self.templates)

    def __imul__(self, other):
        self.value *= other
        self.templates *= other
        return self

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value

    @property
    def templates(self):
        return self._templates
