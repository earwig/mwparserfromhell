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

class TagDefinitions(object):
    """Contains numerical definitions for valid HTML (and wikicode) tags.

    Base class for :py:class:`~.Tag` objects.
    """

    TAG_UNKNOWN = 0

    # Basic HTML:
    TAG_ITALIC = 1
    TAG_BOLD = 2
    TAG_UNDERLINE = 3
    TAG_STRIKETHROUGH = 4
    TAG_UNORDERED_LIST = 5
    TAG_ORDERED_LIST = 6
    TAG_DEF_TERM = 7
    TAG_DEF_ITEM = 8
    TAG_BLOCKQUOTE = 9
    TAG_RULE = 10
    TAG_BREAK = 11
    TAG_ABBR = 12
    TAG_PRE = 13
    TAG_MONOSPACE = 14
    TAG_CODE = 15
    TAG_SPAN = 16
    TAG_DIV = 17
    TAG_FONT = 18
    TAG_SMALL = 19
    TAG_BIG = 20
    TAG_CENTER = 21

    # MediaWiki parser hooks:
    TAG_REF = 101
    TAG_GALLERY = 102
    TAG_MATH = 103
    TAG_NOWIKI = 104
    TAG_NOINCLUDE = 105
    TAG_INCLUDEONLY = 106
    TAG_ONLYINCLUDE = 107

    # Additional parser hooks:
    TAG_SYNTAXHIGHLIGHT = 201
    TAG_POEM = 202

    # Lists of tags:
    TAGS_ALL = set(range(300))
    TAGS_INVISIBLE = {TAG_REF, TAG_GALLERY, TAG_MATH, TAG_NOINCLUDE}
    TAGS_VISIBLE = TAGS_ALL - TAGS_INVISIBLE

    TRANSLATIONS = {
        "i": TAG_ITALIC,
        "em": TAG_ITALIC,
        "b": TAG_BOLD,
        "strong": TAG_BOLD,
        "u": TAG_UNDERLINE,
        "s": TAG_STRIKETHROUGH,
        "ul": TAG_UNORDERED_LIST,
        "ol": TAG_ORDERED_LIST,
        "dt": TAG_DEF_TERM,
        "dd": TAG_DEF_ITEM,
        "blockquote": TAG_BLOCKQUOTE,
        "hl": TAG_RULE,
        "br": TAG_BREAK,
        "abbr": TAG_ABBR,
        "pre": TAG_PRE,
        "tt": TAG_MONOSPACE,
        "code": TAG_CODE,
        "span": TAG_SPAN,
        "div": TAG_DIV,
        "font": TAG_FONT,
        "small": TAG_SMALL,
        "big": TAG_BIG,
        "center": TAG_CENTER,
        "ref": TAG_REF,
        "gallery": TAG_GALLERY,
        "math": TAG_MATH,
        "nowiki": TAG_NOWIKI,
        "noinclude": TAG_NOINCLUDE,
        "includeonly": TAG_INCLUDEONLY,
        "onlyinclude": TAG_ONLYINCLUDE,
        "syntaxhighlight": TAG_SYNTAXHIGHLIGHT,
        "source": TAG_SYNTAXHIGHLIGHT,
        "poem": TAG_POEM,
    }

    WIKICODE = {
        TAG_ITALIC: ("''", "''"),
        TAG_BOLD: ("'''", "'''"),
        TAG_UNORDERED_LIST: ("*", ""),
        TAG_ORDERED_LIST: ("#", ""),
        TAG_DEF_TERM: (";", ""),
        TAG_DEF_ITEM: (":", ""),
        TAG_RULE: ("----", ""),
    }
