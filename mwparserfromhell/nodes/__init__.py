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

"""
This package contains :class:`.Wikicode` "nodes", which represent a single unit
of wikitext, such as a Template, an HTML tag, a Heading, or plain text. The
node "tree" is far from flat, as most types can contain additional
:class:`.Wikicode` types within them - and with that, more nodes. For example,
the name of a :class:`.Template` is a :class:`.Wikicode` object that can
contain text or more templates.
"""

from __future__ import unicode_literals

from ..compat import str
from ..string_mixin import StringMixIn

__all__ = ["Node", "Text", "Argument", "Heading", "HTMLEntity", "Tag",
           "Template"]

class Node(StringMixIn):
    """Represents the base Node type, demonstrating the methods to override.

    :meth:`__unicode__` must be overridden. It should return a ``unicode`` or
    (``str`` in py3k) representation of the node. If the node contains
    :class:`.Wikicode` objects inside of it, :meth:`__children__` should be a
    generator that iterates over them. If the node is printable
    (shown when the page is rendered), :meth:`__strip__` should return its
    printable version, stripping out any formatting marks. It does not have to
    return a string, but something that can be converted to a string with
    ``str()``. Finally, :meth:`__showtree__` can be overridden to build a
    nice tree representation of the node, if desired, for
    :meth:`~.Wikicode.get_tree`.
    """
    def __unicode__(self):
        raise NotImplementedError()

    def __children__(self):
        return
        yield  # pragma: no cover (this is a generator that yields nothing)

    def __strip__(self, normalize, collapse):
        return None

    def __showtree__(self, write, get, mark):
        write(str(self))


from . import extras
from .text import Text
from .argument import Argument
from .comment import Comment
from .external_link import ExternalLink
from .heading import Heading
from .html_entity import HTMLEntity
from .tag import Tag
from .template import Template
from .wikilink import Wikilink
