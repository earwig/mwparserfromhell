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

"""Contains data regarding certain HTML tags."""

from __future__ import unicode_literals

__all__ = ["get_wikicode", "is_parsable", "is_visible"]

PARSER_BLACKLIST = [
    # enwiki extensions @ 2013-06-28
    "categorytree", "gallery", "hiero", "imagemap", "inputbox", "math",
    "nowiki", "pre", "score", "section", "source", "syntaxhighlight",
    "templatedata", "timeline"
]

INVISIBLE_TAGS = [
    # enwiki extensions @ 2013-06-28
    "categorytree", "gallery", "imagemap", "inputbox", "math", "score",
    "section", "templatedata", "timeline"
]

# [mediawiki/core.git]/includes/Sanitizer.php @ 87a0aef762
SINGLE_ONLY = ["br", "hr", "meta", "link", "img"]
SINGLE = SINGLE_ONLY + ["li", "dt", "dd"]

WIKICODE = {
    "i": {"open": "''", "close": "''"},
    "b": {"open": "'''", "close": "'''"},
    "ul": {"open": "*"},
    "ol": {"open": "#"},
    "dt": {"open": ";"},
    "dd": {"open": ":"},
    "hr": {"open": "----"},
}

def get_wikicode(tag):
    """Return the appropriate wikicode before and after the given *tag*."""
    data = WIKICODE[tag.lower()]
    return (data.get("open"), data.get("close"))

def is_parsable(tag):
    """Return if the given *tag*'s contents should be passed to the parser."""
    return tag.lower() not in PARSER_BLACKLIST

def is_visible(tag):
    """Return whether or not the given *tag* contains visible text."""
    return tag.lower() not in INVISIBLE_TAGS
