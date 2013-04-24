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
from mwparserfromhell.nodes import Template, Text
from mwparserfromhell.nodes.extras import Parameter
from mwparserfromhell.smart_list import SmartList
from mwparserfromhell.wikicode import Wikicode
from ._test_tree_equality import TreeEqualityTestCase

wrap = lambda L: Wikicode(SmartList(L))
pgens = lambda k, v: Parameter(wrap([Text(k)]), wrap([Text(v)]), True)
pgenh = lambda k, v: Parameter(wrap([Text(k)]), wrap([Text(v)]), False)

class TestTemplate(TreeEqualityTestCase):
    """Test cases for the Template node."""

    def test_unicode(self):
        """test Template.__unicode__()"""
        node = Template(wrap([Text("foobar")]))
        self.assertEqual("{{foobar}}", str(node))
        node2 = Template(wrap([Text("foo")]),
                         [pgenh("1", "bar"), pgens("abc", "def")])
        self.assertEqual("{{foo|bar|abc=def}}", str(node2))

    def test_strip(self):
        """test Template.__strip__()"""
        node1 = Template(wrap([Text("foobar")]))
        node2 = Template(wrap([Text("foo")]),
                         [pgenh("1", "bar"), pgens("abc", "def")])
        for a in (True, False):
            for b in (True, False):
                self.assertEqual(None, node1.__strip__(a, b))
                self.assertEqual(None, node2.__strip__(a, b))

    def test_showtree(self):
        """test Template.__showtree__()"""
        output = []
        getter, marker = object(), object()
        get = lambda code: output.append((getter, code))
        mark = lambda: output.append(marker)
        node1 = Template(wrap([Text("foobar")]))
        node2 = Template(wrap([Text("foo")]),
                         [pgenh("1", "bar"), pgens("abc", "def")])
        node1.__showtree__(output.append, get, mark)
        node2.__showtree__(output.append, get, mark)
        valid = [
            "{{", (getter, node1.name), "}}", "{{", (getter, node2.name),
            "    | ", marker, (getter, node2.params[0].name), "    = ", marker,
            (getter, node2.params[0].value), "    | ", marker,
            (getter, node2.params[1].name), "    = ", marker,
            (getter, node2.params[1].value), "}}"]
        self.assertEqual(valid, output)

    def test_name(self):
        """test getter/setter for the name attribute"""
        name = wrap([Text("foobar")])
        node1 = Template(name)
        node2 = Template(name, [pgenh("1", "bar")])
        self.assertIs(name, node1.name)
        self.assertIs(name, node2.name)
        node1.name = "asdf"
        node2.name = "téstïng"
        self.assertWikicodeEqual(wrap([Text("asdf")]), node1.name)
        self.assertWikicodeEqual(wrap([Text("téstïng")]), node2.name)

    def test_params(self):
        """test getter for the params attribute"""
        node1 = Template(wrap([Text("foobar")]))
        plist = [pgenh("1", "bar"), pgens("abc", "def")]
        node2 = Template(wrap([Text("foo")]), plist)
        self.assertEqual([], node1.params)
        self.assertIs(plist, node2.params)

    def test_has_param(self):
        """test Template.has_param()"""
        node1 = Template(wrap([Text("foobar")]))
        node2 = Template(wrap([Text("foo")]),
                         [pgenh("1", "bar"), pgens("\nabc ", "def")])
        node3 = Template(wrap([Text("foo")]),
                         [pgenh("1", "a"), pgens("b", "c"), pgens("1", "d")])
        node4 = Template(wrap([Text("foo")]),
                         [pgenh("1", "a"), pgens("b", " ")])
        self.assertFalse(node1.has_param("foobar"))
        self.assertTrue(node2.has_param(1))
        self.assertTrue(node2.has_param("abc"))
        self.assertFalse(node2.has_param("def"))
        self.assertTrue(node3.has_param("1"))
        self.assertTrue(node3.has_param(" b "))
        self.assertFalse(node4.has_param("b"))
        self.assertTrue(node3.has_param("b", False))
        self.assertTrue(node4.has_param("b", False))

    def test_get(self):
        """test Template.get()"""
        node1 = Template(wrap([Text("foobar")]))
        node2p1 = pgenh("1", "bar")
        node2p2 = pgens("abc", "def")
        node2 = Template(wrap([Text("foo")]), [node2p1, node2p2])
        node3p1 = pgens("b", "c")
        node3p2 = pgens("1", "d")
        node3 = Template(wrap([Text("foo")]),
                         [pgenh("1", "a"), node3p1, node3p2])
        node4p1 = pgens(" b", " ")
        node4 = Template(wrap([Text("foo")]), [pgenh("1", "a"), node4p1])
        self.assertRaises(ValueError, node1.get, "foobar")
        self.assertIs(node2p1, node2.get(1))
        self.assertIs(node2p2, node2.get("abc"))
        self.assertRaises(ValueError, node2.get, "def")
        self.assertIs(node3p1, node3.get("b"))
        self.assertIs(node3p2, node3.get("1"))
        self.assertIs(node4p1, node4.get("b "))

    # add

    def test_remove(self):
        """test Template.remove()"""
        node1 = Template(wrap([Text("foobar")]))
        node2 = Template(wrap([Text("foo")]), [pgenh("1", "bar"),
                                               pgens("abc", "def")])
        node3 = Template(wrap([Text("foo")]), [pgenh("1", "bar"),
                                               pgens("abc", "def")])
        node4 = Template(wrap([Text("foo")]), [pgenh("1", "bar"),
                                               pgenh("2", "baz")])
        node5 = Template(wrap([Text("foo")]), [
            pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")])
        node6 = Template(wrap([Text("foo")]), [
            pgens(" a", "b"), pgens("b", "c"), pgens("a ", "d")])
        node7 = Template(wrap([Text("foo")]), [
            pgens("1  ", "a"), pgens("  1", "b"), pgens("2", "c")])
        node8 = Template(wrap([Text("foo")]), [
            pgens("1  ", "a"), pgens("  1", "b"), pgens("2", "c")])
        node9 = Template(wrap([Text("foo")]), [
            pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")])
        node10 = Template(wrap([Text("foo")]), [
            pgens("1  ", "a"), pgenh("1", "b"), pgenh("2", "c")])

        node2.remove("1")
        node2.remove("abc")
        node3.remove(1, keep_field=True)
        node3.remove("abc", keep_field=True)
        node4.remove("1", keep_field=False)
        node5.remove("a", keep_field=False)
        node6.remove("a", keep_field=True)
        node7.remove(1, keep_field=True)
        node8.remove(1, keep_field=False)
        node9.remove(1, keep_field=True)
        node10.remove(1, keep_field=False)

        self.assertRaises(ValueError, node1.remove, 1)
        self.assertRaises(ValueError, node1.remove, "a")
        self.assertRaises(ValueError, node2.remove, "1")
        self.assertEqual("{{foo}}", node2)
        self.assertEqual("{{foo||abc=}}", node3)
        self.assertEqual("{{foo||baz}}", node4)
        self.assertEqual("{{foo|b=c}}", node5)
        self.assertEqual("{{foo| a=|b=c}}", node6)
        self.assertEqual("{{foo|1  =|2=c}}", node7)
        self.assertEqual("{{foo|2=c}}", node8)
        self.assertEqual("{{foo||c}}", node9)
        self.assertEqual("{{foo||c}}", node10)

if __name__ == "__main__":
    unittest.main(verbosity=2)
