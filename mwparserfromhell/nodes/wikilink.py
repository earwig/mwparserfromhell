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

__all__ = ["Wikilink"]

class Wikilink(Node):
    """Represents an internal wikilink, like ``[[Foo|Bar]]``."""

    def __init__(self, title, text=None):
        super(Wikilink, self).__init__()
        self._title = title
        self._text = text

    def __unicode__(self):
        if self.text is not None:
            return "[[" + str(self.title) + "|" + str(self.text) + "]]"
        return "[[" + str(self.title) + "]]"

    def __children__(self):
        yield self.title
        if self.text is not None:
            yield self.text

    def __strip__(self, normalize, collapse):
        if self.text is not None:
            return self.text.strip_code(normalize, collapse)
        return self.title.strip_code(normalize, collapse)

    def __showtree__(self, write, get, mark):
        write("[[")
        get(self.title)
        if self.text is not None:
            write("    | ")
            mark()
            get(self.text)
        write("]]")

    @property
    def title(self):
        """The title of the linked page, as a :class:`.Wikicode` object."""
        return self._title

    @property
    def text(self):
        """The text to display (if any), as a :class:`.Wikicode` object."""
        return self._text

    @title.setter
    def title(self, value):
        self._title = parse_anything(value)

    @text.setter
    def text(self, value):
        if value is None:
            self._text = None
        else:
            self._text = parse_anything(value)
