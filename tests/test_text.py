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
from mwparserfromhell.nodes import Text

class TestText(unittest.TestCase):
    """Test cases for the Text node."""

    def test_unicode(self):
        """test Text.__unicode__()"""
        node = Text("foobar")
        self.assertEqual("foobar", str(node))
        node2 = Text("fóóbar")
        self.assertEqual("fóóbar", str(node2))

    def test_children(self):
        """test Text.__children__()"""
        node = Text("foobar")
        gen = node.__children__()
        self.assertRaises(StopIteration, next, gen)

    def test_strip(self):
        """test Text.__strip__()"""
        node = Text("foobar")
        for a in (True, False):
            for b in (True, False):
                self.assertIs(node, node.__strip__(a, b))

    def test_showtree(self):
        """test Text.__showtree__()"""
        output = []
        node1 = Text("foobar")
        node2 = Text("fóóbar")
        node3 = Text("𐌲𐌿𐍄")
        node1.__showtree__(output.append, None, None)
        node2.__showtree__(output.append, None, None)
        node3.__showtree__(output.append, None, None)
        res = ["foobar", r"f\xf3\xf3bar", "\\U00010332\\U0001033f\\U00010344"]
        self.assertEqual(res, output)

    def test_value(self):
        """test getter/setter for the value attribute"""
        node = Text("foobar")
        self.assertEqual("foobar", node.value)
        self.assertIsInstance(node.value, str)
        node.value = "héhéhé"
        self.assertEqual("héhéhé", node.value)
        self.assertIsInstance(node.value, str)

if __name__ == "__main__":
    unittest.main(verbosity=2)
