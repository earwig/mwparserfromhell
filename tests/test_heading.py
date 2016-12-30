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
from mwparserfromhell.nodes import Heading, Text

from ._test_tree_equality import TreeEqualityTestCase, wrap, wraptext

class TestHeading(TreeEqualityTestCase):
    """Test cases for the Heading node."""

    def test_unicode(self):
        """test Heading.__unicode__()"""
        node = Heading(wraptext("foobar"), 2)
        self.assertEqual("==foobar==", str(node))
        node2 = Heading(wraptext(" zzz "), 5)
        self.assertEqual("===== zzz =====", str(node2))

    def test_children(self):
        """test Heading.__children__()"""
        node = Heading(wrap([Text("foo"), Text("bar")]), 3)
        gen = node.__children__()
        self.assertEqual(node.title, next(gen))
        self.assertRaises(StopIteration, next, gen)

    def test_strip(self):
        """test Heading.__strip__()"""
        node = Heading(wraptext("foobar"), 3)
        for a in (True, False):
            for b in (True, False):
                self.assertEqual("foobar", node.__strip__(a, b))

    def test_showtree(self):
        """test Heading.__showtree__()"""
        output = []
        getter = object()
        get = lambda code: output.append((getter, code))
        node1 = Heading(wraptext("foobar"), 3)
        node2 = Heading(wraptext(" baz "), 4)
        node1.__showtree__(output.append, get, None)
        node2.__showtree__(output.append, get, None)
        valid = ["===", (getter, node1.title), "===",
                 "====", (getter, node2.title), "===="]
        self.assertEqual(valid, output)

    def test_title(self):
        """test getter/setter for the title attribute"""
        title = wraptext("foobar")
        node = Heading(title, 3)
        self.assertIs(title, node.title)
        node.title = "héhehé"
        self.assertWikicodeEqual(wraptext("héhehé"), node.title)

    def test_level(self):
        """test getter/setter for the level attribute"""
        node = Heading(wraptext("foobar"), 3)
        self.assertEqual(3, node.level)
        node.level = 5
        self.assertEqual(5, node.level)
        self.assertRaises(ValueError, setattr, node, "level", 0)
        self.assertRaises(ValueError, setattr, node, "level", 7)
        self.assertRaises(ValueError, setattr, node, "level", "abc")
        self.assertRaises(ValueError, setattr, node, "level", False)

if __name__ == "__main__":
    unittest.main(verbosity=2)
