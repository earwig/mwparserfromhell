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

from __future__ import unicode_literals

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mwparserfromhell.compat import str
from mwparserfromhell.nodes import Comment

from ._test_tree_equality import TreeEqualityTestCase

class TestComment(TreeEqualityTestCase):
    """Test cases for the Comment node."""

    def test_unicode(self):
        """test Comment.__unicode__()"""
        node = Comment("foobar")
        self.assertEqual("<!--foobar-->", str(node))

    def test_children(self):
        """test Comment.__children__()"""
        node = Comment("foobar")
        gen = node.__children__()
        self.assertRaises(StopIteration, next, gen)

    def test_strip(self):
        """test Comment.__strip__()"""
        node = Comment("foobar")
        for a in (True, False):
            for b in (True, False):
                self.assertIs(None, node.__strip__(a, b))

    def test_showtree(self):
        """test Comment.__showtree__()"""
        output = []
        node = Comment("foobar")
        node.__showtree__(output.append, None, None)
        self.assertEqual(["<!--foobar-->"], output)

    def test_contents(self):
        """test getter/setter for the contents attribute"""
        node = Comment("foobar")
        self.assertEqual("foobar", node.contents)
        node.contents = "barfoo"
        self.assertEqual("barfoo", node.contents)

if __name__ == "__main__":
    unittest.main(verbosity=2)
