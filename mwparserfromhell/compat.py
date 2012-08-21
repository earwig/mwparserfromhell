# -*- coding: utf-8 -*-

import sys

v = sys.version_info[0]

if v >= 3:
    bytes = bytes
    str = str
    basestring = (str, bytes)
    import html.entities as htmlentitydefs
else:
    bytes = str
    str = unicode
    basestring = basestring
    import htmlentitydefs