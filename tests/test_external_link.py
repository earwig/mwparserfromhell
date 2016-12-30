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
from mwparserfromhell.nodes import ExternalLink, Text

from ._test_tree_equality import TreeEqualityTestCase, wrap, wraptext

class TestExternalLink(TreeEqualityTestCase):
    """Test cases for the ExternalLink node."""

    def test_unicode(self):
        """test ExternalLink.__unicode__()"""
        node = ExternalLink(wraptext("http://example.com/"), brackets=False)
        self.assertEqual("http://example.com/", str(node))
        node2 = ExternalLink(wraptext("http://example.com/"))
        self.assertEqual("[http://example.com/]", str(node2))
        node3 = ExternalLink(wraptext("http://example.com/"), wrap([]))
        self.assertEqual("[http://example.com/ ]", str(node3))
        node4 = ExternalLink(wraptext("http://example.com/"),
                             wraptext("Example Web Page"))
        self.assertEqual("[http://example.com/ Example Web Page]", str(node4))

    def test_children(self):
        """test ExternalLink.__children__()"""
        node1 = ExternalLink(wraptext("http://example.com/"), brackets=False)
        node2 = ExternalLink(wraptext("http://example.com/"),
                             wrap([Text("Example"), Text("Page")]))
        gen1 = node1.__children__()
        gen2 = node2.__children__()
        self.assertEqual(node1.url, next(gen1))
        self.assertEqual(node2.url, next(gen2))
        self.assertEqual(node2.title, next(gen2))
        self.assertRaises(StopIteration, next, gen1)
        self.assertRaises(StopIteration, next, gen2)

    def test_strip(self):
        """test ExternalLink.__strip__()"""
        node1 = ExternalLink(wraptext("http://example.com"), brackets=False)
        node2 = ExternalLink(wraptext("http://example.com"))
        node3 = ExternalLink(wraptext("http://example.com"), wrap([]))
        node4 = ExternalLink(wraptext("http://example.com"), wraptext("Link"))
        for a in (True, False):
            for b in (True, False):
                self.assertEqual("http://example.com", node1.__strip__(a, b))
                self.assertEqual(None, node2.__strip__(a, b))
                self.assertEqual(None, node3.__strip__(a, b))
                self.assertEqual("Link", node4.__strip__(a, b))

    def test_showtree(self):
        """test ExternalLink.__showtree__()"""
        output = []
        getter, marker = object(), object()
        get = lambda code: output.append((getter, code))
        mark = lambda: output.append(marker)
        node1 = ExternalLink(wraptext("http://example.com"), brackets=False)
        node2 = ExternalLink(wraptext("http://example.com"), wraptext("Link"))
        node1.__showtree__(output.append, get, mark)
        node2.__showtree__(output.append, get, mark)
        valid = [
            (getter, node1.url), "[", (getter, node2.url),
            (getter, node2.title), "]"]
        self.assertEqual(valid, output)

    def test_url(self):
        """test getter/setter for the url attribute"""
        url = wraptext("http://example.com/")
        node1 = ExternalLink(url, brackets=False)
        node2 = ExternalLink(url, wraptext("Example"))
        self.assertIs(url, node1.url)
        self.assertIs(url, node2.url)
        node1.url = "mailto:héhehé@spam.com"
        node2.url = "mailto:héhehé@spam.com"
        self.assertWikicodeEqual(wraptext("mailto:héhehé@spam.com"), node1.url)
        self.assertWikicodeEqual(wraptext("mailto:héhehé@spam.com"), node2.url)

    def test_title(self):
        """test getter/setter for the title attribute"""
        title = wraptext("Example!")
        node1 = ExternalLink(wraptext("http://example.com/"), brackets=False)
        node2 = ExternalLink(wraptext("http://example.com/"), title)
        self.assertIs(None, node1.title)
        self.assertIs(title, node2.title)
        node2.title = None
        self.assertIs(None, node2.title)
        node2.title = "My Website"
        self.assertWikicodeEqual(wraptext("My Website"), node2.title)

    def test_brackets(self):
        """test getter/setter for the brackets attribute"""
        node1 = ExternalLink(wraptext("http://example.com/"), brackets=False)
        node2 = ExternalLink(wraptext("http://example.com/"), wraptext("Link"))
        self.assertFalse(node1.brackets)
        self.assertTrue(node2.brackets)
        node1.brackets = True
        node2.brackets = False
        self.assertTrue(node1.brackets)
        self.assertFalse(node2.brackets)
        self.assertEqual("[http://example.com/]", str(node1))
        self.assertEqual("http://example.com/", str(node2))

if __name__ == "__main__":
    unittest.main(verbosity=2)
