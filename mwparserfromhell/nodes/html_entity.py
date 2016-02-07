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

from . import Node
from ..compat import htmlentities, py3k, str

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

    if not py3k:
        @staticmethod
        def _unichr(value):
            """Implement builtin unichr() with support for non-BMP code points.

            On wide Python builds, this functions like the normal unichr(). On
            narrow builds, this returns the value's encoded surrogate pair.
            """
            try:
                return unichr(value)
            except ValueError:
                # Test whether we're on the wide or narrow Python build. Check
                # the length of a non-BMP code point
                # (U+1F64A, SPEAK-NO-EVIL MONKEY):
                if len("\U0001F64A") == 1:  # pragma: no cover
                    raise
                # Ensure this is within the range we can encode:
                if value > 0x10FFFF:
                    raise ValueError("unichr() arg not in range(0x110000)")
                code = value - 0x10000
                if value < 0:  # Invalid code point
                    raise
                lead = 0xD800 + (code >> 10)
                trail = 0xDC00 + (code % (1 << 10))
                return unichr(lead) + unichr(trail)

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
                int(newval, 16)
            except ValueError:
                if newval not in htmlentities.entitydefs:
                    raise ValueError("entity value is not a valid name")
                self._named = True
                self._hexadecimal = False
            else:
                if int(newval, 16) < 0 or int(newval, 16) > 0x10FFFF:
                    raise ValueError("entity value is not in range(0x110000)")
                self._named = False
                self._hexadecimal = True
        else:
            test = int(newval, 16 if self.hexadecimal else 10)
            if test < 0 or test > 0x10FFFF:
                raise ValueError("entity value is not in range(0x110000)")
            self._named = False
        self._value = newval

    @named.setter
    def named(self, newval):
        newval = bool(newval)
        if newval and self.value not in htmlentities.entitydefs:
            raise ValueError("entity value is not a valid name")
        if not newval:
            try:
                int(self.value, 16)
            except ValueError:
                err = "current entity value is not a valid Unicode codepoint"
                raise ValueError(err)
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
        chrfunc = chr if py3k else HTMLEntity._unichr
        if self.named:
            return chrfunc(htmlentities.name2codepoint[self.value])
        if self.hexadecimal:
            return chrfunc(int(self.value, 16))
        return chrfunc(int(self.value))
