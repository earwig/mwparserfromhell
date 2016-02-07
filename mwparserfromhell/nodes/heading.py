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
from ..compat import str
from ..utils import parse_anything

__all__ = ["Heading"]

class Heading(Node):
    """Represents a section heading in wikicode, like ``== Foo ==``."""

    def __init__(self, title, level):
        super(Heading, self).__init__()
        self._title = title
        self._level = level

    def __unicode__(self):
        return ("=" * self.level) + str(self.title) + ("=" * self.level)

    def __children__(self):
        yield self.title

    def __strip__(self, normalize, collapse):
        return self.title.strip_code(normalize, collapse)

    def __showtree__(self, write, get, mark):
        write("=" * self.level)
        get(self.title)
        write("=" * self.level)

    @property
    def title(self):
        """The title of the heading, as a :class:`.Wikicode` object."""
        return self._title

    @property
    def level(self):
        """The heading level, as an integer between 1 and 6, inclusive."""
        return self._level

    @title.setter
    def title(self, value):
        self._title = parse_anything(value)

    @level.setter
    def level(self, value):
        value = int(value)
        if value < 1 or value > 6:
            raise ValueError(value)
        self._level = value
