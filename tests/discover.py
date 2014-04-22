# -*- coding: utf-8 -*-

"""
Discover tests using ``unittest2` for Python 2.6.

It appears the default distutils test suite doesn't play nice with
``setUpClass`` thereby making some tests fail. Using ``unittest2`` to load
tests seems to work around that issue.

http://stackoverflow.com/a/17004409/753501
"""

import os.path

from mwparserfromhell.compat import py26

if py26:
    import unittest2 as unittest
else:
    import unittest

def additional_tests():
    project_root = os.path.split(os.path.dirname(__file__))[0]
    return unittest.defaultTestLoader.discover(project_root)
