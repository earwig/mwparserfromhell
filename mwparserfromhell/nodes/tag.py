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
from ..tag_defs import get_wiki_markup, is_visible
from ..utils import parse_anything

__all__ = ["Tag"]

class Tag(Node):
    """Represents an HTML-style tag in wikicode, like ``<ref>``."""

    def __init__(self, tag, contents=None, attrs=None, wiki_markup=False,
                 self_closing=False, invalid=False, implicit=False, padding="",
                 closing_tag=None):
        super(Tag, self).__init__()
        self._tag = tag
        if contents is None and not self_closing:
            self._contents = parse_anything("")
        else:
            self._contents = contents
        self._attrs = attrs if attrs else []
        self._wiki_markup = wiki_markup
        self._self_closing = self_closing
        self._invalid = invalid
        self._implicit = implicit
        self._padding = padding
        if closing_tag:
            self._closing_tag = closing_tag
        else:
            self._closing_tag = tag

    def __unicode__(self):
        if self.wiki_markup:
            open_, close = get_wiki_markup(self.tag)
            if self.self_closing:
                return open_
            else:
                return open_ + str(self.contents) + close

        result = ("</" if self.invalid else "<") + str(self.tag)
        if self.attributes:
            result += "".join([str(attr) for attr in self.attributes])
        if self.self_closing:
            result += self.padding + (">" if self.implicit else "/>")
        else:
            result += self.padding + ">" + str(self.contents)
            result += "</" + str(self.closing_tag) + ">"
        return result

    def __iternodes__(self, getter):
        yield None, self
        if not self.wiki_markup:
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
        if not self.self_closing and not self.wiki_markup and self.closing_tag:
            for child in getter(self.closing_tag):
                yield self.closing_tag, child

    def __strip__(self, normalize, collapse):
        if is_visible(self.tag):
            return self.contents.strip_code(normalize, collapse)
        return None

    def __showtree__(self, write, get, mark):
        write("</" if self.invalid else "<")
        get(self.tag)
        for attr in self.attributes:
            get(attr.name)
            if not attr.value:
                continue
            write("    = ")
            mark()
            get(attr.value)
        if self.self_closing:
            write(">" if self.implicit else "/>")
        else:
            write(">")
            get(self.contents)
            write("</")
            get(self.closing_tag)
            write(">")

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
    def wiki_markup(self):
        """Whether to show the wiki version of a tag instead of the HTML."""
        return self._wiki_markup

    @property
    def self_closing(self):
        """Whether the tag is self-closing with no content (like ``<br/>``)."""
        return self._self_closing

    @property
    def invalid(self):
        """Whether the tag starts with a backslash after the opening bracket.

        This makes the tag look like a lone close tag. It is technically
        invalid and is only parsable Wikicode when the tag itself is
        single-only, like ``<br>`` and ``<img>``. See
        :py:func:`.tag_defs.is_single_only`.
        """
        return self._invalid

    @property
    def implicit(self):
        """Whether the tag is implicitly self-closing, with no ending slash.

        This is only possible for specific "single" tags like ``<br>`` and
        ``<li>``. See :py:func:`.tag_defs.is_single`. This field only has an
        effect if :py:attr:`self_closing` is also ``True``.
        """
        return self._implicit

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

    @tag.setter
    def tag(self, value):
        self._tag = self._closing_tag = parse_anything(value)

    @contents.setter
    def contents(self, value):
        self._contents = parse_anything(value)

    @wiki_markup.setter
    def wiki_markup(self, value):
        self._wiki_markup = bool(value)

    @self_closing.setter
    def self_closing(self, value):
        self._self_closing = bool(value)

    @invalid.setter
    def invalid(self, value):
        self._invalid = bool(value)

    @implicit.setter
    def implicit(self, value):
        self._implicit = bool(value)

    @padding.setter
    def padding(self, value):
        if not value:
            self._padding = ""
        else:
            value = str(value)
            if not value.isspace():
                raise ValueError("padding must be entirely whitespace")
            self._padding = value

    @closing_tag.setter
    def closing_tag(self, value):
        self._closing_tag = parse_anything(value)
