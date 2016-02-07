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
Contains data about certain markup, like HTML tags and external links.

When updating this file, please also update the the C tokenizer version:
- mwparserfromhell/parser/ctokenizer/definitions.c
- mwparserfromhell/parser/ctokenizer/definitions.h
"""

from __future__ import unicode_literals

__all__ = ["get_html_tag", "is_parsable", "is_visible", "is_single",
           "is_single_only", "is_scheme"]

URI_SCHEMES = {
    # [mediawiki/core.git]/includes/DefaultSettings.php @ 374a0ad943
    "http": True, "https": True, "ftp": True, "ftps": True, "ssh": True,
    "sftp": True, "irc": True, "ircs": True, "xmpp": False, "sip": False,
    "sips": False, "gopher": True, "telnet": True, "nntp": True,
    "worldwind": True, "mailto": False, "tel": False, "sms": False,
    "news": False, "svn": True, "git": True, "mms": True, "bitcoin": False,
    "magnet": False, "urn": False, "geo": False
}

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
SINGLE = SINGLE_ONLY + ["li", "dt", "dd", "th", "td", "tr"]

MARKUP_TO_HTML = {
    "#": "li",
    "*": "li",
    ";": "dt",
    ":": "dd"
}

def get_html_tag(markup):
    """Return the HTML tag associated with the given wiki-markup."""
    return MARKUP_TO_HTML[markup]

def is_parsable(tag):
    """Return if the given *tag*'s contents should be passed to the parser."""
    return tag.lower() not in PARSER_BLACKLIST

def is_visible(tag):
    """Return whether or not the given *tag* contains visible text."""
    return tag.lower() not in INVISIBLE_TAGS

def is_single(tag):
    """Return whether or not the given *tag* can exist without a close tag."""
    return tag.lower() in SINGLE

def is_single_only(tag):
    """Return whether or not the given *tag* must exist without a close tag."""
    return tag.lower() in SINGLE_ONLY

def is_scheme(scheme, slashes=True):
    """Return whether *scheme* is valid for external links."""
    scheme = scheme.lower()
    if slashes:
        return scheme in URI_SCHEMES
    return scheme in URI_SCHEMES and not URI_SCHEMES[scheme]
