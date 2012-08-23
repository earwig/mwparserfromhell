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
This module contains accessory functions that wrap around existing ones to
provide additional functionality.
"""

from __future__ import unicode_literals

from .compat import bytes, str
from .nodes import Node
from .smart_list import SmartList

def parse_anything(value):
    """Return a :py:class:`~.Wikicode` for *value*, allowing multiple types.

    This differs from :py:func:`mwparserfromhell.parse` in that we accept more
    than just a string to be parsed. Unicode objects (strings in py3k), strings
    (bytes in py3k), integers (converted to strings), ``None``, existing
    :py:class:`~.Node` or :py:class:`~.Wikicode` objects, as well as an
    iterable of these types, are supported. This is used to parse input
    on-the-fly by various methods of :py:class:`~.Wikicode` and others like
    :py:class:`~.Template`, such as :py:meth:`wikicode.insert()
    <.Wikicode.insert>` or setting :py:meth:`template.name <.Template.name>`.
    """
    from . import parse
    from .wikicode import Wikicode

    if isinstance(value, Wikicode):
        return value
    elif isinstance(value, Node):
        return Wikicode(SmartList([value]))
    elif isinstance(value, str):
        return parse(value)
    elif isinstance(value, bytes):
        return parse(value.decode("utf8"))
    elif isinstance(value, int):
        return parse(str(value))
    elif value is None:
        return Wikicode(SmartList())
    try:
        nodelist = SmartList()
        for item in value:
            nodelist += parse_anything(item).nodes
    except TypeError:
        error = "Needs string, Node, Wikicode, int, None, or iterable of these, but got {0}: {1}"
        raise ValueError(error.format(type(value).__name__, value))
    return Wikicode(nodelist)
