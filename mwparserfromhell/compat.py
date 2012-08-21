# -*- coding: utf-8 -*-

"""
Implements support for both Python 2 and Python 3.
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
