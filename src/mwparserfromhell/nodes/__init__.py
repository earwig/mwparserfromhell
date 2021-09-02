# Copyright (C) 2012-2020 Ben Kurtovic <ben.kurtovic@gmail.com>
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

from . import extras
from ._base import Node
from .text import Text
from .argument import Argument
from .comment import Comment
from .external_link import ExternalLink
from .heading import Heading
from .html_entity import HTMLEntity
from .tag import Tag
from .template import Template
from .wikilink import Wikilink

__all__ = [
    "Argument",
    "Comment",
    "ExternalLink",
    "HTMLEntity",
    "Heading",
    "Node",
    "Tag",
    "Template",
    "Text",
    "Wikilink",
]
