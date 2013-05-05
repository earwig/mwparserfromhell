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

from mwparserfromhell.nodes import (Argument, Comment, Heading, HTMLEntity,
                                    Tag, Template, Text, Wikilink)
from mwparserfromhell.smart_list import SmartList
from mwparserfromhell.wikicode import Wikicode
from mwparserfromhell import parse
from mwparserfromhell.compat import str

from ._test_tree_equality import TreeEqualityTestCase, wrap, wraptext

class TestWikicode(TreeEqualityTestCase):
    """Tests for the Wikicode class, which manages a list of nodes."""

    def test_unicode(self):
        """test Wikicode.__unicode__()"""
        code1 = parse("foobar")
        code2 = parse("Have a {{template}} and a [[page|link]]")
        self.assertEqual("foobar", str(code1))
        self.assertEqual("Have a {{template}} and a [[page|link]]", str(code2))

    def test_nodes(self):
        """test getter/setter for the nodes attribute"""
        code = parse("Have a {{template}}")
        self.assertEqual(["Have a ", "{{template}}"], code.nodes)
        L1 = SmartList([Text("foobar"), Template(wraptext("abc"))])
        L2 = [Text("barfoo"), Template(wraptext("cba"))]
        L3 = "abc{{def}}"
        code.nodes = L1
        self.assertIs(L1, code.nodes)
        code.nodes = L2
        self.assertIs(L2, code.nodes)
        code.nodes = L3
        self.assertEqual(["abc", "{{def}}"], code.nodes)
        self.assertRaises(ValueError, setattr, code, "nodes", object)

    def test_get(self):
        """test Wikicode.get()"""
        code = parse("Have a {{template}} and a [[page|link]]")
        self.assertIs(code.nodes[0], code.get(0))
        self.assertIs(code.nodes[2], code.get(2))
        self.assertRaises(IndexError, code.get, 4)

    def test_set(self):
        """test Wikicode.set()"""
        pass

    def test_index(self):
        """test Wikicode.index()"""
        pass

    def test_insert(self):
        """test Wikicode.insert()"""
        pass

    def test_insert_before(self):
        """test Wikicode.insert_before()"""
        pass

    def test_insert_after(self):
        """test Wikicode.insert_after()"""
        pass

    def test_replace(self):
        """test Wikicode.replace()"""
        pass

    def test_append(self):
        """test Wikicode.append()"""
        pass

    def test_remove(self):
        """test Wikicode.remove()"""
        pass

    def test_filter_family(self):
        """test the Wikicode.i?filter() family of functions"""
        pass

    def test_get_sections(self):
        """test Wikicode.get_sections()"""
        pass

    def test_strip_code(self):
        """test Wikicode.strip_code()"""
        pass

    def test_get_tree(self):
        """test Wikicode.get_tree()"""
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
