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

__all__ = ["ExternalLink"]

class ExternalLink(Node):
    """Represents an external link, like ``[http://example.com/ Example]``."""

    def __init__(self, url, title=None, brackets=True):
        super(ExternalLink, self).__init__()
        self._url = url
        self._title = title
        self._brackets = brackets

    def __unicode__(self):
        if self.brackets:
            if self.title is not None:
                return "[" + str(self.url) + " " + str(self.title) + "]"
            return "[" + str(self.url) + "]"
        return str(self.url)

    def __children__(self):
        yield self.url
        if self.title is not None:
            yield self.title

    def __strip__(self, normalize, collapse):
        if self.brackets:
            if self.title:
                return self.title.strip_code(normalize, collapse)
            return None
        return self.url.strip_code(normalize, collapse)

    def __showtree__(self, write, get, mark):
        if self.brackets:
            write("[")
        get(self.url)
        if self.title is not None:
            get(self.title)
        if self.brackets:
            write("]")

    @property
    def url(self):
        """The URL of the link target, as a :class:`.Wikicode` object."""
        return self._url

    @property
    def title(self):
        """The link title (if given), as a :class:`.Wikicode` object."""
        return self._title

    @property
    def brackets(self):
        """Whether to enclose the URL in brackets or display it straight."""
        return self._brackets

    @url.setter
    def url(self, value):
        from ..parser import contexts
        self._url = parse_anything(value, contexts.EXT_LINK_URI)

    @title.setter
    def title(self, value):
        self._title = None if value is None else parse_anything(value)

    @brackets.setter
    def brackets(self, value):
        self._brackets = bool(value)
