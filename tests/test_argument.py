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
from mwparserfromhell.nodes import Argument, Text

from ._test_tree_equality import TreeEqualityTestCase, wrap

class TestArgument(TreeEqualityTestCase):
    """Test cases for the Argument node."""

    def test_unicode(self):
        """test Argument.__unicode__()"""
        node = Argument(wrap([Text("foobar")]))
        self.assertEqual("{{{foobar}}}", str(node))
        node2 = Argument(wrap([Text("foo")]), wrap([Text("bar")]))
        self.assertEqual("{{{foo|bar}}}", str(node2))

    def test_strip(self):
        """test Argument.__strip__()"""
        node = Argument(wrap([Text("foobar")]))
        self.assertIs(None, node.__strip__(True, True))
        self.assertIs(None, node.__strip__(True, False))
        self.assertIs(None, node.__strip__(False, True))
        self.assertIs(None, node.__strip__(False, False))

        node2 = Argument(wrap([Text("foo")]), wrap([Text("bar")]))
        self.assertEqual("bar", node2.__strip__(True, True))
        self.assertEqual("bar", node2.__strip__(True, False))
        self.assertEqual("bar", node2.__strip__(False, True))
        self.assertEqual("bar", node2.__strip__(False, False))

    def test_showtree(self):
        """test Argument.__showtree__()"""
        output = []
        getter, marker = object(), object()
        get = lambda code: output.append((getter, code))
        mark = lambda: output.append(marker)
        node1 = Argument(wrap([Text("foobar")]))
        node2 = Argument(wrap([Text("foo")]), wrap([Text("bar")]))
        node1.__showtree__(output.append, get, mark)
        node2.__showtree__(output.append, get, mark)
        valid = [
            "{{{", (getter, node1.name), "}}}", "{{{", (getter, node2.name),
            "    | ", marker, (getter, node2.default), "}}}"]
        self.assertEqual(valid, output)

    def test_name(self):
        """test getter/setter for the name attribute"""
        name = wrap([Text("foobar")])
        node1 = Argument(name)
        node2 = Argument(name, wrap([Text("baz")]))
        self.assertIs(name, node1.name)
        self.assertIs(name, node2.name)
        node1.name = "héhehé"
        node2.name = "héhehé"
        self.assertWikicodeEqual(wrap([Text("héhehé")]), node1.name)
        self.assertWikicodeEqual(wrap([Text("héhehé")]), node2.name)

    def test_default(self):
        """test getter/setter for the default attribute"""
        default = wrap([Text("baz")])
        node1 = Argument(wrap([Text("foobar")]))
        node2 = Argument(wrap([Text("foobar")]), default)
        self.assertIs(None, node1.default)
        self.assertIs(default, node2.default)
        node1.default = "buzz"
        node2.default = None
        self.assertWikicodeEqual(wrap([Text("buzz")]), node1.default)
        self.assertIs(None, node2.default)

if __name__ == "__main__":
    unittest.main(verbosity=2)
