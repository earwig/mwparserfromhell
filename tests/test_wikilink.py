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
from mwparserfromhell.nodes import Text, Wikilink

from ._test_tree_equality import TreeEqualityTestCase, wrap, wraptext

class TestWikilink(TreeEqualityTestCase):
    """Test cases for the Wikilink node."""

    def test_unicode(self):
        """test Wikilink.__unicode__()"""
        node = Wikilink(wraptext("foobar"))
        self.assertEqual("[[foobar]]", str(node))
        node2 = Wikilink(wraptext("foo"), wraptext("bar"))
        self.assertEqual("[[foo|bar]]", str(node2))

    def test_children(self):
        """test Wikilink.__children__()"""
        node1 = Wikilink(wraptext("foobar"))
        node2 = Wikilink(wraptext("foo"), wrap([Text("bar"), Text("baz")]))
        gen1 = node1.__children__()
        gen2 = node2.__children__()
        self.assertEqual(node1.title, next(gen1))
        self.assertEqual(node2.title, next(gen2))
        self.assertEqual(node2.text, next(gen2))
        self.assertRaises(StopIteration, next, gen1)
        self.assertRaises(StopIteration, next, gen2)

    def test_strip(self):
        """test Wikilink.__strip__()"""
        node = Wikilink(wraptext("foobar"))
        node2 = Wikilink(wraptext("foo"), wraptext("bar"))
        for a in (True, False):
            for b in (True, False):
                self.assertEqual("foobar", node.__strip__(a, b))
                self.assertEqual("bar", node2.__strip__(a, b))

    def test_showtree(self):
        """test Wikilink.__showtree__()"""
        output = []
        getter, marker = object(), object()
        get = lambda code: output.append((getter, code))
        mark = lambda: output.append(marker)
        node1 = Wikilink(wraptext("foobar"))
        node2 = Wikilink(wraptext("foo"), wraptext("bar"))
        node1.__showtree__(output.append, get, mark)
        node2.__showtree__(output.append, get, mark)
        valid = [
            "[[", (getter, node1.title), "]]", "[[", (getter, node2.title),
            "    | ", marker, (getter, node2.text), "]]"]
        self.assertEqual(valid, output)

    def test_title(self):
        """test getter/setter for the title attribute"""
        title = wraptext("foobar")
        node1 = Wikilink(title)
        node2 = Wikilink(title, wraptext("baz"))
        self.assertIs(title, node1.title)
        self.assertIs(title, node2.title)
        node1.title = "héhehé"
        node2.title = "héhehé"
        self.assertWikicodeEqual(wraptext("héhehé"), node1.title)
        self.assertWikicodeEqual(wraptext("héhehé"), node2.title)

    def test_text(self):
        """test getter/setter for the text attribute"""
        text = wraptext("baz")
        node1 = Wikilink(wraptext("foobar"))
        node2 = Wikilink(wraptext("foobar"), text)
        self.assertIs(None, node1.text)
        self.assertIs(text, node2.text)
        node1.text = "buzz"
        node2.text = None
        self.assertWikicodeEqual(wraptext("buzz"), node1.text)
        self.assertIs(None, node2.text)

if __name__ == "__main__":
    unittest.main(verbosity=2)
