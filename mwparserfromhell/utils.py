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

import mwparserfromhell
from mwparserfromhell.nodes import Node

def parse_anything(value):
    wikicode = mwparserfromhell.wikicode.Wikicode
    if isinstance(value, wikicode):
        return value
    if isinstance(value, Node):
        return wikicode([value])
    if isinstance(value, basestring):
        return mwparserfromhell.parse(value)
    if isinstance(value, int):
        return mwparserfromhell.parse(unicode(value))
    if value is None:
        return wikicode([])
    try:
        nodelist = []
        for item in value:
            nodelist += parse_anything(item).nodes
    except TypeError:
        error = "Needs string, Node, Wikicode, int, None, or iterable of these, but got {0}: {1}"
        raise ValueError(error.format(type(value), value))
    return wikicode(nodelist)
