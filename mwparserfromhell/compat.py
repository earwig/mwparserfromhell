# -*- coding: utf-8 -*-

"""
Implements support for both Python 2 and Python 3 by defining common types in
terms of their Python 2/3 variants. For example, :py:class:`str` is set to
:py:class:`unicode` on Python 2 but :py:class:`str` on Python 3; likewise,
:py:class:`bytes` is :py:class:`str` on 2 but :py:class:`bytes` on 3. These
types are meant to be imported directly from within the parser's modules.
"""

import sys

py3k = sys.version_info.major == 3

if py3k:
    bytes = bytes
    str = str
    basestring = str
    maxsize = sys.maxsize
    import html.entities as htmlentities

else:
    bytes = str
    str = unicode
    basestring = basestring
    maxsize = sys.maxint
    import htmlentitydefs as htmlentities

del sys
