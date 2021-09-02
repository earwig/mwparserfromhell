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

import html.entities as htmlentities

from ._base import Node

__all__ = ["HTMLEntity"]


class HTMLEntity(Node):
    """Represents an HTML entity, like ``&nbsp;``, either named or unnamed."""

    def __init__(self, value, named=None, hexadecimal=False, hex_char="x"):
        super().__init__()
        self._value = value
        if named is None:  # Try to guess whether or not the entity is named
            try:
                int(value)
                self._named = False
                self._hexadecimal = False
            except ValueError:
                try:
                    int(value, 16)
                    self._named = False
                    self._hexadecimal = True
                except ValueError:
                    self._named = True
                    self._hexadecimal = False
        else:
            self._named = named
            self._hexadecimal = hexadecimal
        self._hex_char = hex_char

    def __str__(self):
        if self.named:
            return "&{};".format(self.value)
        if self.hexadecimal:
            return "&#{}{};".format(self.hex_char, self.value)
        return "&#{};".format(self.value)

    def __strip__(self, **kwargs):
        if kwargs.get("normalize"):
            return self.normalize()
        return self

    @property
    def value(self):
        """The string value of the HTML entity."""
        return self._value

    @property
    def named(self):
        """Whether the entity is a string name for a codepoint or an integer.

        For example, ``&Sigma;``, ``&#931;``, and ``&#x3a3;`` refer to the same
        character, but only the first is "named", while the others are integer
        representations of the codepoint.
        """
        return self._named

    @property
    def hexadecimal(self):
        """If unnamed, this is whether the value is hexadecimal or decimal."""
        return self._hexadecimal

    @property
    def hex_char(self):
        """If the value is hexadecimal, this is the letter denoting that.

        For example, the hex_char of ``"&#x1234;"`` is ``"x"``, whereas the
        hex_char of ``"&#X1234;"`` is ``"X"``. Lowercase and uppercase ``x``
        are the only values supported.
        """
        return self._hex_char

    @value.setter
    def value(self, newval):
        newval = str(newval)
        try:
            int(newval)
        except ValueError:
            try:
                intval = int(newval, 16)
            except ValueError:
                if newval not in htmlentities.entitydefs:
                    raise ValueError(
                        "entity value {!r} is not a valid name".format(newval)
                    ) from None
                self._named = True
                self._hexadecimal = False
            else:
                if intval < 0 or intval > 0x10FFFF:
                    raise ValueError(
                        "entity value 0x{:x} is not in range(0x110000)".format(intval)
                    ) from None
                self._named = False
                self._hexadecimal = True
        else:
            test = int(newval, 16 if self.hexadecimal else 10)
            if test < 0 or test > 0x10FFFF:
                raise ValueError(
                    "entity value {} is not in range(0x110000)".format(test)
                )
            self._named = False
        self._value = newval

    @named.setter
    def named(self, newval):
        newval = bool(newval)
        if newval and self.value not in htmlentities.entitydefs:
            raise ValueError("entity value {!r} is not a valid name".format(self.value))
        if not newval:
            try:
                int(self.value, 16)
            except ValueError as exc:
                raise ValueError(
                    "current entity value {!r} is not a valid "
                    "Unicode codepoint".format(self.value)
                ) from exc
        self._named = newval

    @hexadecimal.setter
    def hexadecimal(self, newval):
        newval = bool(newval)
        if newval and self.named:
            raise ValueError("a named entity cannot be hexadecimal")
        self._hexadecimal = newval

    @hex_char.setter
    def hex_char(self, newval):
        newval = str(newval)
        if newval not in ("x", "X"):
            raise ValueError(newval)
        self._hex_char = newval

    def normalize(self):
        """Return the unicode character represented by the HTML entity."""
        if self.named:
            return chr(htmlentities.name2codepoint[self.value])
        if self.hexadecimal:
            return chr(int(self.value, 16))
        return chr(int(self.value))
