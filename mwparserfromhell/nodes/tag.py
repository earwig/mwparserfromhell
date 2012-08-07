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

from . import Node, Text

__all__ = ["Tag"]

class Tag(Node):
    TAG_UNKNOWN = 0

    # Basic HTML:
    TAG_ITALIC = 1
    TAG_BOLD = 2
    TAG_UNDERLINE = 3
    TAG_STRIKETHROUGH = 4
    TAG_UNORDERED_LIST = 5
    TAG_ORDERED_LIST = 6
    TAG_DEF_TERM = 7
    TAG_DEF_ITEM = 8
    TAG_BLOCKQUOTE = 9
    TAG_RULE = 10
    TAG_BREAK = 11
    TAG_ABBR = 12
    TAG_PRE = 13
    TAG_MONOSPACE = 14
    TAG_CODE = 15
    TAG_SPAN = 16
    TAG_DIV = 17
    TAG_FONT = 18
    TAG_SMALL = 19
    TAG_BIG = 20
    TAG_CENTER = 21

    # MediaWiki parser hooks:
    TAG_REF = 101
    TAG_GALLERY = 102
    TAG_MATH = 103
    TAG_NOWIKI = 104
    TAG_NOINCLUDE = 105
    TAG_INCLUDEONLY = 106
    TAG_ONLYINCLUDE = 107

    # Additional parser hooks:
    TAG_SYNTAXHIGHLIGHT = 201
    TAG_POEM = 202

    # Lists of tags:
    TAGS_INVISIBLE = set((TAG_REF, TAG_GALLERY, TAG_MATH, TAG_NOINCLUDE))
    TAGS_VISIBLE = set(range(300)) - TAGS_INVISIBLE

    def __init__(self, type_, tag, contents, attrs=None, showtag=True,
                 self_closing=False, open_padding=0, close_padding=0):
        super(Tag, self).__init__(self)
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
            open_, close = self._translate()
            if self.self_closing:
                return open_
            else:
                return open_ + unicode(self.contents) + close

        result = "<" + unicode(self.tag)
        if self.attrs:
            result += " " + u" ".join([unicode(attr) for attr in self.attrs])
        if self.self_closing:
            result += " " * self.open_padding + "/>"
        else:
            result += " " * self.open_padding + ">" + unicode(self.contents)
            result += "</" + unicode(self.tag) + " " * self.close_padding + ">"
        return result

    def __iternodes__(self, getter):
        yield None, self
        if self.showtag:
            for child in getter(self.tag):
                yield self.tag, child
            for attr in self.attrs:
                for child in getter(attr.name):
                    yield attr.name, child
                if attr.value:
                    for child in getter(attr.value):
                        yield attr.value, child
        for child in getter(self.contents):
            yield self.contents, child

    def __strip__(self, normalize, collapse):
        if self.type in self.TAGS_VISIBLE:
            return self.contents.strip_code(normalize, collapse)
        return None

    def __showtree__(self, write, get, mark):
        tagnodes = self.tag.nodes
        if (not self.attrs and len(tagnodes) == 1 and
                                        isinstance(tagnodes[0], Text)):
            write("<" + unicode(tagnodes[0]) + ">")
        else:
            write("<")
            get(self.tag)
            for attr in self.attrs:
                get(attr.name)
                if not attr.value:
                    continue
                write("    = ")
                mark()
                get(attr.value)
            write(">")
        get(self.contents)
        if len(tagnodes) == 1 and isinstance(tagnodes[0], Text):
            write("</" + unicode(tagnodes[0]) + ">")
        else:
            write("</")
            get(self.tag)
            write(">")

    def _translate(self):
        translations = {
            self.TAG_ITALIC: ("''", "''"),
            self.TAG_BOLD: ("'''", "'''"),
            self.TAG_UNORDERED_LIST: ("*", ""),
            self.TAG_ORDERED_LIST: ("#", ""),
            self.TAG_DEF_TERM: (";", ""),
            self.TAG_DEF_ITEM: (":", ""),
            self.TAG_RULE: ("----", ""),
        }
        return translations[self.type]

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
