# -*- coding: utf-8 -*-

"""
Implements support for both Python 2 and Python 3 by defining common types in
terms of their Python 2/3 variants. For example, :class:`str` is set to
:class:`unicode` on Python 2 but :class:`str` on Python 3; likewise,
:class:`bytes` is :class:`str` on 2 but :class:`bytes` on 3. These types are
meant to be imported directly from within the parser's modules.
"""

import sys

py26 = (sys.version_info[0] == 2) and (sys.version_info[1] == 6)
py3k = (sys.version_info[0] == 3)
py32 = py3k and (sys.version_info[1] == 2)

if py3k:
    bytes = bytes
    str = str
    range = range
    import html.entities as htmlentities

else:
    bytes = str
    str = unicode
    range = xrange
    import htmlentitydefs as htmlentities

del sys
