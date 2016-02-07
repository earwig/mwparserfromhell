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
from mwparserfromhell.nodes import HTMLEntity

from ._test_tree_equality import TreeEqualityTestCase, wrap

class TestHTMLEntity(TreeEqualityTestCase):
    """Test cases for the HTMLEntity node."""

    def test_unicode(self):
        """test HTMLEntity.__unicode__()"""
        node1 = HTMLEntity("nbsp", named=True, hexadecimal=False)
        node2 = HTMLEntity("107", named=False, hexadecimal=False)
        node3 = HTMLEntity("6b", named=False, hexadecimal=True)
        node4 = HTMLEntity("6C", named=False, hexadecimal=True, hex_char="X")
        self.assertEqual("&nbsp;", str(node1))
        self.assertEqual("&#107;", str(node2))
        self.assertEqual("&#x6b;", str(node3))
        self.assertEqual("&#X6C;", str(node4))

    def test_children(self):
        """test HTMLEntity.__children__()"""
        node = HTMLEntity("nbsp", named=True, hexadecimal=False)
        gen = node.__children__()
        self.assertRaises(StopIteration, next, gen)

    def test_strip(self):
        """test HTMLEntity.__strip__()"""
        node1 = HTMLEntity("nbsp", named=True, hexadecimal=False)
        node2 = HTMLEntity("107", named=False, hexadecimal=False)
        node3 = HTMLEntity("e9", named=False, hexadecimal=True)
        for a in (True, False):
            self.assertEqual("\xa0", node1.__strip__(True, a))
            self.assertEqual("&nbsp;", node1.__strip__(False, a))
            self.assertEqual("k", node2.__strip__(True, a))
            self.assertEqual("&#107;", node2.__strip__(False, a))
            self.assertEqual("é", node3.__strip__(True, a))
            self.assertEqual("&#xe9;", node3.__strip__(False, a))

    def test_showtree(self):
        """test HTMLEntity.__showtree__()"""
        output = []
        node1 = HTMLEntity("nbsp", named=True, hexadecimal=False)
        node2 = HTMLEntity("107", named=False, hexadecimal=False)
        node3 = HTMLEntity("e9", named=False, hexadecimal=True)
        node1.__showtree__(output.append, None, None)
        node2.__showtree__(output.append, None, None)
        node3.__showtree__(output.append, None, None)
        res = ["&nbsp;", "&#107;", "&#xe9;"]
        self.assertEqual(res, output)

    def test_value(self):
        """test getter/setter for the value attribute"""
        node1 = HTMLEntity("nbsp")
        node2 = HTMLEntity("107")
        node3 = HTMLEntity("e9")
        self.assertEqual("nbsp", node1.value)
        self.assertEqual("107", node2.value)
        self.assertEqual("e9", node3.value)

        node1.value = "ffa4"
        node2.value = 72
        node3.value = "Sigma"
        self.assertEqual("ffa4", node1.value)
        self.assertFalse(node1.named)
        self.assertTrue(node1.hexadecimal)
        self.assertEqual("72", node2.value)
        self.assertFalse(node2.named)
        self.assertFalse(node2.hexadecimal)
        self.assertEqual("Sigma", node3.value)
        self.assertTrue(node3.named)
        self.assertFalse(node3.hexadecimal)

        node1.value = "10FFFF"
        node2.value = 110000
        node2.value = 1114111
        self.assertRaises(ValueError, setattr, node3, "value", "")
        self.assertRaises(ValueError, setattr, node3, "value", "foobar")
        self.assertRaises(ValueError, setattr, node3, "value", True)
        self.assertRaises(ValueError, setattr, node3, "value", -1)
        self.assertRaises(ValueError, setattr, node1, "value", 110000)
        self.assertRaises(ValueError, setattr, node1, "value", "1114112")
        self.assertRaises(ValueError, setattr, node1, "value", "12FFFF")

    def test_named(self):
        """test getter/setter for the named attribute"""
        node1 = HTMLEntity("nbsp")
        node2 = HTMLEntity("107")
        node3 = HTMLEntity("e9")
        self.assertTrue(node1.named)
        self.assertFalse(node2.named)
        self.assertFalse(node3.named)
        node1.named = 1
        node2.named = 0
        node3.named = 0
        self.assertTrue(node1.named)
        self.assertFalse(node2.named)
        self.assertFalse(node3.named)
        self.assertRaises(ValueError, setattr, node1, "named", False)
        self.assertRaises(ValueError, setattr, node2, "named", True)
        self.assertRaises(ValueError, setattr, node3, "named", True)

    def test_hexadecimal(self):
        """test getter/setter for the hexadecimal attribute"""
        node1 = HTMLEntity("nbsp")
        node2 = HTMLEntity("107")
        node3 = HTMLEntity("e9")
        self.assertFalse(node1.hexadecimal)
        self.assertFalse(node2.hexadecimal)
        self.assertTrue(node3.hexadecimal)
        node1.hexadecimal = False
        node2.hexadecimal = True
        node3.hexadecimal = False
        self.assertFalse(node1.hexadecimal)
        self.assertTrue(node2.hexadecimal)
        self.assertFalse(node3.hexadecimal)
        self.assertRaises(ValueError, setattr, node1, "hexadecimal", True)

    def test_hex_char(self):
        """test getter/setter for the hex_char attribute"""
        node1 = HTMLEntity("e9")
        node2 = HTMLEntity("e9", hex_char="X")
        self.assertEqual("x", node1.hex_char)
        self.assertEqual("X", node2.hex_char)
        node1.hex_char = "X"
        node2.hex_char = "x"
        self.assertEqual("X", node1.hex_char)
        self.assertEqual("x", node2.hex_char)
        self.assertRaises(ValueError, setattr, node1, "hex_char", 123)
        self.assertRaises(ValueError, setattr, node1, "hex_char", "foobar")
        self.assertRaises(ValueError, setattr, node1, "hex_char", True)

    def test_normalize(self):
        """test getter/setter for the normalize attribute"""
        node1 = HTMLEntity("nbsp")
        node2 = HTMLEntity("107")
        node3 = HTMLEntity("e9")
        node4 = HTMLEntity("1f648")
        node5 = HTMLEntity("-2")
        node6 = HTMLEntity("110000", named=False, hexadecimal=True)
        self.assertEqual("\xa0", node1.normalize())
        self.assertEqual("k", node2.normalize())
        self.assertEqual("é", node3.normalize())
        self.assertEqual("\U0001F648", node4.normalize())
        self.assertRaises(ValueError, node5.normalize)
        self.assertRaises(ValueError, node6.normalize)

if __name__ == "__main__":
    unittest.main(verbosity=2)
