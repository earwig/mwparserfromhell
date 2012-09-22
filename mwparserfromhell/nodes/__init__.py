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

"""
This package contains :py:class:`~.Wikicode` "nodes", which represent a single
unit of wikitext, such as a Template, an HTML tag, a Heading, or plain text.
The node "tree" is far from flat, as most types can contain additional
:py:class:`~.Wikicode` types within them - and with that, more nodes. For
example, the name of a :py:class:`~.Template` is a :py:class:`~.Wikicode`
object that can contain text or more templates.
"""

from __future__ import unicode_literals

from ..compat import str
from ..string_mixin import StringMixIn

__all__ = ["Node", "Text", "Argument", "Heading", "HTMLEntity", "Tag",
           "Template"]

class Node(StringMixIn):
    """Represents the base Node type, demonstrating the methods to override.

    :py:meth:`__unicode__` must be overridden. It should return a ``unicode``
    or (``str`` in py3k) representation of the node. If the node contains
    :py:class:`~.Wikicode` objects inside of it, :py:meth:`__iternodes__`
    should be overridden to yield tuples of (``wikicode``,
    ``node_in_wikicode``) for each node in each wikicode, as well as the node
    itself (``None``, ``self``). If the node is printable, :py:meth:`__strip__`
    should be overridden to return the printable version of the node - it does
    not have to be a string, but something that can be converted to a string
    with ``str()``. Finally, :py:meth:`__showtree__` can be overridden to build
    a nice tree representation of the node, if desired, for
    :py:meth:`~.Wikicode.get_tree`.
    """
    def __unicode__(self):
        raise NotImplementedError()

    def __iternodes__(self, getter):
        yield None, self

    def __strip__(self, normalize, collapse):
        return None

    def __showtree__(self, write, get, mark):
        write(str(self))


from . import extras
from .text import Text
from .argument import Argument
from .comment import Comment
from .heading import Heading
from .html_entity import HTMLEntity
from .tag import Tag
from .template import Template
from .wikilink import Wikilink
