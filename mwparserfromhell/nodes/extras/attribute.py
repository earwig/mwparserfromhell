# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2013 Ben Kurtovic <ben.kurtovic@verizon.net>
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

from ...compat import str
from ...string_mixin import StringMixIn
from ...utils import parse_anything

__all__ = ["Attribute"]

class Attribute(StringMixIn):
    """Represents an attribute of an HTML tag.

    This is used by :py:class:`~.Tag` objects. For example, the tag
    ``<ref name="foo">`` contains an Attribute whose name is ``"name"`` and
    whose value is ``"foo"``.
    """

    def __init__(self, name, value=None, quoted=True, pad_first=" ",
                 pad_before_eq="", pad_after_eq=""):
        super(Attribute, self).__init__()
        self._name = name
        self._value = value
        self._quoted = quoted
        self._pad_first = pad_first
        self._pad_before_eq = pad_before_eq
        self._pad_after_eq = pad_after_eq

    def __unicode__(self):
        result = self.pad_first + str(self.name) + self.pad_before_eq
        if self.value is not None:
            result += "=" + self.pad_after_eq
            if self.quoted:
                return result + '"' + str(self.value) + '"'
            return result + str(self.value)
        return result

    def _set_padding(self, attr, value):
        """Setter for the value of a padding attribute."""
        if not value:
            setattr(self, attr, "")
        else:
            value = str(value)
            if not value.isspace():
                raise ValueError("padding must be entirely whitespace")
            setattr(self, attr, value)

    @property
    def name(self):
        """The name of the attribute as a :py:class:`~.Wikicode` object."""
        return self._name

    @property
    def value(self):
        """The value of the attribute as a :py:class:`~.Wikicode` object."""
        return self._value

    @property
    def quoted(self):
        """Whether the attribute's value is quoted with double quotes."""
        return self._quoted

    @property
    def pad_first(self):
        """Spacing to insert right before the attribute."""
        return self._pad_first

    @property
    def pad_before_eq(self):
        """Spacing to insert right before the equal sign."""
        return self._pad_before_eq

    @property
    def pad_after_eq(self):
        """Spacing to insert right after the equal sign."""
        return self._pad_after_eq

    @name.setter
    def name(self, value):
        self._name = parse_anything(value)

    @value.setter
    def value(self, newval):
        self._value = None if newval is None else parse_anything(newval)

    @quoted.setter
    def quoted(self, value):
        self._quoted = bool(value)

    @pad_first.setter
    def pad_first(self, value):
        self._set_padding("_pad_first", value)

    @pad_before_eq.setter
    def pad_before_eq(self, value):
        self._set_padding("_pad_before_eq", value)

    @pad_after_eq.setter
    def pad_after_eq(self, value):
        self._set_padding("_pad_after_eq", value)
