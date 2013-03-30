# -*- coding: utf-8 -*-

"""
Serves the same purpose as mwparserfromhell.compat, but only for objects
required by unit tests. This avoids unnecessary imports (like urllib) within
the main library.
"""

from mwparserfromhell.compat import py3k

if py3k:
    range = range
    from io import StringIO
    from urllib.parse import urlencode
    from urllib.request import urlopen

else:
    range = xrange
    from StringIO import StringIO
    from urllib import urlencode, urlopen
