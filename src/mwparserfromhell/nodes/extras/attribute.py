# Copyright (C) 2012-2020 Ben Kurtovic <ben.kurtovic@gmail.com>
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


from ...string_mixin import StringMixIn
from ...utils import parse_anything

__all__ = ["Attribute"]


class Attribute(StringMixIn):
    """Represents an attribute of an HTML tag.

    This is used by :class:`.Tag` objects. For example, the tag
    ``<ref name="foo">`` contains an Attribute whose name is ``"name"`` and
    whose value is ``"foo"``.
    """

    def __init__(
        self,
        name,
        value=None,
        quotes='"',
        pad_first=" ",
        pad_before_eq="",
        pad_after_eq="",
    ):
        super().__init__()
        self.name = name
        self._quotes = None
        self.value = value
        self.quotes = quotes
        self.pad_first = pad_first
        self.pad_before_eq = pad_before_eq
        self.pad_after_eq = pad_after_eq

    def __str__(self):
        result = self.pad_first + str(self.name) + self.pad_before_eq
        if self.value is not None:
            result += "=" + self.pad_after_eq
            if self.quotes:
                return result + self.quotes + str(self.value) + self.quotes
            return result + str(self.value)
        return result

    @staticmethod
    def _value_needs_quotes(val):
        """Return valid quotes for the given value, or None if unneeded."""
        if not val:
            return None
        val = "".join(str(node) for node in val.filter_text(recursive=False))
        if not any(char.isspace() for char in val):
            return None
        if "'" in val and '"' not in val:
            return '"'
        if '"' in val and "'" not in val:
            return "'"
        return "\"'"  # Either acceptable, " preferred over '

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
            raise ValueError("{!r} is not a valid quote type".format(orig))
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
            if quotes and (not self.quotes or self.quotes not in quotes):
                self._quotes = quotes[0]
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
