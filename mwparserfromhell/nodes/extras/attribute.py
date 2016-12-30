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

from ...compat import str
from ...string_mixin import StringMixIn
from ...utils import parse_anything

__all__ = ["Attribute"]

class Attribute(StringMixIn):
    """Represents an attribute of an HTML tag.

    This is used by :class:`.Tag` objects. For example, the tag
    ``<ref name="foo">`` contains an Attribute whose name is ``"name"`` and
    whose value is ``"foo"``.
    """

    def __init__(self, name, value=None, quotes='"', pad_first=" ",
                 pad_before_eq="", pad_after_eq="", check_quotes=True):
        super(Attribute, self).__init__()
        if check_quotes and not quotes and self._value_needs_quotes(value):
            raise ValueError("given value {0!r} requires quotes".format(value))
        self._name = name
        self._value = value
        self._quotes = quotes
        self._pad_first = pad_first
        self._pad_before_eq = pad_before_eq
        self._pad_after_eq = pad_after_eq

    def __unicode__(self):
        result = self.pad_first + str(self.name) + self.pad_before_eq
        if self.value is not None:
            result += "=" + self.pad_after_eq
            if self.quotes:
                return result + self.quotes + str(self.value) + self.quotes
            return result + str(self.value)
        return result

    @staticmethod
    def _value_needs_quotes(val):
        """Return the preferred quotes for the given value, or None."""
        if val and any(char.isspace() for char in val):
            return ('"' in val and "'" in val) or ("'" if '"' in val else '"')
        return None

    def _set_padding(self, attr, value):
        """Setter for the value of a padding attribute."""
        if not value:
            setattr(self, attr, "")
        else:
            value = str(value)
            if not value.isspace():
                raise ValueError("padding must be entirely whitespace")
            setattr(self, attr, value)

    @staticmethod
    def coerce_quotes(quotes):
        """Coerce a quote type into an acceptable value, or raise an error."""
        orig, quotes = quotes, str(quotes) if quotes else None
        if quotes not in [None, '"', "'"]:
            raise ValueError("{0!r} is not a valid quote type".format(orig))
        return quotes

    @property
    def name(self):
        """The name of the attribute as a :class:`.Wikicode` object."""
        return self._name

    @property
    def value(self):
        """The value of the attribute as a :class:`.Wikicode` object."""
        return self._value

    @property
    def quotes(self):
        """How to enclose the attribute value. ``"``, ``'``, or ``None``."""
        return self._quotes

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
        if newval is None:
            self._value = None
        else:
            code = parse_anything(newval)
            quotes = self._value_needs_quotes(code)
            if quotes in ['"', "'"] or (quotes is True and not self.quotes):
                self._quotes = quotes
            self._value = code

    @quotes.setter
    def quotes(self, value):
        value = self.coerce_quotes(value)
        if not value and self._value_needs_quotes(self.value):
            raise ValueError("attribute value requires quotes")
        self._quotes = value

    @pad_first.setter
    def pad_first(self, value):
        self._set_padding("_pad_first", value)

    @pad_before_eq.setter
    def pad_before_eq(self, value):
        self._set_padding("_pad_before_eq", value)

    @pad_after_eq.setter
    def pad_after_eq(self, value):
        self._set_padding("_pad_after_eq", value)
