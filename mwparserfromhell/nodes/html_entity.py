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

from . import Node
from ..compat import htmlentities, str

__all__ = ["HTMLEntity"]

class HTMLEntity(Node):
    """Represents an HTML entity, like ``&nbsp;``, either named or unnamed."""

    def __init__(self, value, named=None, hexadecimal=False, hex_char="x"):
        super(HTMLEntity, self).__init__()
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

    def __unicode__(self):
        if self.named:
            return "&{0};".format(self.value)
        if self.hexadecimal:
            return "&#{0}{1};".format(self.hex_char, self.value)
        return "&#{0};".format(self.value)

    def __strip__(self, normalize, collapse):
        if normalize:
            return self.normalize()
        return self

    def _unichr(self, value):
        """Implement the builtin unichr() with support for non-BMP code points.

        On wide Python builds, this functions like the normal unichr(). On
        narrow builds, this returns the value's corresponding surrogate pair.
        """
        try:
            return unichr(value)
        except ValueError:
            # Test whether we're on the wide or narrow Python build. Check the
            # length of a non-BMP code point (U+1F64A, SPEAK-NO-EVIL MONKEY):
            if len("\U0001F64A") == 2:
                # Ensure this is within the range we can encode:
                if value > 0x10FFFF:
                    raise ValueError("unichr() arg not in range(0x110000)")
                code = value - 0x10000
                if value < 0:  # Invalid code point
                    raise
                lead = 0xD800 + (code >> 10)
                trail = 0xDC00 + (code % (1 << 10))
                return unichr(lead) + unichr(trail)
            raise

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
        if newval not in htmlentities.entitydefs:
            test = int(self.value, 16)
            if test < 0 or (test > 0x10FFFF and int(self.value) > 0x10FFFF):
                raise ValueError(newval)
        self._value = newval

    @named.setter
    def named(self, newval):
        self._named = bool(newval)

    @hexadecimal.setter
    def hexadecimal(self, newval):
        self._hexadecimal = bool(newval)

    @hex_char.setter
    def hex_char(self, newval):
        self._hex_char = bool(newval)

    def normalize(self):
        """Return the unicode character represented by the HTML entity."""
        if self.named:
            return unichr(htmlentities.name2codepoint[self.value])
        if self.hexadecimal:
            return self._unichr(int(self.value, 16))
        return self._unichr(int(self.value))
