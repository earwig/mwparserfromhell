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
This module contains accessory functions for other parts of the library. Parser
users generally won't need stuff from here.
"""

from __future__ import unicode_literals

from .compat import bytes, str
from .nodes import Node
from .smart_list import SmartList

__all__ = ["parse_anything"]

def parse_anything(value, context=0, skip_style_tags=False):
    """Return a :class:`.Wikicode` for *value*, allowing multiple types.

    This differs from :meth:`.Parser.parse` in that we accept more than just a
    string to be parsed. Unicode objects (strings in py3k), strings (bytes in
    py3k), integers (converted to strings), ``None``, existing :class:`.Node`
    or :class:`.Wikicode` objects, as well as an iterable of these types, are
    supported. This is used to parse input on-the-fly by various methods of
    :class:`.Wikicode` and others like :class:`.Template`, such as
    :meth:`wikicode.insert() <.Wikicode.insert>` or setting
    :meth:`template.name <.Template.name>`.

    Additional arguments are passed directly to :meth:`.Parser.parse`.
    """
    from .parser import Parser
    from .wikicode import Wikicode

    if isinstance(value, Wikicode):
        return value
    elif isinstance(value, Node):
        return Wikicode(SmartList([value]))
    elif isinstance(value, str):
        return Parser().parse(value, context, skip_style_tags)
    elif isinstance(value, bytes):
        return Parser().parse(value.decode("utf8"), context, skip_style_tags)
    elif isinstance(value, int):
        return Parser().parse(str(value), context, skip_style_tags)
    elif value is None:
        return Wikicode(SmartList())
    elif hasattr(value, "read"):
        return parse_anything(value.read(), context, skip_style_tags)
    try:
        nodelist = SmartList()
        for item in value:
            nodelist += parse_anything(item, context, skip_style_tags).nodes
        return Wikicode(nodelist)
    except TypeError:
        error = "Needs string, Node, Wikicode, int, None, or iterable of these, but got {0}: {1}"
        raise ValueError(error.format(type(value).__name__, value))
