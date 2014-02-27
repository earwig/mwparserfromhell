# -*- coding: UTF-8 -*-


"""
Discover tests using ``unittest2`.

It appears the default distutils test suite doesn't play nice with
``setUpClass`` thereby making some tests fail. Using ``unittest2``
to load tests seems to work around that issue.

http://stackoverflow.com/a/17004409/753501
"""


# Standard:
import os.path

# External:
import unittest2


def additional_tests():
    return unittest2.defaultTestLoader.discover(os.path.dirname(__file__))
