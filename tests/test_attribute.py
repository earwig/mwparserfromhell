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
from mwparserfromhell.nodes import Template
from mwparserfromhell.nodes.extras import Attribute

from ._test_tree_equality import TreeEqualityTestCase, wrap, wraptext

class TestAttribute(TreeEqualityTestCase):
    """Test cases for the Attribute node extra."""

    def test_unicode(self):
        """test Attribute.__unicode__()"""
        node = Attribute(wraptext("foo"))
        self.assertEqual(" foo", str(node))
        node2 = Attribute(wraptext("foo"), wraptext("bar"))
        self.assertEqual(' foo="bar"', str(node2))
        node3 = Attribute(wraptext("a"), wraptext("b"), '"', "", " ", "   ")
        self.assertEqual('a =   "b"', str(node3))
        node4 = Attribute(wraptext("a"), wraptext("b"), "'", "", " ", "   ")
        self.assertEqual("a =   'b'", str(node4))
        node5 = Attribute(wraptext("a"), wraptext("b"), None, "", " ", "   ")
        self.assertEqual("a =   b", str(node5))
        node6 = Attribute(wraptext("a"), wrap([]), None, " ", "", " ")
        self.assertEqual(" a= ", str(node6))

    def test_name(self):
        """test getter/setter for the name attribute"""
        name = wraptext("id")
        node = Attribute(name, wraptext("bar"))
        self.assertIs(name, node.name)
        node.name = "{{id}}"
        self.assertWikicodeEqual(wrap([Template(wraptext("id"))]), node.name)

    def test_value(self):
        """test getter/setter for the value attribute"""
        value = wraptext("foo")
        node = Attribute(wraptext("id"), value)
        self.assertIs(value, node.value)
        node.value = "{{bar}}"
        self.assertWikicodeEqual(wrap([Template(wraptext("bar"))]), node.value)
        node.value = None
        self.assertIs(None, node.value)
        node2 = Attribute(wraptext("id"), wraptext("foo"), None)
        node2.value = "foo bar baz"
        self.assertWikicodeEqual(wraptext("foo bar baz"), node2.value)
        self.assertEqual('"', node2.quotes)
        node2.value = 'foo "bar" baz'
        self.assertWikicodeEqual(wraptext('foo "bar" baz'), node2.value)
        self.assertEqual("'", node2.quotes)
        node2.value = "foo 'bar' baz"
        self.assertWikicodeEqual(wraptext("foo 'bar' baz"), node2.value)
        self.assertEqual('"', node2.quotes)
        node2.value = "fo\"o 'bar' b\"az"
        self.assertWikicodeEqual(wraptext("fo\"o 'bar' b\"az"), node2.value)
        self.assertEqual('"', node2.quotes)

    def test_quotes(self):
        """test getter/setter for the quotes attribute"""
        node1 = Attribute(wraptext("id"), wraptext("foo"), None)
        node2 = Attribute(wraptext("id"), wraptext("bar"))
        node3 = Attribute(wraptext("id"), wraptext("foo bar baz"))
        self.assertIs(None, node1.quotes)
        self.assertEqual('"', node2.quotes)
        node1.quotes = "'"
        node2.quotes = None
        self.assertEqual("'", node1.quotes)
        self.assertIs(None, node2.quotes)
        self.assertRaises(ValueError, setattr, node1, "quotes", "foobar")
        self.assertRaises(ValueError, setattr, node3, "quotes", None)
        self.assertRaises(ValueError, Attribute, wraptext("id"),
                          wraptext("foo bar baz"), None)

    def test_padding(self):
        """test getter/setter for the padding attributes"""
        for pad in ["pad_first", "pad_before_eq", "pad_after_eq"]:
            node = Attribute(wraptext("id"), wraptext("foo"), **{pad: "\n"})
            self.assertEqual("\n", getattr(node, pad))
            setattr(node, pad, " ")
            self.assertEqual(" ", getattr(node, pad))
            setattr(node, pad, None)
            self.assertEqual("", getattr(node, pad))
            self.assertRaises(ValueError, setattr, node, pad, True)

if __name__ == "__main__":
    unittest.main(verbosity=2)
