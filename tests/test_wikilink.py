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
from mwparserfromhell.nodes import Text, Wikilink

from ._test_tree_equality import TreeEqualityTestCase, wrap

class TestWikilink(TreeEqualityTestCase):
    """Test cases for the Wikilink node."""

    def test_unicode(self):
        """test Wikilink.__unicode__()"""
        node = Wikilink(wrap([Text("foobar")]))
        self.assertEqual("[[foobar]]", str(node))
        node2 = Wikilink(wrap([Text("foo")]), wrap([Text("bar")]))
        self.assertEqual("[[foo|bar]]", str(node2))

    def test_strip(self):
        """test Wikilink.__strip__()"""
        node = Wikilink(wrap([Text("foobar")]))
        self.assertEqual("foobar", node.__strip__(True, True))
        self.assertEqual("foobar", node.__strip__(True, False))
        self.assertEqual("foobar", node.__strip__(False, True))
        self.assertEqual("foobar", node.__strip__(False, False))

        node2 = Wikilink(wrap([Text("foo")]), wrap([Text("bar")]))
        self.assertEqual("bar", node2.__strip__(True, True))
        self.assertEqual("bar", node2.__strip__(True, False))
        self.assertEqual("bar", node2.__strip__(False, True))
        self.assertEqual("bar", node2.__strip__(False, False))

    def test_showtree(self):
        """test Wikilink.__showtree__()"""
        output = []
        getter, marker = object(), object()
        get = lambda code: output.append((getter, code))
        mark = lambda: output.append(marker)
        node1 = Wikilink(wrap([Text("foobar")]))
        node2 = Wikilink(wrap([Text("foo")]), wrap([Text("bar")]))
        node1.__showtree__(output.append, get, mark)
        node2.__showtree__(output.append, get, mark)
        valid = [
            "[[", (getter, node1.title), "]]", "[[", (getter, node2.title),
            "    | ", marker, (getter, node2.text), "]]"]
        self.assertEqual(valid, output)

    def test_title(self):
        """test getter/setter for the title attribute"""
        title = wrap([Text("foobar")])
        node1 = Wikilink(title)
        node2 = Wikilink(title, wrap([Text("baz")]))
        self.assertIs(title, node1.title)
        self.assertIs(title, node2.title)
        node1.title = "héhehé"
        node2.title = "héhehé"
        self.assertWikicodeEqual(wrap([Text("héhehé")]), node1.title)
        self.assertWikicodeEqual(wrap([Text("héhehé")]), node2.title)

    def test_text(self):
        """test getter/setter for the text attribute"""
        text = wrap([Text("baz")])
        node1 = Wikilink(wrap([Text("foobar")]))
        node2 = Wikilink(wrap([Text("foobar")]), text)
        self.assertIs(None, node1.text)
        self.assertIs(text, node2.text)
        node1.text = "buzz"
        node2.text = None
        self.assertWikicodeEqual(wrap([Text("buzz")]), node1.text)
        self.assertIs(None, node2.text)

if __name__ == "__main__":
    unittest.main(verbosity=2)
