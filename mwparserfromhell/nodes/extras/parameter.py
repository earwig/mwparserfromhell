# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2016 Ben Kurtovic <ben.kurtovic@gmail.com>
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
import re

from ...compat import str
from ...string_mixin import StringMixIn
from ...utils import parse_anything

__all__ = ["Parameter"]

class Parameter(StringMixIn):
    """Represents a paramater of a template.

    For example, the template ``{{foo|bar|spam=eggs}}`` contains two
    Parameters: one whose name is ``"1"``, value is ``"bar"``, and ``showkey``
    is ``False``, and one whose name is ``"spam"``, value is ``"eggs"``, and
    ``showkey`` is ``True``.
    """

    def __init__(self, name, value, showkey=True):
        super(Parameter, self).__init__()
        if not showkey and not self.can_hide_key(name):
            raise ValueError("key {0!r} cannot be hidden".format(name))
        self._name = name
        self._value = value
        self._showkey = showkey

    def __unicode__(self):
        if self.showkey:
            return str(self.name) + "=" + str(self.value)
        return str(self.value)

    @staticmethod
    def can_hide_key(key):
        """Return whether or not the given key can be hidden."""
        return re.match(r"[1-9][0-9]*$", str(key).strip())

    @property
    def name(self):
        """The name of the parameter as a :class:`.Wikicode` object."""
        return self._name

    @property
    def value(self):
        """The value of the parameter as a :class:`.Wikicode` object."""
        return self._value

    @property
    def showkey(self):
        """Whether to show the parameter's key (i.e., its "name")."""
        return self._showkey

    @name.setter
    def name(self, newval):
        self._name = parse_anything(newval)

    @value.setter
    def value(self, newval):
        self._value = parse_anything(newval)

    @showkey.setter
    def showkey(self, newval):
        newval = bool(newval)
        if not newval and not self.can_hide_key(self.name):
            raise ValueError("parameter key cannot be hidden")
        self._showkey = newval
