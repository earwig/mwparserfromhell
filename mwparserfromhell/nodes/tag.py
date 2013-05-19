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

from . import Node, Text
from ..compat import str
from ..tag_defs import TagDefinitions
from ..utils import parse_anything

__all__ = ["Tag"]

class Tag(TagDefinitions, Node):
    """Represents an HTML-style tag in wikicode, like ``<ref>``."""

    def __init__(self, type_, tag, contents=None, attrs=None, showtag=True,
                 self_closing=False, padding="", closing_tag=None):
        super(Tag, self).__init__()
        self._type = type_
        self._tag = tag
        self._contents = contents
        if attrs:
            self._attrs = attrs
        else:
            self._attrs = []
        self._showtag = showtag
        self._self_closing = self_closing
        self._padding = padding
        if closing_tag:
            self._closing_tag = closing_tag
        else:
            self._closing_tag = tag

    def __unicode__(self):
        if not self.showtag:
            open_, close = self.WIKICODE[self.type]
            if self.self_closing:
                return open_
            else:
                return open_ + str(self.contents) + close

        result = "<" + str(self.tag)
        if self.attributes:
            result += " " + " ".join([str(attr) for attr in self.attributes])
        if self.self_closing:
            result += self.padding + "/>"
        else:
            result += self.padding + ">" + str(self.contents)
            result += "</" + str(self.closing_tag) + ">"
        return result

    def __iternodes__(self, getter):
        yield None, self
        if self.showtag:
            for child in getter(self.tag):
                yield self.tag, child
            for attr in self.attributes:
                for child in getter(attr.name):
                    yield attr.name, child
                if attr.value:
                    for child in getter(attr.value):
                        yield attr.value, child
        if self.contents:
            for child in getter(self.contents):
                yield self.contents, child

    def __strip__(self, normalize, collapse):
        if self.type in self.TAGS_VISIBLE:
            return self.contents.strip_code(normalize, collapse)
        return None

    def __showtree__(self, write, get, mark):
        tagnodes = self.tag.nodes
        if not self.attributes and (len(tagnodes) == 1 and
                                    isinstance(tagnodes[0], Text)):
            write("<" + str(tagnodes[0]) + ">")
        else:
            write("<")
            get(self.tag)
            for attr in self.attributes:
                get(attr.name)
                if not attr.value:
                    continue
                write("    = ")
                mark()
                get(attr.value)
            write(">")
        get(self.contents)
        if len(tagnodes) == 1 and isinstance(tagnodes[0], Text):
            write("</" + str(tagnodes[0]) + ">")
        else:
            write("</")
            get(self.tag)
            write(">")

    @property
    def type(self):
        """The tag type."""
        return self._type

    @property
    def tag(self):
        """The tag itself, as a :py:class:`~.Wikicode` object."""
        return self._tag

    @property
    def contents(self):
        """The contents of the tag, as a :py:class:`~.Wikicode` object."""
        return self._contents

    @property
    def attributes(self):
        """The list of attributes affecting the tag.

        Each attribute is an instance of :py:class:`~.Attribute`.
        """
        return self._attrs

    @property
    def showtag(self):
        """Whether to show the tag itself instead of a wikicode version."""
        return self._showtag

    @property
    def self_closing(self):
        """Whether the tag is self-closing with no content (like ``<br/>``)."""
        return self._self_closing

    @property
    def padding(self):
        """Spacing to insert before the first closing ``>``."""
        return self._padding

    @property
    def closing_tag(self):
        """The closing tag, as a :py:class:`~.Wikicode` object.

        This will usually equal :py:attr:`tag`, unless there is additional
        spacing, comments, or the like.
        """
        return self._closing_tag

    @type.setter
    def type(self, value):
        value = int(value)
        if value not in self.TAGS_ALL:
            raise ValueError(value)
        self._type = value
        for key in self.TRANSLATIONS:
            if self.TRANSLATIONS[key] == value:
                self._tag = self._closing_tag = parse_anything(key)

    @tag.setter
    def tag(self, value):
        self._tag = self._closing_tag = parse_anything(value)
        try:
            self._type = self.TRANSLATIONS[text]
        except KeyError:
            self._type = self.TAG_UNKNOWN

    @contents.setter
    def contents(self, value):
        self._contents = parse_anything(value)

    @showtag.setter
    def showtag(self, value):
        self._showtag = bool(value)

    @self_closing.setter
    def self_closing(self, value):
        self._self_closing = bool(value)

    @padding.setter
    def padding(self, value):
        self._padding = str(value)

    @closing_tag.setter
    def closing_tag(self, value):
        self._closing_tag = parse_anything(value)
