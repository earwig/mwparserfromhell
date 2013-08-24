# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2013 Ben Kurtovic <ben.kurtovic@verizon.net>
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
        node3 = Attribute(wraptext("a"), wraptext("b"), True, "", " ", "   ")
        self.assertEqual('a =   "b"', str(node3))
        node3 = Attribute(wraptext("a"), wraptext("b"), False, "", " ", "   ")
        self.assertEqual("a =   b", str(node3))
        node4 = Attribute(wraptext("a"), wrap([]), False, " ", "", " ")
        self.assertEqual(" a= ", str(node4))

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

    def test_quoted(self):
        """test getter/setter for the quoted attribute"""
        node1 = Attribute(wraptext("id"), wraptext("foo"), False)
        node2 = Attribute(wraptext("id"), wraptext("bar"))
        self.assertFalse(node1.quoted)
        self.assertTrue(node2.quoted)
        node1.quoted = True
        node2.quoted = ""
        self.assertTrue(node1.quoted)
        self.assertFalse(node2.quoted)

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
