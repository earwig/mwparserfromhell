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

from mwparserfromhell.nodes import Node
from mwparserfromhell.nodes.extras import Attribute

__all__ = ["Tag"]

class Tag(Node):
    TAG_UNKNOWN = 0
    TAG_BOLD = 1
    TAG_ITALIC = 2

    TAG_REF

    TAG_MISC_HTML = 99

    TAGS_VISIBLE = []
    TAGS_INVISIBLE = []

    def __init__(self, type_, tag, contents, attrs=None, showtag=True,
                 self_closing=False, open_padding=0, close_padding=0):
        self._type = type_
        self._tag = tag
        self._contents = contents
        if attrs:
            self._attrs = attrs
        else:
            self._attrs = []
        self._showtag = showtag
        self._self_closing = self_closing
        self._open_padding = open_padding
        self._close_padding = close_padding

    def __unicode__(self):
        if not self.showtag:
            raise NotImplementedError()

        result = "<" + unicode(self.tag)
        if self.attrs:
            result += " " + u" ".join([unicode(attr) for attr in self.attrs])
        if self.self_closing:
            result += " " * self.open_padding + "/>"
        else:
            result += " " * self.open_padding + ">" + unicode(self.contents)
            result += "</" + unicode(self.tag) + " " * self.close_padding + ">"
        return result

    @property
    def type(self):
        return self._type

    @property
    def tag(self):
        return self._tag

    @property
    def contents(self):
        return self._contents

    @property
    def attrs(self):
        return self._attrs

    @property
    def showtag(self):
        return self._showtag

    @property
    def self_closing(self):
        return self._self_closing

    @property
    def open_padding(self):
        return self._open_padding

    @property
    def close_padding(self):
        return self._close_padding
